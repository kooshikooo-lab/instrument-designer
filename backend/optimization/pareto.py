"""Pareto-front optimizer: intonation vs timbre.

Bi-objective optimization exploring the tradeoff between intonation accuracy
and timbre quality.  Implements two methods:

- ``pareto_sweep`` — weighted-sum L-BFGS-B sweep (fast, 8 weight points)
- ``run_pareto``   — NSGA-II population-based Pareto front (thorough)
"""
from __future__ import annotations

import time

import numpy as np
from scipy.optimize import minimize as sp_min

from backend.tmm_acoustics import SPEED_OF_SOUND
from backend.optimization.objectives import evaluate_bi_objective

_c = SPEED_OF_SOUND


def pareto_sweep(
    cfg: dict,
    n_cp: int = 6,
    seed: int = 42,
    n_weights: int = 8,
    maxiter: int = 100,
    verbose: bool = True,
    loss_model: object | None = None,
) -> list[tuple[float, float, float, float]]:
    """Weighted-sum Pareto sweep via L-BFGS-B refinement.

    First runs intonation-only optimisation to find a good starting point,
    then sweeps ``w * intonation + (1-w) * timbre`` for ``w in [0, 1]``.

    Returns list of ``(w_int, intonation_rms, timbre_cost, bore_length_mm)``.
    """
    from backend.jax_optimizer import refine_sequential

    closed_top = cfg["closed_top"]
    targets = cfg["targets"]
    bore_r = cfg["bore_radius"]
    od = cfg["outer_diameter"]
    n_register = 1 if closed_top else 2

    if verbose:
        print("  Phase 1: Intonation-only optimisation (baseline)...")
    rms_init, L_init, radii_init, hp_init, hd_init, _hl_init, _ = refine_sequential(
        cfg, verbose=False, use_jax_bore=False,
    )
    if verbose:
        print(f"    Baseline: RMS={rms_init:.4f}c, L={L_init:.1f}mm, "
              f"{len(hp_init)} holes")

    n_h = len(hp_init)
    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9
    x_baseline = np.concatenate([
        radii_init, np.array(hp_init), np.array(hd_init),
    ])

    def combined_obj(x: np.ndarray, w_int: float) -> float:
        radii = np.maximum(x[:n_cp], 0.1)
        hp = sorted(x[n_cp:n_cp + n_h].tolist())
        hd = x[n_cp + n_h:n_cp + 2 * n_h].tolist()
        hl = [cfg["hole_length"]] * n_h
        intonation, timbre = evaluate_bi_objective(
            radii, L_init, hp, hd, hl, closed_top, targets, bore_r, od,
            n_register, loss_model,
        )
        if intonation >= 1e10 or timbre >= 1e10:
            return 1e10
        return w_int * intonation + (1.0 - w_int) * timbre

    bounds = (
        [(3.0, 15.0)] * n_cp
        + [(30.0, L_init * 1.3)] * n_h
        + [(hd_min, hd_max)] * n_h
    )

    weights = np.linspace(0.0, 1.0, n_weights).tolist()
    results: list[tuple[float, float, float, float]] = []

    if verbose:
        print(f"  Phase 2: Pareto sweep ({n_weights} weights)...")
    for w_int in weights:
        r = sp_min(
            combined_obj, x_baseline.copy(), args=(w_int,), method="L-BFGS-B",
            bounds=bounds, options={"maxiter": maxiter, "ftol": 1e-10},
        )
        x_opt = r.x
        radii = np.maximum(x_opt[:n_cp], 0.1)
        hp = sorted(x_opt[n_cp:n_cp + n_h].tolist())
        hd = x_opt[n_cp + n_h:n_cp + 2 * n_h].tolist()
        hl = [cfg["hole_length"]] * n_h
        intonation, timbre = evaluate_bi_objective(
            radii, L_init, hp, hd, hl, closed_top, targets, bore_r, od,
            n_register, loss_model,
        )
        results.append((w_int, intonation, timbre, L_init))

    if verbose:
        print(f"\n  {'w_int':>6s}  {'Intonation':>12s}  {'Timbre':>12s}  {'Bore L':>8s}")
        print(f"  {'-'*6}  {'-'*12}  {'-'*12}  {'-'*8}")
        for w, intl, timb, L in results:
            intl_s = f"{intl:.4f}" if intl < 1e5 else "FAIL"
            print(f"  {w:6.2f}  {intl_s:>12s}  {timb:12.6f}  {L:8.1f}mm")

    return results


