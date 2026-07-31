"""
Archived optimizers - frozen, do not modify.
Import from these modules only if you need legacy optimizer implementations.

Submodules are imported lazily so that importing this package has no side
effects: several archived modules either fail to import (tmm_optimizer_sequential)
or run benchmarks at import time (benchmark_optimizers).
"""

import importlib

__all__ = [
    "benchmark_optimizers",
    "bore_optimizer",
    "optimizer_global",
    "staged_optimizer",
    "tmm_optimizer",
    "tmm_optimizer_multi",
    "tmm_optimizer_sequential",
    "tmm_optimizer_v2",
    "v2_scipy_optimizer",
    "validate_optimizer",
]


def __getattr__(name):
    if name in __all__:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
