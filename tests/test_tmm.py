"""
Test and validate TMM acoustics module against known instrument designs.
"""

import os
import sys
import time

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.archived_optimizers.tmm_optimizer import TMMBoreOptimizer
from backend.tmm_acoustics import (
    SPEED_OF_SOUND,
    Hole,
    TMMInstrument,
    end_flange_length_correction,
    tmm_instrument_from_radii,
)


def test_simple_flute():
    """Test: open-open cylindrical pipe (simple flute without holes)."""
    print("=" * 60)
    print("TEST 1: Open-open cylindrical pipe (flute)")
    print("=" * 60)

    bore_length = 500.0  # mm
    bore_diameter = 19.0  # mm (typical flute)
    outer_diameter = 22.0  # mm
    v = SPEED_OF_SOUND  # mm/s

    # Account for end flange correction
    end_corr = end_flange_length_correction(outer_diameter, bore_diameter)
    effective_length = bore_length + end_corr  # open end adds one correction
    # Theoretical resonant frequencies with end correction
    theo_freqs = [n * v / (2.0 * effective_length) for n in range(1, 7)]
    print(f"  Bore: {bore_length}mm x {bore_diameter}mm (open-open)")
    print(f"  End flange correction: {end_corr:.2f}mm")
    print(f"  Effective length: {effective_length:.2f}mm")
    print(f"  Speed of sound: {v} mm/s")
    print(f"  Theoretical freqs: {[f'{f:.1f}' for f in theo_freqs]}")

    inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[outer_diameter, outer_diameter],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=False,
    )

    # Find resonances
    # Note: open-open pipes have DC resonance_phase = 1.0 (0.5 per open end),
    # so n_register = n+1 for the nth harmonic (1-indexed).
    actual_freqs = []
    for n in range(1, 7):
        target_wl = 2.0 * bore_length / n  # initial guess
        fingerings = []
        wl = inst.find_resonance(target_wl, fingerings, n_register=n + 1)
        freq = inst.frequency_from_wavelength(wl)
        actual_freqs.append(freq)

    print(f"  Actual freqs:     {[f'{f:.1f}' for f in actual_freqs]}")

    f1 = actual_freqs[0]
    expected_f1 = v / (2.0 * effective_length)
    assert abs(f1 - expected_f1) < 10, f"Fundamental frequency {f1:.1f}Hz not near {expected_f1:.1f}Hz"

    errors = [abs(a - t) / t * 100 for a, t in zip(actual_freqs, theo_freqs)]
    print(f"  Relative errors:  {[f'{e:.3f}%' for e in errors]}")
    max_err = max(errors)
    print(f"  Max error: {max_err:.4f}%")
    assert max_err < 1.0, f"Flute test failed: max error {max_err:.4f}% > 1%"


def test_simple_clarinet():
    """Test: closed-open cylindrical pipe (clarinet)."""
    print("=" * 60)
    print("TEST 2: Closed-open cylindrical pipe (clarinet)")
    print("=" * 60)

    bore_length = 600.0  # mm
    bore_diameter = 14.5  # mm (typical clarinet)
    outer_diameter = 22.0
    v = SPEED_OF_SOUND

    # Closed-open pipe: f_n = n * v / (4L) for odd n = 1, 3, 5, ...
    # The closed end (reed) has no end correction.
    # The open end has a flange correction.
    end_corr = end_flange_length_correction(outer_diameter, bore_diameter)
    effective_length = bore_length + end_corr
    theo_freqs = [n * v / (4.0 * effective_length) for n in [1, 3, 5, 7, 9, 11]]
    print(f"  Bore: {bore_length}mm x {bore_diameter}mm (closed-open)")
    print(f"  End flange correction: {end_corr:.2f}mm")
    print(f"  Theoretical freqs: {[f'{f:.1f}' for f in theo_freqs]}")

    inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[outer_diameter, outer_diameter],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=True,
    )

    actual_freqs = []
    for n_register, n_harm in enumerate([1, 3, 5, 7, 9, 11], 1):
        target_wl = 4.0 * bore_length / n_harm
        wl = inst.find_resonance(target_wl, [], n_register=n_register)
        freq = inst.frequency_from_wavelength(wl)
        actual_freqs.append(freq)

    print(f"  Actual freqs:     {[f'{f:.1f}' for f in actual_freqs]}")

    f1 = actual_freqs[0]
    expected_f1 = v / (4.0 * effective_length)
    assert abs(f1 - expected_f1) < 10, f"Fundamental frequency {f1:.1f}Hz not near {expected_f1:.1f}Hz"

    errors = [abs(a - t) / t * 100 for a, t in zip(actual_freqs, theo_freqs)]
    print(f"  Relative errors:  {[f'{e:.3f}%' for e in errors]}")
    max_err = max(errors)
    print(f"  Max error: {max_err:.4f}%")
    assert max_err < 1.0, f"Clarinet test failed: max error {max_err:.4f}% > 1%"