def run_pareto(
    cfg: dict,
    n_cp: int = 6,
    seed: int = 42,
    pop_size: int = 30,
    n_gen: int = 50,
    verbose: bool = True,
    loss_model: object | None = None,
) -> tuple[list[tuple[float, float]], list[np.ndarray], float]:
    """NSGA-II bi-objective optimisation (intonation vs timbre).

    Parameters
    ----------
    cfg : dict
        Instrument configuration (``"closed_top"``, ``"targets"``,
        ``"bore_radius"``, ``"outer_diameter"``, ``"hole_length"``).
    n_cp : int, optional
        Number of bore control points (default 6).
    seed : int, optional
        Random seed (default 42).
    pop_size : int, optional
        Population size (default 30).
    n_gen : int, optional
        Number of generations (default 50).
    verbose : bool, optional
        Print pymoo progress (default True).
    loss_model : object or None, optional
        Viscothermal loss model.  None for lossless.

    Returns
    -------
    pareto_points : list of (float, float)
        ``(intonation, timbre)`` pairs on the Pareto front, sorted by
        increasing intonation.
    pareto_designs : list of ndarray
        Design vectors corresponding to each Pareto point.
    elapsed : float
        Optimisation time in seconds.
    """
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import Problem
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.lhs import LHS
        from pymoo.optimize import minimize as moo_minimize
    except ImportError:
        print("  pymoo not installed — skipping NSGA-II.")
        print("  Install with: pip install pymoo")
        return [], [], 0.0

    closed_top = cfg["closed_top"]
    targets = cfg["targets"]
    bore_r = cfg["bore_radius"]
    od = cfg["outer_diameter"]
    n_h = len(targets) - (1 if closed_top else 0)
    n_register = 1 if closed_top else 2

    wl_min = _c / max(targets)
    L_est = wl_min / 2.0 * 1.2

    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9

    class ParetoProblem(Problem):
        """Two-objective problem: (intonation, timbre)."""

        def __init__(self) -> None:
            n_vars = n_cp + n_h + n_h
            xl = np.array(
                [3.0] * n_cp + [30.0] * n_h + [hd_min] * n_h
            )
            xu = np.array(
                [15.0] * n_cp + [L_est * 1.3] * n_h + [hd_max] * n_h
            )
            super().__init__(n_var=n_vars, n_obj=2, xl=xl, xu=xu)

        def _evaluate(self, X: np.ndarray, out: dict, *args, **kwargs) -> None:
            F = np.full((X.shape[0], 2), 1e10)
            for i in range(X.shape[0]):
                x = X[i]
                radii = np.maximum(x[:n_cp], 0.1)
                hp = sorted(x[n_cp:n_cp + n_h].tolist())
                hd = x[n_cp + n_h:n_cp + 2 * n_h].tolist()
                hl = [cfg["hole_length"]] * n_h
                intonation, timbre = evaluate_bi_objective(
                    radii, L_est, hp, hd, hl, closed_top, targets,
                    bore_r, od, n_register, loss_model,
                )
                if intonation < 1e10 and timbre < 1e10:
                    F[i, 0] = intonation
                    F[i, 1] = timbre
            out["F"] = F

    problem = ParetoProblem()
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
    )

    t0 = time.time()
    res = moo_minimize(
        problem, algorithm, ("n_gen", n_gen), seed=seed, verbose=verbose,
    )
    elapsed = time.time() - t0

    F = res.F
    X = res.X

    pareto_idx: list[int] = []
    for i in range(len(F)):
        dominated = False
        for j in range(len(F)):
            if i == j:
                continue
            if (F[j, 0] <= F[i, 0] and F[j, 1] <= F[i, 1]
                    and (F[j, 0] < F[i, 0] or F[j, 1] < F[i, 1])):
                dominated = True
                break
        if not dominated:
            pareto_idx.append(i)

    pareto_idx.sort(key=lambda i: F[i, 0])

    if verbose:
        print(f"\n  Pareto front: {len(pareto_idx)} points ({elapsed:.1f}s)")
        print(f"  {'Intonation':>12s}  {'Timbre':>12s}")
        print(f"  {'-'*12}  {'-'*12}")
        for i in pareto_idx:
            print(f"  {F[i, 0]:12.4f}  {F[i, 1]:12.6f}")

    pareto_points = [(F[i, 0], F[i, 1]) for i in pareto_idx]
    pareto_designs = [X[i] for i in pareto_idx]
    return pareto_points, pareto_designs, elapsed


if __name__ == "__main__":
    from backend.benchmark_all import INSTRUMENTS

    print("=" * 70)
    print("  PARETO FRONT: Intonation vs Timbre")
    print("=" * 70)

    cfg = INSTRUMENTS["chalumeau_C"]
    print(f"\n--- {cfg['desc']} ---")
    print(f"  closed_top={cfg['closed_top']}, "
          f"{len(cfg['targets'])} targets, "
          f"{len(cfg['targets']) - 1} holes")

    print("\n  Weighted-sum sweep:")
    pareto_sweep(cfg, n_weights=5, maxiter=80, verbose=True)

    print("\n  NSGA-II Pareto front:")
    front, designs, dt = run_pareto(
        cfg, pop_size=20, n_gen=30, verbose=True,
    )
