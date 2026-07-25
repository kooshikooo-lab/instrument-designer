"""Excitation model interface.

Handles source models (reed, lip, air jet).
"""
from abc import ABC, abstractmethod
import numpy as np


class ExcitationModel(ABC):
    """Abstract base class for excitation models."""

    @abstractmethod
    def input_impedance(self, wavelength: float) -> complex:
        """Compute input impedance of the excitation.

        Args:
            wavelength: acoustic wavelength in mm

        Returns:
            Complex input impedance (normalized)
        """
        pass


class ReedExcitation(ExcitationModel):
    """Single reed excitation (clarinet, saxophone).

    The reed acts as a pressure-controlled valve.
    Input impedance is approximately infinite (rigid termination)
    for impedance calculation purposes.
    """

    def input_impedance(self, wavelength: float) -> complex:
        # For impedance calculation, reed is approximately rigid
        return float('inf')


class LipExcitation(ExcitationModel):
    """Lip reed excitation (brass instruments)."""

    def input_impedance(self, wavelength: float) -> complex:
        # TODO: implement lip model
        raise NotImplementedError


class AirJetExcitation(ExcitationModel):
    """Air jet excitation (flute, recorder)."""

    def input_impedance(self, wavelength: float) -> complex:
        # TODO: implement air jet model
        raise NotImplementedError


class NoExcitation(ExcitationModel):
    """No excitation (for passive impedance calculation)."""

    def input_impedance(self, wavelength: float) -> complex:
        return float('inf')
