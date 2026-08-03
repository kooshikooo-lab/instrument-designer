"""
Metamaterial low-clarinet test batch.

Covers the low-clarinet family (bass, contra-alto, contra-bass, octocontras)
with acoustic-metamaterial low-register extension (Level 1 HR side-branch
array / Level 2 homogenized segment near the closed end):

  - plain-tube quarter-wave fundamentals vs c/(4L)
  - no-metamaterial default stays bit-identical on a real instrument
  - low-register extension is monotonic in array density and compliance
  - Level 1 (explicit array) vs Level 2 (homogenized) parity on the real bore
  - deterministic tuner hits a target low note (bass -> Bb1 / 58.27 Hz)
  - stopband hygiene: the HR stopband sits above the kept register

Run: pytest tests/test_metamaterial_low_clarinets.py -v
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    all_closed_fingers,
    analytic_f1,
    fundamental,
    make_hr_segment,
    make_low_clarinet,
    registers,
    stopband_bounds,
    tune_f0_to_fundamental,
)

KEYS = sorted(LOW_CLARINETS)


def _with_seg(key, f0, spacing, start_frac=0.9):
    seg, _ = make_hr_segment(key, f0, spacing, start_frac)
    return make_low_clarinet(key, metamaterial_segments=[seg])


def _with_array(key, f0, spacing, start_frac=0.9):
    """Level 1: explicit HR side-branch array matching the homogenized segment."""
    from backend.metamaterial_low_clarinets import (
        DEFAULT_NECK_LENGTH_MM,
        DEFAULT_NECK_RADIUS_MM,
        cavity_volume_for_f0,
    )
    from backend.tmm_acoustics import MetamaterialSideBranch

    spec = LOW_CLARINETS[key]
    start = spec["bore_length_mm"] * start_frac
    end = spec["bore_length_mm"]
    v = cavity_volume_for_f0(f0, DEFAULT_NECK_RADIUS_MM, DEFAULT_NECK_LENGTH_MM)
    n = max(2, int((end - start) / spacing))
    slots = []
    for i in range(n):
        pos = start + i * spacing + spacing / 2.0
        if pos > end:
            break
        slots.append(MetamaterialSideBranch(
            position_mm=pos, neck_radius_mm=DEFAULT_NECK_RADIUS_MM,
            neck_length_mm=DEFAULT_NECK_LENGTH_MM, cavity_volume_mm3=v))
    return make_low_clarinet(key, meta_slots=slots)


# ---------------------------------------------------------------------------
# Plain-tube physics
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", KEYS)
def test_plain_fundamental_matches_quarter_wave(key):
    """Closed-open tube: all-closed fundamental ~ c/(4L) (within ~4%, holes add
    slight compliance on the bass)."""
    inst = make_low_clarinet(key)
    f = fundamental(inst, all_closed_fingers(key))
    assert f == pytest.approx(analytic_f1(key), rel=0.04)


@pytest.mark.parametrize("key", KEYS)
def test_plain_odd_harmonic_register_structure(key):
    """Registers 1,2,3 of the plain closed-open tube are ~ 1:3:5."""
    inst = make_low_clarinet(key)
    fs = registers(inst, all_closed_fingers(key), n=3)
    assert fs[1] / fs[0] == pytest.approx(3.0, rel=0.06)
    assert fs[2] / fs[0] == pytest.approx(5.0, rel=0.06)


# ---------------------------------------------------------------------------
# Regression: metamaterial defaults never change the plain instrument
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", KEYS)
def test_meta_default_bit_identical(key):
    """Explicit empty metamaterial lists leave the action chain unchanged."""
    inst = make_low_clarinet(key)
    chain = inst.actions[:]
    inst2 = make_low_clarinet(key, meta_slots=[], metamaterial_segments=[])
    inst2._prepare_phase()
    assert inst2.actions == chain


# ---------------------------------------------------------------------------
# Low-register extension mechanics
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", KEYS)
def test_extension_monotonic_with_array_density(key):
    """Denser arrays (smaller spacing) -> more compliance -> lower f1."""
    f0 = 4.0 * analytic_f1(key)  # keep stopband well above the register
    f_loose = fundamental(_with_seg(key, f0, spacing=80.0), all_closed_fingers(key))
    f_dense = fundamental(_with_seg(key, f0, spacing=20.0), all_closed_fingers(key))
    assert f_dense < f_loose < analytic_f1(key)


@pytest.mark.parametrize("key", KEYS)
def test_extension_monotonic_with_compliance(key):
    """Lower f0 (more compliance) -> lower f1 at fixed spacing."""
    f1 = all_closed_fingers(key)
    base = analytic_f1(key)
    f_high = fundamental(_with_seg(key, 6.0 * base, 30.0), f1)
    f_mid = fundamental(_with_seg(key, 3.0 * base, 30.0), f1)
    f_low = fundamental(_with_seg(key, 1.8 * base, 30.0), f1)
    assert f_low < f_mid < f_high < base


# ---------------------------------------------------------------------------
# Level 1 (explicit array) vs Level 2 (homogenized) parity on a real bore
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", KEYS)
def test_level1_vs_level2_fundamental_parity(key):
    """L1 explicit HR array and L2 homogenized segment agree on f1 in the
    weak-loading regime (homogenization is valid; strong loading diverges and
    is covered separately by the conservative-guarantee test)."""
    fingers = all_closed_fingers(key)
    f0 = 12.0 * analytic_f1(key)  # weak loading: parity holds
    spacing = 40.0
    f_l2 = fundamental(_with_seg(key, f0, spacing), fingers)
    f_l1 = fundamental(_with_array(key, f0, spacing), fingers)
    assert f_l2 == pytest.approx(f_l1, rel=0.08)


def test_level1_vs_level2_parity_full_register_bass():
    """On the validated bass bore, L1/L2 agree across registers 1-3."""
    key = "bass"
    fingers = all_closed_fingers(key)
    f0 = 12.0 * analytic_f1(key)
    spacing = 40.0
    r2 = registers(_with_seg(key, f0, spacing), fingers, 3)
    r1 = registers(_with_array(key, f0, spacing), fingers, 3)
    for a, b in zip(r1, r2):
        assert a == pytest.approx(b, rel=0.08)


def test_l2_design_is_conservative_under_strong_loading():
    """At strong loading the homogenized model UNDER-estimates the extension:
    an explicit L1 array of the same design must reach at least as low as the
    L2 prediction (i.e. f1_L1 <= f1_L2). L2 is therefore a safe lower bound
    on how much low register a printed array will gain."""
    key = "bass"
    fingers = all_closed_fingers(key)
    f0 = 3.0 * analytic_f1(key)
    spacing = 40.0
    f_l2 = fundamental(_with_seg(key, f0, spacing), fingers)
    f_l1 = fundamental(_with_array(key, f0, spacing), fingers)
    assert f_l1 < f_l2 < analytic_f1(key)


# ---------------------------------------------------------------------------
# Tuner: hit a real low note, keep the stopband out of the kept register
# ---------------------------------------------------------------------------

def test_tune_bass_to_low_c_bb1():
    """Bass clarinet: metamaterial extends the all-closed note D2 -> Bb1
    (58.27 Hz, the low-C equivalent) at the same 1211.3 mm physical length."""
    key = "bass"
    target = LOW_CLARINETS[key]["extension_target_hz"]
    _, _, achieved = tune_f0_to_fundamental(key, target, spacing_mm=30.0)
    cents = 1200.0 * math.log2(achieved / target)
    assert abs(cents) < 5.0


def test_tune_every_family_member_reaches_target():
    """Every family member can hit its extension target (0.8 x plain f1)."""
    for key in KEYS:
        target = LOW_CLARINETS[key]["extension_target_hz"]
        _, _, achieved = tune_f0_to_fundamental(key, target, spacing_mm=40.0)
        cents = 1200.0 * math.log2(achieved / target)
        assert abs(cents) < 10.0, f"{key}: {achieved:.2f} vs {target:.2f}"


def test_tuned_config_guarantees_target_as_explicit_array():
    """An L2-tuned design, built as an explicit L1 array, reaches AT LEAST the
    target note (conservative L2 design -> overshoot, never shortfall)."""
    key = "bass"
    target = LOW_CLARINETS[key]["extension_target_hz"]
    f0, seg, _ = tune_f0_to_fundamental(key, target, spacing_mm=30.0)
    inst = _with_array(key, f0, seg.spacing_mm)
    achieved = fundamental(inst, all_closed_fingers(key))
    assert achieved <= target + 0.05


def test_stopband_hygiene_after_tuning():
    """Design window: HR f0 (stopband start) lands between register-2 (the
    12th, kept) and register-3 (suppressed), and the stopband is a finite gap
    the medium recovers above."""
    key = "bass"
    target = LOW_CLARINETS[key]["extension_target_hz"]
    f0, seg, achieved = tune_f0_to_fundamental(key, target, spacing_mm=30.0)
    fingers = all_closed_fingers(key)
    inst = make_low_clarinet(key, metamaterial_segments=[seg])
    r = registers(inst, fingers, 3)
    assert f0 > 1.5 * achieved, "stopband too close to the kept fundamental"
    assert r[1] < f0 < r[2], "f0 must sit between the 12th and register 3"
    lo, hi = stopband_bounds(key, f0, seg.spacing_mm)
    assert lo is not None and hi > f0, "expected a finite stopband above f0"
    assert hi < 1e6, "medium must recover at finite frequency"


def test_stopband_finite_gap_all_family():
    """For every member, a tuned configuration yields a finite stopband above
    f0 (gap present, medium recovers higher up)."""
    for key in KEYS:
        target = LOW_CLARINETS[key]["extension_target_hz"]
        f0, seg, _ = tune_f0_to_fundamental(key, target, spacing_mm=40.0)
        lo, hi = stopband_bounds(key, f0, seg.spacing_mm)
        assert lo is not None
        assert hi > f0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
