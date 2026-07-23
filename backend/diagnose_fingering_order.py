"""Verify fingering convention: trace exactly what fingering index maps to which hole position."""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Xaphoon: sequential places holes at [101, 169, 457, 472, 487, 502]
# The fingering opens from index 0. Which physical hole is that?

bore_radii = np.full(8, 7.0)
L = 662
hd, hl, od = 6.5, 3.0, 20.0

positions = [101, 169, 457, 472, 487, 502]
hd_list = [hd] * 6
hl_list = [hl] * 6

inst = tmm_instrument_from_radii(bore_radii, L, positions, hd_list, hl_list, od, False, 0.5)

print("Hole positions (sorted by position):", positions)
print(f"Bore length: {L}mm")
print()

# Test each fingering pattern
targets = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9]
fingerings = [
    ["closed"] * 6,                              # C4 (261.6)
    ["open", "closed", "closed", "closed", "closed", "closed"],  # D4 (293.7)
    ["open", "open", "closed", "closed", "closed", "closed"],    # E4 (329.6)
    ["open", "open", "open", "closed", "closed", "closed"],      # F4 (349.2)
    ["open", "open", "open", "open", "closed", "closed"],        # G4 (392.0)
    ["open", "open", "open", "open", "open", "closed"],          # A4 (440.0)
    ["open", "open", "open", "open", "open", "open"],            # B4 (493.9)
]

print("Convention A (current): opens holes at positions 101, 169, 457, ...")
print("  (index 0 = position 101mm = closest to mouthpiece)")
for i, (fing, target) in enumerate(zip(fingerings, targets)):
    try:
        wl = inst.find_resonance(c / target, fing, 2)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / target)
        open_pos = [positions[j] for j in range(6) if fing[j] == 'open']
        print(f"  {fing}: target={target:.1f}Hz, got={f:.1f}Hz, err={err:+.1f}c, open at {open_pos}")
    except Exception as e:
        print(f"  {fing}: FAILED: {e}")

print()
print("Convention B (reversed): opens holes at positions 502, 487, 472, ...")
print("  (index 0 = position 502mm = closest to bell)")
fingerings_reversed = [
    ["closed"] * 6,
    ["closed", "closed", "closed", "closed", "closed", "open"],  # open hole at 502mm
    ["closed", "closed", "closed", "closed", "open", "open"],    # open holes at 487, 502
    ["closed", "closed", "closed", "open", "open", "open"],      # open holes at 472, 487, 502
    ["closed", "closed", "open", "open", "open", "open"],        # open holes at 457, 472, 487, 502
    ["closed", "open", "open", "open", "open", "open"],          # open holes at 169, 457, 472, 487, 502
    ["open", "open", "open", "open", "open", "open"],            # open all
]
for i, (fing, target) in enumerate(zip(fingerings_reversed, targets)):
    try:
        wl = inst.find_resonance(c / target, fing, 2)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / target)
        open_pos = [positions[j] for j in range(6) if fing[j] == 'open']
        print(f"  {fing}: target={target:.1f}Hz, got={f:.1f}Hz, err={err:+.1f}c, open at {open_pos}")
    except Exception as e:
        print(f"  {fing}: FAILED: {e}")
