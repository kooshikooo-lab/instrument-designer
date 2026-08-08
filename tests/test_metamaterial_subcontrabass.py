"""
Sub-contrabass clarinet (BBBb, 3000 mm) — deepest family member tests.

Extends the low-clarinet family beyond the octocontras. Uses the exact same
pipeline (tuner + L1 array + STL section) and must stay on the family curves:
target reach, monotonic family order, 12th in the family band.

Run: pytest tests/test_metamaterial_subcontrabass.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    SPEED_OF_SOUND,
    all_closed_fingers,
    explicit_hr_array,
    fundamental,
    tune_f0_to_fundamental_l1,
    twelfth_deviation,
)

KEY = "subcontrabass"


def test_quarter_wave_fundamental():
    spec = LOW_CLARINETS[KEY]
    inst = explicit_hr_array(KEY, 2000.0, 40.0)  # no effective array
    f1 = fundamental(inst, all_closed_fingers(KEY))
    analytic = SPEED_OF_SOUND / (4.0 * spec["bore_length_mm"])
    assert abs(f1 - analytic) < 0.5


def test_extension_target_reached():
    target = LOW_CLARINETS[KEY]["extension_target_hz"]
    f0, n, achieved, _ = tune_f0_to_fundamental_l1(KEY, target, spacing_mm=40.0)
    assert abs(achieved - target) < 0.1
    assert n >= 5  # deep member carries a real array


def test_deepest_in_the_family():
    """Subcontrabass all-closed note is the lowest of the 6-member family."""
    f1 = fundamental(explicit_hr_array(KEY, 2000.0, 40.0),
                     all_closed_fingers(KEY))
    for other in ("octocontrabass", "octocontra_alto", "contra_bass"):
        f_other = fundamental(explicit_hr_array(other, 2000.0, 40.0),
                              all_closed_fingers(other))
        assert f1 < f_other


def test_twelfth_stays_in_family_band():
    target = LOW_CLARINETS[KEY]["extension_target_hz"]
    _, _, _, inst = tune_f0_to_fundamental_l1(KEY, target, spacing_mm=40.0)
    dev = twelfth_deviation(inst, all_closed_fingers(KEY))
    assert 50.0 < dev < 120.0


def test_stopband_sits_above_register_three():
    """The tuned design keeps the stopband clear of the kept registers."""
    target = LOW_CLARINETS[KEY]["extension_target_hz"]
    f0, n, _, inst = tune_f0_to_fundamental_l1(KEY, target, spacing_mm=40.0)
    from backend.metamaterial_low_clarinets import registers

    r = registers(inst, all_closed_fingers(KEY), 3)
    assert f0 > r[1]  # stopband starts above the 12th


def test_extends_more_than_octocontrabass():
    target = LOW_CLARINETS[KEY]["extension_target_hz"]
    _, _, _, inst = tune_f0_to_fundamental_l1(KEY, target, spacing_mm=40.0)
    f1 = fundamental(inst, all_closed_fingers(KEY))
    target_ocb = LOW_CLARINETS["octocontrabass"]["extension_target_hz"]
    _, _, f1_ocb, _ = tune_f0_to_fundamental_l1(
        "octocontrabass", target_ocb, spacing_mm=40.0)
    assert f1 < f1_ocb


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
