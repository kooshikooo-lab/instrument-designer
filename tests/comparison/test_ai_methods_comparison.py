"""
Comparative tests for the four AI/ML optimization families on a shared
Bb-clarinet-family tuning task.

Families covered (per the AI-methods plan):
  1. Bayesian Optimization  - Gaussian-Process surrogate (botorch)
  2. Neural Surrogate Models - MLP surrogate + offline optimization (PyTorch)
  3. Reinforcement Learning  - REINFORCE over sequential design decisions
  4. Gradient-free methods   - CMA-ES, PSO, DE

Assertions are intentionally loose (each family must converge sanely and
finish within budget); the report test prints the head-to-head table. Run
with::

    pytest tests/comparison/test_ai_methods_comparison.py -m comparison -s
"""
import math

import numpy as np
import pytest

from comparison_framework import AlgorithmResult
import ai_methods_benchmark as bench

pytestmark = [
    pytest.mark.comparison,
    pytest.mark.slow,
]

# Generous sanity bound: every family must land well inside the achievable
# range (the uniform-10mm baseline is ~77 cents; the tuned floor is ~6 cents).
SANE_RMS_CENTS = 150.0


@pytest.fixture(scope="module")
def comparison_cache():
    """Shared module cache so the report test reuses per-family results."""
    return {}


@pytest.fixture(scope="module")
def shared_objective():
    """The exact objective every family optimizes."""
    return bench.benchmark_objective


def test_benchmark_is_well_posed(shared_objective):
    """Fast smoke check that the shared problem has room to improve."""
    baseline = shared_objective(np.full(bench.N_BORE_CTRL, 10.0))
    assert math.isfinite(baseline), "objective must be finite at the baseline"
    assert baseline > 10.0, "baseline should leave room for optimization"
    # A near-optimal bore (sequential_placement skeleton radii) must beat it.
    good = shared_objective([7.25] * bench.N_BORE_CTRL)
    assert good < baseline, "known-good bore must beat the uniform baseline"


@pytest.mark.parametrize(
    "family,runner_name,extra_dep",
    [
        ("bayesian_optimization", "run_bayesian_optimization", "botorch"),
        ("neural_surrogate", "run_neural_surrogate", "torch"),
        ("reinforcement_learning", "run_reinforcement_learning", "torch"),
        ("gradient_free", "run_gradient_free", "cma"),
    ],
)
def test_ai_method_family(family, runner_name, extra_dep, comparison_cache):
    """Each family converges sanely on the shared Bb-clarinet tuning task."""
    if extra_dep:
        pytest.importorskip(extra_dep)
    runner = getattr(bench, runner_name)
    result = bench._wrap(runner)

    comparison_cache[family] = result
    assert result.success, f"{family} failed: {result.error}"
    rms = result.metrics["rms_cents"]
    assert math.isfinite(rms), f"{family} produced a non-finite RMS"
    assert rms < SANE_RMS_CENTS, f"{family} did not converge sanely: {rms:.1f} cents"
    assert result.metrics["objective_evals"] > 0, f"{family} made no evaluations"
    assert result.metrics["wall_time"] > 0, f"{family} wall time not recorded"


def test_ai_methods_report(comparison_cache):
    """Print the head-to-head table from the per-family test results."""
    missing = [f for f in bench.FAMILIES if f not in comparison_cache]
    if missing:
        pytest.skip(
            f"run the four 'test_ai_method_family' cases first "
            f"(missing: {', '.join(missing)})"
        )

    results = [(name, comparison_cache[name]) for name in bench.FAMILIES]
    print("\n" + bench.build_report(results))
    assert all(res.success for _, res in results)
