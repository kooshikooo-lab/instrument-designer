"""Single-objective NSGA-II wrapper — generic cost function minimization.

Usage::

    from backend.optimization.nsga2 import nsga2_minimize

    result = nsga2_minimize(my_cost_fn, n_var=6, xl=xl, xu=xu)
    if result is not None:
        best_x, best_cost = result["x"], result["fun"]
"""
from __future__ import annotations

import numpy as np


def nsga2_minimize(
    cost_fn: callable,
    n_var: int,
    xl: np.ndarray,
    xu: np.ndarray,
    pop_size: int = 30,
    n_gen: int = 20,
    seed: int = 42,
    verbose: bool = False,
) -> dict | None:
    """Single-objective minimization via NSGA-II (pymoo).

    Parameters
    ----------
    cost_fn : callable
        ``cost_fn(x) -> float`` where ``x`` is a 1-D ``np.ndarray``.
    n_var : int
        Number of decision variables.
    xl, xu : np.ndarray
        Lower and upper bounds, shape ``(n_var,)``.
    pop_size, n_gen : int
        Population size and number of generations.
    seed : int
        Random seed for reproducibility.
    verbose : bool
        If True, print progress.

    Returns
    -------
    dict with keys ``x`` (best decision vector), ``fun`` (best cost),
    or ``None`` if pymoo is not available.
    """
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import Problem
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.lhs import LHS
        from pymoo.optimize import minimize as moo_minimize
    except ImportError:
        return None

    class _SingleObjectiveProblem(Problem):
        def __init__(self):
            super().__init__(n_var=n_var, n_obj=1, xl=xl, xu=xu)

        def _evaluate(self, X, out, *args, **kwargs):
            out["F"] = np.array([[cost_fn(x)] for x in X])

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
    )

    res = moo_minimize(
        _SingleObjectiveProblem(), algorithm, ("n_gen", n_gen),
        seed=seed, verbose=verbose,
    )
    return {"x": res.X, "fun": float(res.F[0])}
