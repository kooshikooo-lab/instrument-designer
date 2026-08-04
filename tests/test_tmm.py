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
    # Convention (benchmark_all.py:291-293): for open-open pipes the fundamental
    # is the 2nd resonance (phase starts at 0.5 at each open end), so harmonic
    # n corresponds to n_register = n + 1.
    actual_freqs = []
    for n in range(1, 7):
        target_wl = 2.0 * bore_length / n  # initial guess
        fingerings = []
        wl = inst.find_resonance(target_wl, fingerings, n_register=n + 1)
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
    wl = inst.find_resonance(2.0 * bore_length, all_closed, n_register=2)
    freq_all_closed = inst.frequency_from_wavelength(wl)
    end_corr = end_flange_length_correction(22.0, bore_diameter)
    theo_f1 = v / (2.0 * (bore_length + end_corr))
    print(f"  All holes closed: {freq_all_closed:.1f} Hz (theoretical: {theo_f1:.1f} Hz)")
    err = abs(freq_all_closed - theo_f1) / theo_f1 * 100
    print(f"  Error: {err:.2f}%")

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


def test_numba_resonance_phase_matches_python():
    """Numba fast path must produce bit-identical phases to pure Python."""
    import random
    from backend.tmm_acoustics import _NUMBA_ENABLED
    from backend.tmm_numba import build_action_arrays, numba_resonance_phase

    if not _NUMBA_ENABLED:
        import pytest
        pytest.skip("numba not available")

    rng = random.Random(1234)
    max_diff = 0.0
    for _ in range(8):
        n_holes = rng.randint(3, 8)
        radii = np.linspace(3.0, 7.5, rng.randint(30, 60))
        hp = sorted(rng.sample(range(40, 290), n_holes))
        inst = tmm_instrument_from_radii(
            radii_mm=radii,
            bore_length_mm=300.0,
            hole_positions_mm=hp,
            hole_diameters_mm=[rng.uniform(5, 9) for _ in hp],
            hole_lengths_mm=[rng.uniform(3, 5) for _ in hp],
            cone_step=rng.choice([0.3, 0.5, 1.0]),
            closed_top=rng.choice([True, False]),
        )
        assert inst._action_arrays is not None, "numba arrays not built"
        types, p1, p2, p3, p4, p5 = inst._action_arrays
        for _ in range(6):
            fg = [rng.choice([Hole.OPEN, Hole.CLOSED]) for _ in range(n_holes)]
            mask = np.array([1 if f == Hole.OPEN else 0 for f in fg], dtype=np.int32)
            for wl in (250.0, 320.0, 400.0, 500.0, 620.0):
                py = inst.resonance_phase(wl, fg)
                nb = numba_resonance_phase(
                    types, p1, p2, p3, p4, p5, mask, wl, closed_top=inst.closed_top
                )
                max_diff = max(max_diff, abs(py - nb))
    assert max_diff == 0.0, f"numba phase mismatch: max diff {max_diff}"


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
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
