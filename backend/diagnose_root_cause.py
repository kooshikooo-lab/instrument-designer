"""
Root cause analysis: For an open-open tube, opening a hole should SHORTEN the effective tube.
Opening a hole near the mouthpiece shortens from the top = less effect (short tube segment).
Opening a hole near the bell shortens from the bottom = more effect (removes most of tube).

This test: uniform bore xaphoon, find what happens with single holes at various positions.
Expected: hole near bell raises pitch more, hole near mouthpiece raises pitch less.
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Xaphoon: L=662mm, r=7mm
bore_radii = np.full(8, 7.0)
L = 662
hd, hl, od = 6.5, 3.0, 20.0

# First: confirm the baseline
inst = tmm_instrument_from_radii(bore_radii, L, [], [], [], od, False, 0.5)
wl_all = inst.find_resonance(c / 261.6, ["closed"], 2)
f_all = inst.frequency_from_wavelength(wl_all)
print(f"All-closed: {f_all:.1f}Hz (target 261.6Hz, err={1200*math.log2(f_all/261.6):+.1f}c)")
print()

# Now test single holes at different positions
# For open-open, the fingering for "single hole open" is just ["open"] for that hole
print("Single hole effect (one hole at position, ['open'] fingering):")
print(f"{'pos':>6s}  {'freq':>8s}  {'delta':>8s}  {'note'}")
print("-" * 50)

# Note names for reference
note_names = ["C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4", "C5"]
note_freqs = [261.6, 277.2, 293.7, 311.1, 329.6, 349.2, 369.9, 392.0, 415.3, 440.0, 466.2, 493.9, 523.3]

for pos in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650]:
    try:
        inst2 = tmm_instrument_from_radii(bore_radii, L, [pos], [hd], [hl], od, False, 0.5)
        wl = inst2.find_resonance(c / 400.0, ["open"], 2)
        f = inst2.frequency_from_wavelength(wl)
        delta = f - f_all
        # Find closest note
        closest = min(note_freqs, key=lambda nf: abs(nf - f))
        note_idx = note_freqs.index(closest)
        print(f"  {pos:4d}mm  {f:7.1f}Hz  {delta:+7.1f}Hz  {note_names[note_idx]} ({closest:.1f}Hz)")
    except Exception as e:
        print(f"  {pos:4d}mm  FAILED: {e}")

print()
print("For open-open: hole near BELL should raise pitch MORE (removes more tube)")
print("Hole near MOUTHPIECE should raise pitch LESS (removes less tube)")
print()

# Now test cumulative: open hole A, then open A+B
print("Cumulative effect test:")
print("Open holes at [300mm], then [300mm + Xmm]:")
print(f"{'X':>6s}  {'f(A)':>8s}  {'f(A+B)':>8s}  {'delta':>8s}")
print("-" * 40)

inst_a = tmm_instrument_from_radii(bore_radii, L, [300], [hd], [hl], od, False, 0.5)
wl_a = inst_a.find_resonance(c / 400.0, ["open"], 2)
f_a = inst_a.frequency_from_wavelength(wl_a)
print(f"  Only 300mm: {f_a:.1f}Hz")

for x in [50, 100, 150, 200, 300, 400]:
    pos_b = 300 + x
    if pos_b > 650:
        continue
    try:
        inst2 = tmm_instrument_from_radii(bore_radii, L, [300, pos_b], [hd, hd], [hl, hl], od, False, 0.5)
        # Fingering: both open
        wl = inst2.find_resonance(c / 500.0, ["open", "open"], 2)
        f = inst2.frequency_from_wavelength(wl)
        print(f"  +{pos_b:4d}mm: {f_a:.1f}Hz -> {f:.1f}Hz  delta={f-f_a:+.1f}Hz")
    except Exception as e:
        print(f"  +{pos_b:4d}mm: FAILED: {e}")

print()
print("=== The key test: what fingering convention does the TMM model use? ===")
print("In TMM, opening a hole models an acoustic junction that vents pressure.")
print("For open-open: the effective tube length is measured from the FIRST OPEN HOLE to the bell.")
print("So opening a hole near the MOUTHPIECE should create a SHORT effective tube = HIGH pitch.")
print("Opening a hole near the BELL should create a LONG effective tube = LOW pitch.")
print()

# THE critical test
print("Fingering test: what does 'open hole at index 0' do?")
inst3 = tmm_instrument_from_radii(bore_radii, L, [100, 300, 500], [hd]*3, [hl]*3, od, False, 0.5)

# Convention A: index 0 = position 100mm (mouthpiece end)
print("\nConvention A: ['open','closed','closed'] = open hole at 100mm (near mouthpiece)")
wl = inst3.find_resonance(c / 400.0, ["open", "closed", "closed"], 2)
f = inst3.frequency_from_wavelength(wl)
print(f"  Result: {f:.1f}Hz")

# Convention B: index 0 = position 100mm, but fingering reversed
print("\nConvention B: ['closed','closed','open'] = open hole at 500mm (near bell)")
wl = inst3.find_resonance(c / 400.0, ["closed", "closed", "open"], 2)
f = inst3.frequency_from_wavelength(wl)
print(f"  Result: {f:.1f}Hz")

print("\nWhich raises pitch more? Opening near mouthpiece or near bell?")
