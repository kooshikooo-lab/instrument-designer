"""Two-phase parametric bore shape optimizer with self-tuning scale cost.

Phase 1: DE — global search over bore shape parameters + optional hole positions
Phase 2: L-BFGS-B — local refinement from DE best solution

Cost function: computes actual resonances for ascending fingerings,
finds best-fitting pentatonic/major/minor scale from the fundamental,
and minimizes RMS cents deviation from that scale.

When optimize_holes=True, hole positions are included as optimization
variables via two offset parameters (linear + quadratic bend).
"""

import math
import time
import numpy as np
from scipy.optimize import differential_evolution, minimize as sp_min

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.physics.bore_generators import (
    BORE_SHAPE_GENERATORS, BORE_TYPE_META,
)

_c = SPEED_OF_SOUND
_LENGTH_BOUNDS = (200.0, 1200.0)
_BORE_CTRL = 6
_HOLE_OFFSET_BOUNDS = (-100.0, 100.0)

SCALE_INTERVALS = {
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "major":           [0, 2, 4, 5, 7, 9, 11],
    "minor":           [0, 2, 3, 5, 7, 8, 10],
}


def _param_keys(bore_type: str) -> list[str]:
    meta = BORE_TYPE_META.get(bore_type, {})
    return list(meta.get("params", {}).keys())


def _param_bounds(bore_type: str) -> list[tuple[float, float]]:
    meta = BORE_TYPE_META.get(bore_type, {})
    return [(v[0], v[1]) for v in meta.get("params", {}).values()]


def _generate_radii(bore_type: str, length_mm: float, params: dict, n_cp: int = _BORE_CTRL):
    """Dispatch to bore generator using meta-specified parameter names."""
    gen = BORE_SHAPE_GENERATORS[bore_type]
    meta = BORE_TYPE_META.get(bore_type, {})
    pnames = list(meta.get("params", {}).keys())

    if bore_type == "spline":
        cp = params.get("control_points", [(0, 7.0), (length_mm, 10.0)])
        return gen(length_mm, cp, n_samples=50)

    kwargs = {k: params[k] for k in pnames}
    if bore_type in ("spiral", "ridged"):
        kwargs["n_cp"] = 50
    else:
        kwargs["n_cp"] = n_cp
    return gen(length_mm, **kwargs)


def _build_ascending_fingerings(n_holes: int, n_notes: int) -> list[list[str]]:
    """Ascending fingerings: hole 0 = nearest bell, note i opens holes 0..i-1."""
    fingerings = []
    for i in range(min(n_notes, n_holes + 1)):
        fng = ["closed"] * n_holes
        for j in range(min(i, n_holes)):
            fng[j] = "open"
        fingerings.append(fng)
    while len(fingerings) < n_notes:
        fingerings.append(["open"] * n_holes)
    return fingerings


def _apply_hole_offsets(base_positions: list[float], offset_a: float, offset_b: float, length_mm: float) -> list[float]:
    """Apply linear+quadratic offset to equally-spaced hole positions."""
    n = len(base_positions)
    if n == 0:
        return []
    hpos = []
    for i, p in enumerate(base_positions):
        nr = (i + 1) / n
        hp = p + offset_a * nr + offset_b * nr ** 2
        hpos.append(max(5.0, min(length_mm - 5.0, hp)))
    hpos.sort()
    return hpos


def _compute_resonances(inst, fingerings, closed_top: bool, n_notes: int, bore_length_mm: float = 600.0):
    """Compute resonant frequencies for each fingering. Returns list of Hz."""
    n_reg = 1 if closed_top else 2
    f0 = _c / (2 * bore_length_mm) if closed_top else _c / (4 * bore_length_mm)
    freqs = []
    for i in range(min(n_notes, len(fingerings))):
        try:
            guess_wl = _c / max(f0 * (i + 1) * 0.8, 1.0)
            wl = inst.find_resonance(guess_wl, fingerings[i], n_register=n_reg)
            f = inst.frequency_from_wavelength(wl) if wl and wl > 0 else 0.0
        except Exception:
            f = 0.0
        freqs.append(f)
    return freqs


