"""Same fingering order test for soprano sax to confirm the convention bug."""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Soprano sax positions from sequential refined
positions = [58, 93, 105, 138, 164, 189]
bore_radii = np.full(8, 6.0)
L = 371
hd, hl, od = 5.0, 3.0, 15.0

inst = tmm_instrument_from_radii(bore_radii, L, positions, [hd]*6, [hl]*6, od, False, 0.5)

targets = [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0]

print("Soprano sax positions:", positions)
print(f"Bore length: {L}mm")
print()

# Convention A: open from index 0 (smallest position = closest to mouthpiece)
print("Convention A (current): opens from position 58mm (mouthpiece end)")
fingerings_a = [
    ["closed"] * 6,
    ["open", "closed", "closed", "closed", "closed", "closed"],
    ["open", "open", "closed", "closed", "closed", "closed"],
    ["open", "open", "open", "closed", "closed", "closed"],
    ["open", "open", "open", "open", "closed", "closed"],
    ["open", "open", "open", "open", "open", "closed"],
    ["open", "open", "open", "open", "open", "open"],
]
for fing, target in zip(fingerings_a, targets):
    try:
        wl = inst.find_resonance(c / target, fing, 2)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / target)
        open_pos = [positions[j] for j in range(6) if fing[j] == 'open']
        print(f"  target={target:.1f}  got={f:.1f}  err={err:+.1f}c  open at {open_pos}")
    except Exception as e:
        print(f"  target={target:.1f}  FAILED: {e}")

print()

# Convention B: open from last index (largest position = closest to bell)
print("Convention B (reversed): opens from position 189mm (bell end)")
fingerings_b = [
    ["closed"] * 6,
    ["closed", "closed", "closed", "closed", "closed", "open"],
    ["closed", "closed", "closed", "closed", "open", "open"],
    ["closed", "closed", "closed", "open", "open", "open"],
    ["closed", "closed", "open", "open", "open", "open"],
    ["closed", "open", "open", "open", "open", "open"],
    ["open", "open", "open", "open", "open", "open"],
]
for fing, target in zip(fingerings_b, targets):
    try:
        wl = inst.find_resonance(c / target, fing, 2)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / target)
        open_pos = [positions[j] for j in range(6) if fing[j] == 'open']
        print(f"  target={target:.1f}  got={f:.1f}  err={err:+.1f}c  open at {open_pos}")
    except Exception as e:
        print(f"  target={target:.1f}  FAILED: {e}")
