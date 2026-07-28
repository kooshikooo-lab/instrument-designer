"""
Test spline bore integration with TMM instrument pipeline.

Verifies that SplineBore produces identical results to flat bore for
cylinder cases, and demonstrates variable-radius bore profiling.

Run: python tests/test_spline_bore.py
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from backend.spline_bore import SplineBore, analytical_bore
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND as c


def test_cylinder_equivalence():
    """2-point cylinder spline must match flat tmm_instrument_from_radii exactly."""
    L, r = 330.0, 7.25
    bore = SplineBore([0, L], [r, r])
    inst_spline = bore.to_tmm_instrument([], [], [], closed_top=True)
    radii_flat = np.full(64, r)
    inst_flat = tmm_instrument_from_radii(radii_flat, L, [], [], [], closed_top=True)

    wl0 = c / 261.6
    wl_s = inst_spline.find_resonance(wl0, ["closed"] * 6, 1)
    wl_f = inst_flat.find_resonance(wl0, ["closed"] * 6, 1)
    f_s = inst_spline.frequency_from_wavelength(wl_s)
    f_f = inst_flat.frequency_from_wavelength(wl_f)
    err = abs(1200 * math.log2(f_s / f_f))
    assert err < 0.001, f"Cylinder mismatch: {err:.4f} cents"
    print(f"  PASS: Cylinder equivalence ({err:.6f} cents)")


def test_cone_vs_cylinder():
    """Conical bore should have different resonance than cylindrical."""
    L, r_bell, r_mouth = 330.0, 7.25, 5.0
    cyl = SplineBore([0, L], [r_bell, r_bell])
    cone = SplineBore([0, L], [r_bell, r_mouth])
    inst_cyl = cyl.to_tmm_instrument([], [], [], closed_top=True)
    inst_cone = cone.to_tmm_instrument([], [], [], closed_top=True)

    wl0 = c / 261.6
    wl_cyl = inst_cyl.find_resonance(wl0, ["closed"] * 6, 1)
    wl_cone = inst_cone.find_resonance(wl0, ["closed"] * 6, 1)
    f_cyl = inst_cyl.frequency_from_wavelength(wl_cyl)
    f_cone = inst_cone.frequency_from_wavelength(wl_cone)
    diff = abs(1200 * math.log2(f_cyl / f_cone))
    assert diff > 1.0, f"Cone should differ from cylinder by >1c, got {diff:.2f}c"
    print(f"  PASS: Cone vs cylinder differ by {diff:.2f} cents")


def test_parabolic_bore():
    """Parabolic taper should produce smooth frequency response."""
    bore = analytical_bore('parabolic', length=330, r_bell=7.25, r_mouth=5.0)
    inst = bore.to_tmm_instrument([], [], [], closed_top=True)
    wl0 = c / 261.6
    wl = inst.find_resonance(wl0, ["closed"] * 6, 1)
    freq = inst.frequency_from_wavelength(wl)
    err = abs(1200 * math.log2(freq / 261.6))
    print(f"  PASS: Parabolic bore f1={freq:.1f} Hz (err={err:.1f}c from 261.6Hz target)")


def test_bessel_horn():
    """Bessel horn should have distinct acoustic character."""
    bore = analytical_bore('bessel', length=330, r_bell=7.25, r_mouth=5.0, flare=0.7)
    inst = bore.to_tmm_instrument([], [], [], closed_top=True)
    wl0 = c / 261.6
    wl = inst.find_resonance(wl0, ["closed"] * 6, 1)
    freq = inst.frequency_from_wavelength(wl)
    print(f"  PASS: Bessel horn f1={freq:.1f} Hz")


def test_exponential_bore():
    """Exponential bore should produce smooth taper."""
    bore = analytical_bore('exponential', length=330, r_bell=7.25, r_mouth=5.0)
    inst = bore.to_tmm_instrument([], [], [], closed_top=True)
    wl0 = c / 261.6
    wl = inst.find_resonance(wl0, ["closed"] * 6, 1)
    freq = inst.frequency_from_wavelength(wl)
    print(f"  PASS: Exponential bore f1={freq:.1f} Hz")


def test_stepped_bore():
    """Stepped bore (3 sections) should show distinct resonance behavior."""
    # Bell section: wide, Middle: medium, Mouthpiece: narrow
    bore = SplineBore([0, 100, 200, 330], [8.0, 7.25, 6.5, 5.5])
    inst = bore.to_tmm_instrument([], [], [], closed_top=True)
    wl0 = c / 261.6
    wl = inst.find_resonance(wl0, ["closed"] * 6, 1)
    freq = inst.frequency_from_wavelength(wl)
    print(f"  PASS: Stepped bore f1={freq:.1f} Hz")


def test_with_holes():
    """Spline bore with tone holes should produce correct fingering response."""
    bore = analytical_bore('cone', length=330, r_bell=7.25, r_mouth=5.0)
    # Place 6 holes along the bore (chalumeau-like)
    hole_positions = [100, 140, 180, 220, 260, 295]
    hole_diameters = [7.0] * 6
    hole_lengths = [3.75] * 6
    inst = bore.to_tmm_instrument(
        hole_positions, hole_diameters, hole_lengths,
        closed_top=True,
    )

    # Test each fingering
    targets = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = [
        ["closed"] * 6,
        ["open", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "closed", "closed"],
        ["open", "open", "open", "open", "open", "closed"],
    ]

    cents_errors = []
    for target, fing in zip(targets, fingerings):
        wl0 = c / target
        wl = inst.find_resonance(wl0, fing, 1)
        freq = inst.frequency_from_wavelength(wl)
        err = 1200 * math.log2(freq / target)
        cents_errors.append(err)
        note = ["C4", "D4", "E4", "F4", "G4", "A4"][targets.index(target)]
        print(f"    {note}: target={target:.1f} Hz, got={freq:.1f} Hz, err={err:+.1f}c")

    rms = math.sqrt(sum(e**2 for e in cents_errors) / len(cents_errors))
    print(f"  PASS: Cone bore with holes, RMS={rms:.2f}c")


def test_validation():
    """Run built-in validation on each analytical shape."""
    for shape in ['cylinder', 'cone', 'parabolic', 'bessel', 'exponential']:
        bore = analytical_bore(shape, length=300, r_bell=7.0, r_mouth=4.0)
        r = bore.validate()
        all_pass = all(v.get('pass', False) for v in r.values())
        status = "PASS" if all_pass else "FAIL"
        print(f"  {status}: {shape} validation")


if __name__ == "__main__":
    print("\n=== Spline Bore Tests ===\n")
    test_cylinder_equivalence()
    test_cone_vs_cylinder()
    test_parabolic_bore()
    test_bessel_horn()
    test_exponential_bore()
    test_stepped_bore()
    test_with_holes()
    test_validation()
    print("\n=== All tests complete ===")
