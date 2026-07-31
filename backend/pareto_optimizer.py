"""
Bi-objective Pareto optimization for wind instrument design.

Optimizes intonation (frequency accuracy) vs timbre (bore smoothness,
hole radiation consistency) using weighted-sum sweep (scipy) or NSGA-II (pymoo).

Usage:
    from backend.pareto_optimizer import pareto_sweep, run_pareto

    # Fast weighted-sum sweep
    results = pareto_sweep(cfg, n_weights=8)

    # Thorough NSGA-II
    points, designs, elapsed = run_pareto(cfg, pop_size=30, n_gen=50)
"""

from __future__ import annotations

import math
import time
from typing import Any, List, Tuple

import numpy as np
from scipy.optimize import minimize

from backend.tmm_acoustics import SPEED_OF_SOUND, TMMInstrument, tmm_instrument_from_radii
from backend.benchmark_all import sequential_refined


def build_fingerings(n_holes: int, closed_top: bool) -> list[list[str]]:
    fingerings: list[list[str]] = []
    if closed_top:
        for k in range(n_holes + 1):
            fing = ["closed"] * n_holes
            for j in range(k):
                fing[n_holes - 1 - j] = "open"
            fingerings.append(fing)
    else:
        for k in range(n_holes):
            fing = ["closed"] * n_holes
            fing[0] = "open"
            for j in range(k):
                fing[n_holes - 1 - j] = "open"
            fingerings.append(fing)
    return fingerings


def compute_timbre_cost(
    radii: np.ndarray,
    hole_diameters: list[float],
    bore_radius: float,
    w_smooth: float = 1.0,
    w_consist: float = 0.5,
) -> float:
    if len(radii) < 3:
        bore_smoothness = 0.0
    else:
        second_diff = np.diff(radii, n=2)
        bore_smoothness = float(np.std(second_diff)) if len(second_diff) > 0 else 0.0

    if len(hole_diameters) < 2:
        hole_radiation_consistency = 0.0
    else:
        ratios = [(d / (2.0 * bore_radius)) ** 2 for d in hole_diameters]
        hole_radiation_consistency = float(np.std(ratios))

    return w_smooth * bore_smoothness + w_consist * hole_radiation_consistency


def compute_intonation_cost(
    inst: TMMInstrument,
    fingerings: list[list[str]],
    targets: list[float],
    n_register: int | list[int] = 1,
) -> float:
    wavelengths = [SPEED_OF_SOUND / f for f in targets]
    try:
        freqs = inst.compute_fingered_frequencies(wavelengths, fingerings, n_register)
    except Exception:
        return 1e10
    cents: list[float] = []
    for a, t in zip(freqs, targets):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
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
    targets: list[float],
    bore_radius: float,
    outer_diameter: float,
    n_register: int | None = None,
    loss_model: object = None,
) -> tuple[float, float]:
    if n_register is None:
        n_register = 1 if closed_top else 2
    try:
        inst = tmm_instrument_from_radii(
            radii, bore_length, hole_positions, hole_diameters, hole_lengths,
            outer_diameter, closed_top, 0.5, loss_model,
        )
    except Exception:
        return (1e10, 1e10)

    fingerings = build_fingerings(len(hole_positions), closed_top)
    int_cost = compute_intonation_cost(inst, fingerings, targets, n_register=n_register)
    timbre_cost = compute_timbre_cost(radii, hole_diameters, bore_radius)
    return (int_cost, timbre_cost)


