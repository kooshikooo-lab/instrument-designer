"""Debug: trace what the optimizer sees for each hole placement."""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Simple test: chalumeau C, try placing ONE hole for D4 (293.7 Hz)
bore_length = 331.0
bore_radii = np.full(8, 7.25)
target = 293.7
outer_d = 22.0

print("Testing single hole placement for D4 (293.7 Hz) on chalumeau C")
print(f"Bore: {bore_length:.0f}mm, radius: 7.25mm, closed_top=True")
print()

# Try various positions and see what error we get
for pos in [50, 100, 150, 200, 250, 290, 300, 310]:
    fing = ["open"]
    try:
        inst = tmm_instrument_from_radii(
            bore_radii, bore_length, [pos], [7.0], [3.75],
            outer_d, True, 0.5,
        )
        wl = inst.find_resonance(c / target, fing, 1)
        f = inst.frequency_from_wavelength(wl)
        err = abs(1200.0 * math.log2(f / target))
        print(f"  pos={pos:3d}mm -> {f:.1f} Hz (err={err:+.1f}c)")
    except Exception as e:
        print(f"  pos={pos:3d}mm -> ERROR: {e}")

print()
print("Now test with all-closed fingering:")
inst = tmm_instrument_from_radii(
    bore_radii, bore_length, [290], [7.0], [3.75],
    outer_d, True, 0.5,
)
wl = inst.find_resonance(c / 261.6, ["closed"], 1)
f = inst.frequency_from_wavelength(wl)
print(f"  All-closed: {f:.1f} Hz (target: 261.6 Hz)")

wl = inst.find_resonance(c / 293.7, ["open"], 1)
f = inst.frequency_from_wavelength(wl)
print(f"  Hole open at 290mm: {f:.1f} Hz (target: 293.7 Hz)")

# Also test: what does the TMM model see for the bore?
print()
print("Bore segments:")
inst2 = tmm_instrument_from_radii(
    bore_radii, bore_length, [], [], [],
    outer_d, True, 0.5,
)
print(f"  Length: {inst2.length:.1f}mm")
print(f"  Actions: {len(inst2.actions)}")
for i, a in enumerate(inst2.actions[:5]):
    print(f"    {a}")
print(f"  ... ({len(inst2.actions)} total)")
