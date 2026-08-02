"""Bore Surrogate Package

MLP surrogate models for wind instrument acoustic prediction.
"""
from .mlp_surrogate import (
    BoreSurrogate,
    SurrogateConfig,
    SurrogateTrainer,
    generate_training_data,
    build_surrogate_pipeline,
)
from .bi_objective_bo import (
    BiObjectiveBO,
    BOConfig,
    SurrogateWrapper,
    run_bi_objective_optimization,
)

__all__ = [
    "BoreSurrogate",
    "SurrogateConfig",
    "SurrogateTrainer",
    "generate_training_data",
    "build_surrogate_pipeline",
    "BiObjectiveBO",
    "BOConfig",
    "SurrogateWrapper",
    "run_bi_objective_optimization",
]