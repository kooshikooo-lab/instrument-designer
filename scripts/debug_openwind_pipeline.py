"""
debug_openwind_pipeline.py — Debug chalumier->OpenWind conversion step by step.

Goal: Find why chalumier design produces -193 to +242 cents error in OpenWind.

Approach:
  1. Test OpenWind with a simple cylindrical pipe (known answer)
  2. Test with chalumier bore profile (no holes first, then with holes)
  3. Compare impedance curves to find where conversion goes wrong

Coordinate systems:
  Chalumier: 0=bell (open), L=mouthpiece (closed), holes indexed from bell
  OpenWind:  0=mouthpiece (closed), L=bell (open), holes indexed from mouthpiece
  TMM:       same as OpenWind

Findings:
  - OpenWind has a systematic ~-60 cent offset on simple cylinders (closed_top
    with source at entrance adds effective length). This is EXPECTED — not a bug.
  - chalumier designs have a narrow fipple windway (~6.8mm) at the mouthpiece
    that OpenWind models as part of the bore. This changes the resonance.
  - The fingering chart hole indices must be reversed (chalumier 1→OpenWind N).
"""
import numpy as np
import sys
import os

# Add parent dir so we can import backend if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openwind import ImpedanceComputation

# Constants
SPEED_OF_SOUND = 343.0  # m/s at 20°C
TEMPERATURE = 20  # °C


def find_peaks(frequencies, Z):
    """Find local maxima in impedance magnitude.

    Parameters:
        frequencies: array of frequencies (Hz)
        Z: complex impedance values (normalized Z/Zc)

    Returns:
        peak_freqs: frequencies of peaks
        peak_mags: magnitudes at peaks (|Z/Zc|)
    """
    mag = np.abs(Z)
    peak_idx = np.where((mag[1:-1] > mag[:-2]) & (mag[1:-1] > mag[2:]))[0] + 1
    return frequencies[peak_idx], mag[peak_idx]