def pareto_sweep(
    cfg: dict[str, Any],
    n_cp: int = 6,
    seed: int = 42,
    n_weights: int = 8,
    maxiter: int = 100,
    verbose: bool = True,
    loss_model: object = None,
) -> list[tuple[float, float, float, float]]:
    rng = np.random.RandomState(seed)
    closed_top: bool = cfg["closed_top"]
    targets: list[float] = cfg["targets"]
    bore_radius: float = cfg["bore_radius"]
    outer_diameter: float = cfg["outer_diameter"]
    n_register: int = 1 if closed_top else 2

    baseline = sequential_refined(cfg)
    L_base: float = baseline[1]
    hp_seq: list[float] = baseline[2]
    hd_seq: list[float] = baseline[3] if len(baseline) > 4 else [cfg["hole_diameter"]] * len(hp_seq)

    n_h = len(hp_seq)
    hl: list[float] = [cfg["hole_length"]] * n_h

    bounds: list[tuple[float, float]] = [(3.0, 15.0)] * n_cp
    for i in range(n_h):
        lo = max((hp_seq[i - 1] + 5.0) if i > 0 else 30.0, 30.0)
        hi = min((hp_seq[i + 1] - 5.0) if i < n_h - 1 else L_base * 1.3 - 30.0, L_base * 1.3 - 30.0)
        if lo > hi:
            lo, hi = hp_seq[i] - 2.0, hp_seq[i] + 2.0
        bounds.append((lo, hi))
    hd_min = bore_radius * 0.4
    hd_max = bore_radius * 0.9
    for _ in range(n_h):
        bounds.append((hd_min, hd_max))

    x0 = np.concatenate([
        np.full(n_cp, bore_radius),
        np.array(hp_seq),
        np.array(hd_seq),
    ])
    x0 = np.clip(x0, [b[0] for b in bounds], [b[1] for b in bounds])

    weights = np.linspace(0.0, 1.0, n_weights)
    results: list[tuple[float, float, float, float]] = []

    for w_int in weights:
        w_timbre = 1.0 - w_int

        def objective(x: np.ndarray, wi: float = w_int, wt: float = w_timbre) -> float:
            rad = x[:n_cp]
            hp = sorted(x[n_cp:n_cp + n_h].tolist())
            hd = x[n_cp + n_h:].tolist()
            int_cost, timbre_cost = evaluate_bi_objective(
                rad, L_base, hp, hd, hl, closed_top, targets,
                bore_radius, outer_diameter, n_register, loss_model,
            )
            return wi * int_cost + wt * timbre_cost

        res = minimize(objective, x0, method="L-BFGS-B", bounds=bounds,
                       options={"maxiter": maxiter, "ftol": 1e-8})
        x_opt = np.clip(res.x, [b[0] for b in bounds], [b[1] for b in bounds])
        rad_opt = x_opt[:n_cp]
        hp_opt = sorted(x_opt[n_cp:n_cp + n_h].tolist())
        hd_opt = x_opt[n_cp + n_h:].tolist()
        int_opt, timbre_opt = evaluate_bi_objective(
            rad_opt, L_base, hp_opt, hd_opt, hl, closed_top, targets,
            bore_radius, outer_diameter, n_register, loss_model,
        )
        results.append((float(w_int), float(int_opt), float(timbre_opt), float(L_base)))
        if verbose:
            print(f"  w_int={w_int:.3f}  int={int_opt:.3f}c  timbre={timbre_opt:.6f}  L={L_base:.1f}mm")

    return results


def run_pareto(
    cfg: dict[str, Any],
    n_cp: int = 6,
    seed: int = 42,
    pop_size: int = 30,
    n_gen: int = 50,
    verbose: bool = True,
    loss_model: object = None,
) -> tuple[list[tuple[float, float]], list[np.ndarray], float]:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.lhs import LHS
    from pymoo.optimize import minimize as pymoo_minimize

    closed_top: bool = cfg["closed_top"]
    targets: list[float] = cfg["targets"]
    bore_radius: float = cfg["bore_radius"]
    outer_diameter: float = cfg["outer_diameter"]
    n_register: int = 1 if closed_top else 2

    baseline = sequential_refined(cfg)
    L_base: float = baseline[1]
    hp_seq: list[float] = baseline[2]
    hd_seq: list[float] = baseline[3] if len(baseline) > 4 else [cfg["hole_diameter"]] * len(hp_seq)

    n_h = len(hp_seq)
    hl: list[float] = [cfg["hole_length"]] * n_h
    n_var = n_cp + 2 * n_h

    hd_min = bore_radius * 0.4
    hd_max = bore_radius * 0.9

    xl_list: list[float] = [3.0] * n_cp
    xu_list: list[float] = [15.0] * n_cp
    for i in range(n_h):
        lo = max((hp_seq[i - 1] + 5.0) if i > 0 else 30.0, 30.0)
        hi = min((hp_seq[i + 1] - 5.0) if i < n_h - 1 else L_base * 1.3 - 30.0, L_base * 1.3 - 30.0)
        if lo > hi:
            lo, hi = hp_seq[i] - 2.0, hp_seq[i] + 2.0
        xl_list.append(lo)
        xu_list.append(hi)
    for _ in range(n_h):
        xl_list.append(hd_min)
        xu_list.append(hd_max)
    xl = np.array(xl_list, dtype=float)
    xu = np.array(xu_list, dtype=float)

    class ParetoProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=n_var, n_obj=2, xl=xl, xu=xu)

        def _evaluate(self, x, out, *args, **kwargs):
            rad = np.maximum(x[:n_cp], 3.0)
            hp = sorted(x[n_cp:n_cp + n_h].tolist())
            hd = np.clip(x[n_cp + n_h:], hd_min, hd_max).tolist()
            int_cost, timbre_cost = evaluate_bi_objective(
                rad, L_base, hp, hd, hl, closed_top, targets,
                bore_radius, outer_diameter, n_register, loss_model,
            )
            out["F"] = [int_cost, timbre_cost]

    problem = ParetoProblem()
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=1.0 / n_var, eta=20),
        eliminate_duplicates=True,
    )

    t0 = time.time()
    res = pymoo_minimize(problem, algorithm, ("n_gen", n_gen), seed=seed, verbose=verbose)
    elapsed = time.time() - t0

    pareto_points: list[tuple[float, float]] = [(float(f[0]), float(f[1])) for f in res.F]
    pareto_designs: list[np.ndarray] = [np.array(x) for x in res.X]

    return (pareto_points, pareto_designs, elapsed)
