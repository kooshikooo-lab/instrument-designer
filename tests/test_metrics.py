"""Unit tests for the canonical tuning-error metrics, intonation tiers, and
the two-stage (screen-then-extended-budget) acceptance policy."""

import math

import pytest

from backend.metrics import (
    ACCEPTABLE_MAX_ABS_CENTS,
    ACCEPTABLE_RMS_CENTS,
    PROFESSIONAL_MAX_ABS_CENTS,
    PROFESSIONAL_RMS_CENTS,
    SANE_RMS_CENTS,
    UNCONVENTIONAL_MAX_ABS_CENTS,
    UNCONVENTIONAL_RMS_CENTS,
    cents_from_frequencies,
    compute_metrics,
    intonation_passes,
    rms_cents,
)
from backend.verification import verify_with_retries


def test_compute_metrics_basic():
    m = compute_metrics([0.0, 5.0, -5.0])
    assert m["final_rms_cents"] == pytest.approx(math.sqrt(50.0 / 3.0))
    assert m["scale_rms_cents"] == pytest.approx(m["final_rms_cents"])
    assert m["median_offset_cents"] == pytest.approx(0.0)
    assert m["peak_error_cents"] == pytest.approx(5.0)


def test_compute_metrics_penalty_sentinel_on_all_invalid():
    m = compute_metrics([float("nan"), float("inf")])
    assert m["final_rms_cents"] == 1e10
    assert m["peak_error_cents"] == 1e10


def test_cents_from_frequencies():
    assert cents_from_frequencies([440.0], [440.0]) == [0.0]
    # one note up in pitch = 1200 * log2(880/440) = 1200 cents
    assert cents_from_frequencies([880.0], [440.0]) == [1200.0]
    # invalid readings become the penalty sentinel
    assert cents_from_frequencies([None, 0.0], [440.0, 440.0]) == [1e10, 1e10]


def test_tiers_are_ordered():
    assert SANE_RMS_CENTS > ACCEPTABLE_RMS_CENTS > PROFESSIONAL_RMS_CENTS
    assert UNCONVENTIONAL_RMS_CENTS >= ACCEPTABLE_RMS_CENTS
    assert UNCONVENTIONAL_MAX_ABS_CENTS >= ACCEPTABLE_MAX_ABS_CENTS > PROFESSIONAL_MAX_ABS_CENTS


def test_intonation_passes_boundaries():
    assert intonation_passes(ACCEPTABLE_RMS_CENTS, tier="acceptable")
    assert not intonation_passes(ACCEPTABLE_RMS_CENTS + 0.01, tier="acceptable")
    assert intonation_passes(5.0, 20.0, tier="acceptable")
    assert not intonation_passes(5.0, ACCEPTABLE_MAX_ABS_CENTS + 1.0, tier="acceptable")


def test_intonation_passes_nonfinite_or_none_never_passes():
    assert not intonation_passes(float("inf"), tier="acceptable")
    assert not intonation_passes(float("nan"), tier="acceptable")
    assert not intonation_passes(None, tier="acceptable")


def test_sane_tier_is_rms_only():
    assert intonation_passes(120.0, tier="sane")
    assert intonation_passes(5.0, 1000.0, tier="sane")  # no per-note max defined


def test_intonation_passes_unknown_tier_raises():
    with pytest.raises(KeyError):
        intonation_passes(5.0, tier="nope")


def test_verify_passes_on_first_attempt():
    calls = []

    def run(scale):
        calls.append(scale)
        return {"rms_cents": 5.0, "max_abs_cents": 12.0}

    v = verify_with_retries(run, tier="acceptable")
    assert v["status"] == "PASS"
    assert v["passed_attempt"] == 0
    assert len(v["attempts"]) == 1
    assert calls == [1.0]


def test_verify_retries_with_extended_budget_then_passes():
    calls = []

    def run(scale):
        calls.append(scale)
        return {"rms_cents": 50.0 if scale == 1.0 else 5.0}

    v = verify_with_retries(run, tier="acceptable", attempts=2, budget_scale=2.0)
    assert v["status"] == "PASS"
    assert v["passed_attempt"] == 1
    assert calls == [1.0, 2.0]
    assert [a["budget_scale"] for a in v["attempts"]] == [1.0, 2.0]
    assert [a["passed"] for a in v["attempts"]] == [False, True]


def test_verify_fails_only_after_all_attempts():
    calls = []

    def run(scale):
        calls.append(scale)
        return {"rms_cents": 50.0}

    v = verify_with_retries(run, tier="acceptable", attempts=3, budget_scale=2.0)
    assert v["status"] == "FAIL"
    assert v["passed_attempt"] is None
    assert calls == [1.0, 2.0, 4.0]


def test_verify_failed_run_never_passes():
    def run(scale):
        return {"rms_cents": float("inf"), "error": "boom"}

    v = verify_with_retries(run, tier="sane", attempts=1)
    assert v["status"] == "FAIL"


def test_verify_rejects_zero_attempts():
    with pytest.raises(ValueError):
        verify_with_retries(lambda s: {"rms_cents": 1.0}, attempts=0)


def test_rms_cents_helper():
    assert rms_cents([0.0, 0.0]) == 0.0
    assert rms_cents([]) == 1e10
