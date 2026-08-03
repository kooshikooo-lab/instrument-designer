"""
Low-register-extension vs 12th-intonation trade-off test batch.

Extending the all-closed note with a near-closed-end compliance array also
stretches the register-2 (12th) ratio above 3:1. These tests lock the
characterization of that trade-off:

  - the plain (unloaded) instrument has a near-perfect 12th
  - the distortion is monotonic in extension depth (deeper = sharper 12th)
  - the family targets sit at a documented, bounded distortion level
  - extra low-f0 resonators do NOT fix the ratio (they break register 2)

Run: pytest tests/test_metamaterial_intonation.py -v
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    MetamaterialSideBranch,
    analytic_f1,
    all_closed_fingers,
    explicit_hr_array,
    make_low_clarinet,
    registers,
    tune_f0_to_fundamental_l1,
    twelfth_deviation,
)

KEYS = sorted(LOW_CLARINETS)


def _tuned(key, target_frac=0.8):
    target = target_frac * analytic_f1(key)
    f0, n, f1, inst = tune_f0_to_fundamental_l1(
        key, target, spacing_mm=40.0)
    return inst, f0, f1


def test_plain_instrument_has_perfect_twelfth():
    for key in KEYS:
        inst = explicit_hr_array(key, 2000.0, 40.0)  # no effective array
        dev = twelfth_deviation(inst, all_closed_fingers(key))
        assert abs(dev) < 5.0, f"{key}: plain 12th dev {dev:.1f}c"


def test_twelfth_deviation_matches_registers():
    inst = explicit_hr_array("bass", 2000.0, 40.0)
    fingers = all_closed_fingers("bass")
    r = registers(inst, fingers, 2)
    dev = 1200.0 * math.log2((r[1] / r[0]) / 3.0)
    assert abs(twelfth_deviation(inst, fingers) - dev) < 1e-9


def test_distortion_is_monotonic_in_extension_depth():
    """Deeper low-register extension => sharper 12th (design curve is smooth)."""
    devs = []
    for frac in (0.95, 0.90, 0.85, 0.80, 0.75):
        inst, _, _ = _tuned("bass", target_frac=frac)
        devs.append(twelfth_deviation(inst, all_closed_fingers("bass")))
    assert all(devs[i] < devs[i + 1] for i in range(len(devs) - 1))
    assert devs[0] < 15.0  # shallow extension: 12th nearly intact
    assert devs[-1] > 100.0  # deep extension: 12th seriously stretched


def test_family_targets_bounded_distortion():
    """All family targets (0.8 x plain f1) sit in the documented +60..+110c band."""
    for key in KEYS:
        inst, _, _ = _tuned(key, target_frac=0.8)
        dev = twelfth_deviation(inst, all_closed_fingers(key))
        assert 50.0 < dev < 120.0, f"{key}: 12th dev {dev:.1f}c out of band"


def test_shallow_target_keeps_12th_usable():
    """Backing off to 0.9 x plain f1 keeps the 12th within ~30c."""
    inst, _, _ = _tuned("bass", target_frac=0.9)
    dev = twelfth_deviation(inst, all_closed_fingers("bass"))
    assert abs(dev) < 30.0


def test_extra_low_resonator_breaks_register_two():
    """A resonator tuned near f2 suppresses register 2 (ratio diverges)."""
    base = explicit_hr_array("bass", 572.0, 30.0)
    dev_base = twelfth_deviation(base, all_closed_fingers("bass"))
    from backend.metamaterial_low_clarinets import cavity_volume_for_f0

    slots = base.meta_slots + [MetamaterialSideBranch(
        position_mm=1100.0, neck_radius_mm=4.0, neck_length_mm=8.0,
        cavity_volume_mm3=cavity_volume_for_f0(250.0))]
    broke = make_low_clarinet("bass", meta_slots=slots)
    dev_broke = twelfth_deviation(broke, all_closed_fingers("bass"))
    assert dev_broke > dev_base + 100.0


def test_extension_is_the_goal_and_12th_is_the_price():
    """The trade-off is real: deep extension hits the target, shallow keeps 12th."""
    target = 0.8 * analytic_f1("bass")
    inst, f0, f1 = _tuned("bass", target_frac=0.8)
    assert abs(f1 - target) < 0.1
    assert twelfth_deviation(inst, all_closed_fingers("bass")) > 60.0


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
