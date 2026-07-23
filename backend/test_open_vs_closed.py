"""Test: does open-open need reversed hole order?"""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Soprano sax open-open, bore=371mm, radius=6mm
bore_length = 371.0
bore_radii = np.full(8, 6.0)
target_fundamental = 466.2

# Check: which note does each hole position produce?
print("Open-open (soprano sax): single hole sweep")
print("="*60)
for note, target in [(1, 523.3), (2, 587.3), (3, 622.3), (4, 698.5), (5, 784.0)]:
    best_pos, best_err = 0, 1e10
    for pos in np.linspace(30, 341, 60):
        fing = ["open"] * (note) + ["closed"] * (7 - note)
        try:
            inst = tmm_instrument_from_radii(bore_radii, bore_length, [pos], [6.5], [3.0], 20.0, False, 0.5)
            wl = inst.find_resonance(c / target, fing, 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target))
            if err < best_err:
                best_err, best_pos = err, pos
        except: pass
    print(f"  Note {note} ({target:.1f} Hz): best pos={best_pos:.0f}mm, err={best_err:.1f}c")

print()
print("Closed-open (chalumeau): single hole sweep")
print("="*60)
bore_length2 = 331.0
bore_radii2 = np.full(8, 7.25)
for note, target in [(1, 293.7), (2, 329.6), (3, 349.2), (4, 392.0), (5, 440.0)]:
    best_pos, best_err = 0, 1e10
    for pos in np.linspace(30, 301, 60):
        fing = ["open"] * (note) + ["closed"] * (6 - note)
        try:
            inst = tmm_instrument_from_radii(bore_radii2, bore_length2, [pos], [7.0], [3.75], 22.0, True, 0.5)
            wl = inst.find_resonance(c / target, fing, 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target))
            if err < best_err:
                best_err, best_pos = err, pos
        except: pass
    print(f"  Note {note} ({target:.1f} Hz): best pos={best_pos:.0f}mm, err={best_err:.1f}c")

print()
print("CONCLUSION:")
print("  If open-open best positions go LOW->HIGH, hole order is same as closed-open")
print("  If open-open best positions go HIGH->LOW, hole order must be reversed")
