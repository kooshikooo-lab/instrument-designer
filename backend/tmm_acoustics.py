"""
Transfer Matrix Method (TMM) acoustics — phase-based resonance model.

Faithfully ported from chalumier's ResonanceMath.kt and Instrument.kt
(Mark C. Chu-Carroll, Paul Francis Harrison — Apache 2.0 license).

This module computes resonant frequencies of wind instruments using the
phase-based TMM approach from demakein. It supports:
  - Open-open pipes (flutes, recorders)
  - Closed-open pipes (clarinets, saxophones)
  - Bore profile steps (area discontinuities)
  - Tone holes (open and closed, with length corrections)
  - End flange corrections

The key advantage over impulse-response methods (OpenWInD) is speed:
a single resonance evaluation takes microseconds instead of milliseconds,
making gradient-based optimization with many design variables feasible.

Usage:
    from backend.tmm_acoustics import TMMInstrument

    inst = TMMInstrument(
        inner_positions=[0, 100, 200, ...],
        inner_diameters=[14.5, 14.5, 15.0, ...],
        outer_diameters=[22.0, 22.0, 24.0, ...],
        hole_positions=[60, 100, ...],
        hole_diameters=[7.0, 7.0, ...],
        hole_lengths=[3.75, 3.75, ...],
        closed_top=False,
    )
    freq = inst.find_resonance(wavelength_near=800.0, fingerings=[...])
"""

import math
import numpy as np
from typing import List, Tuple, Optional

# Matches chalumier's SPEED_OF_SOUND exactly (cm/s)
SPEED_OF_SOUND = 346100.0

FOUR_PI = 4.0 * math.pi


# ============================================================================
# Core TMM math (from ResonanceMath.kt)
# ============================================================================

def circle_area(diameter: float) -> float:
    """Cross-sectional area of a circle from diameter."""
    r = diameter / 2.0
    return math.pi * r * r


def tanner(phase: float) -> float:
    """Convert phase to tangent domain."""
    return math.tan(phase * math.pi)


def untanner(x: float) -> float:
    """Convert from tangent domain back to phase."""
    return math.atan(x) / math.pi


def pipe_reply_phase(phase_end: float, length_on_wavelength: float) -> float:
    """Advance phase through a pipe segment of given length/wavelength."""
    return phase_end + length_on_wavelength * 2.0


def junction2_reply_phase(a0: float, a1: float, p1: float) -> float:
    """
    Phase reply for pipe 0 of a two-pipe junction.
    a0 = area of pipe 0, a1 = area of pipe 1, p1 = relative phase reply of pipe 1.
    """
    shift = math.floor(p1 + 0.5)
    return untanner(a1 / a0 * tanner(p1 - shift)) + shift


def junction3_reply_phase(a0: float, a1: float, a2: float, p1: float, p2: float) -> float:
    """
    Phase reply for pipe 0 of a three-pipe junction.
    Used for tone holes: a0 = bore area, a1 = bore area, a2 = hole area.
    """
    shift1 = math.floor(p1 + 0.5)
    shift2 = math.floor(p2 + 0.5)
    return untanner(
        a1 / a0 * tanner(p1 - shift1) + a2 / a0 * tanner(p2 - shift2)
    ) + shift1 + shift2


def end_flange_length_correction(outer_diameter: float, inner_diameter: float) -> float:
    """
    End correction for a pipe with a flange (bell).
    From Nederveen / chalumier.
    """
    a = inner_diameter / 2.0
    if a <= 0:
        return 0.0
    w = (outer_diameter - inner_diameter) / 2.0
    base = max(0.01, 0.42 + w / a)
    return a * (0.821 - 0.13 * base ** (-0.54))


def hole_length_correction(hole_diameter: float, bore_diameter: float, closed: bool) -> float:
    """
    Length correction for a tone hole.
    Per Nederveen p.63-64. Returns 0 for closed holes.
    """
    if closed:
        return 0.0
    outer_correction = 0.7
    inner_correction = 1.3 - 0.9 * hole_diameter / bore_diameter
    a = hole_diameter / 2.0
    return a * (inner_correction + outer_correction)


# ============================================================================
# Profile — stepped bore representation
# ============================================================================

