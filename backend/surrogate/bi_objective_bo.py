"""
Bi-Objective Bayesian Optimization for Instrument Design

Multi-objective Bayesian Optimization using BoTorch qNEHVI/qEHVI for Pareto front optimization.
Complements NSGA-II in pareto_optimizer.py by using surrogate models for faster evaluation.

Based on Petiot et al. 2025 (RF surrogate + bi-objective GA) and BoTorch tutorials.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Callable, List, Tuple
import numpy as np
import torch
from botorch.models import SingleTaskGP
from botorch.models.transforms.outcome import Standardize
from botorch.acquisition.multi_objective import (
    qNoisyExpectedHypervolumeImprovement,
    qExpectedHypervolumeImprovement,
    ExpectedHypervolumeImprovement,
)
from botorch.optim import optimize_acqf
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.utils.multi_objective.pareto import is_non_dominated
from botorch.utils.multi_objective.box_decompositions.non_dominated import FastNondominatedPartitioning
from gpytorch.mlls import ExactMarginalLogLikelihood
import torch.nn as nn


@dataclass
class BOConfig:
    """Configuration for Bayesian Optimization."""
    n_initial: int = 20  # Initial random samples
    n_iterations: int = 50  # BO iterations
    batch_size: int = 4  # q-batch size (parallel evaluations)
    mc_samples: int = 256  # MC samples for qNEHVI
    acquisition_type: str = "qnehvi"  # "qnehvi", "qehvi", "nehvi"
    standardize: bool = True
    noise_prior: bool = True
    seed: int = 42


class SurrogateWrapper:
    """Wrapper to use JAX/Flax surrogate as a BO objective."""
    
    def __init__(self, surrogate_trainer, input_dim: int, bounds: np.ndarray):
        self.trainer = surrogate_trainer
        self.input_dim = input_dim
        self.bounds = torch.tensor(bounds, dtype=torch.double)
    
    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        """Evaluate surrogate at x.
        
        Args:
            x: Tensor of shape (batch, input_dim)
            
        Returns:
            Tensor of shape (batch, n_objectives)
        """
        # Convert to numpy for surrogate prediction
        x_np = x.detach().cpu().numpy()
        
        # Denormalize inputs (surrogate expects normalized inputs)
        # Note: This assumes inputs are normalized; adjust based on actual normalization
        preds = self.trainer.predict(x_np)
        
        # Return objectives: [RMS, -EFP] (minimize RMS, maximize EFP)
        # We negate EFP so both objectives are minimized
        rms = preds[:, 0]
        efp = -preds[:, 1]  # Negative because we want to maximize EFP
        return torch.tensor(np.stack([rms, efp], axis=1), dtype=torch.double)


def generate_initial_design(n: int, bounds: np.ndarray, seed: int = 42) -> np.ndarray:
    """Generate initial Sobol design."""
    from scipy.stats import qmc
    sampler = qmc.Sobol(d=bounds.shape[0], seed=seed)
    samples = sampler.random(n)
    # Scale to bounds
    lower = bounds[:, 0]
    upper = bounds[:, 1]
    return qmc.scale(samples, lower, upper)


class BiObjectiveBO:
    """Bi-Objective Bayesian Optimization using qNEHVI/qEHVI."""
    
    def __init__(self, 
                 objective_fn: Callable,
                 bounds: np.ndarray,
                 config: Optional[BOConfig] = None):
        """
        Args:
            objective_fn: Function mapping (n, dim) -> (n, 2) objectives (both to minimize)
            bounds: Array of shape (dim, 2) with [lower, upper] for each dimension
            config: BO configuration
        """
        self.objective_fn = objective_fn
        self.bounds = torch.tensor(bounds, dtype=torch.double)
        self.config = config or BOConfig()
        self.dim = bounds.shape[0]
        
        # Data storage
        self.train_x = None
        self.train_y = None
        self.model = None
        self.mll = None
        
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)
    
    def _initialize_model(self, train_x: torch.Tensor, train_y: torch.Tensor) -> SingleTaskGP:
        """Initialize GP model."""
        model = SingleTaskGP(
            train_X=train_x,
            train_Y=train_y,
            outcome_transform=Standardize(m=train_y.shape[-1]) if self.config.standardize else None,
        )
        
        mll = ExactMarginalLogLikelihood(model.likelihood, model)
        return model, mll
    
    def _fit_model(self, train_x: torch.Tensor, train_y: torch.Tensor):
        """Fit GP model to data."""
        self.model, self.mll = self._initialize_model(train_x, train_y)
        
        # Fit model
        from botorch.fit import fit_gpytorch_mll
        fit_gpytorch_mll(self.mll)
    
    def _get_acquisition_function(self, train_y: torch.Tensor):
        """Create acquisition function based on config."""
        # Compute Pareto front of current observations
        pareto_y = train_y[is_non_dominated(train_y)]
        
        # Reference point for hypervolume (slightly worse than worst observed)
        ref_point = train_y.max(dim=0).values + 0.1 * (train_y.max(dim=0).values - train_y.min(dim=0).values)
        
        partitioning = FastNondominatedPartitioning(ref_point=ref_point, Y=pareto_y)
        
        if self.config.acquisition_type == "qnehvi":
            sampler = SobolQMCNormalSampler(sample_shape=torch.Size([self.config.mc_samples]))
            return qNoisyExpectedHypervolumeImprovement(
                model=self.model,
                ref_point=ref_point,
                X_baseline=self.train_x,
                prune_baseline=True,
                sampler=sampler,
            )
        elif self.config.acquisition_type == "qehvi":
            return ExpectedHypervolumeImprovement(
                model=self.model,
                ref_point=ref_point,
                partitioning=partitioning,
            )
        else:
            raise ValueError(f"Unknown acquisition type: {self.config.acquisition_type}")
    
    def optimize(self, 
                 objective_fn: Optional[Callable] = None,
                 n_iterations: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Run BO optimization loop.
        
        Args:
            objective_fn: Objective function (n, dim) -> (n, n_obj); defaults to self.objective_fn
            n_iterations: Number of iterations; defaults to self.config.n_iterations
            
        Returns:
            (pareto_x, pareto_y) - Pareto optimal inputs and objectives
        """
        if objective_fn is None:
            objective_fn = self.objective_fn
        n_iter = n_iterations or self.config.n_iterations
        
        # Initial design
        print(f"Generating initial design ({self.config.n_initial} samples)...")
        init_x = generate_initial_design(self.config.n_initial, self.bounds.numpy(), self.config.seed)
        self.train_x = torch.tensor(init_x, dtype=torch.double)
        
        # Evaluate initial points
        print("Evaluating initial design...")
        init_y_list = []
        for i in range(self.config.n_initial):
            y = np.asarray(self.objective_fn(self.train_x[i:i+1].numpy())).squeeze()
            init_y_list.append(y)
        self.train_y = torch.tensor(np.array(init_y_list), dtype=torch.double)
        
        print(f"Initial Pareto front size: {is_non_dominated(self.train_y).sum().item()}")
        
        # BO loop
        for iteration in range(self.config.n_iterations):
            print(f"\nIteration {iteration + 1}/{self.config.n_iterations}")
            
            # Fit GP model
            self._fit_model(self.train_x, self.train_y)
            
            # Get acquisition function
            acq_fn = self._get_acquisition_function(self.train_y)
            
            # Optimize acquisition function (botorch>=0.16 expects 2 x d bounds)
            candidates, _ = optimize_acqf(
                acq_function=acq_fn,
                bounds=self.bounds.T,
                q=self.config.batch_size,
                num_restarts=20,
                raw_samples=512,
                options={"batch_limit": 5, "maxiter": 200},
            )
            
            # Evaluate new candidates
            new_y_list = []
            for i in range(self.config.batch_size):
                y = np.asarray(objective_fn(candidates[i:i+1].numpy())).squeeze()
                new_y_list.append(y)
            new_y = torch.tensor(np.array(new_y_list), dtype=torch.double)
            
            # Update data
            self.train_x = torch.cat([self.train_x, candidates], dim=0)
            self.train_y = torch.cat([self.train_y, new_y], dim=0)
            
            pareto_mask = is_non_dominated(self.train_y)
            print(f"  Pareto front size: {pareto_mask.sum().item()}")
        
        # Return final Pareto front
        pareto_mask = is_non_dominated(self.train_y)
        pareto_x = self.train_x[pareto_mask].numpy()
        pareto_y = self.train_y[pareto_mask].numpy()
        
        return pareto_x, pareto_y


