"""TMMInstrument — phase-based resonance computation for wind instruments."""
from __future__ import annotations

import math
from typing import List, Optional

from backend.acoustics.tmm_math import (
    SPEED_OF_SOUND,
    circle_area,
    end_flange_length_correction,
    hole_length_correction,
    junction2_reply_phase,
    junction3_reply_phase,
    pipe_reply_phase,
)
from backend.acoustics.profile import Profile


try:
    from backend.physics.losses import KeefeLoss, NoLoss
    _LOSSES_AVAILABLE = True
except ImportError:
    _LOSSES_AVAILABLE = False
    class KeefeLoss:
        def bore_loss(self, length, radius, wavelength): return 1.0
        def hole_loss(self, hole_radius, hole_length, wavelength): return 1.0
    NoLoss = KeefeLoss


class Hole:
    """Represents a tone hole state."""
    OPEN = 'open'
    CLOSED = 'closed'


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
        reed_virtual_length: float = 0.0,
        whistle_clip: float = 0.0,
        whistle_windway_diameter: float = 0.0,
        whistle_windway_length: float = 0.0,
        loss_model: Optional[object] = None,
    ):
        self.closed_top = closed_top
        self.cone_step = cone_step
        self.speed_of_sound = speed_of_sound

        # Build inner and outer profiles
        self.inner = Profile(inner_positions, inner_diameters)
        self.outer = Profile(inner_positions, outer_diameters)

        # Apply patchInstrument transforms (chalumier convention)
        if whistle_clip > 0.0:
            self._apply_whistle_clip(whistle_clip, whistle_windway_diameter, whistle_windway_length)
        if reed_virtual_length > 0.0:
            self._apply_reed_tube(reed_virtual_length)

        self.hole_positions = list(hole_positions)
        self.hole_diameters = list(hole_diameters)
        self.hole_lengths = list(hole_lengths)
        self.n_holes = len(hole_positions)
        self.loss_model = loss_model

        # Build stepped inner profile
        self.stepped_inner = self.inner.as_stepped(cone_step)
        self.length = self.stepped_inner.pos[-1]

        # Precompute action chain for phase-based resonance
        self._prepare_phase()

    def _apply_whistle_clip(
        self,
        clip_fraction: float,
        windway_diameter: float = 0.0,
        windway_length: float = 0.0,
    ):
        """
        Apply WhistleDesigner.patchInstrument() bore clipping.

        Clips the bore short by bore_diameter * clip_fraction at the top end,
        then optionally extends with a windway section.
        """
        from backend.acoustics.tmm_math import circle_area
        bore_diameter = self.inner.at(self.inner.pos[-1], use_high=True)
        clip_length = bore_diameter * clip_fraction
        new_length = self.inner.pos[-1] - clip_length

        clipped_pos = []
        clipped_low = []
        clipped_high = []
        for i, p in enumerate(self.inner.pos):
            if p <= new_length:
                clipped_pos.append(p)
                clipped_low.append(self.inner.low[i])
                clipped_high.append(self.inner.high[i])
        if clipped_pos[-1] < new_length:
            clipped_pos.append(new_length)
            d = self.inner.at(new_length)
            clipped_low.append(d)
            clipped_high.append(d)

        if windway_diameter > 0.0 and windway_length > 0.0:
            clipped_pos.append(new_length + windway_length)
            clipped_low.append(windway_diameter)
            clipped_high.append(windway_diameter)

        self.inner = Profile(clipped_pos, clipped_low, clipped_high)

    def _apply_reed_tube(self, reed_virtual_length: float):
        """
        Apply ReedInstrumentDesigner.patchInstrument() reed tube.

        For closed-top reed instruments (clarinets, saxophones):
        Appends a conical reed tube at the reed end (top) of the bore.
        reedLength = boreDiameter * reedVirtualLength
        reedTop = boreDiameter * reedVirtualTop (default 1.0 = same as bore)
        """
        bore_diameter = self.inner.at(self.inner.pos[-1], use_high=True)
        reed_length = bore_diameter * reed_virtual_length
        reed_top = bore_diameter  # reedVirtualTop = 1.0 by default

        # Append reed tube profile after existing bore
        new_end = self.inner.pos[-1] + reed_length
        self.inner.pos.append(new_end)
        self.inner.low.append(reed_top)
        self.inner.high.append(reed_top)

    def _prepare_phase(self):
        """
        Build the action chain for phase-based resonance computation.
        This is the Python equivalent of Instrument.preparePhase() in chalumier.
        """
        from backend.acoustics.tmm_math import end_flange_length_correction

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
            self.actions.append(('pipe', seg_length, diameter))
            position = pos

            if descriptor == 'step':
                # Bore diameter step
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
        from backend.acoustics.tmm_math import pipe_reply_phase

        phase = 0.5  # Open end

        for action in self.actions:
            if action[0] == 'pipe':
                _, seg_length, seg_diameter = action
                phase = pipe_reply_phase(phase, seg_length / wavelength)
                if self.loss_model is not None and seg_diameter > 0:
                    radius = seg_diameter / 2.0
                    loss_factor = self.loss_model.bore_loss(seg_length, radius, wavelength)
                    if isinstance(loss_factor, complex):
                        phase += -loss_factor.imag

            elif action[0] == 'junction2':
                _, area_a, area_b = action
                from backend.acoustics.tmm_math import junction2_reply_phase
                phase = junction2_reply_phase(area_a, area_b, phase)

            elif action[0] == 'hole':
                _, hole_idx, area_bore, hole_area, open_length, closed_length = action
                is_open = fingerings[hole_idx] == Hole.OPEN

                if is_open:
                    hole_phase = pipe_reply_phase(-0.5, open_length / wavelength)
                else:
                    hole_phase = pipe_reply_phase(0.0, closed_length / wavelength)

                from backend.acoustics.tmm_math import junction3_reply_phase
                phase = junction3_reply_phase(area_bore, area_bore, hole_area, phase, hole_phase)

        if not self.closed_top:
            phase += 0.5

        return phase

    def wavelength_near(
        self,
        wavelength: float,
        fingerings: List[str],
        step_cents: float = 1.0,
        step_increase: float = 1.05,
        max_steps: int = 100,
        target_register: int = 1,
        scorer=None,
    ) -> float:
        """
        Find the nearest resonant wavelength to the given guess.
        Uses linear interpolation to find where phase crosses target_register.
        """
        step = 2.0 ** (step_cents / 1200.0)
        half_step = math.sqrt(step)

        if scorer is None:
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

        if abs(scores[-1]) < abs(scores[0]):
            return probes[-1]
        return probes[0]

    def true_wavelength_near(
        self,
        wavelength: float,
        fingerings: List[str],
        step_cents: float = 1.0,
        step_increase: float = 1.05,
        max_steps: int = 100,
    ) -> float:
        """
        Find the nearest resonant wavelength regardless of register.
        Scorer: ((resonancePhase + 0.5) % 1.0) - 0.5
        Wraps phase into [-0.5, 0.5) and finds zero crossing.
        """
        def scorer(w):
            p = self.resonance_phase(w, fingerings)
            return ((p + 0.5) % 1.0) - 0.5

        step = 2.0 ** (step_cents / 1200.0)
        half_step = math.sqrt(step)
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
            if scores[-2] >= 0.0 and scores[-1] < 0.0:
                return evaluate(len(scores) - 2)

            new_w = probes[0] / step
            probes.insert(0, new_w)
            scores.insert(0, scorer(new_w))

            if scores[0] >= 0 and scores[1] < 0:
                return evaluate(0)

            new_w = probes[-1] * step
            probes.append(new_w)
            scores.append(scorer(new_w))
            step = step ** step_increase

        if abs(scores[-1]) < abs(scores[0]):
            return probes[-1]
        return probes[0]

    def compute_fingered_frequencies(
        self,
        target_wavelengths: List[float],
        fingerings: List[List[str]],
        register: int = 1,
    ) -> List[float]:
        """Compute resonant frequencies for multiple fingerings at target wavelengths."""
        return [
            self.speed_of_sound / self.wavelength_near(tw, f, target_register=register)
            for tw, f in zip(target_wavelengths, fingerings)
        ]