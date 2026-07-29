"""Optimization objective functions — TMM-aware intonation and timbre costs."""
from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from backend.tmm_acoustics import SPEED_OF_SOUND, TMMInstrument, tmm_instrument_from_radii
from backend.physics.timbre_proxy import compute_timbre_cost

_c = SPEED_OF_SOUND


def _build_fingerings(n_holes: int, closed_top: bool) -> list[list[str]]:
    """Build cumulative fingering sets for a sequential-hole instrument."""
    fingerings: list[list[str]] = []
    for k in range(n_holes):
        fingerings.append(["open"] * (k + 1) + ["closed"] * (n_holes - k - 1))
    if closed_top:
        fingerings.insert(0, ["closed"] * n_holes)
    return fingerings


def compute_intonation_cost(
    inst: TMMInstrument,
    fingerings: list[list[str]],
    targets: Sequence[float],
    n_register: int = 1,
) -> float:
    """RMS cents deviation from target frequencies.

    Returns 1e10 on evaluation failure.
    """
    tw = [_c / f for f in targets]
    try:
        freqs = inst.compute_fingered_frequencies(tw, fingerings, n_register)
    except Exception:
        return 1e10

    cents = []
    for f, t in zip(freqs, targets):
        if f > 0 and math.isfinite(f):
            cents.append(1200.0 * math.log2(f / t))

    if not cents:
        return 1e10
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    return float(np.sqrt(np.mean(ca ** 2)))


def evaluate_bi_objective(
    radii: np.ndarray,
    bore_length: float,
    hole_positions: list[float],
    hole_diameters: list[float],
    hole_lengths: list[float],
    closed_top: bool,
    targets: Sequence[float],
    bore_radius: float,
    outer_diameter: float,
    n_register: int | None = None,
    loss_model: object | None = None,
) -> tuple[float, float]:
    """Evaluate both intonation and timbre for a candidate instrument.

    Returns ``(intonation_cost, timbre_cost)``.  Both are lower-is-better.
    Returns ``(1e10, 1e10)`` on construction or evaluation failure.
    """
    if n_register is None:
        n_register = 1 if closed_top else 2

    try:
        inst = tmm_instrument_from_radii(
            radii, bore_length, hole_positions, hole_diameters, hole_lengths,
            outer_diameter_mm=outer_diameter, closed_top=closed_top,
            cone_step=0.5, loss_model=loss_model,
        )
    except Exception:
        return 1e10, 1e10

    n_holes = len(hole_positions)
    fingerings = _build_fingerings(n_holes, closed_top)
    intonation = compute_intonation_cost(inst, fingerings, targets, n_register)
    timbre = compute_timbre_cost(radii, hole_diameters, bore_radius)
    return intonation, timbre