def _best_scale_cost(resonances: list[float]) -> tuple[float, str, list[float]]:
    """Score resonances against candidate scales. Returns (best_rms_cents, best_scale_name, best_scale_freqs)."""
    valid = [f for f in resonances if f > 0]
    if len(valid) < 3:
        return 1e10, "none", []
    f0 = valid[0]
    if f0 <= 0:
        return 1e10, "none", []

    best_score = 1e10
    best_name = "none"
    best_freqs = []

    for scale_name, intervals in SCALE_INTERVALS.items():
        if len(intervals) < 2:
            continue
        scale_freqs = [f0 * (2 ** (s / 12.0)) for s in intervals]
        cents_errs = []
        for f in valid[:len(intervals)]:
            cents = min(abs(1200.0 * math.log2(f / sf)) for sf in scale_freqs)
            cents_errs.append(cents)
        rms = math.sqrt(sum(e * e for e in cents_errs) / len(cents_errs))
        if rms < best_score:
            best_score = rms
            best_name = scale_name
            best_freqs = scale_freqs

    return best_score, best_name, best_freqs


def _build_scale_bore_cost(
    bore_type: str,
    fingerings: list[list[str]],
    hole_positions: list[float],
    hole_diameters: list[float],
    closed_top: bool,
    optimize_holes: bool = False,
):
    """Build cost(x) -> float RMS cents from best-fitting scale.

    When optimize_holes=True, x includes [bore_length, params..., hole_offset_a, hole_offset_b].
    hole_positions are used as base positions that get offset.
    """
    pkeys = _param_keys(bore_type)
    n_holes = len(hole_positions)
    hole_lengths = [3.75] * n_holes
    n_notes = len(fingerings)
    n_extra = 2 if optimize_holes else 0

    def cost(x: np.ndarray) -> float:
        length_mm = float(x[0])
        params = {k: float(x[1 + i]) for i, k in enumerate(pkeys)}

        if optimize_holes:
            offset_a = float(x[1 + len(pkeys)])
            offset_b = float(x[2 + len(pkeys)])
            hpos = _apply_hole_offsets(hole_positions, offset_a, offset_b, length_mm)
        else:
            hpos = hole_positions

        try:
            radii = _generate_radii(bore_type, length_mm, params)
        except Exception:
            return 1e10

        try:
            inst = tmm_instrument_from_radii(
                radii_mm=np.asarray(radii),
                bore_length_mm=length_mm,
                hole_positions_mm=hpos,
                hole_diameters_mm=hole_diameters,
                hole_lengths_mm=hole_lengths,
                closed_top=closed_top,
            )
        except Exception:
            return 1e10

        resonances = _compute_resonances(inst, fingerings, closed_top, n_notes, length_mm)
        rms, _, _ = _best_scale_cost(resonances)
        return rms

    return cost


def _build_inst(bore_type, length_mm, params, hole_positions, hole_diameters, closed_top):
    radii = _generate_radii(bore_type, length_mm, params)
    n_holes = len(hole_positions)
    hl = [3.75] * n_holes
    return tmm_instrument_from_radii(
        radii_mm=np.asarray(radii),
        bore_length_mm=length_mm,
        hole_positions_mm=hole_positions,
        hole_diameters_mm=hole_diameters,
        hole_lengths_mm=hl,
        closed_top=closed_top,
    )


