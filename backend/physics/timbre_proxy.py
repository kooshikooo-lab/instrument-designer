"""Bore-geometry timbre proxy — pure numpy, no TMM dependency.

Provides fast-to-evaluate proxy functions that correlate with perceptual
timbre consistency, used during optimization when direct impedance-peak
computation is too slow.

References
----------
- Ernoult et al. (2020) JASA: intonation and timbre tradeoff
- Petiot et al. (2025) JASA: bore-geometry proxies for timbre
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def bore_smoothness(radii: np.ndarray) -> float:
    """Standard deviation of bore radius second differences.

    Measures how smoothly the bore tapers.  Lower = smoother profile,
    which correlates with more consistent timbre across the playing range.
    """
    if len(radii) < 3:
        return 0.0
    dd = np.diff(radii, n=2)
    return float(np.std(dd))


def hole_radiation_consistency(
    hole_diameters: Sequence[float],
    bore_radius: float,
) -> float:
    """Standard deviation of per-hole radiation ratios.

    Each hole's radiation ratio is ``(d / (2*R))^2``.
    Lower std = more uniform hole radiation = more consistent timbre.
    """
    if not hole_diameters or bore_radius <= 0:
        return 0.0
    ratios = np.array([(d / (2.0 * bore_radius)) ** 2 for d in hole_diameters])
    return float(np.std(ratios))


def compute_timbre_cost(
    radii: np.ndarray,
    hole_diameters: Sequence[float],
    bore_radius: float,
    w_smooth: float = 1.0,
    w_consist: float = 0.5,
) -> float:
    """Combined bore-geometry timbre proxy (lower = better).

    Parameters
    ----------
    radii : ndarray
        Bore radii at control-point positions (mm).
    hole_diameters : sequence of float
        Tone-hole diameters (mm).
    bore_radius : float
        Nominal bore radius (mm), used to normalise hole radiation.
    w_smooth : float, optional
        Weight for the bore-smoothness term (default 1.0).
    w_consist : float, optional
        Weight for the hole-radiation-consistency term (default 0.5).

    Returns
    -------
    float
        Combined timbre cost (dimensionless, lower is better).
    """
    smooth = bore_smoothness(radii)
    consist = hole_radiation_consistency(hole_diameters, bore_radius)
    return w_smooth * smooth + w_consist * consist
