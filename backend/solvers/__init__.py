"""Solvers package."""
from .tmm_solver import TMMSolver

try:
    from .openwind_solver import OpenWindSolver
except ImportError:
    OpenWindSolver = None

__all__ = ["TMMSolver", "OpenWindSolver"]