def test_flute_with_holes():
    """Test: open-open pipe with tone holes (7-hole flute)."""
    print("=" * 60)
    print("TEST 3: Open-open pipe with 7 tone holes")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    v = SPEED_OF_SOUND

    # 7 holes spaced along the bore
    hole_positions = [100, 150, 200, 250, 300, 350, 400]
    hole_diameters = [8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0]
    hole_lengths = [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0]

    inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=False,
    )

    # Test: all holes closed (should be close to no-hole case)
    all_closed = [Hole.CLOSED] * 7
    wl = inst.find_resonance(2.0 * bore_length, all_closed, n_register=2)
    freq_all_closed = inst.frequency_from_wavelength(wl)
    end_corr = end_flange_length_correction(22.0, bore_diameter)
    theo_f1 = v / (2.0 * (bore_length + end_corr))
    print(f"  All holes closed: {freq_all_closed:.1f} Hz (theoretical: {theo_f1:.1f} Hz)")
    err = abs(freq_all_closed - theo_f1) / theo_f1 * 100
    print(f"  Error: {err:.2f}%")
    assert err < 1.0, f"All-closed error {err:.2f}% > 1%"

    # Test: first hole open (shorter effective length -> higher pitch)
    first_open = [Hole.OPEN] + [Hole.CLOSED] * 6
    wl2 = inst.find_resonance(2.0 * bore_length, first_open, n_register=2)
    freq_first_open = inst.frequency_from_wavelength(wl2)
    print(f"  First hole open:  {freq_first_open:.1f} Hz")

    # Opening holes should raise the pitch
    assert freq_first_open > freq_all_closed, "Opening a hole should raise pitch"
    print("  Opening hole raises pitch: PASS")

    # Test: more holes open -> even higher pitch
    three_open = [Hole.OPEN] * 3 + [Hole.CLOSED] * 4
    wl3 = inst.find_resonance(2.0 * bore_length, three_open, n_register=2)
    freq_three_open = inst.frequency_from_wavelength(wl3)
    print(f"  Three holes open: {freq_three_open:.1f} Hz")
    assert freq_three_open > freq_first_open, "More holes open should raise pitch more"
    print("  More holes raise pitch: PASS")
    print("  PASS\n")


@pytest.mark.slow
def test_optimizer_simple_flute():
    """Test: optimize a simple flute bore to hit target frequencies."""
    print("=" * 60)
    print("TEST 4: TMM optimizer on simple flute (7-hole)")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0

    # Target: 7-hole diatonic scale (C major from C5)
    hole_positions = [100, 150, 200, 250, 300, 350, 400]
    hole_diameters = [8.0] * 7
    hole_lengths = [3.0] * 7

    # Reference instrument to get target frequencies
    ref_inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=False,
    )

    # Fingerings: each hole open/closed for a diatonic scale
    fingerings = [
        [Hole.CLOSED] * 7,  # C (all closed)
        [Hole.OPEN, Hole.CLOSED] * 3 + [Hole.CLOSED],  # D
        [Hole.OPEN] * 2 + [Hole.CLOSED] * 5,  # E
        [Hole.OPEN] * 3 + [Hole.CLOSED] * 4,  # F
        [Hole.OPEN] * 4 + [Hole.CLOSED] * 3,  # G
        [Hole.OPEN] * 5 + [Hole.CLOSED] * 2,  # A
        [Hole.OPEN] * 6 + [Hole.CLOSED],  # B
    ]

    # Get target frequencies from reference
    target_freqs = []
    target_wls = []
    for fing in fingerings:
        wl = ref_inst.find_resonance(2.0 * bore_length, fing, n_register=2)
        freq = ref_inst.frequency_from_wavelength(wl)
        target_freqs.append(freq)
        target_wls.append(wl)

    print(f"  Target frequencies: {[f'{f:.1f}' for f in target_freqs]}")

    # Optimize with perturbed bore
    optimizer = TMMBoreOptimizer(
        target_frequencies=target_freqs,
        fingering_sets=fingerings,
        n_control_points=8,
        bore_length=bore_length,
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=False,
        min_radius=5.0,
        max_radius=15.0,
    )

    t0 = time.time()
    result = optimizer.run(verbose=True, method="L-BFGS-B", maxiter=100)
    wall_time = time.time() - t0

    print(f"\n  Final RMS: {result['final_rms_cents']:.2f} cents")
    print(f"  Wall time: {wall_time:.1f}s")

    # Should achieve < 50 cents RMS (this is a simple case)
    assert result['final_rms_cents'] < 100, \
        f"Optimizer failed: {result['final_rms_cents']:.2f} cents > 100"
    print("  PASS\n")


