"""
Pareto-front optimizer — backward-compatible re-export layer.

All implementation has moved to:

- ``backend.physics.timbre_proxy``     — bore-smoothness & radiation-consistency proxies
- ``backend.optimization.objectives``   — intonation & bi-objective evaluation
- ``backend.optimization.pareto``       — NSGA-II and weighted-sweep Pareto front
- ``backend.optimization.nsga2``        — single-objective NSGA-II wrapper

This module re-exports all public names so existing imports keep working.
"""
from backend.physics.timbre_proxy import (  # noqa: F401
    bore_smoothness,
    compute_timbre_cost,
    hole_radiation_consistency,
)
from backend.optimization.objectives import (  # noqa: F401
    compute_intonation_cost,
    evaluate_bi_objective,
)
from backend.optimization.nsga2 import nsga2_minimize  # noqa: F401
from backend.optimization.pareto import (  # noqa: F401
    pareto_sweep,
    run_pareto,
)

# Backward-compat aliases for renamed private functions
_bore_smoothness = bore_smoothness
_hole_radiation_consistency = hole_radiation_consistency