def run_bi_objective_optimization(
    surrogate_trainer,
    input_dim: int,
    bounds: np.ndarray,
    n_iterations: int = 50,
    n_initial: int = 20,
    batch_size: int = 4,
    verbose: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    High-level function to run bi-objective BO on a trained surrogate.
    
    Args:
        surrogate_trainer: Trained SurrogateTrainer instance
        input_dim: Dimension of input space
        bounds: Array of shape (dim, 2) with [lower, upper]
        n_iterations: Number of BO iterations
        n_initial: Number of initial random samples
        batch_size: Parallel batch size
        
    Returns:
        (pareto_x, pareto_y) - Pareto optimal designs and objectives
    """
    
    def objective_fn(x: np.ndarray) -> np.ndarray:
        """Wrapper to evaluate surrogate and return [RMS, -EFP]."""
        preds = surrogate_trainer.predict(x)
        # Return [RMS, -EFP] (both to minimize)
        rms = preds[:, 0]
        efp = -preds[:, 1]  # Negative because we maximize EFP
        return np.stack([rms, efp], axis=1)
    
    config = BOConfig(
        n_initial=20,
        n_iterations=n_iterations,
        batch_size=batch_size,
        acquisition_type="qnehvi",
    )
    
    bo = BiObjectiveBO(
        objective_fn=objective_fn,
        bounds=np.array(bounds),
        config=BOConfig(n_initial=n_initial, n_iterations=n_iterations, batch_size=batch_size)
    )
    
    pareto_x, pareto_y = bo.optimize(objective_fn, n_iterations)
    
    return pareto_x, pareto_y


if __name__ == "__main__":
    print("Bi-objective BO module ready")
    print("Requires: botorch, gpytorch, botorch, gpytorch")