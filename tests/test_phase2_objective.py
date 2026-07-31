"""
Regression tests for the Phase 2 L-BFGS-B objective in two_phase_optimizer.

Guards the finding that the sin^2 phase costs (phase_cost / phase_cost_with_offset)
are register-blind (periodic in the phase deviation) and therefore unsuitable as
the Phase 2 refinement objective: a local optimizer can drift every note to the
next register and report ~0 cost while the instrument is hundreds of cents off.

The Phase 2 objective is the phase-based ABSOLUTE cost peak_cost_nearest (RMS
cents, located via resonance_phase / find_resonance), which is register-safe and
smooth under geometry perturbation.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.tmm_acoustics import tmm_instrument_from_radii
from backend.two_phase_optimizer import (
    phase2_lbfgsb_refine, detect_registers, peak_cost_nearest,
)

BORE_LENGTH = 240.0
N_HOLES = 5
HOLE_LENS = [3.0] * N_HOLES
TARGETS = [523.25, 587.33, 659.25, 698.46, 783.99]
FINGERINGS = [["open"] * (N_HOLES - i) + ["closed"] * i for i in range(N_HOLES)]


def _build(radii, hd, hp):
    return tmm_instrument_from_radii(
        radii, BORE_LENGTH, sorted(hp), hd, HOLE_LENS,
        outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
    )


def _baseline():
    radii = np.array([7.5] * 6)
    hd = np.array([6.5] * N_HOLES)
    hp = np.array([40.0 + i * (150.0 / N_HOLES) for i in range(N_HOLES)])
    return radii, hd, hp


def _recorder_baseline():
    """Recorder-like 320mm/7-hole config; registers sit in the register-2 basin."""
    radii = np.array([8.5] * 6)
    hd = np.array([7.0] * 7)
    hp = np.array([80.0, 110.0, 140.0, 170.0, 200.0, 230.0, 260.0])
    return radii, hd, hp


RECORDER_BORE_LENGTH = 320.0
RECORDER_TARGETS = [523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77]
RECORDER_FINGERINGS = [
    ["open"] * 7,
    ["open"] * 6 + ["closed"],
    ["open"] * 5 + ["closed"] * 2,
    ["open"] * 4 + ["closed"] * 3,
    ["open"] * 3 + ["closed"] * 4,
    ["open"] * 2 + ["closed"] * 5,
    ["open"] + ["closed"] * 6,
]


def test_sin2_phase_cost_is_register_blind():
    """sin^2 phase cost cannot distinguish register n from n+1; absolute cost can."""
    radii, hd, hp = _baseline()
    inst = _build(radii, hd, hp)
    regs = detect_registers(inst, TARGETS, FINGERINGS)
    shifted = [r + 1 for r in regs]

    sin2_regs = inst.phase_cost(TARGETS, FINGERINGS, n_register=regs)
    sin2_shifted = inst.phase_cost(TARGETS, FINGERINGS, n_register=shifted)
    assert abs(sin2_regs - sin2_shifted) < 1e-6

    peak_regs = peak_cost_nearest(inst, TARGETS, FINGERINGS, regs)
    peak_shifted = peak_cost_nearest(inst, TARGETS, FINGERINGS, shifted)
    assert abs(peak_regs - peak_shifted) > 100.0


def test_peak_cost_smooth_under_small_perturbation():
    """Phase-based absolute cost is smooth under small geometry changes near
    the register basin (gradient-friendly for L-BFGS-B)."""
    radii, hd, hp = _recorder_baseline()
    inst = tmm_instrument_from_radii(
        radii, RECORDER_BORE_LENGTH, hp, hd, [3.5] * 7,
        outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
    )
    regs = detect_registers(inst, RECORDER_TARGETS, RECORDER_FINGERINGS)
    p0 = peak_cost_nearest(inst, RECORDER_TARGETS, RECORDER_FINGERINGS, regs)

    radii2 = radii.copy()
    radii2[2] += 0.2
    inst2 = tmm_instrument_from_radii(
        radii2, RECORDER_BORE_LENGTH, hp, hd, [3.5] * 7,
        outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
    )
    p2 = peak_cost_nearest(inst2, RECORDER_TARGETS, RECORDER_FINGERINGS, regs)
    assert abs(p2 - p0) < 5.0


def test_phase2_refinement_improves_absolute_pitch():
    """Phase 2 refinement reduces the absolute RMS cents error and reports an
    objective value consistent with the true peak cost (i.e. no register cheat)."""
    radii, hd, hp = _baseline()
    inst = _build(radii, hd, hp)
    regs = detect_registers(inst, TARGETS, FINGERINGS)
    p_start = peak_cost_nearest(inst, TARGETS, FINGERINGS, regs)

    x0 = np.concatenate([radii, hd, hp])
    x0[2] += 0.2
    x0[6 + N_HOLES] += 0.3

    x2, cost2, _ = phase2_lbfgsb_refine(
        x0, BORE_LENGTH, N_HOLES, HOLE_LENS, TARGETS, FINGERINGS, regs,
        bore_bounds_range=(3.0, 18.0),
        hole_pos_bounds_range=(10.0, BORE_LENGTH - 10.0),
        n_iters=12, verbose=False,
    )
    inst2 = _build(x2[:6], x2[6:6 + N_HOLES], x2[6 + N_HOLES:])
    p_fin = peak_cost_nearest(inst2, TARGETS, FINGERINGS, regs)

    assert p_fin < p_start
    assert abs(cost2 - p_fin) < 1e-3
