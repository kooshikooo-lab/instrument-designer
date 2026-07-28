"""Test: does absolute RMS (no median correction) reveal the true picture?"""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
cfg = {
    "desc": "Soprano sax in Bb (open-open)",
    "closed_top": False,
    "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
    "names": ["Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5"],
    "bore_radius": 6.0, "outer_diameter": 20.0,
    "hole_diameter": 6.5, "hole_length": 3.0,
    "fingerings": [
        ["closed"] * 7,
        ["open", "closed", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "open", "closed", "closed"],
        ["open", "open", "open", "open", "open", "open", "closed"],
    ],
}


def eval_cents(radii, bore_length, hp, hd, hl):
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [c / f for f in cfg["targets"]]
    freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 2)
    cents = []
    for a, t in zip(freqs, cfg["targets"]):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
    return np.array(cents)


def median_rms(ca):
    return float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))


def absolute_rms(ca):
    return float(np.sqrt(np.mean(ca ** 2)))


# Start with sequential result
bore_length = 371.2
hp = [61.6, 99.1, 117.9, 154.1, 183.7, 198.7]
hd = [6.5] * 6
hl = [3.0] * 6
radii = np.full(8, 6.0)

ca = eval_cents(radii, bore_length, hp, hd, hl)
print(f"Starting point (sequential):")
print(f"  Median RMS: {median_rms(ca):.2f}c")
print(f"  Absolute RMS: {absolute_rms(ca):.2f}c")
print(f"  Per-note: {[f'{x:.1f}' for x in ca]}")

# Refine using ABSOLUTE RMS (not median-corrected)
print(f"\n--- Refining with ABSOLUTE RMS objective ---")
t0 = time.time()

n_cp = 0  # fixed bore for simplicity
n_h = len(hp)

# Build bounds
GAP = 5.0
hole_lo, hole_hi = [0.0]*n_h, [0.0]*n_h
for i in range(n_h):
    hole_lo[i] = (hp[i-1] + GAP) if i > 0 else 30.0
    hole_hi[i] = (hp[i+1] - GAP) if i < n_h-1 else (bore_length*1.3 - 30.0)
    hole_lo[i] = max(hole_lo[i], hp[i] - 20)
    hole_hi[i] = min(hole_hi[i], hp[i] + 20)
    if hole_lo[i] > hole_hi[i]:
        hole_lo[i] = hp[i] - 1
        hole_hi[i] = hp[i] + 1

# Stage 1: Bore length (absolute RMS)
def obj_bore(x):
    ca = eval_cents(radii, x[0], hp, hd, hl)
    return absolute_rms(ca)

r = sp_min(obj_bore, [bore_length], method='L-BFGS-B',
           bounds=[(200.0, 600.0)], options={"maxiter": 100, "ftol": 1e-8})
bore_length = r.x[0]
ca = eval_cents(radii, bore_length, hp, hd, hl)
print(f"  After bore length: abs={absolute_rms(ca):.2f}c median={median_rms(ca):.2f}c L={bore_length:.1f}mm")
print(f"  Per-note: {[f'{x:.1f}' for x in ca]}")

# Stage 2: Hole positions (absolute RMS)
def obj_holes(x):
    ca = eval_cents(radii, bore_length, x.tolist(), hd, hl)
    return absolute_rms(ca)

r = sp_min(obj_holes, np.array(hp), method='L-BFGS-B',
           bounds=[(hole_lo[i], hole_hi[i]) for i in range(n_h)],
           options={"maxiter": 200, "ftol": 1e-8})
hp = r.x.tolist()
ca = eval_cents(radii, bore_length, hp, hd, hl)
print(f"  After holes:        abs={absolute_rms(ca):.2f}c median={median_rms(ca):.2f}c")
print(f"  Per-note: {[f'{x:.1f}' for x in ca]}")

# Stage 3: Simultaneous (absolute RMS)
all_bounds = [(200.0, 600.0)]
all_bounds += [(hole_lo[i], hole_hi[i]) for i in range(n_h)]

def obj_all(x):
    ca = eval_cents(radii, x[0], x[1:].tolist(), hd, hl)
    return absolute_rms(ca)

x0 = np.concatenate([[bore_length], np.array(hp)])
r = sp_min(obj_all, x0, method='L-BFGS-B',
           bounds=all_bounds, options={"maxiter": 300, "ftol": 1e-10})
bore_length = r.x[0]
hp = r.x[1:].tolist()

ca = eval_cents(radii, bore_length, hp, hd, hl)
print(f"  After simultaneous: abs={absolute_rms(ca):.2f}c median={median_rms(ca):.2f}c L={bore_length:.1f}mm")
print(f"  Per-note: {[f'{x:.1f}' for x in ca]}")
print(f"  Hole positions: {[f'{x:.1f}' for x in hp]}")
print(f"  Time: {time.time()-t0:.1f}s")


# Also test: what if we add the all-closed fundamental to the targets?
print(f"\n--- Test with all-closed fundamental added as 8th target ---")
targets_with_fund = [466.2] + cfg["targets"]
fingerings_with_fund = [["closed"] * 7] + cfg["fingerings"]

def eval_with_fund(radii, bore_length, hp, hd, hl):
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [c / f for f in targets_with_fund]
    freqs = inst.compute_fingered_frequencies(tw, fingerings_with_fund, 2)
    cents = []
    for a, t in zip(freqs, targets_with_fund):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
    return np.array(cents)

ca = eval_with_fund(radii, bore_length, hp, hd, hl)
print(f"  Including all-closed:")
print(f"  Median RMS: {median_rms(ca):.2f}c")
print(f"  Absolute RMS: {absolute_rms(ca):.2f}c")
print(f"  Per-note: {[f'{x:.1f}' for x in ca]}")
