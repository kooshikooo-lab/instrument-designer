"""Two-stage intonation acceptance: screen, then extended budget.

Guards against scrapping a design on a short run: if a screening run misses
its intonation tier, the check is retried with a multiplied optimization
budget (more DE generations, BO iterations, RL episodes, ...) before a FAIL
is declared. The policy is documented in docs/PHYSICS_PRINCIPLES.md
("Intonation pass standards"). The retry exists because optimizer results are
noisy: a too-short run can look worse than the design actually is.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from backend.metrics import intonation_passes


def verify_with_retries(
    run_fn: Callable[[float], Dict[str, Any]],
    tier: str = "acceptable",
    attempts: int = 2,
    budget_scale: float = 2.0,
) -> Dict[str, Any]:
    """Screen an optimization run against ``tier``, retrying with more budget.

    Args:
        run_fn: ``run_fn(budget_scale)`` must return a dict containing
            ``rms_cents`` (absolute RMS intonation error in cents) and
            optionally ``max_abs_cents``. ``budget_scale`` is ``1.0`` for the
            first attempt and multiplied by ``budget_scale`` on each retry;
            the consumer maps it onto its own budget knobs.
        tier: one of ``backend.metrics.INTONATION_TIERS``.
        attempts: maximum number of runs (screen + retries).
        budget_scale: multiplier applied to the budget on each retry.

    Returns:
        ``{"status": "PASS" | "FAIL", "tier": tier,
           "passed_attempt": 0-based index of first passing attempt or None,
           "attempts": [run_fn dict augmented with "budget_scale" and
                        "passed": bool, ...]}``
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    history: list[dict] = []
    scale = 1.0
    passed_at = None
    for i in range(int(attempts)):
        metrics = run_fn(scale)
        passed = bool(
            intonation_passes(
                metrics.get("rms_cents"), metrics.get("max_abs_cents"), tier
            )
        )
        entry = dict(metrics)
        entry["budget_scale"] = scale
        entry["passed"] = passed
        history.append(entry)
        if passed:
            passed_at = i
            break
        scale *= budget_scale
    return {
        "status": "PASS" if passed_at is not None else "FAIL",
        "tier": tier,
        "passed_attempt": passed_at,
        "attempts": history,
    }
