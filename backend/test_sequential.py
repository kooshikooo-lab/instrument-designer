"""Quick test: Sequential method on chalumeau only."""
import sys, os, time, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

cfg = {
    "desc": "Chalumeau in C (closed-open)",
    "closed_top": True,
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
    "names": ["C4", "D4", "E4", "F4", "G4", "A4"],
    "bore_radius": 7.25,
    "outer_diameter": 22.0,
    "hole_diameter": 7.0,
    "hole_length": 3.75,
    "fingerings": [
        ["closed"] * 6,
        ["open", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "closed", "closed"],
        ["open", "open", "open", "open", "open", "closed"],
    ],
}

c = SPEED_OF_SOUND
targets = sorted(cfg["targets"])
fundamental = min(targets)
L_est = c / (4.0 * fundamental)

print(f"Fundamental: {fundamental:.1f} Hz")
print(f"Bore length estimate: {L_est:.1f} mm")
print(f"Bore radius: {cfg['bore_radius']} mm")
print()

# Phase 1: Bore length scan
print("=== Phase 1: Bore length ===")
best_L = L_est
best_err = 1e10
for L in np.linspace(L_est * 0.8, L_est * 1.3, 30):
    try:
        inst = tmm_instrument_from_radii(
            np.array([cfg["bore_radius"]]), L,
            [], [], [],
            cfg["outer_diameter"], cfg["closed_top"], 0.5,
        )
        wl = inst.find_resonance(c / fundamental, [], 1)
        f = inst.frequency_from_wavelength(wl)
        err = abs(1200.0 * math.log2(f / fundamental)) if f > 0 else 1e10
        if err < best_err:
            best_err = err
            best_L = L
    except:
        pass

print(f"  Best bore length: {best_L:.1f} mm (error: {best_err:.1f} cents)")
bore_length = best_L
bore_radii = np.full(8, cfg["bore_radius"])

# Phase 2: Place holes one-by-one
print(f"\n=== Phase 2: Sequential hole placement ===")
holes_pos = []
holes_dia = []
holes_len = []

for i, target in enumerate(targets):
    target_wl = c / target
    print(f"\n  Hole {i}: target {target:.1f} Hz ({cfg['names'][i]})")

    best_pos = 0
    best_err = 1e10

    min_p = holes_pos[-1] + 15 if holes_pos else 30
    max_p = bore_length - 30

    for pos in np.linspace(min_p, max_p, 40):
        pos_list = holes_pos + [pos]
        dia_list = holes_dia + [cfg["hole_diameter"]]
        len_list = holes_len + [cfg["hole_length"]]

        idx = np.argsort(pos_list)
        pos_list_s = [pos_list[j] for j in idx]
        dia_list_s = [dia_list[j] for j in idx]
        len_list_s = [len_list[j] for j in idx]

        fing = ["closed"] * len(pos_list)
        new_idx = list(idx).index(i)
        fing[new_idx] = "open"

        try:
            inst = tmm_instrument_from_radii(
                bore_radii, bore_length,
                pos_list_s, dia_list_s, len_list_s,
                cfg["outer_diameter"], cfg["closed_top"], 0.5,
            )
            wl = inst.find_resonance(target_wl, fing, 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
            if err < best_err:
                best_err = err
                best_pos = pos
        except:
            pass

    holes_pos.append(best_pos)
    holes_dia.append(cfg["hole_diameter"])
    holes_len.append(cfg["hole_length"])
    print(f"    Best position: {best_pos:.1f} mm (error: {best_err:.1f} cents)")

# Sort by position
idx = np.argsort(holes_pos)
holes_pos = [holes_pos[j] for j in idx]
holes_dia = [holes_dia[j] for j in idx]
holes_len = [holes_len[j] for j in idx]

print(f"\n=== Final evaluation ===")
print(f"Bore: {bore_length:.0f}mm x {cfg['bore_radius']}mm")
print(f"Holes: {len(holes_pos)}")
for i, (p, d) in enumerate(zip(holes_pos, holes_dia)):
    print(f"  Hole {i}: pos={p:.1f}mm, dia={d:.1f}mm")

inst = tmm_instrument_from_radii(
    bore_radii, bore_length,
    holes_pos, holes_dia, holes_len,
    cfg["outer_diameter"], cfg["closed_top"], 0.5,
)
tw = [c / f for f in cfg["targets"]]
freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 1)

print(f"\n  {'Note':<6} {'Target':>8} {'Actual':>8} {'Cents':>8}")
print(f"  {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
cents = []
for name, actual, target in zip(cfg["names"], freqs, cfg["targets"]):
    if actual > 0 and math.isfinite(actual):
        err = 1200.0 * math.log2(actual / target)
        cents.append(err)
    else:
        err = 1e10
        cents.append(err)
    print(f"  {name:<6} {target:>8.1f} {actual:>8.1f} {err:>+8.1f}")

ca = np.array(cents)
if np.any(np.abs(ca) > 1e5):
    print("\n  FAILED")
else:
    offset = np.median(ca)
    corrected = ca - offset
    rms = float(np.sqrt(np.mean(corrected ** 2)))
    peak = float(np.max(np.abs(corrected)))
    print(f"\n  RMS: {rms:.2f} cents")
    print(f"  Peak: {peak:.2f} cents")
    print(f"  Offset: {offset:+.1f} cents")
