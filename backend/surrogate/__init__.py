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

__all__ = [
    "BoreSurrogate",
    "SurrogateConfig",
    "SurrogateTrainer",
    "generate_training_data",
    "build_surrogate_pipeline",
]