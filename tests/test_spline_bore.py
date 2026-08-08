import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.spline_bore import SplineBore, analytical_bore, spline_bore_from_optimization
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND, Hole

c = SPEED_OF_SOUND


def test_cylinder_equivalence():
    L = 600.0
    r = 7.25
    bore = SplineBore([0.0, L], [r, r])
    inst1 = bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    wl1 = inst1.find_resonance(4.0 * L, [], n_register=1)
    f1 = inst1.frequency_from_wavelength(wl1)
    radii = np.full(64, r)
    inst2 = tmm_instrument_from_radii(radii, L, [], [], [], outer_diameter_mm=22.0, closed_top=True)
    wl2 = inst2.find_resonance(4.0 * L, [], n_register=1)
    f2 = inst2.frequency_from_wavelength(wl2)
    cents = 1200.0 * abs(math.log2(f1 / f2))
    print(f"  Cylinder equivalence: {cents:.6f} cents")
    assert cents < 0.001, f"Exceeded 0.001 cents: {cents:.6f}"
    print("  PASS")


def test_cone_vs_cylinder():
    L = 600.0
    r_mouth = 7.25
    r_bell = 10.0
    cylinder_bore = SplineBore([0.0, L], [r_mouth, r_mouth])
    cone_bore = SplineBore([0.0, L], [r_mouth, r_bell])
    inst_cyl = cylinder_bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    inst_cone = cone_bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    f_cyl = inst_cyl.frequency_from_wavelength(inst_cyl.find_resonance(4.0 * L, [], n_register=2))
    f_cone = inst_cone.frequency_from_wavelength(inst_cone.find_resonance(4.0 * L, [], n_register=2))
    cents = 1200.0 * abs(math.log2(f_cone / f_cyl))
    print(f"  Cone vs cylinder (register 2): {cents:.4f} cents")
    assert cents > 1.0, f"Difference too small: {cents:.4f} cents"
    print("  PASS")


def test_parabolic_bore_resonates():
    L = 600.0
    bore = analytical_bore('parabolic', length=L, r_bell=10.0, r_mouth=7.25)
    inst = bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    f = inst.frequency_from_wavelength(inst.find_resonance(4.0 * L, [], n_register=1))
    target_f = c / (4.0 * L)
    error = abs(f - target_f) / target_f
    print(f"  Parabolic bore: {f:.2f} Hz (target: {target_f:.2f} Hz, error: {error*100:.1f}%)")
    assert error < 0.20, f"Frequency error too large: {error*100:.1f}%"
    assert f > 0 and math.isfinite(f)
    print("  PASS")


def test_bessel_horn():
    L = 600.0
    bore = analytical_bore('bessel', length=L, r_bell=10.0, r_mouth=7.25, flare=0.7)
    inst = bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    f = inst.frequency_from_wavelength(inst.find_resonance(4.0 * L, [], n_register=1))
    print(f"  Bessel horn: {f:.2f} Hz")
    assert f > 0 and math.isfinite(f)
    print("  PASS")


def test_exponential_bore():
    L = 600.0
    bore = analytical_bore('exponential', length=L, r_bell=10.0, r_mouth=7.25)
    inst = bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    f = inst.frequency_from_wavelength(inst.find_resonance(4.0 * L, [], n_register=1))
    print(f"  Exponential bore: {f:.2f} Hz")
    assert f > 0 and math.isfinite(f)
    print("  PASS")


def test_stepped_bore():
    L = 600.0
    positions = [0.0, 150.0, 300.0, 450.0, L]
    radii = [6.0, 6.0, 8.0, 8.0, 10.0]
    bore = SplineBore(positions, radii)
    inst = bore.to_tmm_instrument([], [], [], outer_diameter=22.0, closed_top=True)
    f = inst.frequency_from_wavelength(inst.find_resonance(4.0 * L, [], n_register=1))
    print(f"  Stepped bore: {f:.2f} Hz")
    assert f > 0 and math.isfinite(f)
    cylinder_f = c / (4.0 * L)
    cents_diff = 1200.0 * abs(math.log2(f / cylinder_f))
    assert cents_diff > 0.5, f"Stepped bore should differ from cylinder: {cents_diff:.2f} cents"
    print("  PASS")


