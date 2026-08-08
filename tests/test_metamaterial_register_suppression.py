"""Register-2 squeak suppression tests (bass clarinet metamaterial).

An HR array whose stopband covers the all-closed register-2 (the 12th) removes
the resonance AT the squeak frequency: phase_at(squeak) drops below the
resonance condition 2.0. The compliance tail below f0 retunes the low register
(f1 drops) - the documented suppression-vs-shift coupling.
"""

import math

from backend.metamaterial_low_clarinets import (
    all_closed_fingers,
    explicit_hr_array,
    fundamental,
    make_hr_segment,
    make_low_clarinet,
    phase_at,
    registers,
    stopband_bounds,
    twelfth_deviation,
)

KEY = "bass"
SQUEAK_CONDITION = 2.0


def _design(f0_ratio, spacing=30.0):
    """Shared design: closed-end segment/array, f0 = ratio x the plain 12th."""
    squeak = registers(make_low_clarinet(KEY), all_closed_fingers(KEY), 2)[1]
    f0 = f0_ratio * squeak
    seg, _ = make_hr_segment(KEY, f0, spacing, start_frac=0.9)
    inst2 = make_low_clarinet(KEY, metamaterial_segments=[seg])
    inst1 = explicit_hr_array(KEY, f0, spacing, start_frac=0.9)
    return squeak, f0, inst2, inst1


def test_plain_bass_12th_is_clean():
    """The plain 12th is a near-perfect 3:1 - the clean 'squeak' baseline."""
    inst = make_low_clarinet(KEY)
    fingers = all_closed_fingers(KEY)
    dev = twelfth_deviation(inst, fingers)
    assert abs(dev) < 5.0


def test_squeak_is_the_register_2_resonance():
    """The squeak target is the all-closed 12th (~3x f1) at a resonant phase."""
    inst = make_low_clarinet(KEY)
    fingers = all_closed_fingers(KEY)
    regs = registers(inst, fingers, 2)
    cents_12th = 1200.0 * math.log2(regs[1] / regs[0] / 3.0)
    assert abs(cents_12th) < 10.0
    assert abs(phase_at(inst, fingers, regs[1]) - SQUEAK_CONDITION) < 0.05


def test_l2_stopband_covers_and_suppresses_squeak():
    """L2: squeak inside the stopband and no longer resonant, f1 preserved-ish."""
    fingers = all_closed_fingers(KEY)
    squeak, f0, inst2, _ = _design(0.8)
    lo, hi = stopband_bounds(KEY, f0, 30.0)
    assert lo is not None and lo <= squeak <= hi
    assert phase_at(inst2, fingers, squeak) < SQUEAK_CONDITION
    f1 = fundamental(make_low_clarinet(KEY), fingers)
    assert 0.9 < phase_at(inst2, fingers, f1) < 1.5


def test_l1_stopband_suppresses_squeak():
    """L1 explicit array: squeak inside the band and no longer resonant."""
    fingers = all_closed_fingers(KEY)
    squeak, f0, _, inst1 = _design(0.8)
    lo, hi = stopband_bounds(KEY, f0, 30.0)
    assert lo is not None and lo <= squeak <= hi
    assert phase_at(inst1, fingers, squeak) < SQUEAK_CONDITION


def test_l1_exact_f0_is_a_blind_spot():
    """Tuning the HR array EXACTLY at the squeak gives ~zero suppression (design
    warning: the squeak sits at the band's lower edge, not inside it)."""
    fingers = all_closed_fingers(KEY)
    squeak, _, _, inst1 = _design(1.0)
    assert SQUEAK_CONDITION - phase_at(inst1, fingers, squeak) < 0.01


def test_suppression_costs_low_register_shift():
    """The compliance tail below f0 lowers the fundamental - the trade-off."""
    fingers = all_closed_fingers(KEY)
    plain = make_low_clarinet(KEY)
    f1_plain = fundamental(plain, fingers)
    _, _, inst2, inst1 = _design(0.8)
    assert fundamental(inst2, fingers) < f1_plain
    assert fundamental(inst1, fingers) < f1_plain
    assert phase_at(inst2, fingers, f1_plain) > 1.0  # plain f1 no longer a resonance
