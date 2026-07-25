"""Radiation model interface.

Handles open-end radiation impedance.
"""
from abc import ABC, abstractmethod
import numpy as np


class RadiationModel(ABC):
    """Abstract base class for radiation models."""

    @abstractmethod
    def radiation_impedance(self, radius: float, wavelength: float) -> complex:
        """Compute radiation impedance at an open end.

        Args:
            radius: bore radius in mm
            wavelength: acoustic wavelength in mm

        Returns:
            Complex radiation impedance (normalized)
        """
        pass

    @abstractmethod
    def end_correction(self, radius: float) -> float:
        """Compute end correction for an open end.

        Args:
            radius: bore radius in mm

        Returns:
            End correction in mm
        """
        pass


class BesselRadiation(RadiationModel):
    """Bessel horn radiation (chalumier-style)."""

    def radiation_impedance(self, radius: float, wavelength: float) -> complex:
        # Simplified: phase shift at open end
        # Full Bessel would require horn geometry
        return 0.5  # phase = 0.5 at open end (chalumier convention)

    def end_correction(self, radius: float) -> float:
        """Flange correction (chalumier-style)."""
        # From chalumier: endFlangeLengthCorrection
        # Based on flanged open pipe
        return 0.6133 * radius


class NoRadiation(RadiationModel):
    """No radiation model (ideal open end)."""

    def radiation_impedance(self, radius: float, wavelength: float) -> complex:
        return 0.5

    def end_correction(self, radius: float) -> float:
        return 0.0