class Profile:
    """
    A stepped bore profile: arrays of (position, low_diameter, high_diameter).
    low = diameter at bottom of segment, high = diameter at top of segment.
    For cylindrical bores, low == high at each position.
    """

    def __init__(self, pos: List[float], low: List[float], high: Optional[List[float]] = None):
        self.pos = list(pos)
        self.low = list(low)
        self.high = list(high) if high is not None else list(low)

    def at(self, location: float, use_high: bool = False) -> float:
        """Interpolate diameter at a given position along the bore."""
        if location <= self.pos[0]:
            return self.low[0]
        if location >= self.pos[-1]:
            return self.high[-1]
        # Binary search for the segment
        lo, hi = 0, len(self.pos) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.pos[mid] <= location:
                lo = mid
            else:
                hi = mid
        # Linear interpolation within segment
        t = (location - self.pos[lo]) / (self.pos[hi] - self.pos[lo])
        return (1.0 - t) * self.high[lo] + t * self.low[hi]

    def as_stepped(self, max_step: float) -> 'Profile':
        """
        Create a smooth stepped version of the profile.
        Replaces hard diameter changes with a sequence of smaller steps.
        """
        new_pos = []
        for i in range(len(self.pos) - 1):
            new_pos.append(self.pos[i])
            lower_top_pos = self.pos[i]
            lower_top_diam = self.high[i]
            higher_bot_pos = self.pos[i + 1]
            higher_bot_diam = self.low[i + 1]
            n_steps = int(abs(higher_bot_diam - lower_top_diam) / max_step) + 1
            if n_steps <= 1:
                continue
            for s in range(1, n_steps):
                frac = s / n_steps
                new_pos.append((higher_bot_pos - lower_top_pos) * frac + lower_top_pos)
        new_pos.append(self.pos[-1])
        # Compute diameters at midpoints
        new_diams = []
        for i in range(len(new_pos) - 1):
            mid = 0.5 * (new_pos[i] + new_pos[i + 1])
            new_diams.append(self.at(mid, use_high=False))
        new_low = [new_diams[0]] + new_diams
        new_high = new_diams + [new_diams[-1]]
        return Profile(new_pos, new_low, new_high)


# ============================================================================
# Hole state
# ============================================================================

class Hole:
    """Represents a tone hole state."""
    OPEN = 'open'
    CLOSED = 'closed'


# ============================================================================
# TMM Instrument — resonance computation
# ============================================================================

