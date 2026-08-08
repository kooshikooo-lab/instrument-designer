"""Top-k polish: DE global search + L-BFGS-B refinement of k elite candidates.

Generic over the objective, so it can be dropped into any comparison suite or
optimization pipeline that exposes a vector objective and per-variable bounds
(e.g. the shared Bb-clarinet contract: 6 bore radii -> absolute RMS cents).

Result keys match the comparison framework's ``AlgorithmResult.metrics``
(``rms_cents``, ``objective_evals``, ``wall_time``) so a runner can wrap this
directly. Tuning evidence on the shared contract (test_output/benchmark_contract):
top-k polish scored 5.9-7.7c RMS vs a 9.6c single-restart gradient-free baseline;
a neural-surrogate warm-start scored 19-167c and was dropped.
"""
import time
from typing import Callable, List, Optional, Sequence, Tuple
import numpy as np
from scipy.optimize import differential_evolution, minimize


def topk_polish(
    objective: Callable[[np.ndarray], float],
    bounds: Sequence[Tuple[float, float]],
    popsize: int = 15,
    maxiter: int = 60,
    n_polish: int = 5,
    seed: int = 42,
    polish_method: str = "L-BFGS-B",
    polish_options: Optional[dict] = None,
    workers: int = 1,
) -> dict:
    """Run DE, then L-BFGS-B polish on the n_polish best elite candidates.

    Args:
        objective: callable(vector) -> cost (lower is better)
        bounds: per-variable (lo, hi) bounds
        popsize: DE population multiplier
        maxiter: DE max iterations
        n_polish: number of elite candidates to refine locally
        seed: random seed
        polish_method: scipy minimize method for the local refinement
        polish_options: options dict for the local refinement
        workers: passed to scipy differential_evolution (int for local
            processes, or a map-like callable such as a Dask-backed mapper).
            The L-BFGS-B polish step stays serial.

    Returns:
        dict with ``rms_cents`` (best cost), ``radii`` (best vector),
        ``objective_evals``, ``wall_time``, and diagnostics.
    """
    opts = polish_options or {"maxiter": 400, "ftol": 1e-12, "gtol": 1e-10}
    t0 = time.time()

    res = differential_evolution(
        objective, bounds,
        maxiter=maxiter, popsize=popsize, seed=seed,
        tol=1e-6, mutation=(0.5, 1.0), recombination=0.7, polish=False,
        workers=workers,
    )
    pop = np.vstack([res.population, res.x])
    vals = np.array([objective(x) for x in pop])
    n_evals = int(res.nfev) + len(pop)
    order = np.argsort(vals)[:n_polish]

    best_cost = float(vals[order[0]])
    best_x = pop[order[0]]
    polished = {}
    for rank, idx in enumerate(order):
        ref = minimize(
            objective, pop[idx], method=polish_method,
            bounds=bounds, options=opts,
        )
        n_evals += int(ref.nfev)
        polished[rank] = round(float(ref.fun), 4)
        if ref.fun < best_cost:
            best_cost = float(ref.fun)
            best_x = ref.x

    return {
        "rms_cents": best_cost,
        "radii": [round(float(v), 4) for v in best_x],
        "objective_evals": n_evals,
        "wall_time": time.time() - t0,
        "de_best": round(float(vals[order[0]]), 4),
        "polished": polished,
        "config": {
            "popsize": popsize, "maxiter": maxiter,
            "n_polish": n_polish, "seed": seed,
            "polish_method": polish_method,
        },
    }
