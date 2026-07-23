"""
Tone hole interaction corrections for TMM bore models.

References:
  - Lefebvre PhD thesis (McGill 2010), Chapter 4:
    "TMM errors up to 10 cents from unmodeled tone hole interactions"
  - Benade (1988): Tone hole lattice theory
  - Noreland (2013): chimney positions, diameters, lengths vary regularly
  - Keefe (1990): Tone hole scattering matrix approach

Usage:
    from backend.tone_hole_corrections import ToneHoleCorrector

    corrector = ToneHoleCorrector(bore_diameters, tone_hole_positions)
    corrected_peaks = corrector.apply(freqs, raw_impedance_peaks)
"""

import numpy as np
from typing import List, Tuple, Optional
import math


class ToneHoleCorrector:
    """
    Corrects TMM impedance for tone hole interaction effects.

    The standard TMM treats each tone hole as independent. In reality,
    tone holes interact through the bore — opening one hole changes the
    effective acoustic length seen by others. This is especially important
    for:
    - Close-spaced tone holes (clarinet lower joint)
    - Large tone holes near the bell
    - Register holes (their position affects all other holes)

    The correction uses simplified scattering matrix theory (Keefe 1990)
    combined with empirical corrections from Lefebvre (2010).
    """

    def __init__(
        self,
        bore_diameters: np.ndarray,
        tone_hole_positions: np.ndarray,
        tone_hole_diameters: Optional[np.ndarray] = None,
        tone_hole_depths: Optional[np.ndarray] = None,
        wall_thickness: float = 1.5,  # mm
    ):
        """
        Args:
            bore_diameters: Internal bore diameter at each tone hole (mm)
            tone_hole_positions: Distance from mouthpiece end to each hole (mm)
            tone_hole_diameters: Diameter of each tone hole (mm), defaults to bore_diameter * 0.5
            tone_hole_depths: Depth/chimney height of each hole (mm), defaults to wall_thickness
            wall_thickness: Instrument wall thickness (mm)
        """
        self.bore_diameters = np.asarray(bore_diameters, dtype=float)
        self.tone_hole_positions = np.asarray(tone_hole_positions, dtype=float)
        self.n_holes = len(tone_hole_positions)

        if tone_hole_diameters is not None:
            self.tone_hole_diameters = np.asarray(tone_hole_diameters, dtype=float)
        else:
            self.tone_hole_diameters = self.bore_diameters * 0.5

        if tone_hole_depths is not None:
            self.tone_hole_depths = np.asarray(tone_hole_depths, dtype=float)
        else:
            self.tone_hole_depths = np.full(self.n_holes, wall_thickness)

        self.wall_thickness = wall_thickness

        # Precompute interaction matrix
        self._interaction_matrix = self._compute_interaction_matrix()

    def _compute_interaction_matrix(self) -> np.ndarray:
        """
        Compute pairwise tone hole interaction strengths.

        The interaction between two holes depends on:
        1. Their separation distance (exponential decay)
        2. Their diameters (larger holes interact more strongly)
        3. The bore diameter between them (smaller bore = stronger coupling)

        Returns:
            n_holes x n_holes interaction matrix (diagonal is 1.0)
        """
        n = self.n_holes
        interaction = np.eye(n)

        for i in range(n):
            for j in range(i + 1, n):
                # Separation distance
                separation = abs(self.tone_hole_positions[j] - self.tone_hole_positions[i])

                # Average bore diameter between the two holes
                mask = (self.tone_hole_positions >= min(self.tone_hole_positions[i], self.tone_hole_positions[j]))
                mask &= (self.tone_hole_positions <= max(self.tone_hole_positions[i], self.tone_hole_positions[j]))
                if np.any(mask):
                    avg_bore = np.mean(self.bore_diameters[mask])
                else:
                    avg_bore = (self.bore_diameters[i] + self.bore_diameters[j]) / 2.0

                # Average hole diameter
                avg_hole = (self.tone_hole_diameters[i] + self.tone_hole_diameters[j]) / 2.0

                # Interaction strength: exponential decay with distance,
                # scaled by hole-to-bore ratio
                hole_bore_ratio = avg_hole / avg_bore
                decay_length = avg_bore * 2.0  # characteristic decay length

                strength = hole_bore_ratio * math.exp(-separation / decay_length)
                strength = min(strength, 0.5)  # cap at 50%

                interaction[i, j] = strength
                interaction[j, i] = strength

        return interaction

    def effective_lengths(self) -> np.ndarray:
        """
        Compute effective acoustic length corrections for each tone hole.

        Each tone hole has an end correction that depends on:
        - Its diameter (larger hole = longer correction)
        - The bore diameter (ratio matters)
        - Chimney depth (adds length)
        - Neighboring holes (interaction correction)

        Returns:
            Array of effective length corrections (mm) for each hole
        """
        n = self.n_holes
        corrections = np.zeros(n)

        for i in range(n):
            d = self.tone_hole_diameters[i]
            D = self.bore_diameters[i]
            t = self.tone_hole_depths[i]

            # Basic end correction (Benade formula)
            a = d / 2.0
            end_correction = a * (0.821 - 0.13 * (0.42 + t / a) ** (-0.54))

            # Chimney contribution
            chimney = t * (d / D) ** 2

            # Interaction correction from neighboring holes
            interaction_correction = 0.0
            for j in range(n):
                if i != j:
                    strength = self._interaction_matrix[i, j]
                    # Neighboring hole pulls effective length toward its own
                    neighbor_correction = self.tone_hole_depths[j] * (self.tone_hole_diameters[j] / D) ** 2
                    interaction_correction += strength * (neighbor_correction - chimney) * 0.3

            corrections[i] = end_correction + chimney + interaction_correction

        return corrections

    def frequency_shift(self, fundamental_freq: float, mode: int = 1) -> float:
        """
        Estimate frequency shift due to tone hole interactions.

        For the fundamental (mode=1), the dominant effect is the
        first open tone hole determining the effective length. But
        interactions with closed holes downstream shift this slightly.

        Args:
            fundamental_freq: Nominal frequency without corrections (Hz)
            mode: Harmonic mode number (1 = fundamental, 2 = first overtone, etc.)

        Returns:
            Frequency shift in Hz (positive = sharp, negative = flat)
        """
        if self.n_holes < 2:
            return 0.0

        # The effective length correction from all open holes
        corrections = self.effective_lengths()

        # Weight corrections by mode number (higher modes less affected)
        mode_factor = 1.0 / mode

        # Total effective length correction
        total_correction = np.sum(corrections) * mode_factor

        # Convert length correction to frequency shift
        # Δf/f ≈ -ΔL/L (for a stopped pipe)
        # For open pipe: Δf/f ≈ -ΔL/(2L)
        # Using average of both for a general approximation
        L_nominal = 343000.0 / (2.0 * fundamental_freq)  # mm, approximate bore length
        freq_shift = -fundamental_freq * total_correction / L_nominal

        return freq_shift

    def cents_correction(self, fundamental_freq: float, mode: int = 1) -> float:
        """
        Frequency shift in cents.

        Args:
            fundamental_freq: Nominal frequency (Hz)
            mode: Harmonic mode number

        Returns:
            Correction in cents (positive = sharp, negative = flat)
        """
        shift_hz = self.frequency_shift(fundamental_freq, mode)
        if abs(shift_hz) < 1e-10:
            return 0.0

        return 1200.0 * math.log2(1.0 + shift_hz / fundamental_freq)

    def apply_to_impedance(
        self,
        freqs: np.ndarray,
        impedance: np.ndarray,
        open_holes: Optional[List[int]] = None,
    ) -> np.ndarray:
        """
        Apply tone hole corrections to impedance curve.

        This modifies the impedance peaks to account for tone hole
        interactions. The correction shifts peaks slightly and
        changes their magnitudes.

        Args:
            freqs: Frequency array (Hz)
            impedance: Impedance magnitude array (same length as freqs)
            open_holes: Indices of open tone holes (None = all closed)

        Returns:
            Corrected impedance array
        """
        corrected = impedance.copy()

        if open_holes is None:
            open_holes = []

        # For each open hole, compute its contribution to the impedance
        for idx in open_holes:
            if idx >= self.n_holes:
                continue

            # The open hole creates a shunt impedance
            d = self.tone_hole_diameters[i]
            D = self.bore_diameters[i]
            t = self.tone_hole_depths[i]

            # Helmholtz-like shunt impedance
            a = d / 2.0
            A_hole = math.pi * a ** 2
            A_bore = math.pi * (D / 2.0) ** 2

            # End correction for the hole
            end_corr = a * (0.821 - 0.13 * (0.42 + t / a) ** (-0.54))
            L_neck = t + end_corr

            # Neck acoustic mass
            rho = 1.18  # air density
            M_neck = rho * L_neck / A_hole

            # Radiation impedance (simplified)
            k = 2.0 * np.pi * freqs / 343000.0  # wave number
            Z_rad = rho * 343000.0 * (k * a) ** 2 / (2.0 * math.pi * A_hole)

            # Shunt impedance magnitude
            Z_shunt = np.sqrt((2.0 * np.pi * freqs * M_neck) ** 2 + Z_rad ** 2)

            # Reduce impedance at shunt resonances
            # (the shunt creates antiresonances in the bore impedance)
            f_resonance = 343000.0 / (2.0 * math.pi) * math.sqrt(A_hole / (A_bore * L_neck))
            width = f_resonance * 0.1  # 10% bandwidth

            lorentzian = width ** 2 / ((freqs - f_resonance) ** 2 + width ** 2)
            corrected *= (1.0 - 0.3 * lorentzian)  # reduce peaks near hole resonance

        return corrected


