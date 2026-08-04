"""
Tests for the reusable top-k polish optimizer.

Locks the interface and the quality claim used on the shared benchmark
contract: polishing several DE elites beats polishing only the global best.
Runs are kept small so the suite stays fast.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.optimize import differential_evolution, minimize

from backend.optimization.topk_polish import topk_polish


def _sphere(x):
    return float(np.sum(np.asarray(x, float) ** 2))


BOUNDS = [(-3.0, 3.0)] * 4


def test_topk_polish_returns_expected_keys():
    res = topk_polish(_sphere, BOUNDS, popsize=6, maxiter=10, n_polish=3, seed=42)
    for key in ("rms_cents", "radii", "objective_evals", "wall_time", "config"):
        assert key in res, f"missing key {key}"
    assert res["radii"] is not None
    assert res["objective_evals"] > 0


def test_topk_polish_finds_sphere_optimum():
    res = topk_polish(_sphere, BOUNDS, popsize=8, maxiter=15, n_polish=3, seed=7)
    assert res["rms_cents"] < 1e-6, f"expected near-zero, got {res['rms_cents']}"


def test_topk_polish_beats_single_polish_on_multi_modal():
    """On a multi-modal Rastrigin-like surface, top-k polish should reach
    lower cost than polishing only the single DE best."""

    def rastrigin(x):
        x = np.asarray(x, float)
        return float(10 * len(x) + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x)))

    def single_polish(popsize=8, maxiter=15, seed=42):
        res = differential_evolution(
            rastrigin, BOUNDS, maxiter=maxiter, popsize=popsize,
            seed=seed, polish=False, tol=1e-6,
        )
        ref = minimize(rastrigin, res.x, method="L-BFGS-B", bounds=BOUNDS)
        return float(ref.fun)

    topk = topk_polish(
        rastrigin, BOUNDS, popsize=8, maxiter=15, n_polish=5, seed=42
    )
    single = single_polish()
    assert topk["rms_cents"] <= single + 1e-9, (
        f"topk={topk['rms_cents']:.4f} should not exceed single={single:.4f}"
    )