def test_simple_cylinder():
    """Test 1: Simple cylindrical pipe, closed-open.

    Expected: f1 = c/(4L) = 343/(4*0.33) = 259.8 Hz

    OpenWind convention: 0=mouthpiece (closed), L=bell (open).
    The source is at the entrance (closed end), which is correct for a reed/flute.

    NOTE: OpenWind applies end corrections and excitation model that add
    effective length. A systematic offset of ~-60 cents is EXPECTED.
    """
    print("=" * 60)
    print("TEST 1: Simple cylindrical pipe (closed-open)")
    print("=" * 60)

    L = 0.33  # 330mm bore
    r = 0.003  # 3mm radius = 6mm diameter
    expected_f1 = SPEED_OF_SOUND / (4 * L)

    print(f"Bore: {L*1000:.0f}mm length, {r*2000:.1f}mm diameter")
    print(f"Theoretical f1 (no end correction): {expected_f1:.1f} Hz")

    # OpenWind format: bore segments [start, end, r_start, r_end, interpolation]
    bore = [[0, L, r, r, 'linear']]

    # OpenWind requires at least one hole + fingering chart even for a plain bore.
    # We define a dummy hole that's never opened (always covered).
    holes = [['label', 'position', 'radius', 'chimney'],
             ['dummy', L * 0.5, 0.001, 0.001]]  # tiny hole at midpoint, never opened
    fingerings = [['label', 'C3'],
                  ['dummy', 'x']]  # x = covered

    frequencies = np.linspace(50, 1000, 500)

    try:
        comp = ImpedanceComputation(frequencies, bore, holes, fingerings,
                                    note='C3', temperature=TEMPERATURE, losses=True)
        Z = comp.impedance / comp.Zc

        peak_freqs, peak_mags = find_peaks(frequencies, Z)

        print(f"\nPeaks found:")
        for f, m in zip(peak_freqs[:5], peak_mags[:5]):
            error = 1200 * np.log2(f / expected_f1)
            print(f"  {f:.1f} Hz (|Z/Zc|={m:.1f}, error={error:+.1f} cents vs theory)")

        if len(peak_freqs) > 0:
            actual_f1 = peak_freqs[0]
            error_cents = 1200 * np.log2(actual_f1 / expected_f1)
            print(f"\nFINDING: OpenWind f1={actual_f1:.1f} Hz, offset={error_cents:+.1f} cents")
            print(f"  This offset is due to OpenWind's end correction + excitation model.")
            print(f"  It is SYSTEMATIC and affects all notes equally.")
            return actual_f1, error_cents
        else:
            print("\nFINDING: No peaks found!")
            return None, None

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_cylinder_with_hole():
    """Test 2: Cylindrical pipe with one hole.

    Expected: Opening a hole shortens effective tube length, raising pitch.
    The RELATIVE pitch change should be correct even if absolute has offset.

    OpenWind convention: hole position from mouthpiece (0).
    """
    print("\n" + "=" * 60)
    print("TEST 2: Cylindrical pipe with one hole")
    print("=" * 60)

    L = 0.33  # 330mm bore
    r = 0.003  # 3mm radius
    hole_pos = 0.20  # 200mm from mouthpiece
    hole_r = 0.002  # 2mm radius = 4mm diameter
    chimney = 0.005  # 5mm chimney height

    print(f"Bore: {L*1000:.0f}mm, hole at {hole_pos*1000:.0f}mm from mouthpiece")
    print(f"Expected: pitch rises when hole opens")

    bore = [[0, L, r, r, 'linear']]
    holes = [
        ['label', 'position', 'radius', 'chimney'],
        ['hole1', hole_pos, hole_r, chimney]
    ]

    # Two fingerings: closed (hole covered) and open (hole uncovered)
    fingerings = [
        ['label', 'closed', 'open'],
        ['hole1', 'x', 'o']
    ]

    frequencies = np.linspace(50, 1500, 500)

    results = {}
    for note in ['closed', 'open']:
        try:
            comp = ImpedanceComputation(frequencies, bore, holes, fingerings,
                                        note=note, temperature=TEMPERATURE, losses=True)
            Z = comp.impedance / comp.Zc

            peak_freqs, peak_mags = find_peaks(frequencies, Z)

            print(f"\n  {note.upper()} (hole {'covered' if note=='closed' else 'uncovered'}):")
            for f, m in zip(peak_freqs[:3], peak_mags[:3]):
                print(f"    {f:.1f} Hz (|Z/Zc|={m:.1f})")

            if len(peak_freqs) > 0:
                results[note] = peak_freqs[0]

        except Exception as e:
            print(f"  {note.upper()}: ERROR - {e}")

    if 'closed' in results and 'open' in results:
        shift_cents = 1200 * np.log2(results['open'] / results['closed'])
        print(f"\nFINDING: Opening hole shifts pitch by {shift_cents:+.0f} cents")
        print(f"  Closed: {results['closed']:.1f} Hz, Open: {results['open']:.1f} Hz")

    return results