class TMMInstrument:
    """
    Phase-based TMM instrument model.

    Computes resonant wavelengths by walking phase through the bore:
    1. Start at open end: phase = 0.5
    2. Walk through pipe segments: phase += 2 * length / wavelength
    3. At bore steps: phase = junction2_reply_phase(...)
    4. At tone holes: phase = junction3_reply_phase(...)
    5. At open end: phase += 0.5
    6. Resonance when phase is integer (phase % 1.0 == 0)
    """

    def __init__(
        self,
        inner_positions: List[float],
        inner_diameters: List[float],
        outer_diameters: List[float],
        hole_positions: List[float],
        hole_diameters: List[float],
        hole_lengths: List[float],
        closed_top: bool = False,
        cone_step: float = 0.5,
        speed_of_sound: float = SPEED_OF_SOUND,
    ):
        self.closed_top = closed_top
        self.cone_step = cone_step
        self.speed_of_sound = speed_of_sound

        # Build inner and outer profiles
        self.inner = Profile(inner_positions, inner_diameters)
        self.outer = Profile(inner_positions, outer_diameters)

        self.hole_positions = list(hole_positions)
        self.hole_diameters = list(hole_diameters)
        self.hole_lengths = list(hole_lengths)
        self.n_holes = len(hole_positions)

        # Build stepped inner profile
        self.stepped_inner = self.inner.as_stepped(cone_step)
        self.length = self.stepped_inner.pos[-1]

        # Precompute action chain for phase-based resonance
        self._prepare_phase()

    def _prepare_phase(self):
        """
        Build the action chain for phase-based resonance computation.
        This is the Python equivalent of Instrument.preparePhase() in chalumier.
        """
        # Collect all events: bore steps, holes, and the end
        events = []  # (position, descriptor, index)

        # Bore steps (diameter changes in the stepped profile)
        for i, pos in enumerate(self.stepped_inner.pos):
            if 0.0 < pos < self.length:
                events.append((pos, 'step', i))

        # Tone holes
        for i, pos in enumerate(self.hole_positions):
            events.append((pos, 'hole', i))

        # The end of the instrument
        events.append((self.length, 'end', 0))

        # Sort events by position
        events.sort(key=lambda e: e[0])

        # Build action chain
        self.actions = []
        position = -end_flange_length_correction(
            self.outer.at(0.0, use_high=True),
            self.stepped_inner.at(0.0, use_high=True),
        )
        diameter = self.stepped_inner.at(0.0, use_high=True)

        for pos, descriptor, index in events:
            seg_length = pos - position

            # Pipe segment action
            self.actions.append(('pipe', seg_length))
            position = pos

            if descriptor == 'step':
                # Bore diameter step
                # assert diameter == self.stepped_inner.low[index]
                area_before = circle_area(diameter)
                diameter = self.stepped_inner.high[index]
                area_after = circle_area(diameter)
                self.actions.append(('junction2', area_after, area_before))

            elif descriptor == 'hole':
                # Tone hole
                area_bore = circle_area(diameter)
                hole_dia = self.hole_diameters[index]
                hole_area = circle_area(hole_dia)
                true_length = self.hole_lengths[index]
                open_length = true_length + hole_length_correction(hole_dia, diameter, False)
                closed_length = true_length + hole_length_correction(hole_dia, diameter, True)
                self.actions.append(('hole', index, area_bore, hole_area, open_length, closed_length))

        self.emission_divide = circle_area(diameter)

    def resonance_phase(self, wavelength: float, fingerings: List[str]) -> float:
        """
        Compute the resonance phase for a given wavelength and fingering.
        Phase should be integer at resonance.

        Args:
            wavelength: wavelength in mm (same units as bore positions)
            fingerings: list of 'open' or 'closed' for each hole

        Returns:
            Phase value (integer at resonance)
        """
        phase = 0.5  # Open end

        for action in self.actions:
            if action[0] == 'pipe':
                _, seg_length = action
                phase = pipe_reply_phase(phase, seg_length / wavelength if wavelength > 0 else 1e10)

            elif action[0] == 'junction2':
                _, area_a, area_b = action
                phase = junction2_reply_phase(area_a, area_b, phase)

            elif action[0] == 'hole':
                _, hole_idx, area_bore, hole_area, open_length, closed_length = action
                is_open = fingerings[hole_idx] == Hole.OPEN

                if is_open:
                    hole_phase = pipe_reply_phase(-0.5, open_length / wavelength if wavelength > 0 else 1e10)
                else:
                    hole_phase = pipe_reply_phase(0.0, closed_length / wavelength if wavelength > 0 else 1e10)

                phase = junction3_reply_phase(area_bore, area_bore, hole_area, phase, hole_phase)

        if not self.closed_top:
            phase += 0.5

        return phase

    def wavelength_near(
        self,
        wavelength: float,
        fingerings: List[str],
        step_cents: float = 1.0,
        step_increase: float = 1.2,
        max_steps: int = 100,
        target_register: int = 1,
    ) -> float:
        """
        Find the nearest resonant wavelength to the given guess.
        Uses linear interpolation to find where phase crosses target_register.

        Port of Instrument.wavelengthNear() from chalumier.
        """
        step = 2.0 ** (step_cents / 1200.0)
        half_step = math.sqrt(step)

        def scorer(w):
            p = self.resonance_phase(w, fingerings)
            return p - target_register

        probes = [wavelength / half_step, wavelength * half_step]
        scores = [scorer(probes[0]), scorer(probes[1])]

        def evaluate(i):
            y1, x1 = scores[i], probes[i]
            y2, x2 = scores[i + 1], probes[i + 1]
            m = (y2 - y1) / (x2 - x1)
            if abs(m) < 1e-30:
                return 0.5 * (x1 + x2)
            c = y1 - m * x1
            return -c / m

        for _ in range(max_steps):
            # Check for sign change at right end
            if scores[-2] >= 0.0 and scores[-1] < 0.0:
                return evaluate(len(scores) - 2)

            # Extend left
            new_w = probes[0] / step
            probes.insert(0, new_w)
            scores.insert(0, scorer(new_w))

            if scores[0] >= 0 and scores[1] < 0:
                return evaluate(0)

            # Extend right
            new_w = probes[-1] * step
            probes.append(new_w)
            scores.append(scorer(new_w))
            step = step ** step_increase

        # Return best guess
        if abs(scores[-1]) < abs(scores[0]):
            return probes[-1]
        return probes[0]

    def find_resonance(
        self,
        wavelength_near: float,
        fingerings: List[str],
        n_register: int = 1,
        max_steps: int = 100,
    ) -> float:
        """
        Find the resonant wavelength for a given fingering and register.
        Returns wavelength in mm.

        Args:
            wavelength_near: initial guess for the wavelength
            fingerings: list of 'open' or 'closed' for each hole
            n_register: register number (1 = fundamental, 2 = first overtone, etc.)
            max_steps: maximum search steps
        """
        return self.wavelength_near(wavelength_near, fingerings, target_register=n_register, max_steps=max_steps)

    def frequency_from_wavelength(self, wavelength_mm: float) -> float:
        """Convert wavelength (mm) to frequency (Hz)."""
        return self.speed_of_sound / wavelength_mm

    def cents_error(self, actual_freq: float, target_freq: float) -> float:
        """Compute pitch error in cents."""
        if actual_freq <= 0 or target_freq <= 0:
            return 1e10
        return 1200.0 * math.log2(actual_freq / target_freq)

    def compute_fingered_frequencies(
        self,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> List[float]:
        """
        Compute resonant frequencies for a set of fingerings.

        Args:
            target_wavelengths: initial wavelength guesses for each fingering
            fingering_sets: list of fingering configurations
            n_register: which register to target

        Returns:
            List of resonant frequencies in Hz
        """
        freqs = []
        for target_wl, fingerings in zip(target_wavelengths, fingering_sets):
            wl = self.find_resonance(target_wl, fingerings, n_register=n_register)
            freq = self.frequency_from_wavelength(wl)
            freqs.append(freq)
        return freqs

    def phase_cost(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> float:
        """
        Phase-based cost function (Ernoult 2020).

        Evaluates how well the bore's resonance structure matches target frequencies.
        For each target, computes the phase at the target wavelength and measures
        deviation from integer (resonance condition). This is SMOOTHER than
        peak-matching because phase is continuous even when peaks merge/split.

        Args:
            target_frequencies: list of target frequencies in Hz
            fingering_sets: list of fingering configurations (one per target)
            n_register: which register to target

        Returns:
            Cost value (0.0 = perfect match)
        """
        costs = []
        for target_freq, fingerings in zip(target_frequencies, fingering_sets):
            target_wl = self.speed_of_sound / target_freq
            try:
                phase = self.resonance_phase(target_wl, fingerings)
                # Phase should be integer at resonance (n_register)
                # Distance from nearest integer register
                deviation = phase - n_register
                # Use sinusoidal cost: 0 at integer, peaks at half-integer
                # This is smooth and differentiable everywhere
                costs.append(math.sin(math.pi * deviation) ** 2)
            except Exception:
                costs.append(1.0)
        return float(np.mean(costs))

    def phase_cost_with_offset(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> float:
        """
        Phase-based cost with global offset correction.

        Like phase_cost(), but first computes and removes the median phase
        error (global tuning offset). This isolates scale evenness from
        overall pitch.

        Args:
            target_frequencies: list of target frequencies in Hz
            fingering_sets: list of fingering configurations (one per target)
            n_register: which register to target

        Returns:
            Cost value (0.0 = perfect evenness)
        """
        deviations = []
        for target_freq, fingerings in zip(target_frequencies, fingering_sets):
            target_wl = self.speed_of_sound / target_freq
            try:
                phase = self.resonance_phase(target_wl, fingerings)
                deviations.append(phase - n_register)
            except Exception:
                deviations.append(0.0)

        if not deviations:
            return 1.0

        # Remove global offset (median)
        median_dev = np.median(deviations)
        corrected = [d - median_dev for d in deviations]

        # Cost: mean squared deviation from integer
        return float(np.mean([math.sin(math.pi * d) ** 2 for d in corrected]))


# ============================================================================
# Utility: build TMM instrument from bore radius array
# ============================================================================

def tmm_instrument_from_radii(
    radii_mm: np.ndarray,
    bore_length_mm: float,
    hole_positions_mm: List[float],
    hole_diameters_mm: List[float],
    hole_lengths_mm: List[float],
    outer_diameter_mm: float = 22.0,
    closed_top: bool = False,
    cone_step: float = 0.5,
) -> TMMInstrument:
    """
    Create a TMMInstrument from an array of bore radii.

    Args:
        radii_mm: bore radii in mm at evenly-spaced positions
        bore_length_mm: total bore length in mm
        hole_positions_mm: position of each hole along the bore (mm)
        hole_diameters_mm: diameter of each hole (mm)
        hole_lengths_mm: effective length of each hole channel (mm)
        outer_diameter_mm: outer diameter of the instrument body (mm)
        closed_top: True for clarinets (closed reed end)
        cone_step: maximum step size for profile smoothing

    Returns:
        TMMInstrument instance
    """
    bore_length_scalar = float(bore_length_mm)
    n = max(len(radii_mm), 2)
    if len(radii_mm) < 2:
        r = float(radii_mm[0]) if len(radii_mm) == 1 else 7.0
        positions = [0.0, bore_length_scalar]
        diameters = [r * 2.0, r * 2.0]
    else:
        positions = np.linspace(0, bore_length_scalar, n).tolist()
        diameters = (np.asarray(radii_mm, dtype=float) * 2.0).tolist()
    outer_diams = [outer_diameter_mm] * n

    return TMMInstrument(
        inner_positions=positions,
        inner_diameters=diameters,
        outer_diameters=outer_diams,
        hole_positions=hole_positions_mm,
        hole_diameters=hole_diameters_mm,
        hole_lengths=hole_lengths_mm,
        closed_top=closed_top,
        cone_step=cone_step,
    )
