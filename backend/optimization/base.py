"""Base optimizer interface.

All optimizers implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class OptimizationResult:
    """Result of an optimization run.

    Attributes:
        success: whether optimization converged
        parameters: optimized parameter values
        cost: final cost value
        rms_cents: RMS intonation error in cents
        peak_cents: peak intonation error in cents
        n_evaluations: number of function evaluations
        wall_time: optimization time in seconds
        metadata: additional information
    """
    success: bool
    parameters: Dict[str, Any]
    cost: float
    rms_cents: float = 0.0
    peak_cents: float = 0.0
    n_evaluations: int = 0
    wall_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Optimizer(ABC):
    """Abstract base class for instrument optimizers."""

    @abstractmethod
    def optimize(self, verbose: bool = False) -> OptimizationResult:
        """Run the optimization.

        Returns:
            OptimizationResult with optimized parameters
        """
        pass

    @abstractmethod
    def evaluate(self, parameters: Dict[str, Any]) -> float:
        """Evaluate the cost function for given parameters.

        Args:
            parameters: dictionary of parameter values

        Returns:
            Cost value (lower is better)
        """
        pass
