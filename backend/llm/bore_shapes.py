"""Bore profile generators for different instrument families."""
from __future__ import annotations

import math

import numpy as np


def generate_cylindrical_radii(length_mm: float, radius_mm: float,
                                flare_radius_mm: float | None = None,
                                n_cp: int = 6) -> np.ndarray:
    """Constant bore radius (straight cylinder)."""
    return np.full(n_cp, radius_mm)


def generate_conical_radii(length_mm: float, radius_start_mm: float,
                           radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    """Linear taper from start to end radius."""
    return np.linspace(radius_start_mm, radius_end_mm, n_cp)


def generate_parabolic_radii(length_mm: float, radius_min_mm: float,
                             radius_max_mm: float, n_cp: int = 6) -> np.ndarray:
    """Parabolic flare: r = r_min + (r_max - r_min) * t^2."""
    t = np.linspace(0, 1, n_cp)
    r = radius_min_mm + (radius_max_mm - radius_min_mm) * t ** 2
    return r


def generate_bessel_radii(length_mm: float, radius_start_mm: float,
                          radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    """Bessel-function inspired profile (placeholder, clipped)."""
    x = np.linspace(0.1, 1.0, n_cp)
    r = radius_start_mm + (radius_end_mm - radius_start_mm) * (1.0 - 1.0 / x) / (1.0 - 1.0)
    return np.clip(r, 1.0, 50.0)


def generate_exponential_radii(length_mm: float, radius_start_mm: float,
                               radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    """Exponential flare profile."""
    x = np.linspace(0, 1, n_cp)
    growth = math.log(radius_end_mm / max(radius_start_mm, 0.1))
    r = radius_start_mm * np.exp(growth * x)
    return r


BORE_SHAPE_GENERATORS = {
    "cylindrical": generate_cylindrical_radii,
    "conical": generate_conical_radii,
    "parabolic": generate_parabolic_radii,
    "bessel": generate_bessel_radii,
    "exponential": generate_exponential_radii,
}