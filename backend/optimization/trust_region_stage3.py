"""Trust-region regularization for Stage 3 joint optimization.

Per ChatGPT: J = J_intonation + λ|x - x_stage2|²

Allows escape from poor local basin when benefit is clear,
without encouraging arbitrary wandering.
"""
import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TrustRegionResult:
    """Result of trust-region regularized optimization."""
    success: bool
    x: np.ndarray
    fun: float
    nfev: int
    nit: int
    message: str
    regularization_cost: float
    original_cost: float


def trust_region_objective(
    objective: Callable,
    stage2_solution: np.ndarray,
    lambda_reg: float = 1.0,
) -> Callable:
    """Wrap objective with trust-region regularization.
    
    J_total(x) = J_intonation(x) + λ * ||x - x_stage2||²
    
    Args:
        objective: original cost function J_intonation(x)
        stage2_solution: x_stage2 from Stage 2 optimization
        lambda_reg: regularization strength (higher = stay closer to Stage 2)
    
    Returns:
        Regularized objective function
    """
    def regularized(x):
        x = np.asarray(x)
        reg_cost = lambda_reg * np.sum((x - stage2_solution) ** 2)
        orig_cost = objective(x)
        return orig_cost + reg_cost
    
    return regularized


def trust_region_objective_with_bounds(
    objective: Callable,
    stage2_solution: np.ndarray,
    lambda_reg: float = 1.0,
    bounds: List[Tuple[float, float]] = None,
) -> Callable:
    """Trust-region with bounds checking."""
    def regularized(x):
        x = np.asarray(x)
        if bounds:
            # Check bounds
            for i, (lo, hi) in enumerate(bounds):
                if x[i] < lo or x[i] > hi:
                    return 1e10  # penalty for out of bounds
        reg_cost = lambda_reg * np.sum((x - stage2_solution) ** 2)
        orig_cost = objective(x)
        return orig_cost + reg_cost
    return regularized


def optimize_stage3_trust_region(
    objective: Callable,
    stage2_solution: np.ndarray,
    bounds: List[Tuple[float, float]],
    lambda_reg: float = 1.0,
    maxiter: int = 500,
    method: str = 'L-BFGS-B',
    **kwargs
) -> TrustRegionResult:
    """Run Stage 3 optimization with trust-region regularization.
    
    Args:
        objective: J_intonation(x) cost function
        stage2_solution: x from Stage 2 (bore + toneholes optimized)
        bounds: parameter bounds
        lambda_reg: regularization strength
        maxiter: maximum iterations
        method: scipy optimization method
    
    Returns:
        TrustRegionResult with both original and regularization costs
    """
    reg_obj = trust_region_objective_with_bounds(
        objective, stage2_solution, lambda_reg, bounds
    )
    
    result = minimize(
        reg_obj,
        stage2_solution,
        bounds=bounds,
        method=method,
        options={'maxiter': maxiter, **kwargs},
    )
    
    # Evaluate original cost at solution
    orig_cost = objective(result.x)
    reg_cost = lambda_reg * np.sum((result.x - stage2_solution) ** 2)
    
    return TrustRegionResult(
        success=result.success,
        x=result.x,
        fun=result.fun,
        nfev=result.nfev,
        nit=result.nit,
        message=result.message,
        regularization_cost=reg_cost,
        original_cost=orig_cost,
    )


def adaptive_trust_region(
    objective: Callable,
    stage2_solution: np.ndarray,
    bounds: List[Tuple[float, float]],
    lambda_init: float = 1.0,
    lambda_max: float = 100.0,
    lambda_min: float = 1e-3,
    tolerance: float = 1e-4,
    **kwargs
) -> TrustRegionResult:
    """Adaptive trust-region: adjust λ based on improvement.
    
    If regularization cost is small → decrease λ (allow more exploration)
    If regularization cost is large → increase λ (stay closer to Stage 2)
    """
    lambda_reg = lambda_init
    
    for attempt in range(5):
        result = optimize_stage3_trust_region(
            objective, stage2_solution, bounds,
            lambda_reg=lambda_reg, **kwargs
        )
        
        # Check if we improved on original cost
        if result.original_cost < objective(stage2_solution):
            # Improvement found
            if result.regularization_cost < tolerance:
                # Very close to Stage 2, decrease λ for next time
                lambda_reg = max(lambda_reg * 0.5, lambda_min)
            else:
                # Some movement, keep λ
                pass
            return result
        else:
            # No improvement, increase λ and try again
            lambda_reg = min(lambda_reg * 2, lambda_max)
    
    return result


# Example usage
if __name__ == "__main__":
    # Mock objective: quadratic with minimum at [10, 20, 30]
    def mock_objective(x):
        return np.sum((x - [10, 20, 30]) ** 2)
    
    stage2 = np.array([12, 22, 32])  # Stage 2 solution (close to true)
    bounds = [(5, 15), (15, 25), (25, 35)]
    
    # Test with different λ
    for lam in [0.0, 0.1, 1.0, 10.0]:
        result = optimize_stage3_trust_region(
            mock_objective, stage2, bounds, lambda_reg=lam
        )
        print(f"λ={lam}: x={result.x}, orig={result.original_cost:.4f}, reg={result.regularization_cost:.4f}")
    
    # Adaptive
    print("\nAdaptive:")
    result = adaptive_trust_region(mock_objective, stage2, bounds)
    print(f"  x={result.x}, orig={result.original_cost:.4f}, reg={result.regularization_cost:.4f}")