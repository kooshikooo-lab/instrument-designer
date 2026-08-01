"""Canonical tuning-error metrics (one source of truth).

Convention (see docs/ARCHITECTURE_DECISIONS.md, ADR: absolute-RMS primary metric):

- ``final_rms_cents``  absolute RMS of cents errors -- the primary accuracy metric.
  Median correction is deliberately NOT applied here: it allows an optimizer to
  score 0c by making every note uniformly wrong.
- ``scale_rms_cents``  RMS of cents errors after subtracting the median offset
  (evenness / scale-fit quality; subordinate diagnostic).
- ``median_offset_cents``  global tuning offset (median of cents errors).
- ``peak_error_cents``  maximum |cents error| (absolute).

All functions accept raw cents deviations relative to the target frequencies.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def compute_metrics(cents: Sequence[float]) -> dict:
    """Compute the canonical metric dict from raw cents deviations.

    Invalid / non-finite readings are excluded unless every reading is
    invalid, in which case all metrics are set to 1e10 (penalty sentinel).
    """
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {
            "final_rms_cents": 1e10,
            "scale_rms_cents": 1e10,
            "median_offset_cents": 0.0,
            "peak_error_cents": 1e10,
        }
    rms = float(np.sqrt(np.mean(finite ** 2)))
    offset = float(np.median(finite))
    scale_rms = float(np.sqrt(np.mean((finite - offset) ** 2)))
    peak = float(np.max(np.abs(finite)))
    return {
        "final_rms_cents": rms,
        "scale_rms_cents": scale_rms,
        "median_offset_cents": offset,
        "peak_error_cents": peak,
    }


def rms_cents(cents: Sequence[float]) -> float:
    """Absolute RMS of cents errors (primary accuracy metric)."""
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 1e10
    return float(np.sqrt(np.mean(finite ** 2)))


def scale_rms_cents(cents: Sequence[float]) -> float:
    """RMS of cents errors after removing the median offset (evenness)."""
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 1e10
    return float(np.sqrt(np.mean((finite - np.median(finite)) ** 2)))


def median_offset_cents(cents: Sequence[float]) -> float:
    """Median cents error (global tuning offset)."""
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 0.0
    return float(np.median(finite))


def cents_from_frequencies(actual, target) -> list:
    """Convert frequency pairs to cents deviations (1200*log2(f_actual/f_target))."""
    out = []
    for a, t in zip(actual, target):
        if a is not None and t is not None and math.isfinite(float(a)) and float(a) > 0 and float(t) > 0:
            out.append(1200.0 * math.log2(float(a) / float(t)))
        else:
            out.append(1e10)
    return out
