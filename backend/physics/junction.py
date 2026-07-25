"""Junction model interface.

Handles bore diameter changes (step junctions).
"""
from abc import ABC, abstractmethod
import numpy as np


class JunctionModel(ABC):
    """Abstract base class for bore junction models."""

    @abstractmethod
    def junction2(
        self, area_in: float, area_out: float, wavelength: float
    ) -> complex:
        """Two-port junction (diameter change).

        Args:
            area_in: cross-sectional area before junction
            area_out: cross-sectional area after junction
            wavelength: acoustic wavelength in mm

        Returns:
            Complex transmission coefficient
        """
        pass


class LosslessJunction(JunctionModel):
    """Lossless step junction (area ratio only)."""

    def junction2(
        self, area_in: float, area_out: float, wavelength: float
    ) -> complex:
        # Simple area ratio transmission
        # From conservation of mass and pressure continuity
        return 2.0 * area_out / (area_in + area_out)
