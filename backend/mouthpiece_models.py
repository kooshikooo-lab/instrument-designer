"""
Empirical mouthpiece models for wind instrument optimization.

Based on WIDesigner approach (Patkau/Lefebvre/Kort 2017):
- Treat mouthpiece as separate empirical model
- Encapsulates drive mechanism influence
- Reduces design variables for bore optimization

References:
  - WIDesigner: https://github.com/edwardkort/WWIDesigner
  - Patkau, Lefebvre, Kort (ISMA 2017)
  - Lefebvre PhD thesis (McGill 2010)

Usage:
    from backend.mouthpiece_models import ClarinetMouthpiece, SaxophoneMouthpiece

    mp = ClarinetMouthpiece(model="standard")
    effective_length = mp.effective_length(reed_strength=2.5)
    impedance = mp.input_impedance(freq_array)
"""

import math
import numpy as np
from typing import Optional


class MouthpieceModel:
    """
    Base class for empirical mouthpiece models.

    The mouthpiece acts as an acoustic filter at the input end of the
    instrument. Its effective length and impedance characteristics
    depend on the mouthpiece geometry and reed properties.
    """

    def __init__(
        self,
        effective_bore_diameter: float = 14.5,  # mm
        facing_length: float = 28.0,  # mm (tip to first point of reed contact)
        tip_opening: float = 1.0,  # mm (gap between reed and mouthpiece)
        chamber_volume: float = 3.5,  # cm^3
    ):
        self.effective_bore_diameter = effective_bore_diameter
        self.facing_length = facing_length
        self.tip_opening = tip_opening
        self.chamber_volume = chamber_volume

    def effective_length(self, **kwargs) -> float:
        """Effective acoustic length added by mouthpiece (mm)."""
        raise NotImplementedError

    def input_impedance(self, freqs: np.ndarray, **kwargs) -> np.ndarray:
        """Input impedance contribution of the mouthpiece."""
        raise NotImplementedError

    def end_correction(self, **kwargs) -> float:
        """End correction due to mouthpiece geometry (mm)."""
        raise NotImplementedError


