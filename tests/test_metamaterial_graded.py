"""
Graded / broadband metamaterial HR-array test batch (IOP 2025 non-uniform
Helmholtz resonator arrays).

Graded arrays sweep each resonator's resonance across the closed-end segment
(rainbow-trapping / broadened attenuation) instead of tuning every resonator
to the same f0. Level 2 (homogenized) holds a single f0, so graded designs
are explicit-array (Level 1) only. These tests lock:

  - the f0 schedule (linear / geometric) and the uniform-array special case
  - monotonic cavity-volume ramp along the array
  - resonator_f0 round-trip vs the schedule
  - low-register extension on the real bass bore
  - the broadband knob: wider f0 sweep -> wider resonance band at same N

Run: pytest tests/test_metamaterial_graded.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    array_resonance_band,
    all_closed_fingers,
    cavity_volume_for_f0,
    explicit_hr_array,
    fundamental,
    graded_f0_schedule,
    graded_hr_array,
    resonator_f0,
)

KEYS = sorted(LOW_CLARINETS)
BASS = "bass"


def _graded(key, f0_lo, f0_hi, spacing=40.0, profile="linear"):
    inst = graded_hr_array(key, f0_lo, f0_hi, spacing, profile=profile)
    f1 = fundamental(inst, all_closed_fingers(key))
    return inst, f1


def test_linear_schedule_endpoints():
    n = 5
    sched = graded_f0_schedule(n, 200.0, 600.0, "linear")
    assert len(sched) == n
    assert sched[0] == 200.0
    assert sched[-1] == 600.0
    assert all(sched[i] < sched[i + 1] for i in range(n - 1))


def test_geometric_schedule_constant_ratio():
    n = 5
    sched = graded_f0_schedule(n, 200.0, 800.0, "geometric")
    ratios = [sched[i + 1] / sched[i] for i in range(n - 1)]
    assert sched[0] == 200.0
    assert abs(sched[-1] - 800.0) < 1e-9
    assert max(ratios) - min(ratios) < 1e-12


def test_schedule_uniform_special_case():
    assert graded_f0_schedule(4, 500.0, 500.0) == [500.0] * 4


def test_schedule_rejects_bad_profile():
    import pytest

    with pytest.raises(ValueError):
        graded_f0_schedule(3, 200.0, 600.0, "bogus")


def test_graded_array_volumes_ramp_monotonically():
    inst = graded_hr_array(BASS, 300.0, 900.0, 30.0, profile="linear")
    vols = [s.cavity_volume_mm3 for s in inst.meta_slots]
    assert len(vols) >= 3
    assert all(vols[i] > vols[i + 1] for i in range(len(vols) - 1))


def test_resonator_f0_round_trips_schedule():
    n = 4
    sched = graded_f0_schedule(n, 300.0, 900.0, "linear")
    slots = []
    from backend.tmm_acoustics import MetamaterialSideBranch

    for i, f0 in enumerate(sched):
        v = cavity_volume_for_f0(f0)
        slots.append(MetamaterialSideBranch(
            position_mm=100.0 + 10.0 * i, neck_radius_mm=4.0,
            neck_length_mm=8.0, cavity_volume_mm3=v))
    got = [resonator_f0(s) for s in slots]
    for want, g in zip(sched, got):
        assert abs(want - g) < 1e-9


def test_graded_array_band_is_monotonic_in_sweep():
    for f0_hi in (600.0, 900.0, 1200.0):
        inst = graded_hr_array(BASS, 400.0, f0_hi, 30.0, profile="linear")
        lo, hi = array_resonance_band(inst.meta_slots)
        assert lo is not None and hi is not None
        assert abs(lo - 400.0) < 1.0


def test_graded_array_extends_low_register_bass():
    plain = fundamental(explicit_hr_array(BASS, 2000.0, 30.0),
                        all_closed_fingers(BASS))
    graded, f1 = _graded(BASS, 350.0, 900.0)
    assert f1 < plain * 0.85  # graded array loads the closed end too


def test_geometric_vs_linear_same_extension_same_n():
    _, f1_lin = _graded(BASS, 300.0, 1000.0, profile="linear")
    _, f1_geo = _graded(BASS, 300.0, 1000.0, profile="geometric")
    assert abs(f1_lin - f1_geo) < 5.0


def test_wider_sweep_extends_more():
    """The broadband knob: a wider f0 sweep loads the low register more."""
    _, f1_narrow = _graded(BASS, 500.0, 700.0)
    _, f1_wide = _graded(BASS, 300.0, 1200.0)
    assert f1_wide < f1_narrow


def test_graded_matches_uniform_when_sweep_zero():
    inst_u = explicit_hr_array(BASS, 600.0, 30.0)
    inst_g = graded_hr_array(BASS, 600.0, 600.0, 30.0, profile="linear")
    f1_u = fundamental(inst_u, all_closed_fingers(BASS))
    f1_g = fundamental(inst_g, all_closed_fingers(BASS))
    assert abs(f1_u - f1_g) < 1e-9


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