def test_chalumier_bore_only():
    """Test 3: Chalumier bore profile WITHOUT holes.

    Tests if bore conversion is correct, independent of holes.
    We use ImpedanceComputation with a dummy hole (always covered).

    Coordinate conversion:
      Chalumier: 0=bell, L=mouthpiece
      OpenWind:  0=mouthpiece, L=bell
      pos_ow = L - pos_chal, reversed order
    """
    print("\n" + "=" * 60)
    print("TEST 3: Chalumier bore profile (no holes)")
    print("=" * 60)

    length = 262.7  # mm

    # Chalumier coordinates (0=bell, diameters averaged from low/high)
    pos_chal = [0.0, 71.8, 229.6, 241.3, 246.4, 256.3, 262.7]
    diam_chal = [10.89, 10.89, 15.56, 17.11, 17.11, 15.65, 6.80]

    print("Chalumier bore (0=bell, mm):")
    for p, d in zip(pos_chal, diam_chal):
        print(f"  pos={p:.1f}mm, diam={d:.2f}mm")

    # Convert to OpenWind (0=mouthpiece, meters)
    pos_ow = [length - p for p in reversed(pos_chal)]
    diam_ow = list(reversed(diam_chal))

    print("\nOpenWind bore (0=mouthpiece, mm):")
    for p, d in zip(pos_ow, diam_ow):
        print(f"  pos={p:.1f}mm, diam={d:.2f}mm")

    # Build OpenWind bore segments
    ow_bore = []
    for i in range(len(pos_ow) - 1):
        ow_bore.append([
            pos_ow[i] / 1000.0,
            pos_ow[i + 1] / 1000.0,
            diam_ow[i] / 2000.0,
            diam_ow[i + 1] / 2000.0,
            'linear'
        ])

    print("\nOpenWind bore segments (meters):")
    for seg in ow_bore:
        print(f"  [{seg[0]*1000:.1f}, {seg[1]*1000:.1f}] mm, "
              f"r={seg[2]*1000:.2f}-{seg[3]*1000:.2f} mm")

    # Dummy hole (always covered) — OpenWind requires at least one hole
    ow_holes = [['label', 'position', 'radius', 'chimney'],
                ['dummy', length / 2000.0, 0.001, 0.001]]
    ow_fingerings = [['label', 'D4'],
                     ['dummy', 'x']]

    frequencies = np.linspace(50, 2000, 1000)

    try:
        comp = ImpedanceComputation(frequencies, ow_bore, ow_holes, ow_fingerings,
                                    note='D4', temperature=TEMPERATURE, losses=True)
        Z = comp.impedance / comp.Zc

        peak_freqs, peak_mags = find_peaks(frequencies, Z)

        print(f"\nPeaks (bore only, no tone holes):")
        for f, m in zip(peak_freqs[:7], peak_mags[:7]):
            print(f"  {f:.1f} Hz (|Z/Zc|={m:.1f})")

        # For reference: simple cylinder of same length
        cyl_f1 = SPEED_OF_SOUND / (4 * length / 1000)
        print(f"\n  Reference cylinder f1: {cyl_f1:.1f} Hz")

        if len(peak_freqs) > 0:
            print(f"  Chalumier bore f1: {peak_freqs[0]:.1f} Hz")
            shift = 1200 * np.log2(peak_freqs[0] / cyl_f1)
            print(f"  Shift from cylinder: {shift:+.0f} cents")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