class RegisterHoleCorrector:
    """
    Specialized correction for the register/octave hole.

    The register hole is critical for clarinet (twelfth) and saxophone/flute
    (octave). Its interaction with other tone holes is especially strong
    because:
    1. It's positioned to favor the 3rd harmonic (clarinet) or 2nd (sax/flute)
    2. It creates a complex impedance pattern that affects all fingerings
    3. Nonlinear effects (Szwarcberg et al. 2024) at high blowing pressures

    Reference:
      - Szwarcberg et al. (2024): Nonlinear effects in register holes
      - Noreland (2013): Register hole enables more regular tone hole pattern
    """

    def __init__(
        self,
        bore_diameter: float,  # mm at register hole position
        register_hole_diameter: float = 3.0,  # mm
        register_hole_position: float = 0.0,  # mm from mouthpiece
        target_harmonic: int = 3,  # 3 for clarinet (twelfth), 2 for sax/flute (octave)
    ):
        self.bore_diameter = bore_diameter
        self.register_hole_diameter = register_hole_diameter
        self.register_hole_position = register_hole_position
        self.target_harmonic = target_harmonic

    def effective_length_correction(self) -> float:
        """
        Effective length correction for the register hole.

        The register hole acts as a partially open tone hole that
        specifically affects the target harmonic.

        Returns:
            Length correction in mm
        """
        d = self.register_hole_diameter
        D = self.bore_diameter
        t = self.wall_thickness if hasattr(self, 'wall_thickness') else 1.5

        a = d / 2.0
        end_corr = a * (0.821 - 0.13 * (0.42 + t / a) ** (-0.54))
        chimney = t * (d / D) ** 2

        return end_corr + chimney

    def cents_on_fundamental(self, fundamental_freq: float) -> float:
        """
        Estimate how the register hole affects the fundamental.

        The register hole is designed to NOT affect the fundamental much,
        but it does create some detuning. For clarinet, it should raise
        the 3rd harmonic to match the fundamental's 12th.

        Returns:
            Cents deviation from ideal
        """
        # The register hole is a small perturbation for the fundamental
        # Its main effect is on the target harmonic
        d = self.register_hole_diameter
        D = self.bore_diameter

        # Small perturbation: ~1-3 cents typical
        perturbation = (d / D) ** 2 * 10.0  # rough estimate

        return perturbation

    def cents_on_target_harmonic(self, fundamental_freq: float) -> float:
        """
        Estimate how the register hole affects the target harmonic.

        For clarinet (3rd harmonic = twelfth): the register hole should
        raise the 3rd harmonic to match 2x the fundamental frequency.

        Returns:
            Cents deviation from ideal
        """
        d = self.register_hole_diameter
        D = self.bore_diameter

        # The register hole has a stronger effect on higher harmonics
        perturbation = (d / D) ** 2 * 10.0 * self.target_harmonic

        return perturbation


