"""Tonehole model interface.

Handles side branch coupling (toneholes, register vents).
"""
from abc import ABC, abstractmethod
import numpy as np


class ToneholeModel(ABC):
    """Abstract base class for tonehole models."""

    @abstractmethod
    def tonehole_open(
        self, bore_area: float, hole_area: float,
        bore_length: float, hole_length: float,
        wavelength: float,
    ) -> complex:
        """Transmission through an open tonehole.

        Args:
            bore_area: bore cross-sectional area
            hole_area: tonehole cross-sectional area
            bore_length: bore segment length (for shunt model)
            hole_length: chimney height
            wavelength: acoustic wavelength in mm

        Returns:
            Complex transmission coefficient
        """
        pass

    @abstractmethod
    def tonehole_closed(
        self, bore_area: float, hole_area: float,
        bore_length: float, hole_length: float,
        wavelength: float,
    ) -> complex:
        """Transmission through a closed tonehole.

        Args:
            bore_area: bore cross-sectional area
            hole_area: tonehole cross-sectional area
            bore_length: bore segment length (for shunt model)
            hole_length: chimney height
            wavelength: acoustic wavelength in mm

        Returns:
            Complex transmission coefficient
        """
        pass


class SimpleTonehole(ToneholeModel):
    """Simple tonehole model (chalumier-style)."""

    def tonehole_open(
        self, bore_area: float, hole_area: float,
        bore_length: float, hole_length: float,
        wavelength: float,
    ) -> complex:
        # Simplified open tonehole: shunt admittance
        # Based on chalumier/demakein approach
        k = 2.0 * np.pi / wavelength
        # Chimney admittance (short tube approximation)
        Y_chimney = 1j * np.tan(k * hole_length) * hole_area / bore_area
        # Series impedance of bore segment
        Z_bore = 1j * np.tan(k * bore_length)
        # Transmission coefficient
        return 1.0 / (1.0 + Y_chimney * Z_bore)

    def tonehole_closed(
        self, bore_area: float, hole_area: float,
        bore_length: float, hole_length: float,
        wavelength: float,
    ) -> complex:
        # Closed tonehole: series impedance
        k = 2.0 * np.pi / wavelength
        Z_chimney = 1j * np.tan(k * hole_length) * bore_area / hole_area
        Z_bore = 1j * np.tan(k * bore_length)
        return 1.0 / (1.0 + Z_chimney / Z_bore)
