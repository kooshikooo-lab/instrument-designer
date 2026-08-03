import pytest

from backend.optimization.problem import build_metric_summary


def test_build_metric_summary_uses_absolute_rms_as_primary_metric():
    summary = build_metric_summary([0.0, 10.0, -10.0])

    assert summary["final_rms_cents"] == pytest.approx(8.16496580927726)
    assert summary["scale_rms_cents"] == pytest.approx(8.16496580927726)
    assert summary["median_offset_cents"] == pytest.approx(0.0)
    assert summary["peak_error_cents"] == pytest.approx(10.0)
