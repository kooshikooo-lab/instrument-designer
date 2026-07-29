"""Cost function registry for the design pipeline."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from backend.tmm_acoustics import TMMInstrument


def _cost_intonation(inst: TMMInstrument, fingerings: list[list[str]],
                     targets: list[float], n_register: int = 1) -> float:
    """RMS cents intonation cost."""
    from backend.optimization.objectives import compute_intonation_cost
    return compute_intonation_cost(inst, fingerings, targets, n_register)


def _cost_smoothness(bore_radii: np.ndarray, **kwargs: Any) -> float:
    """Bore smoothness cost (second-difference std)."""
    from backend.physics.timbre_proxy import bore_smoothness
    return bore_smoothness(bore_radii)


def _cost_consistency(hole_diameters: list[float], bore_radius: float, **kwargs: Any) -> float:
    """Hole radiation consistency cost."""
    from backend.physics.timbre_proxy import hole_radiation_consistency
    return hole_radiation_consistency(hole_diameters, bore_radius)


def _cost_timbre_proxy(radii: np.ndarray, hole_diameters: list[float],
                       bore_radius: float, **kwargs: Any) -> float:
    """Combined timbre proxy: smoothness + consistency."""
    from backend.physics.timbre_proxy import compute_timbre_cost
    return compute_timbre_cost(radii, hole_diameters, bore_radius)


# Cost function registry
COST_REGISTRY: dict[str, dict] = {
    "intonation": {
        "fn": _cost_intonation,
        "tier": 2,
        "requires": ["inst", "fingerings", "targets", "n_register"],
    },
    "smoothness": {
        "fn": _cost_smoothness,
        "tier": 3,
        "requires": ["bore_radii"],
    },
    "consistency": {
        "fn": _cost_consistency,
        "tier": 3,
        "requires": ["hole_diameters", "bore_radius"],
    },
    "timbre_proxy": {
        "fn": _cost_timbre_proxy,
        "tier": 3,
        "requires": ["radii", "hole_diameters", "bore_radius"],
    },
    "magnitude_error": {
        "fn": "_cost_magnitude_error",
        "tier": 3,
        "requires": ["inst", "target_mags", "n_harmonics"],
    },
}

__all__ = [
    "COST_REGISTRY",
    "cost_smoothness",
    "cost_consistency",
    "cost_timbre_proxy",
    "cost_intonation",
]