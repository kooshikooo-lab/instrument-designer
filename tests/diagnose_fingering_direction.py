"""
Test: fix fingering direction for open-open instruments.

Real saxophone: index 0 = hole closest to bell (largest position).
You lift fingers from bell-end upward.

Current code: index 0 = hole closest to mouthpiece (smallest position) after position sort.
This is BACKWARDS.

Test: use Convention B (bell-end-first) with the sequential optimizer's positions.
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer

c = SPEED_OF_SOUND


def test_convention(name, cfg, positions):
    """Test both fingering conventions with given hole positions."""
    bore_radii = np.full(8, cfg["bore_radius"])
    L = cfg["bore_length_mm"]
    hd, hl, od = cfg["hole_diameter"], cfg["hole_length"], cfg["outer_diameter"]
    n_holes = len(positions)
    
    # All targets including fundamental
    fundamental = min(cfg["targets"])
    all_targets = sorted(cfg["targets"])
    
    inst = tmm_instrument_from_radii(
        bore_radii, L, positions, [hd]*n_holes, [hl]*n_holes, od, False, 0.5
    )
    
    # Convention A (current): index 0 = smallest position (mouthpiece end)
    # ["open", "closed", ...] opens hole closest to mouthpiece
    fing_a = [["closed"] * n_holes]
    for i in range(n_holes):
        fing_a.append(["open"] * (i+1) + ["closed"] * (n_holes - i - 1))
    
    # Convention B (correct sax): index 0 = largest position (bell end)
    # ["open", "closed", ...] opens hole closest to bell
    fing_b = [["closed"] * n_holes]
    for i in range(n_holes):
        fing_b.append(["closed"] * (n_holes - i - 1) + ["open"] * (i+1))
    
    tw = [c / f for f in all_targets]
    
    print(f"\n{'='*60}")
    print(f"{name} — positions: {[f'{p:.0f}' for p in positions]}")
    print(f"{'='*60}")
    
    for label, fingerings in [("Convention A (mouthpiece-first, CURRENT)", fing_a),
                               ("Convention B (bell-first, CORRECT SAX)", fing_b)]:
        freqs = inst.compute_fingered_frequencies(tw, fingerings, 2)
        cents = []
        for f, t in zip(freqs, all_targets):
            if f > 0 and math.isfinite(f):
                cents.append(1200.0 * math.log2(f / t))
            else:
                cents.append(1e10)
        rms = float(np.sqrt(np.mean(np.array(cents) ** 2)))
        
        print(f"\n  {label}")
        print(f"  RMS: {rms:.1f}c")
        for i, (f, t, ct) in enumerate(zip(freqs, all_targets, cents)):
            note = cfg["names"][i] if i < len(cfg["names"]) else f"note{i}"
            print(f"    {note:6s} target={t:7.1f}  got={f:7.1f}  err={ct:+7.1f}c")


# === Soprano sax positions from sequential refined ===
print("\n" + "="*60)
print("SOPRANO SAX — positions from sequential (L=379mm)")
print("="*60)
test_convention("Soprano sax", {
    "bore_length_mm": 379,
    "bore_radius": 6.0,
    "outer_diameter": 20.0,
    "hole_diameter": 6.5,
    "hole_length": 3.0,
    "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
    "names": ["Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5"],
}, [58, 93, 105, 138, 164, 189])


# === Xaphoon positions from sequential refined ===
print("\n" + "="*60)
print("XAPHOON — positions from sequential (L=622mm)")
print("="*60)
test_convention("Xaphoon", {
    "bore_length_mm": 622,
    "bore_radius": 7.0,
    "outer_diameter": 20.0,
    "hole_diameter": 6.5,
    "hole_length": 3.0,
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
    "names": ["C4", "D4", "E4", "F4", "G4", "A4", "B4"],
}, [101, 169, 457, 472, 487, 502])


# === Xaphoon with EVENLY SPACED holes (physically realistic) ===
print("\n" + "="*60)
print("XAPHOON — evenly spaced holes (physically realistic)")
print("="*60)
# Real sax holes are roughly evenly spaced
even_spaced = np.linspace(60, 600, 6).tolist()
test_convention("Xaphoon even", {
    "bore_length_mm": 622,
    "bore_radius": 7.0,
    "outer_diameter": 20.0,
    "hole_diameter": 6.5,
    "hole_length": 3.0,
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
    "names": ["C4", "D4", "E4", "F4", "G4", "A4", "B4"],
}, even_spaced)


# === Xaphoon with "realistic" sax hole positions ===
# Sax holes typically: ~20%, ~33%, ~43%, ~53%, ~63%, ~75% of bore from mouthpiece
print("\n" + "="*60)
print("XAPHOON — realistic sax proportions")
print("="*60)
L = 622
realistic = [L*0.20, L*0.33, L*0.43, L*0.53, L*0.63, L*0.75]
test_convention("Xaphoon realistic", {
    "bore_length_mm": 622,
    "bore_radius": 7.0,
    "outer_diameter": 20.0,
    "hole_diameter": 6.5,
    "hole_length": 3.0,
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
    "names": ["C4", "D4", "E4", "F4", "G4", "A4", "B4"],
}, realistic)
