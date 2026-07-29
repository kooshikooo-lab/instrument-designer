"""Optimization framework.

Optimizes instrument parameters using the acoustic network model.
"""
from .base import Optimizer, OptimizationResult
from .nsga2 import nsga2_minimize
from .pareto import run_pareto, pareto_sweep
from .objectives import compute_intonation_cost, evaluate_bi_objective

__all__ = [
    "Optimizer",
    "OptimizationResult",
    "nsga2_minimize",
    "run_pareto",
    "pareto_sweep",
    "compute_intonation_cost",
    "evaluate_bi_objective",
]