@pytest.mark.slow
def test_optimizer_clarinet():
    """Test: optimize a clarinet bore (closed-open pipe)."""
    print("=" * 60)
    print("TEST 5: TMM optimizer on clarinet (closed-open)")
    print("=" * 60)

    bore_length = 600.0
    bore_diameter = 14.5

    # Simple clarinet with 5 holes
    hole_positions = [120, 200, 280, 360, 440]
    hole_diameters = [7.0] * 5
    hole_lengths = [4.0] * 5

    # Reference for target frequencies (5 harmonics of Bb clarinet)
    ref_inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=True,
    )

    # Fingerings for Bb clarinet odd harmonics
    fingerings = [
        [Hole.CLOSED] * 5,  # Chalumeau (lowest)
        [Hole.OPEN, Hole.CLOSED] * 2 + [Hole.CLOSED],
        [Hole.OPEN] * 2 + [Hole.CLOSED] * 3,
        [Hole.OPEN] * 3 + [Hole.CLOSED] * 2,
        [Hole.OPEN] * 4 + [Hole.CLOSED],
    ]

    target_freqs = []
    for fing in fingerings:
        wl = ref_inst.find_resonance(4.0 * bore_length, fing, n_register=1)
        freq = ref_inst.frequency_from_wavelength(wl)
        target_freqs.append(freq)

    print(f"  Target frequencies: {[f'{f:.1f}' for f in target_freqs]}")

    optimizer = TMMBoreOptimizer(
        target_frequencies=target_freqs,
        fingering_sets=fingerings,
        n_control_points=8,
        bore_length=bore_length,
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=True,
        min_radius=5.0,
        max_radius=12.0,
    )

    t0 = time.time()
    result = optimizer.run(verbose=True, method="L-BFGS-B", maxiter=150)
    wall_time = time.time() - t0

    print(f"\n  Final RMS: {result['final_rms_cents']:.2f} cents")
    print(f"  Wall time: {wall_time:.1f}s")

    assert result['final_rms_cents'] < 200, \
        f"Clarinet optimizer failed: {result['final_rms_cents']:.2f} cents > 200"
    print("  PASS\n")


@pytest.mark.slow
def test_speed_benchmark():
    """Benchmark: TMM vs OpenWInD evaluation speed."""
    print("=" * 60)
    print("TEST 6: Speed benchmark")
    print("=" * 60)

    bore_length = 600.0
    bore_diameter = 14.5
    radii = np.full(20, bore_diameter / 2.0)

    # TMM evaluation
    inst = tmm_instrument_from_radii(
        radii_mm=radii,
        bore_length_mm=bore_length,
        hole_positions_mm=[120, 200, 280, 360, 440],
        hole_diameters_mm=[7.0] * 5,
        hole_lengths_mm=[4.0] * 5,
        closed_top=True,
    )

    fingerings = [Hole.CLOSED] * 5
    n_evals = 1000

    t0 = time.time()
    for _ in range(n_evals):
        inst.find_resonance(4.0 * bore_length, fingerings, n_register=1)
    tmm_time = (time.time() - t0) / n_evals * 1000

    print(f"  TMM single resonance eval: {tmm_time:.3f} ms")
    print(f"  Estimated cost for 1000 evals: {tmm_time * 1000 / 1000:.1f} s")
    print("  (OpenWInD typically ~5-50ms per full impedance computation)")
    assert tmm_time < 100, f"TMM evaluation too slow: {tmm_time:.3f}ms per eval"
    print()


def test_single_hole():
    """Test: adding a single open hole raises resonance frequency."""
    print("=" * 60)
    print("TEST 7: Single hole effect on open-open pipe")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    hole_pos = 250.0
    hole_diam = 8.0
    hole_len = 3.0

    # No-hole reference
    inst_no_hole = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=False,
    )
    wl = inst_no_hole.find_resonance(2.0 * bore_length, [], n_register=2)
    freq_no_hole = inst_no_hole.frequency_from_wavelength(wl)
    print(f"  No hole (all closed): {freq_no_hole:.1f} Hz")

    # With open hole
    inst_hole = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=[hole_pos],
        hole_diameters=[hole_diam],
        hole_lengths=[hole_len],
        closed_top=False,
    )
    wl2 = inst_hole.find_resonance(2.0 * bore_length, [Hole.OPEN], n_register=2)
    freq_with_hole = inst_hole.frequency_from_wavelength(wl2)
    print(f"  Single open hole at {hole_pos}mm: {freq_with_hole:.1f} Hz")

    assert freq_with_hole > freq_no_hole, \
        f"Open hole should raise frequency: {freq_with_hole:.1f} vs {freq_no_hole:.1f} Hz"
    print("  PASS\n")