class ClarinetMouthpiece(MouthpieceModel):
    """
    Empirical clarinet mouthpiece model.

    Based on measurements from Lefebvre (2010) and WIDesigner.
    The clarinet mouthpiece adds an effective length that depends on:
    - Facing curve geometry
    - Tip opening
    - Reed strength (affects damping)
    - Chamber shape (baffle + sidewalls)
    """

    def __init__(
        self,
        model: str = "standard",  # "standard", "open", "close"
        reed_strength: float = 2.5,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.model = model
        self.reed_strength = reed_strength

        # Model-specific parameters (from WIDesigner empirical data)
        if model == "standard":
            self.facing_length = 28.0
            self.tip_opening = 1.0
            self.chamber_volume = 3.5
            self.bore_diameter = 14.5
        elif model == "open":
            self.facing_length = 30.0
            self.tip_opening = 1.3
            self.chamber_volume = 4.0
            self.bore_diameter = 14.5
        elif model == "close":
            self.facing_length = 26.0
            self.tip_opening = 0.8
            self.chamber_volume = 3.0
            self.bore_diameter = 14.5

    def effective_length(self, reed_strength: Optional[float] = None) -> float:
        """
        Effective acoustic length of the mouthpiece (mm).

        The mouthpiece adds length because:
        1. The reed closes the bore (closed end boundary)
        2. The facing curve adds effective length
        3. The chamber volume creates a compliance

        From Lefebvre (2010): typical values are 25-35mm for Bb clarinet.
        """
        strength = reed_strength or self.reed_strength

        # Base length from facing geometry
        base_length = self.facing_length * 0.8  # ~80% of facing length

        # Tip opening effect: larger opening = slightly shorter effective length
        tip_correction = (self.tip_opening - 1.0) * 5.0  # mm

        # Reed strength effect: softer reed = longer effective length
        strength_correction = (strength - 2.5) * 2.0  # mm

        # Chamber volume effect: larger chamber = longer effective length
        chamber_correction = (self.chamber_volume - 3.5) * 3.0  # mm

        return base_length + tip_correction + strength_correction + chamber_correction

    def input_impedance(self, freqs: np.ndarray, reed_strength: Optional[float] = None) -> np.ndarray:
        """
        Input impedance of the mouthpiece.

        Modeled as a compliance (chamber) + resistance (facing curve)
        + mass (air column in mouthpiece).

        Returns impedance in acoustic ohms (Pa·s/m³).
        """
        strength = reed_strength or self.reed_strength
        omega = 2.0 * np.pi * freqs

        # Chamber compliance (volume -> impedance)
        gamma = 1.4  # ratio of specific heats
        rho = 1.18  # air density kg/m^3
        c = 343.0  # speed of sound m/s
        V = self.chamber_volume * 1e-6  # cm^3 -> m^3

        compliance = 1.0 / (gamma * rho * c**2 * V) * omega  # inductive

        # Reed resistance (frequency-dependent)
        # Softer reeds have higher resistance at low frequencies
        reed_resistance = 1e4 * (3.0 / strength) * np.exp(-freqs / 2000.0)

        # Air mass in mouthpiece bore
        L_eff = self.effective_length(reed_strength=strength) * 1e-3  # mm -> m
        A = math.pi * (self.bore_diameter * 1e-3 / 2.0)**2
        mass_impedance = omega * rho * L_eff / A

        # Total impedance (magnitude)
        Z = np.sqrt(compliance**2 + reed_resistance**2 + mass_impedance**2)

        return Z

    def end_correction(self, reed_strength: Optional[float] = None) -> float:
        """
        End correction for the mouthpiece end (mm).

        The reed end acts as a closed boundary with additional
        compliance from the reed and chamber.
        """
        strength = reed_strength or self.reed_strength
        base = self.effective_length(reed_strength=strength)

        # Add radiation-like correction for reed compliance
        reed_compliance = (3.0 - strength) * 2.0  # softer reed = more compliance

        return base + reed_compliance


class SaxophoneMouthpiece(MouthpieceModel):
    """
    Empirical saxophone mouthpiece model.

    Saxophone mouthpieces are similar to clarinet but with:
    - Larger bore diameter
    - Different chamber geometry (baffle shape)
    - Conical bore interaction
    """

    def __init__(
        self,
        model: str = "standard",  # "standard", "jazz", "classical", "pop"
        reed_strength: float = 2.5,
        instrument: str = "alto",  # "soprano", "alto", "tenor", "baritone"
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.model = model
        self.reed_strength = reed_strength
        self.instrument = instrument

        # Instrument-specific parameters
        bore_sizes = {
            "soprano": 12.5,
            "alto": 14.5,
            "tenor": 16.0,
            "baritone": 19.0,
        }
        self.bore_diameter = bore_sizes.get(instrument, 14.5)

        # Model-specific parameters
        if model == "standard":
            self.facing_length = 26.0
            self.tip_opening = 1.2
            self.chamber_volume = 4.0
        elif model == "jazz":
            self.facing_length = 28.0
            self.tip_opening = 1.5
            self.chamber_volume = 5.0
        elif model == "classical":
            self.facing_length = 24.0
            self.tip_opening = 0.9
            self.chamber_volume = 3.5
        elif model == "pop":
            self.facing_length = 27.0
            self.tip_opening = 1.4
            self.chamber_volume = 4.5

    def effective_length(self, reed_strength: Optional[float] = None) -> float:
        """Effective acoustic length of the saxophone mouthpiece (mm)."""
        strength = reed_strength or self.reed_strength

        base_length = self.facing_length * 0.75
        tip_correction = (self.tip_opening - 1.2) * 4.0
        strength_correction = (strength - 2.5) * 1.5
        chamber_correction = (self.chamber_volume - 4.0) * 2.5

        return base_length + tip_correction + strength_correction + chamber_correction

    def input_impedance(self, freqs: np.ndarray, reed_strength: Optional[float] = None) -> np.ndarray:
        """Input impedance of the saxophone mouthpiece."""
        strength = reed_strength or self.reed_strength
        omega = 2.0 * np.pi * freqs

        gamma = 1.4
        rho = 1.18
        c = 343.0
        V = self.chamber_volume * 1e-6

        compliance = 1.0 / (gamma * rho * c**2 * V) * omega
        reed_resistance = 8e3 * (3.0 / strength) * np.exp(-freqs / 2500.0)
        L_eff = self.effective_length(reed_strength=strength) * 1e-3
        A = math.pi * (self.bore_diameter * 1e-3 / 2.0)**2
        mass_impedance = omega * rho * L_eff / A

        Z = np.sqrt(compliance**2 + reed_resistance**2 + mass_impedance**2)
        return Z

    def end_correction(self, reed_strength: Optional[float] = None) -> float:
        """End correction for saxophone mouthpiece (mm)."""
        strength = reed_strength or self.reed_strength
        return self.effective_length(reed_strength=strength) + (3.0 - strength) * 1.5


class FluteEmbouchure(MouthpieceModel):
    """
    Empirical flute embouchure model.

    Based on McIntyre et al. (1983) jet drive model.
    The embouchure hole acts as:
    - Radiation impedance at the open end
    - Jet drive mechanism (blowing across the hole)
    - Nonlinear coupling between jet and bore resonances

    Note: OpenWInD says flute embouchure is "coming soon" since 2020.
    This is a simplified empirical model.
    """

    def __init__(
        self,
        hole_diameter: float = 12.0,  # mm
        wall_thickness: float = 3.0,  # mm
        chimney_height: float = 4.0,  # mm (distance from hole to bore center)
        blow_angle: float = 45.0,  # degrees from bore axis
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.hole_diameter = hole_diameter
        self.wall_thickness = wall_thickness
        self.chimney_height = chimney_height
        self.blow_angle = blow_angle

    def effective_length(self, **kwargs) -> float:
        """
        Effective length contribution of the embouchure hole.

        The embouchure hole acts as an open end with an end correction
        that depends on the hole geometry and blowing angle.
        """
        # End correction for embouchure hole (Benade model)
        a = self.hole_diameter / 2.0
        correction = a * (0.821 - 0.13 * (0.42 + self.chimney_height / a) ** (-0.54))

        # Blowing angle effect: more perpendicular = shorter effective length
        angle_factor = math.cos(math.radians(self.blow_angle))
        correction *= angle_factor

        return correction

    def input_impedance(self, freqs: np.ndarray, **kwargs) -> np.ndarray:
        """
        Input impedance of the embouchure hole.

        Modeled as a Helmholtz resonator (hole + chimney).
        """
        omega = 2.0 * np.pi * freqs
        rho = 1.18
        c = 343.0

        # Hole area
        A = math.pi * (self.hole_diameter * 1e-3 / 2.0)**2

        # Neck length (chimney height + wall thickness)
        L = (self.chimney_height + self.wall_thickness) * 1e-3

        # Helmholtz resonance frequency
        V_neck = A * L
        V_body = self.chamber_volume * 1e-6 if hasattr(self, 'chamber_volume') else 1e-6
        f_helmholtz = c / (2.0 * math.pi) * math.sqrt(A / (V_body * L))

        # Impedance magnitude (peaks at Helmholtz frequency)
        Z = rho * c / A * 1.0 / np.sqrt(1.0 + ((freqs / f_helmholtz)**2 - 1.0)**2 + 0.1**2)

        return Z

    def end_correction(self, **kwargs) -> float:
        """End correction for embouchure hole (mm)."""
        return self.effective_length(**kwargs)


# ============================================================================
# Factory function
# ============================================================================

def get_mouthpiece_model(
    instrument_type: str = "clarinet",
    model: str = "standard",
    **kwargs,
) -> MouthpieceModel:
    """
    Factory function to get the appropriate mouthpiece model.

    Args:
        instrument_type: "clarinet", "soprano_sax", "alto_sax", "tenor_sax", "flute"
        model: mouthpiece model variant
    """
    if instrument_type == "clarinet":
        return ClarinetMouthpiece(model=model, **kwargs)
    elif instrument_type in ("soprano_sax", "saxophone"):
        return SaxophoneMouthpiece(model=model, instrument="soprano", **kwargs)
    elif instrument_type == "alto_sax":
        return SaxophoneMouthpiece(model=model, instrument="alto", **kwargs)
    elif instrument_type == "tenor_sax":
        return SaxophoneMouthpiece(model=model, instrument="tenor", **kwargs)
    elif instrument_type == "baritone_sax":
        return SaxophoneMouthpiece(model=model, instrument="baritone", **kwargs)
    elif instrument_type == "flute":
        return FluteEmbouchure(**kwargs)
    else:
        return MouthpieceModel(**kwargs)
