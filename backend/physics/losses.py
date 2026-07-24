"""Loss model interface.

Handles viscothermal and thermoviscous losses in bore and toneholes.
"""
from abc import ABC, abstractmethod
import numpy as np


class LossModel(ABC):
    """Abstract base class for loss models."""

    @abstractmethod
    def bore_loss(
        self, length: float, radius: float, wavelength: float
    ) -> complex:
        """Compute loss factor for a bore segment.

        Args:
            length: segment length in mm
            radius: bore radius in mm
            wavelength: acoustic wavelength in mm

        Returns:
            Complex loss factor (magnitude < 1 for lossy)
        """
        pass

    @abstractmethod
    def hole_loss(
        self, hole_radius: float, hole_length: float, wavelength: float
    ) -> complex:
        """Compute loss factor for a tonehole chimney.

        Args:
            hole_radius: tonehole radius in mm
            hole_length: chimney height in mm
            wavelength: acoustic wavelength in mm

        Returns:
            Complex loss factor
        """
        pass


class NoLoss(LossModel):
    """No losses (lossless model)."""

    def bore_loss(self, length: float, radius: float, wavelength: float) -> complex:
        return 1.0

    def hole_loss(self, hole_radius: float, hole_length: float, wavelength: float) -> complex:
        return 1.0


class KeefeLoss(LossModel):
    """Keefe viscothermal losses (future)."""

    def bore_loss(self, length: float, radius: float, wavelength: float) -> complex:
        # TODO: implement Keefe (1981-1982) losses
        raise NotImplementedError

    def hole_loss(self, hole_radius: float, hole_length: float, wavelength: float) -> complex:
        raise NotImplementedError
