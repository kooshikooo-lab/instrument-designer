"""Spectral validation metrics.

Reuses backend.metrics for the canonical cents computation.
"""

from __future__ import annotations

import numpy as np

from backend.metrics import compute_metrics, cents_from_frequencies


def compute_spectral_metrics(
    actual_f0s: np.ndarray,
    target_f0s: np.ndarray,
) -> dict:
    """Compute intonation metrics between actual and target f0 values.

    Args:
        actual_f0s: array of extracted fundamental frequencies (Hz)
        target_f0s: array of target frequencies (Hz), same length

    Returns:
        dict with canonical metrics plus spectral-specific fields
    """
    actual = np.asarray(actual_f0s, dtype=float)
    target = np.asarray(target_f0s, dtype=float)

    valid = np.isfinite(actual) & np.isfinite(target) & (target > 0) & (actual > 0)
    if not np.any(valid):
        return {
            **compute_metrics([]),
            "n_valid": 0,
            "n_total": len(actual),
        }

    cents = 1200.0 * np.log2(actual[valid] / target[valid])
    base_metrics = compute_metrics(cents)

    return {
        **base_metrics,
        "n_valid": int(np.sum(valid)),
        "n_total": len(actual),
        "mean_cents": float(np.mean(cents)),
        "std_cents": float(np.std(cents)),
    }