def test_spline_with_holes():
    L = 600.0
    bore = analytical_bore('cone', length=L, r_bell=10.0, r_mouth=7.25)
    n_holes = 6
    hole_positions = [100.0, 180.0, 260.0, 340.0, 420.0, 500.0]
    hole_diameters = [7.0] * n_holes
    hole_lengths = [3.5] * n_holes
    fingerings = [
        [Hole.CLOSED] * n_holes,
        [Hole.CLOSED] * 5 + [Hole.OPEN],
        [Hole.CLOSED] * 4 + [Hole.OPEN] * 2,
        [Hole.CLOSED] * 3 + [Hole.OPEN] * 3,
        [Hole.CLOSED] * 2 + [Hole.OPEN] * 4,
        [Hole.CLOSED] + [Hole.OPEN] * 5,
        [Hole.OPEN] * n_holes,
    ]
    inst = bore.to_tmm_instrument(hole_positions, hole_diameters, hole_lengths, outer_diameter=22.0, closed_top=True)
    freqs = inst.compute_fingered_frequencies([4.0 * L] * len(fingerings), fingerings, n_register=1)
    for i, f in enumerate(freqs):
        print(f"    Fingering {i}: {f:.2f} Hz")
        assert f > 0 and math.isfinite(f)
    for i in range(len(freqs) - 1):
        assert freqs[i + 1] > freqs[i], f"Frequency dropped at step {i}: {freqs[i]:.2f} -> {freqs[i+1]:.2f}"
    cents = []
    for i in range(len(freqs)):
        cents.append(1200.0 * math.log2(freqs[i] / (c / (4.0 * L))))
    rms = math.sqrt(sum(cc * cc for cc in cents) / len(cents))
    print(f"    RMS cents from cylinder fundamental: {rms:.2f}")
    assert rms > 0, "RMS should be positive"
    print("  PASS")


def test_analytical_shapes_validation():
    L = 600.0
    r_bell = 10.0
    r_mouth = 7.25
    shapes = ['cylinder', 'cone', 'parabolic', 'bessel', 'exponential']
    for shape in shapes:
        bore = analytical_bore(shape, length=L, r_bell=r_bell, r_mouth=r_mouth)
        v = bore.validate()
        assert not v['has_negative_radius'], f"{shape} has negative radius"
        assert v['min_radius'] > 0, f"{shape} has zero radius"
        print(f"  {shape}: min_r={v['min_radius']:.3f}, cyl_dev={v['cylinder_deviation']:.4f}")
    print("  PASS")


def test_spline_bore_from_optimization():
    bore = spline_bore_from_optimization(bore_length=600.0, n_control=8)
    v = bore.validate()
    assert not v['has_negative_radius']
    assert v['min_radius'] > 0
    assert v['cylinder_deviation'] < 1e-6
    print(f"  Optimization bore: min_r={v['min_radius']:.3f}, dev={v['cylinder_deviation']:.6f}")
    print("  PASS")


def test_to_profile():
    bore = SplineBore([0.0, 300.0, 600.0], [7.25, 8.0, 10.0])
    n = 5
    profile = bore.to_profile(n=n)
    assert len(profile.pos) == n
    assert len(profile.low) == n
    expected_pos = np.linspace(0.0, 600.0, n)
    for i in range(n):
        assert math.isclose(profile.pos[i], expected_pos[i], rel_tol=1e-10)
        expected_d = 2.0 * bore.radius_at(profile.pos[i])
        assert math.isclose(profile.low[i], expected_d, rel_tol=1e-10)
        assert math.isclose(profile.high[i], expected_d, rel_tol=1e-10)
    print("  PASS")


def test_to_radii_array():
    bore = SplineBore([0.0, 300.0, 600.0], [7.25, 8.0, 10.0])
    n = 5
    radii = bore.to_radii_array(n=n)
    assert len(radii) == n
    xs = np.linspace(0.0, 600.0, n)
    for i in range(n):
        assert math.isclose(radii[i], bore.radius_at(xs[i]), rel_tol=1e-10)
    print("  PASS")


if __name__ == "__main__":
    tests = [
        test_cylinder_equivalence,
        test_cone_vs_cylinder,
        test_parabolic_bore_resonates,
        test_bessel_horn,
        test_exponential_bore,
        test_stepped_bore,
        test_spline_with_holes,
        test_analytical_shapes_validation,
        test_spline_bore_from_optimization,
        test_to_profile,
        test_to_radii_array,
    ]
    for test in tests:
        print(f"\n{test.__name__}:")
        test()
    print("\nALL TESTS PASSED")
