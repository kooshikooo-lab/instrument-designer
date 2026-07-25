"""
Simple recorder benchmark — open-open pipe, 6 finger holes.
No fingering reversal, no coordinate conversion.
Just pass chalumier-style positions and fingerings straight through to TMM.
"""

import sys, os, time, math
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND  # 346100 mm/s

# Recorder in C, ~330mm, open-open pipe
# Chalumier coordinates: position 0 = bell/foot, position L = mouthpiece
# Fingerings: X=closed, O=index 0 opens first going up in pitch
BORE_LENGTH = 330.0
BORE_RADIUS = 7.8  # ~15.6mm diameter
OUTER_DIAMETER = 24.0

# Hole positions from foot (chalumier convention, same as benchmark)
# These are rough positions for a recorder in C
HOLE_POSITIONS = [50.0, 90.0, 130.0, 170.0, 210.0, 250.0]
HOLE_DIAMETERS = [8.0] * 6
HOLE_LENGTHS = [4.0] * 6

# Target notes (fundamental register, open-open pipe)
# f = c / (2L_eff) for open-open
TARGETS = [523.3, 587.3, 659.3, 698.5, 784.0, 880.0]  # C5-D6
NAMES = ["C5", "D5", "E5", "F5", "G5", "A5"]

# Fingering: all closed = lowest note, open holes from foot end going up
# Chalumier convention: index 0 = hole nearest foot (position 50)
FINGERINGS = [
    ["X", "X", "X", "X", "X", "X"],  # C5: all closed
    ["O", "X", "X", "X", "X", "X"],  # D5: hole 0 open
    ["O", "O", "X", "X", "X", "X"],  # E5: holes 0,1 open
    ["O", "O", "O", "X", "X", "X"],  # F5: holes 0,1,2 open
    ["O", "O", "O", "O", "X", "X"],  # G5: holes 0-3 open
    ["O", "O", "O", "O", "O", "X"],  # A5: holes 0-4 open
]


def make_instrument(radii_mm):
    """Build TMM instrument directly from chalumier-style parameters."""
    return tmm_instrument_from_radii(
        radii_mm, BORE_LENGTH,
        HOLE_POSITIONS, HOLE_DIAMETERS, HOLE_LENGTHS,
        OUTER_DIAMETER, closed_top=False, cone_step=0.5,
    )


def evaluate(radii_mm, label=""):
    """Evaluate bore profile and print results."""
    inst = make_instrument(radii_mm)
    target_wls = [c / f for f in TARGETS]

    print(f"\n  {label}")
    print(f"  {'Note':<8} {'Target':>10} {'Actual':>10} {'Cents':>8}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*8}")

    cents_errors = []
    for name, target, twl, fing in zip(NAMES, TARGETS, target_wls, FINGERINGS):
        try:
            wl = inst.find_resonance(twl, fing, 1)
            actual = inst.frequency_from_wavelength(wl)
            cents = 1200.0 * math.log2(actual / target)
        except Exception as e:
            actual = 0.0
            cents = 1e10
        cents_errors.append(cents)
        print(f"  {name:<8} {target:>10.1f} {actual:>10.1f} {cents:>+8.1f}")

    arr = np.array(cents_errors)
    offset = np.median(arr)
    corrected = arr - offset
    rms = float(np.sqrt(np.mean(corrected**2)))
    peak = float(np.max(np.abs(corrected)))
    print(f"\n  Median offset: {offset:+.1f} cents")
    print(f"  RMS intonation: {rms:.2f} cents")
    print(f"  Peak error: {peak:.2f} cents")
    return rms, peak


# ======================================================================
# Test 1: Cylindrical bore (baseline)
# ======================================================================
print("=" * 60)
print("TEST 1: Cylindrical bore baseline")
print("=" * 60)
radii_cyl = np.full(8, BORE_RADIUS)
evaluate(radii_cyl, "Cylindrical (r=%.1fmm)" % BORE_RADIUS)


# ======================================================================
# Test 2: Verify fingering actually changes pitch
# ======================================================================
print("\n" + "=" * 60)
print("TEST 2: Single-hole sweep — does opening a hole change pitch?")
print("=" * 60)

for hole_idx in range(6):
    pos = HOLE_POSITIONS[hole_idx]
    fing = ["X"] * 6
    fing[hole_idx] = "O"
    try:
        inst = make_instrument(radii_cyl)
        wl = inst.find_resonance(c / TARGETS[0], fing, 1)
        f = inst.frequency_from_wavelength(wl)
        cents = 1200 * math.log2(f / TARGETS[0])
        print(f"  Open hole {hole_idx} (pos={pos:.0f}mm): {f:.1f} Hz ({cents:+.1f}c from C5)")
    except Exception as e:
        print(f"  Open hole {hole_idx} (pos={pos:.0f}mm): FAILED ({e})")


# ======================================================================
# Test 3: Find optimal bore length for C5 (all closed)
# ======================================================================
print("\n" + "=" * 60)
print("TEST 3: What bore length gives C5 (523.3 Hz) with all closed?")
print("=" * 60)

for bl in [280, 300, 320, 330, 340, 360, 380]:
    inst = tmm_instrument_from_radii(
        np.full(8, BORE_RADIUS), bl,
        HOLE_POSITIONS, HOLE_DIAMETERS, HOLE_LENGTHS,
        OUTER_DIAMETER, closed_top=False, cone_step=0.5,
    )
    try:
        wl = inst.find_resonance(c / 523.3, ["X"]*6, 1)
        f = inst.frequency_from_wavelength(wl)
        cents = 1200 * math.log2(f / 523.3)
        print(f"  L={bl}mm: {f:.1f} Hz ({cents:+.1f}c)")
    except:
        print(f"  L={bl}mm: FAILED")