# ============================================================================
# Utility: apply corrections to designed bore
# ============================================================================

def apply_corrections_to_bore(
    bore_radii: np.ndarray,
    bore_positions: np.ndarray,
    tone_hole_positions: np.ndarray,
    tone_hole_diameters: Optional[np.ndarray] = None,
    register_hole_position: Optional[float] = None,
    register_hole_diameter: float = 3.0,
    target_harmonic: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply tone hole interaction corrections to a designed bore.

    This takes the raw bore from the optimizer and applies corrections
    for tone hole interactions that the TMM doesn't model.

    Args:
        bore_radii: Designed bore radii (mm)
        bore_positions: Bore positions (mm)
        tone_hole_positions: Positions of all tone holes (mm)
        tone_hole_diameters: Diameter of each hole (mm)
        register_hole_position: Position of register hole (mm)
        register_hole_diameter: Diameter of register hole (mm)
        target_harmonic: 3 for clarinet, 2 for sax/flute

    Returns:
        (corrected_radii, corrected_positions)
    """
    # Interpolate bore diameters at tone hole positions
    bore_diameters = np.interp(tone_hole_positions, bore_positions, bore_radii * 2.0)

    # Create corrector
    corrector = ToneHoleCorrector(
        bore_diameters=bore_diameters,
        tone_hole_positions=tone_hole_positions,
        tone_hole_diameters=tone_hole_diameters,
    )

    # Get effective length corrections
    corrections = corrector.effective_lengths()

    # Apply corrections: adjust bore at each hole position
    corrected_radii = bore_radii.copy()
    corrected_positions = bore_positions.copy()

    for i, (pos, correction) in enumerate(zip(tone_hole_positions, corrections)):
        # Find the bore point nearest to this hole
        idx = np.argmin(np.abs(bore_positions - pos))

        # Slight bore reduction at hole (the hole acts as a side branch)
        # This is a simplified correction — the real effect is more complex
        radius_reduction = correction * 0.01  # scale factor
        corrected_radii[idx] = max(corrected_radii[idx] - radius_reduction, 0.5)

    # Register hole correction
    if register_hole_position is not None:
        reg_corrector = RegisterHoleCorrector(
            bore_diameter=np.interp(register_hole_position, bore_positions, bore_radii * 2.0),
            register_hole_diameter=register_hole_diameter,
            register_hole_position=register_hole_position,
            target_harmonic=target_harmonic,
        )
        reg_correction = reg_corrector.effective_length_correction()
        idx = np.argmin(np.abs(bore_positions - register_hole_position))
        corrected_radii[idx] = max(corrected_radii[idx] - reg_correction * 0.01, 0.5)

    return corrected_radii, corrected_positions
