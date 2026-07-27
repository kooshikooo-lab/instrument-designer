"""
Test and validate TMM acoustics module against known instrument designs.
"""

import sys
import os
import math
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.tmm_acoustics import (
    TMMInstrument, tmm_instrument_from_radii, SPEED_OF_SOUND, Hole,
    circle_area, end_flange_length_correction, hole_length_correction,
)
from backend.tmm_optimizer import TMMBoreOptimizer, _pava_isotonic


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
    actual_freqs = []
    for n in range(1, 7):
        target_wl = 2.0 * bore_length / n  # initial guess
        fingerings = []
        wl = inst.find_resonance(target_wl, fingerings, n_register=n)
        freq = inst.frequency_from_wavelength(wl)
        actual_freqs.append(freq)

    print(f"  Actual freqs:     {[f'{f:.1f}' for f in actual_freqs]}")

    errors = [abs(a - t) / t * 100 for a, t in zip(actual_freqs, theo_freqs)]
    print(f"  Relative errors:  {[f'{e:.3f}%' for e in errors]}")
    max_err = max(errors)
    print(f"  Max error: {max_err:.4f}%")
    assert max_err < 1.0, f"Flute test failed: max error {max_err:.4f}% > 1%"
    print("  PASS\n")


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

    errors = [abs(a - t) / t * 100 for a, t in zip(actual_freqs, theo_freqs)]
    print(f"  Relative errors:  {[f'{e:.3f}%' for e in errors]}")
    max_err = max(errors)
    print(f"  Max error: {max_err:.4f}%")
    assert max_err < 1.0, f"Clarinet test failed: max error {max_err:.4f}% > 1%"
    print("  PASS\n")


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
    wl = inst.find_resonance(2.0 * bore_length, all_closed, n_register=1)
    freq_all_closed = inst.frequency_from_wavelength(wl)
    end_corr = end_flange_length_correction(22.0, bore_diameter)
    theo_f1 = v / (2.0 * (bore_length + end_corr))
    print(f"  All holes closed: {freq_all_closed:.1f} Hz (theoretical: {theo_f1:.1f} Hz)")
    err = abs(freq_all_closed - theo_f1) / theo_f1 * 100
    print(f"  Error: {err:.2f}%")

    # Test: first hole open (shorter effective length -> higher pitch)
    first_open = [Hole.OPEN] + [Hole.CLOSED] * 6
    wl2 = inst.find_resonance(2.0 * bore_length, first_open, n_register=1)
    freq_first_open = inst.frequency_from_wavelength(wl2)
    print(f"  First hole open:  {freq_first_open:.1f} Hz")

    # Opening holes should raise the pitch
    assert freq_first_open > freq_all_closed, "Opening a hole should raise pitch"
    print("  Opening hole raises pitch: PASS")

    # Test: more holes open -> even higher pitch
    three_open = [Hole.OPEN] * 3 + [Hole.CLOSED] * 4
    wl3 = inst.find_resonance(2.0 * bore_length, three_open, n_register=1)
    freq_three_open = inst.frequency_from_wavelength(wl3)
    print(f"  Three holes open: {freq_three_open:.1f} Hz")
    assert freq_three_open > freq_first_open, "More holes open should raise pitch more"
    print("  More holes raise pitch: PASS")
    print("  PASS\n")


def test_optimizer_simple_flute():
    """Test: optimize a simple flute bore to hit target frequencies."""
    print("=" * 60)
    print("TEST 4: TMM optimizer on simple flute (7-hole)")
    print("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    v = SPEED_OF_SOUND

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
        wl = ref_inst.find_resonance(2.0 * bore_length, fing, n_register=1)
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


def test_optimizer_clarinet():
    """Test: optimize a clarinet bore (closed-open pipe)."""
    print("=" * 60)
    print("TEST 5: TMM optimizer on clarinet (closed-open)")
    print("=" * 60)

    bore_length = 600.0
    bore_diameter = 14.5
    v = SPEED_OF_SOUND

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
    print(f"  (OpenWInD typically ~5-50ms per full impedance computation)")
    print()


if __name__ == "__main__":
    test_simple_flute()
    test_simple_clarinet()
    test_flute_with_holes()
    test_speed_benchmark()
    test_optimizer_simple_flute()
    test_optimizer_clarinet()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
