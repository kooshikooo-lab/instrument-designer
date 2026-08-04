"""Optimization framework.

Optimizes instrument parameters using the acoustic network model.
"""
from .base import Optimizer, OptimizationResult
from .bore_optimizer import BoreOptimizer
from .fingering_optimizer import FingeringOptimizer
from .metamaterial_optimizer import MetamaterialOptimizer, optimize_family
from .topk_polish import topk_polish

__all__ = [
    "Optimizer",
    "OptimizationResult",
    "BoreOptimizer",
    "FingeringOptimizer",
    "MetamaterialOptimizer",
    "optimize_family",
    "topk_polish",
]
