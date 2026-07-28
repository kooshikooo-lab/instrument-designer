"""Propagation model interface.

Handles wave propagation through bore segments.
"""
from abc import ABC, abstractmethod
import numpy as np


class PropagationModel(ABC):
    """Abstract base class for bore propagation models.

    A propagation model computes how acoustic waves travel through
    a cylindrical or conical bore segment.
    """

    @abstractmethod
    def propagate_cylindrical(
        self, length: float, radius: float, wavelength: float
    ) -> complex:
        """Compute propagation through a cylindrical segment.

        Args:
            length: segment length in mm
            radius: bore radius in mm
            wavelength: acoustic wavelength in mm

        Returns:
            Complex transmission coefficient
        """
        pass

    @abstractmethod
    def propagate_conical(
        self, length: float, radius_in: float, radius_out: float, wavelength: float
    ) -> complex:
        """Compute propagation through a conical segment.

        Args:
            length: segment length in mm
            radius_in: radius at input end in mm
            radius_out: radius at output end in mm
            wavelength: acoustic wavelength in mm

        Returns:
            Complex transmission coefficient
        """
        pass


class LosslessPropagation(PropagationModel):
    """Ideal lossless propagation (phase-only)."""

    def propagate_cylindrical(
        self, length: float, radius: float, wavelength: float
    ) -> complex:
        phase = 2.0 * np.pi * length / wavelength
        return np.exp(1j * phase)

    def propagate_conical(
        self, length: float, radius_in: float, radius_out: float, wavelength: float
    ) -> complex:
        phase = 2.0 * np.pi * length / wavelength
        return np.exp(1j * phase)


class ViscothermalPropagation(PropagationModel):
    """Viscothermal propagation with Keefe losses.

    Uses KeefeLoss model for viscothermal attenuation magnitude,
    combined with standard lossless propagation phase.

    NOTE 2026-07-28: Uses magnitude-only from KeefeLoss (ignores the
    small additional phase shift from viscothermal effects, typically
    <0.1% of propagation phase). This may need refinement for very
    narrow bores or high frequencies.
    """

    def __init__(self, temperature: float = 20.0):
        from backend.physics.losses import KeefeLoss
        self.loss = KeefeLoss(temperature=temperature)

    def propagate_cylindrical(
        self, length: float, radius: float, wavelength: float
    ) -> complex:
        phase = 2.0 * np.pi * length / wavelength
        loss_factor = self.loss.bore_loss(length, radius, wavelength)
        return np.exp(1j * phase) * abs(loss_factor)

    def propagate_conical(
        self, length: float, radius_in: float, radius_out: float, wavelength: float
    ) -> complex:
        # Use average radius for conical segment loss approximation
        avg_radius = (radius_in + radius_out) / 2.0
        phase = 2.0 * np.pi * length / wavelength
        loss_factor = self.loss.bore_loss(length, avg_radius, wavelength)
        return np.exp(1j * phase) * abs(loss_factor)