def bore_phase1_de_search(
    bore_type: str, fingerings: list[list[str]],
    hole_positions: list[float], hole_diameters: list[float],
    closed_top: bool,
    optimize_holes: bool = False,
    length_bounds: tuple[float, float] = _LENGTH_BOUNDS,
    param_bounds_list: list | None = None,
    popsize: int = 15, maxiter: int = 25, seed: int = 42,
):
    """Phase 1: DE over [bore_length, params...] + optionally [offset_a, offset_b]."""
    cost_fn = _build_scale_bore_cost(
        bore_type, fingerings, hole_positions, hole_diameters, closed_top,
        optimize_holes=optimize_holes,
    )
    pbl = param_bounds_list or _param_bounds(bore_type)
    bounds = [length_bounds] + pbl
    if optimize_holes:
        bounds += [_HOLE_OFFSET_BOUNDS] * 2

    t0 = time.time()
    result = differential_evolution(
        cost_fn, bounds, seed=seed, maxiter=maxiter,
        popsize=popsize, tol=1e-6, mutation=(0.5, 1.5), recombination=0.9,
    )
    elapsed = time.time() - t0

    x_best = result.x
    pkeys = _param_keys(bore_type)
    length_mm = float(x_best[0])
    params = {k: float(x_best[1 + i]) for i, k in enumerate(pkeys)}
    hpos = hole_positions
    if optimize_holes:
        hpos = _apply_hole_offsets(hole_positions, float(x_best[1 + len(pkeys)]), float(x_best[2 + len(pkeys)]), length_mm)
    inst = _build_inst(bore_type, length_mm, params, hpos, hole_diameters, closed_top)

    return x_best, float(result.fun), elapsed, inst


def bore_phase2_lbfgsb_refine(
    x0: np.ndarray,
    bore_type: str, fingerings: list[list[str]],
    hole_positions: list[float], hole_diameters: list[float],
    closed_top: bool,
    optimize_holes: bool = False,
    length_bounds: tuple[float, float] = _LENGTH_BOUNDS,
    param_bounds_list: list | None = None,
    maxiter: int = 100,
):
    """Phase 2: L-BFGS-B local refinement from Phase 1 solution."""
    cost_fn = _build_scale_bore_cost(
        bore_type, fingerings, hole_positions, hole_diameters, closed_top,
        optimize_holes=optimize_holes,
    )
    pbl = param_bounds_list or _param_bounds(bore_type)
    bounds = [length_bounds] + pbl
    if optimize_holes:
        bounds += [_HOLE_OFFSET_BOUNDS] * 2

    t0 = time.time()
    result = sp_min(cost_fn, x0, method="L-BFGS-B", bounds=bounds,
                    options={"maxiter": maxiter, "ftol": 1e-8})
    elapsed = time.time() - t0

    x_opt = result.x
    pkeys = _param_keys(bore_type)
    length_mm = float(x_opt[0])
    params = {k: float(x_opt[1 + i]) for i, k in enumerate(pkeys)}
    hpos = hole_positions
    if optimize_holes:
        hpos = _apply_hole_offsets(hole_positions, float(x_opt[1 + len(pkeys)]), float(x_opt[2 + len(pkeys)]), length_mm)
    inst = _build_inst(bore_type, length_mm, params, hpos, hole_diameters, closed_top)

    return x_opt, float(result.fun), elapsed, inst


