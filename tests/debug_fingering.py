"""Minimal test: place ONE hole for D4 (293.7 Hz) on chalumeau C, check all positions."""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
bore_length = 331.0
bore_radii = np.full(8, 7.25)
target = 293.7

# What does the sequential optimizer ACTUALLY do?
# It places the first hole (for D4=293.7) with fingering=["open"]
# Let's sweep all positions and find the best

print("Single hole sweep for D4 (293.7 Hz), fingering=['open']")
print("="*50)
best_pos, best_err = 0, 1e10
for pos in np.linspace(30, 301, 60):
    fing = ["open"]
    try:
        inst = tmm_instrument_from_radii(
            bore_radii, bore_length, [pos], [7.0], [3.75],
            22.0, True, 0.5,
        )
        wl = inst.find_resonance(c / target, fing, 1)
        f = inst.frequency_from_wavelength(wl)
        err = abs(1200.0 * math.log2(f / target))
        if err < best_err:
            best_err, best_pos = err, pos
    except:
        pass

print(f"Best: pos={best_pos:.1f}mm, err={best_err:.1f}c")

# Now check what the SECOND hole placement does
# After placing hole 0 at best_pos, place hole 1 for E4 (329.6)
# Fingering should be ["open", "open"] (both holes open)
target2 = 329.6
print(f"\nTwo holes: hole0={best_pos:.0f}mm, searching for hole1 (E4=329.6)")
print("Fingering=['open','open'] (both holes open)")
print("="*50)
best_pos2, best_err2 = 0, 1e10
for pos2 in np.linspace(best_pos + 15, bore_length - 30, 60):
    pl = [best_pos, pos2]
    fing = ["open", "open"]  # Both holes open for E4
    try:
        inst = tmm_instrument_from_radii(
            bore_radii, bore_length, pl, [7.0, 7.0], [3.75, 3.75],
            22.0, True, 0.5,
        )
        wl = inst.find_resonance(c / target2, fing, 1)
        f = inst.frequency_from_wavelength(wl)
        err = abs(1200.0 * math.log2(f / target2))
        if err < best_err2:
            best_err2, best_pos2 = err, pos2
    except:
        pass

print(f"Best: pos={best_pos2:.1f}mm, err={best_err2:.1f}c")

# Now evaluate the full set
print("\nFull evaluation with both holes:")
print("="*50)
hp = sorted([best_pos, best_pos2])
inst = tmm_instrument_from_radii(
    bore_radii, bore_length, hp, [7.0, 7.0], [3.75, 3.75],
    22.0, True, 0.5,
)
targets = [261.6, 293.7, 329.6]
# Fingering for all-closed: ["closed", "closed"]
# Fingering for D4 (hole0 open): need to figure out which sorted index is hole0
# Fingering for E4 (hole0+hole1 open): ["open", "open"]
fingerings = [
    ["closed", "closed"],  # C4: all closed
    None,  # D4: one hole open
    ["open", "open"],  # E4: both open
]

# D4: which hole produces 293.7? Open only the one that gives closest to 293.7
for try_open in [0, 1]:
    fing = ["closed", "closed"]
    fing[try_open] = "open"
    wl = inst.find_resonance(c / 293.7, fing, 1)
    f = inst.frequency_from_wavelength(wl)
    err = 1200*math.log2(f / 293.7)
    print(f"  D4: open hole {try_open} (pos={hp[try_open]:.0f}mm) -> {f:.1f} Hz ({err:+.1f}c)")

# What about opening only the HIGHER position hole for D4?
# In real clarinet, the note above all-closed opens the first hole from the bottom
# The "first hole" is the one nearest the bell (lowest position)

# Let's also check: what fingering does the sequential algorithm use?
# During placement of hole 0: fing = ["open"] (correct)
# During placement of hole 1: fing = ["open", "open"] (both open)
# But D4 should only have ONE hole open!

print("\n--- KEY INSIGHT ---")
print("The sequential algorithm places hole 0 for D4 with fing=['open']")
print("Then places hole 1 for E4 with fing=['open','open']")
print("But the FINAL fingering for D4 should be: only hole0 open, hole1 closed!")
print("The sequential method assumes: when placing hole k, all holes 0..k are open")
print("This is correct for the PLACEMENT step (finding where to put hole k)")
print("But the final evaluation must use the CORRECT fingering for each note.")