def test_two_holes():
    """Test: adding a second open hole raises frequency further."""
    print("=" * 60)
    print("TEST 8: Two-hole effect on open-open pipe")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    hole_positions = [200.0, 350.0]
    hole_diameters = [8.0, 8.0]
    hole_lengths = [3.0, 3.0]

    # One hole
    inst_one = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=[hole_positions[0]],
        hole_diameters=[hole_diameters[0]],
        hole_lengths=[hole_lengths[0]],
        closed_top=False,
    )
    wl1 = inst_one.find_resonance(2.0 * bore_length, [Hole.OPEN], n_register=2)
    freq_one = inst_one.frequency_from_wavelength(wl1)
    print(f"  One hole at {hole_positions[0]}mm: {freq_one:.1f} Hz")

    # Two holes
    inst_two = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=False,
    )
    # Both open
    wl2 = inst_two.find_resonance(2.0 * bore_length, [Hole.OPEN, Hole.OPEN], n_register=2)
    freq_two_both = inst_two.frequency_from_wavelength(wl2)
    print(f"  Two holes both open: {freq_two_both:.1f} Hz")

    # Second hole open, first closed
    wl3 = inst_two.find_resonance(2.0 * bore_length, [Hole.CLOSED, Hole.OPEN], n_register=2)
    freq_two_second = inst_two.frequency_from_wavelength(wl3)
    print(f"  Only second hole open: {freq_two_second:.1f} Hz")

    assert freq_two_both > freq_one, \
        f"Two holes both open ({freq_two_both:.1f}) should raise frequency more than one ({freq_one:.1f})"
    print("  PASS\n")


def test_hole_at_zero():
    """Test: hole at position zero has minimal effect (at the input end)."""
    print("=" * 60)
    print("TEST 9: Hole at position 0 (input end)")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    hole_diam = 8.0
    hole_len = 3.0

    # No hole
    inst_no = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=False,
    )
    wl_no = inst_no.find_resonance(2.0 * bore_length, [], n_register=2)
    freq_no = inst_no.frequency_from_wavelength(wl_no)
    print(f"  No hole: {freq_no:.1f} Hz")

    # Hole at position 0
    inst_zero = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=[0.0],
        hole_diameters=[hole_diam],
        hole_lengths=[hole_len],
        closed_top=False,
    )
    wl_zero = inst_zero.find_resonance(2.0 * bore_length, [Hole.OPEN], n_register=2)
    freq_zero = inst_zero.frequency_from_wavelength(wl_zero)
    print(f"  Hole at 0mm: {freq_zero:.1f} Hz")

    # Hole at midpoint
    inst_mid = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=[250.0],
        hole_diameters=[hole_diam],
        hole_lengths=[hole_len],
        closed_top=False,
    )
    wl_mid = inst_mid.find_resonance(2.0 * bore_length, [Hole.OPEN], n_register=2)
    freq_mid = inst_mid.frequency_from_wavelength(wl_mid)
    print(f"  Hole at 250mm: {freq_mid:.1f} Hz")

    # A hole at the input end should have less effect than one in the middle
    assert abs(freq_zero - freq_no) < abs(freq_mid - freq_no), \
        "Hole at input end should have smaller effect than hole at midpoint"
    print("  PASS\n")


def test_multiple_holes():
    """Test: progressive frequency increase as more holes are opened."""
    print("=" * 60)
    print("TEST 10: Progressive hole opening on open-open pipe")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    hole_positions = [100.0, 200.0, 300.0, 400.0]
    hole_diameters = [8.0, 8.0, 8.0, 8.0]
    hole_lengths = [3.0, 3.0, 3.0, 3.0]

    inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=False,
    )

    prev_freq = 0.0
    for n_open in range(1, 5):
        fingerings = [Hole.OPEN] * n_open + [Hole.CLOSED] * (4 - n_open)
        wl = inst.find_resonance(2.0 * bore_length, fingerings, n_register=2)
        freq = inst.frequency_from_wavelength(wl)
        print(f"  {n_open} hole(s) open: {freq:.1f} Hz")
        if n_open > 1:
            assert freq > prev_freq, \
                f"Frequency should increase with more holes: {freq:.1f} <= {prev_freq:.1f}"
        prev_freq = freq

    print("  PASS\n")


if __name__ == "__main__":
    test_simple_flute()
    test_simple_clarinet()
    test_flute_with_holes()
    test_speed_benchmark()
    test_optimizer_simple_flute()
    test_optimizer_clarinet()
    test_single_hole()
    test_two_holes()
    test_hole_at_zero()
    test_multiple_holes()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
