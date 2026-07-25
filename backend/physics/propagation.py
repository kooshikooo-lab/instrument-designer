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
    """Viscothermal propagation with losses (future)."""

    def propagate_cylindrical(
        self, length: float, radius: float, wavelength: float
    ) -> complex:
        # TODO: implement Keefe/Nederveen losses
        raise NotImplementedError

    def propagate_conical(
        self, length: float, radius_in: float, radius_out: float, wavelength: float
    ) -> complex:
        raise NotImplementedError
