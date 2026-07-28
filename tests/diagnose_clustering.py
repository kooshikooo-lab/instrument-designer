"""Check what positions each method produces for xaphoon and whether they cluster."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.target_frequencies import TARGETS
import numpy as np

cfg = {
    "name": "Xaphoon",
    "bore_length_mm": 662,
    "bore_radius_mm": 7.0,
    "closed_top": False,
    "n_bore_cp": 0,
    "hole_diameter_mm": 6.5,
    "hole_length_mm": 3.0,
    "outer_diameter_mm": 20.0,
    "register_ratio": 2.0,
}
targets = TARGETS["xaphoon"]
c = SPEED_OF_SOUND

print("=" * 60)
print("Sequential method positions")
print("=" * 60)
opt = SequentialBoreOptimizer(cfg)
result = opt.sequential(
    targets, n_bore_cp=0, bore_radius_bounds=(5.0, 15.0),
    hole_diameter_bounds=(5.0, 8.0), hole_length_bounds=(2.0, 5.0),
    outer_diameter_bounds=(12.0, 25.0), bore_length_bounds=(500, 800),
    bore_length_step=10,
)
positions = result["positions"]
print(f"  Positions: {positions}")
print(f"  RMS: {result['rms']:.1f}c")

# Check if they're clustered
if len(positions) > 1:
    gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
    print(f"  Gaps between holes: {gaps}")
    print(f"  Max gap: {max(gaps)}mm")
    print(f"  Total spread: {positions[-1] - positions[0]}mm / {cfg['bore_length_mm']}mm bore")

print()
print("=" * 60)
print("Independent method positions")
print("=" * 60)
opt2 = SequentialBoreOptimizer(cfg)
# Use the independent placement logic directly
bore_radii = np.full(8, cfg["bore_radius_mm"])
sorted_targets = sorted(targets)
notes_needing = sorted_targets[1:]
notes_reversed = list(reversed(notes_needing))

existing = []
for target_freq in notes_reversed:
    best_rms = 1e9
    best_pos = 0
    for test_pos in np.arange(20, cfg["bore_length_mm"] - 20, 5):
        test_existing = existing + [test_pos]
        test_sets = [["open" if j < len(test_existing) + 1 else "closed" for j in range(len(test_existing) + 1)]]
        test_sets[0][len(test_existing)] = "open"
        try:
            inst = tmm_instrument_from_radii(
                bore_radii, cfg["bore_length_mm"],
                test_existing, [cfg["hole_diameter_mm"]]*len(test_existing),
                [cfg["hole_length_mm"]]*len(test_existing),
                cfg["outer_diameter_mm"], False, 0.5
            )
            wl = inst.find_resonance(c / target_freq, test_sets[0], 2)
            f = inst.frequency_from_wavelength(wl)
            err = 1200.0 * np.log2(f / target_freq)
            if abs(err) < abs(best_rms):
                best_rms = err
                best_pos = test_pos
        except:
            pass
    existing.append(best_pos)

existing_reversed = list(reversed(existing))
print(f"  Positions: {existing_reversed}")
if len(existing_reversed) > 1:
    gaps = [existing_reversed[i+1] - existing_reversed[i] for i in range(len(existing_reversed)-1)]
    print(f"  Gaps between holes: {gaps}")
    print(f"  Max gap: {max(gaps)}mm")
    print(f"  Total spread: {existing_reversed[-1] - existing_reversed[0]}mm / {cfg['bore_length_mm']}mm bore")

print()
print("=" * 60)
print("Expected evenly-spaced positions for 6 holes")
print("=" * 60)
evenly_spaced = np.linspace(20, 640, 6).tolist()
print(f"  Positions: {[f'{p:.0f}' for p in evenly_spaced]}")
gaps = [evenly_spaced[i+1] - evenly_spaced[i] for i in range(len(evenly_spaced)-1)]
print(f"  Gaps between holes: {[f'{g:.0f}' for g in gaps]}")

print()
print("=" * 60)
print("Postma reference: real saxophone hole positions")
print("=" * 60)
# From Postma (2019) and Selmer Series II measurements
# Alto sax: L=705mm bore, holes at roughly: 180, 240, 310, 380, 450, 520mm
# Scaled to xaphoon L=662mm:
scale = 662 / 705
ref_positions = [p * scale for p in [180, 240, 310, 380, 450, 520]]
print(f"  Reference (scaled): {[f'{p:.0f}' for p in ref_positions]}")
gaps = [ref_positions[i+1] - ref_positions[i] for i in range(len(ref_positions)-1)]
print(f"  Gaps between holes: {[f'{g:.0f}' for g in gaps]}")
print(f"  Total spread: {ref_positions[-1] - ref_positions[0]:.0f}mm / {cfg['bore_length_mm']}mm bore")
