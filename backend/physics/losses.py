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
    """Keefe viscothermal losses for cylindrical bore and tonehole chimneys.

    References:
    - Keefe, D. H. (1981). "Acoustical wave propagation in cylindrical ducts."
    - Keefe, D. H. (1982). "Woodwind tone hole acoustics."
    - Keefe, D. H. (1984). "Acoustical wave propagation in cylindrical ducts."

    Air properties at 20°C:
    - ρ = 1.204 kg/m³
    - η = 1.846e-5 Pa·s (dynamic viscosity)
    - κ = 0.02624 W/(m·K) (thermal conductivity)
    - c_p = 1005 J/(kg·K) (specific heat at constant pressure)
    - γ = 1.4 (ratio of specific heats)
    - Pr = 0.71 (Prandtl number)
    """

    # Air properties at 20°C
    RHO = 1.204  # kg/m³
    ETA = 1.846e-5  # Pa·s
    KAPPA = 0.02624  # W/(m·K)
    CP = 1005.0  # J/(kg·K)
    GAMMA = 1.4
    PR = 0.71

    def __init__(self, temperature: float = 20.0):
        """Initialize with temperature in °C."""
        # Temperature correction for air properties
        T = 273.15 + temperature
        T0 = 293.15  # 20°C reference
        self.rho = self.RHO * (T0 / T)
        self.eta = self.ETA * (T / T0) ** 1.5 * (T0 + 110.4) / (T + 110.4)  # Sutherland's formula
        self.kappa = self.KAPPA * (T / T0) ** 0.75
        self.cp = self.CP
        self.gamma = self.GAMMA
        self.pr = self.PR

    def _boundary_layers(self, wavelength: float):
        """Compute viscous and thermal boundary layer thicknesses in mm."""
        # wavelength in mm, convert to m
        lam_m = wavelength * 1e-3
        f = 343200 / lam_m  # frequency in Hz (using c=343.2 m/s for boundary layers)
        omega = 2 * np.pi * f

        # Viscous boundary layer: δ_v = sqrt(2η/ρω)
        delta_v = np.sqrt(2 * self.eta / (self.rho * omega))  # in meters
        # Thermal boundary layer: δ_t = sqrt(2κ/(ρ c_p ω))
        delta_t = np.sqrt(2 * self.kappa / (self.rho * self.cp * omega))

        return delta_v * 1000, delta_t * 1000  # convert to mm

    def bore_loss(self, length: float, radius: float, wavelength: float) -> complex:
        """Complex propagation constant for cylindrical bore with viscothermal losses.

        Returns exp(-γ * length) where γ = α + iβ is the complex propagation constant.

        The loss factor magnitude < 1, phase gives additional phase shift from losses.
        """
        if radius <= 0 or length <= 0 or wavelength <= 0:
            return 1.0

        delta_v, delta_t = self._boundary_layers(wavelength)

        # Normalized boundary layer thicknesses
        r = radius
        epsilon_v = delta_v / r
        epsilon_t = delta_t / r

        # Complex propagation constant from Keefe 1984
        # γ = (ω/c) * (1 + (1+i)/√2 * [(γ-1)δ_t/r + δ_v/r])
        # For loss factor over length L: exp(-γ * L)
        # ω/c = 2π/λ
        omega_over_c = 2 * np.pi / wavelength

        factor = (1 + 1j) / np.sqrt(2) * ((self.gamma - 1) * epsilon_t + epsilon_v)
        gamma = omega_over_c * (1 + factor)  # complex propagation constant

        # Loss factor = exp(-γ * length)
        return np.exp(-gamma * length)

    def hole_loss(self, hole_radius: float, hole_length: float, wavelength: float) -> complex:
        """Loss factor for tonehole chimney.

        For a short cylindrical chimney, we apply the same viscothermal model.
        The chimney is typically short (3-5mm) so losses are small but non-zero.
        """
        if hole_radius <= 0 or hole_length <= 0 or wavelength <= 0:
            return 1.0

        delta_v, delta_t = self._boundary_layers(wavelength)

        r = hole_radius
        epsilon_v = delta_v / r
        epsilon_t = delta_t / r

        omega_over_c = 2 * np.pi / wavelength
        factor = (1 + 1j) / np.sqrt(2) * ((self.gamma - 1) * epsilon_t + epsilon_v)
        gamma = omega_over_c * (1 + factor)

        return np.exp(-gamma * hole_length)