def two_phase_optimize_bore_parameters(
    bore_type: str,
    targets: list[float] | None = None,
    fingerings: list[list[str]] | None = None,
    hole_positions: list[float] | None = None,
    hole_diameters: list[float] | None = None,
    bore_length_mm: float = 600.0,
    radius_params: dict | None = None,
    closed_top: bool = True,
    optimize_holes: bool = False,
    pop_size: int = 15,
    n_generations: int = 25,
    seed: int = 42,
) -> dict:
    """Two-phase bore optimization using self-tuning scale cost.

    Computes actual resonances for ascending fingerings, finds best
    pentatonic/major/minor scale match, and minimizes RMS cents error.

    When optimize_holes=True, two hole offset parameters are added to the
    search space to fine-tune hole positions along with bore shape.
    """
    pkeys = _param_keys(bore_type)
    if not pkeys and bore_type != "spline":
        raise ValueError(f"No tunable parameters for bore type '{bore_type}'")

    rp = radius_params or {}
    pbl = _param_bounds(bore_type)

    n_holes = len(hole_positions) if hole_positions else 6
    if fingerings is None:
        n_notes = len(targets) if targets else 8
        fingerings = _build_ascending_fingerings(n_holes, n_notes)
    if hole_positions is None:
        spacing = bore_length_mm / (n_holes + 1)
        hole_positions = [spacing * (i + 1) for i in range(n_holes)]
    if hole_diameters is None:
        hole_diameters = [7.0] * n_holes

    x0 = [bore_length_mm]
    for k in pkeys:
        meta = BORE_TYPE_META[bore_type]["params"][k]
        x0.append(rp.get(k, meta[2]))
    if optimize_holes:
        x0 += [0.0, 0.0]
    x0 = np.array(x0)

    x1, cost1, t1, inst1 = bore_phase1_de_search(
        bore_type, fingerings, hole_positions, hole_diameters, closed_top,
        optimize_holes=optimize_holes,
        length_bounds=_LENGTH_BOUNDS, param_bounds_list=pbl,
        popsize=pop_size, maxiter=n_generations, seed=seed,
    )

    x2, cost2, t2, inst2 = bore_phase2_lbfgsb_refine(
        x1, bore_type, fingerings, hole_positions, hole_diameters, closed_top,
        optimize_holes=optimize_holes,
        length_bounds=_LENGTH_BOUNDS, param_bounds_list=pbl,
    )

    length_opt = float(x2[0])
    params_opt = {k: float(x2[1 + i]) for i, k in enumerate(pkeys)}
    radii_opt = _generate_radii(bore_type, length_opt, params_opt)

    hpos_opt = hole_positions
    hole_offsets = None
    if optimize_holes:
        hole_offsets = (float(x2[1 + len(pkeys)]), float(x2[2 + len(pkeys)]))
        hpos_opt = _apply_hole_offsets(hole_positions, hole_offsets[0], hole_offsets[1], length_opt)

    final_inst = _build_inst(bore_type, length_opt, params_opt, hpos_opt, hole_diameters, closed_top)
    resonances = _compute_resonances(final_inst, fingerings, closed_top, len(fingerings), length_opt)
    scale_rms, scale_name, scale_freqs = _best_scale_cost(resonances)
    f0 = resonances[0] if resonances and resonances[0] > 0 else 0.0

    init_cost_fn = _build_scale_bore_cost(
        bore_type, fingerings, hole_positions, hole_diameters, closed_top,
        optimize_holes=optimize_holes,
    )
    init_cost = init_cost_fn(x0)

    return {
        "phase1": {
            "variables": x1.tolist(),
            "cost": round(cost1, 4),
            "time_s": round(t1, 4),
            "instrument": inst1,
        },
        "phase2": {
            "variables": x2.tolist(),
            "cost": round(cost2, 4),
            "time_s": round(t2, 4),
            "instrument": inst2,
        },
        "total_time_s": round(t1 + t2, 3),
        "phase1_time_s": round(t1, 3),
        "refine_time_s": round(t2, 3),
        "initial_cost_rms_cents": round(float(init_cost), 3),
        "de_cost_rms_cents": round(cost1, 3),
        "final_cost_rms_cents": round(cost2, 3),
        "bore_type": bore_type,
        "bore_length_mm": round(length_opt, 2),
        "optimized_params": {k: round(v, 4) for k, v in params_opt.items()},
        "hole_offsets": [round(v, 2) for v in hole_offsets] if hole_offsets else None,
        "hole_positions_opt": [round(p, 2) for p in hpos_opt],
        "radii": [float(r) for r in radii_opt],
        "n_holes": len(hole_positions),
        "fundamental_hz": round(f0, 2),
        "best_scale": scale_name,
        "scale_rms_cents": round(scale_rms, 2),
        "resonances_hz": [round(f, 2) for f in resonances],
        "scale_frequencies_hz": [round(f, 2) for f in scale_freqs],
        "optimize_holes": optimize_holes,
        "best_instrument": inst2,
    }
