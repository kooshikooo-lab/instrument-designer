"""Legacy optimizer package.

Redirects to archived_optimizers.bore_optimizer for backward compatibility.
"""
from backend.archived_optimizers.bore_optimizer import (  # noqa: F401
    BoreOptimizer,
    BoreOptimizationProblem,
    _compute_impedance_from_bore,
    _match_peaks_to_targets,
)
