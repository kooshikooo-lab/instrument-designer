"""Shared register detection for two-phase optimization.

Extracts the register detection logic from two_phase_optimizer.py so it can be
shared between the standalone optimizer and the selector's TwoPhaseOptimizer.

Per Discussion #23 decision: registers are derived ONCE from the initial geometry,
frozen, and never re-derived during optimization.
"""
from typing import List
import numpy as np

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.physics.bore_design import speed_of_sound_at


def cents_error(actual: float, target: float) -> float:
    """Cents error between actual and target frequency."""
    if actual <= 0 or target <= 0:
        return 1e10
    return 1200.0 * np.log2(actual / target)


def detect_registers(
    inst,
    targets: List[float],
    fingerings: List[List[str]],
    max_reg: int = 5,
    temperature: float = 20.0,
) -> List[int]:
    """Detect the best register for each fingering using peak search.

    NOTE: Per Discussion #23 decision, registers should be derived
    ONCE from the INITIAL geometry before optimization, frozen, and never
    re-derived post-hoc. This function should only be called on the INITIAL
    geometry before any optimization begins.
    """
    regs = []
    for tgt, fl in zip(targets, fingerings):
        best_pr = 1
        best_dist = 1e10
        for pr in range(1, max_reg + 1):
            try:
                wl = inst.find_resonance(SPEED_OF_SOUND / tgt, fl, n_register=pr)
                f = inst.frequency_from_wavelength(wl)
                dist = abs(cents_error(f, tgt))
                if dist < best_dist:
                    best_dist = dist
                    best_pr = pr
            except Exception:
                continue
        regs.append(best_pr)
    return regs


def build_initial_instrument(
    bore_length: float,
    n_holes: int,
    hole_lens: List[float],
    bore_radii: np.ndarray,
    hole_positions: np.ndarray,
    hole_diameters: np.ndarray,
    outer_diameter: float,
    closed_top: bool,
    loss_model=None,
    cone_step: float = 0.5,
):
    """Build initial instrument for register detection."""
    return tmm_instrument_from_radii(
        radii=bore_radii,
        bore_length=bore_length,
        hole_positions=sorted(hole_positions),
        hole_diameters=hole_diameters,
        hole_lengths=hole_lens,
        outer_diameter_mm=outer_diameter,
        closed_top=closed_top,
        cone_step=0.5,
        loss_model=loss_model,
    )