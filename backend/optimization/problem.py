"""Shared optimization problem helpers for the instrument optimizer stack.

This module centralizes the metric contract and evaluation plumbing so the
various optimizer entry points (two-phase, Pareto, benchmark) all speak the
same language.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np

from backend.metrics import compute_metrics


@dataclass
class OptimizationProblem:
    """Simple description of an optimization problem.

    The goal is to keep physics-specific details outside the optimizer entry
    points while still allowing each caller to supply its own evaluation logic.
    """

    targets: Sequence[float]
    fingerings: Sequence[Sequence[str]]
    n_register: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Canonical summary of intonation quality for an optimization candidate."""

    final_rms_cents: float
    scale_rms_cents: float
    median_offset_cents: float
    peak_error_cents: float


def build_metric_summary(cents: Sequence[float]) -> dict[str, float]:
    """Build the canonical metric summary from raw cents deviations.

    The primary accuracy metric is absolute RMS. Median-corrected RMS is still
    returned as a secondary diagnostic.
    """
    metrics = compute_metrics(list(cents))
    return {
        "final_rms_cents": metrics["final_rms_cents"],
        "scale_rms_cents": metrics["scale_rms_cents"],
        "median_offset_cents": metrics["median_offset_cents"],
        "peak_error_cents": metrics["peak_error_cents"],
    }


def cents_from_frequency_pairs(actual: Sequence[float], target: Sequence[float]) -> list[float]:
    """Convert frequency pairs to cents deviations with the shared metric contract."""
    return [1200.0 * np.log2(float(a) / float(t)) if float(a) > 0 and np.isfinite(float(a)) and float(t) > 0 else 1e10 for a, t in zip(actual, target)]


def summarize_cents(cents: Sequence[float]) -> MetricSummary:
    """Return a typed metric summary object."""
    metrics = build_metric_summary(cents)
    return MetricSummary(**metrics)