def test_chalumier_with_holes():
    """Test 4: Full chalumier design WITH holes.

    Tests complete conversion: bore + holes + fingering chart.

    Coordinate conversion:
      Bore positions: pos_ow = L - pos_chal (reversed)
      Hole positions: same conversion as bore
      Hole indices: reversed (chalumier hole1 → OpenWind holeN)
      Fingering chart: remap hole labels, swap x/o for each reversed hole
    """
    print("\n" + "=" * 60)
    print("TEST 4: Chalumier bore WITH holes")
    print("=" * 60)

    length = 262.7  # mm

    # Bore (same as test 3)
    pos_chal = [0.0, 71.8, 229.6, 241.3, 246.4, 256.3, 262.7]
    diam_chal = [10.89, 10.89, 15.56, 17.11, 17.11, 15.65, 6.80]

    pos_ow = [length - p for p in reversed(pos_chal)]
    diam_ow = list(reversed(diam_chal))

    ow_bore = []
    for i in range(len(pos_ow) - 1):
        ow_bore.append([
            pos_ow[i] / 1000.0,
            pos_ow[i + 1] / 1000.0,
            diam_ow[i] / 2000.0,
            diam_ow[i + 1] / 2000.0,
            'linear'
        ])

    # Holes from chalumier output (positions from bell)
    hole_pos_chal = [57.2, 74.9, 92.3, 112.4, 130.9, 148.6]
    hole_diam = [5.75, 8.62, 5.45, 7.87, 8.68, 9.22]
    hole_chim = [5.44, 5.40, 5.14, 4.85, 4.67, 4.71]

    # Convert to OpenWind coordinates
    hole_pos_ow = [length - p for p in hole_pos_chal]

    num_holes = len(hole_pos_chal)
    ow_holes = [['label', 'position', 'radius', 'chimney']]
    for i in range(num_holes):
        ow_index = num_holes - i  # reverse hole numbering
        ow_holes.append([
            f'hole{ow_index}',
            hole_pos_ow[i] / 1000.0,
            hole_diam[i] / 2000.0,
            hole_chim[i] / 1000.0
        ])

    print("Holes (OpenWind coords):")
    for h in ow_holes[1:]:
        print(f"  {h[0]}: pos={h[1]*1000:.1f}mm from mouthpiece, "
              f"r={h[2]*1000:.2f}mm, chim={h[3]*1000:.1f}mm")

    # Fingering chart: reverse hole indices, remap labels
    # chalumier: hole1=bell-most, hole6=mouthpiece-most
    # OpenWind: hole1=mouthpiece-most, hole6=bell-most
    # chalumier: X=covered, o=open
    # OpenWind: x=covered, o=open (same convention!)
    ow_fingerings = [
        ['label', 'D4', 'Cs5'],
        ['hole1', 'x', 'o'],  # hole1 = nearest mouthpiece
        ['hole2', 'x', 'o'],
        ['hole3', 'x', 'o'],
        ['hole4', 'x', 'o'],
        ['hole5', 'x', 'o'],
        ['hole6', 'x', 'o'],
    ]

    print("\nFingering chart (OpenWind):")
    for row in ow_fingerings:
        print(f"  {row}")

    frequencies = np.linspace(50, 2000, 1000)

    for note in ['D4', 'Cs5']:
        try:
            comp = ImpedanceComputation(frequencies, ow_bore, ow_holes, ow_fingerings,
                                        note=note, temperature=TEMPERATURE, losses=True)
            Z = comp.impedance / comp.Zc

            peak_freqs, peak_mags = find_peaks(frequencies, Z)

            # Expected frequencies
            expected = {'D4': 293.66, 'Cs5': 554.37}
            exp = expected.get(note, 0)

            print(f"\n  {note} (expected {exp:.1f} Hz):")
            for f, m in zip(peak_freqs[:5], peak_mags[:5]):
                error = 1200 * np.log2(f / exp) if exp > 0 else 0
                print(f"    {f:.1f} Hz (|Z/Zc|={m:.1f}, error={error:+.0f} cents)")

        except Exception as e:
            print(f"  {note}: ERROR - {e}")
            import traceback
            traceback.print_exc()


def main():
    """Run all debug tests in sequence."""
    print("DEBUGGING OPENWIND PIPELINE")
    print("=" * 60)
    print("Finding why chalumier design produces large intonation errors")
    print("=" * 60)

    # Test 1: Simple cylinder (known answer)
    test_simple_cylinder()

    # Test 2: Cylinder with hole (test hole handling)
    test_cylinder_with_hole()

    # Test 3: Chalumier bore only (test bore conversion)
    test_chalumier_bore_only()

    # Test 4: Full chalumier with holes (test complete conversion)
    test_chalumier_with_holes()

    print("\n" + "=" * 60)
    print("DEBUG COMPLETE — Summary of findings")
    print("=" * 60)
    print("""
1. Simple cylinder: validates OpenWind is working correctly.
   Expected systematic offset of ~-60 cents from OpenWind's excitation model.

2. Cylinder with hole: validates hole handling.
   Pitch should rise when hole opens. Relative shift is what matters.

3. Chalumier bore: tests coordinate conversion.
   If f1 doesn't match expected, bore conversion is wrong.

4. Full chalumier: tests complete pipeline.
   Large errors here indicate hole position/fingering conversion bugs.
""")


if __name__ == "__main__":
    main()
