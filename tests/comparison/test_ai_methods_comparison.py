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
import time

import numpy as np
import pytest

from comparison_framework import AlgorithmResult
import ai_methods_benchmark as bench
from backend.metrics import SANE_RMS_CENTS
from backend.verification import verify_with_retries

pytestmark = [
    pytest.mark.comparison,
    pytest.mark.slow,
]

# Generous sanity bound: every family must land well inside the achievable
# range (the uniform-10mm baseline is ~77 cents; the tuned floor is ~6 cents).
# Canonical value lives in backend.metrics.


@pytest.fixture(scope="module")
def comparison_cache():
    """Shared module cache so the report test reuses per-family results."""
    return {}


@pytest.fixture(scope="module")
def shared_objective():
    """The exact objective every family optimizes."""
    return bench.benchmark_objective


# Budget knobs per family; ``scale`` (1.0 on the screen, then multiplied per
# retry) extends the dominant budget of each runner.
_BUDGET_KWARGS = {
    "bayesian_optimization": lambda scale: {"n_iter": max(30, int(30 * scale))},
    "neural_surrogate": lambda scale: {"n_de_iter": max(25, int(25 * scale))},
    "reinforcement_learning": lambda scale: {"n_episodes": max(150, int(150 * scale))},
    "gradient_free": lambda scale: {"max_evals": max(600, int(600 * scale))},
}


def _wrap_budgeted(runner, kwargs):
    """Run a family runner with explicit budget kwargs -> AlgorithmResult."""
    name = runner.__name__.replace("run_", "").replace("_", " ").title()
    t0 = time.time()
    try:
        metrics = runner(**kwargs)
        return AlgorithmResult(
            name=name,
            success=True,
            runtime_seconds=metrics["wall_time"],
            metrics=metrics,
            metadata={"method": runner.__name__},
        )
    except Exception as exc:  # pragma: no cover - defensive
        return AlgorithmResult(
            name=name,
            success=False,
            runtime_seconds=time.time() - t0,
            error=str(exc),
            metadata={"method": runner.__name__},
        )


def _family_metrics(family, scale):
    """Run one family with a scaled budget; return a verify_with_retries dict."""
    result = _wrap_budgeted(bench.FAMILIES[family], _BUDGET_KWARGS[family](scale))
    if not result.success:
        return {
            "rms_cents": float("inf"),
            "success": False,
            "error": result.error,
            "result": result,
        }
    return {"rms_cents": result.metrics["rms_cents"], "success": True, "result": result}


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
    """Each family converges sanely on the shared Bb-clarinet tuning task.

    A failing screen is retried once with a doubled budget (see
    backend.verification.verify_with_retries) so a short-run artifact --
    optimizer noise or a non-converged population -- does not fail a family
    that is fine on a longer run.
    """
    if extra_dep:
        pytest.importorskip(extra_dep)
    ver = verify_with_retries(
        lambda scale: _family_metrics(family, scale),
        tier="sane",
        attempts=2,
        budget_scale=2.0,
    )
    passing = [a for a in ver["attempts"] if a["passed"]]
    assert ver["status"] == "PASS", (
        f"{family} missed the sane tier ({SANE_RMS_CENTS:.0f}c) after "
        f"{len(ver['attempts'])} attempt(s); best rms "
        f"{min(a.get('rms_cents', float('inf')) for a in ver['attempts']):.1f}c"
    )
    result = passing[0]["result"]
    comparison_cache[family] = result
    rms = result.metrics["rms_cents"]
    assert math.isfinite(rms), f"{family} produced a non-finite RMS"
    assert rms <= SANE_RMS_CENTS, f"{family} did not converge sanely: {rms:.1f} cents"
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
