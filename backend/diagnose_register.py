"""Diagnose the soprano sax result with correct n_register=2.

Check: is 0.00c RMS really achievable, or is it a median-correction artifact?
"""
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


def eval_detail(radii, bore_length, hp, hd, hl):
    """Evaluate with both median-corrected and absolute RMS."""
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [c / f for f in cfg["targets"]]
    freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 2)
    cents = []
    for i, (a, t) in enumerate(zip(freqs, cfg["targets"])):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
    ca = np.array(cents)
    median_rms = float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))
    absolute_rms = float(np.sqrt(np.mean(ca ** 2)))
    return ca, median_rms, absolute_rms, freqs


# Test 1: Sequential placement only (no refinement)
print("=" * 70)
print("TEST 1: Sequential placement (n_register=2, no bore radii optimization)")
print("=" * 70)

targets = sorted(cfg["targets"])
fundamental = min(targets)
L_est = c / (2.0 * fundamental)
bore_radii = np.full(8, cfg["bore_radius"])

# Phase 1: Optimize bore length
def bore_obj(L):
    try:
        inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
            cfg["outer_diameter"], cfg["closed_top"], 0.5)
        wl = inst.find_resonance(c / fundamental, [], 2)
        f = inst.frequency_from_wavelength(wl)
        if f <= 0 or not math.isfinite(f): return 1e10
        return abs(1200.0 * math.log2(f / fundamental))
    except: return 1e10

r = sp_min(bore_obj, [L_est], method='L-BFGS-B',
           bounds=[(L_est * 0.7, L_est * 1.3)],
           options={"maxiter": 50, "ftol": 1e-8})
bore_length = r.x[0]
print(f"Bore length: {bore_length:.1f}mm")

# Phase 2: Place holes
hp, hd, hl = [], [], []
for k, target in enumerate(targets[1:]):
    min_p = hp[-1] + 15 if hp else 30
    max_p = bore_length - 30
    if min_p >= max_p: break
    best_pos, best_err = 0, 1e10
    for pos in np.linspace(min_p, max_p, 60):
        try:
            inst = tmm_instrument_from_radii(bore_radii, bore_length,
                [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                cfg["outer_diameter"], cfg["closed_top"], 0.5)
            wl = inst.find_resonance(c / target, ["open"], 2)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
            if err < best_err:
                best_err, best_pos = err, pos
        except: pass
    hp.append(best_pos)
    hd.append(cfg["hole_diameter"])
    hl.append(cfg["hole_length"])

idx = np.argsort(hp)
hp = [hp[j] for j in idx]
hd = [hd[j] for j in idx]
hl = [hl[j] for j in idx]

ca, median_rms, absolute_rms, freqs = eval_detail(bore_radii, bore_length, hp, hd, hl)
print(f"\nSequential result:")
print(f"  Median-corrected RMS: {median_rms:.2f}c")
print(f"  Absolute RMS:         {absolute_rms:.2f}c")
print(f"  Per-note cents:       {[f'{x:.1f}' for x in ca]}")
print(f"  Bore radii:           {[f'{x:.1f}' for x in bore_radii]}")
print(f"  Hole positions:       {[f'{x:.1f}' for x in hp]}")


# Test 2: Full refinement with n_cp=6 (like sequential_refined)
print("\n" + "=" * 70)
print("TEST 2: Full refinement (n_cp=6, 4-stage L-BFGS-B)")
print("=" * 70)

n_cp = 6
radii = np.full(n_cp, cfg["bore_radius"])

# Build non-crossing bounds for holes
GAP = 5.0
hole_lo, hole_hi = [0.0]*len(hp), [0.0]*len(hp)
for i in range(len(hp)):
    hole_lo[i] = (hp[i-1] + GAP) if i > 0 else 30.0
    hole_hi[i] = (hp[i+1] - GAP) if i < len(hp)-1 else (bore_length*1.3 - 30.0)
    hole_lo[i] = max(hole_lo[i], hp[i] - 20)
    hole_hi[i] = min(hole_hi[i], hp[i] + 20)
    if hole_lo[i] > hole_hi[i]:
        hole_lo[i] = hp[i] - 1
        hole_hi[i] = hp[i] + 1

# Stage 1: Bore length only
def obj_bore_length(x):
    return eval_detail(radii, x[0], hp, hd, hl)[1]
r = sp_min(obj_bore_length, [bore_length], method='L-BFGS-B',
           bounds=[(bore_length*0.85, bore_length*1.15)],
           options={"maxiter": 100, "ftol": 1e-8})
bore_length = r.x[0]

# Stage 2: Bore-radii only
rad_bounds = [(3.0, 15.0)] * n_cp
def obj_radii(x):
    return eval_detail(np.maximum(x, 3.0), bore_length, hp, hd, hl)[1]
r = sp_min(obj_radii, radii, method='L-BFGS-B',
           bounds=rad_bounds,
           options={"maxiter": 200, "ftol": 1e-8})
radii = np.maximum(r.x, 3.0)

# Stage 3: Hole positions only
def obj_holes(x):
    return eval_detail(radii, bore_length, x.tolist(), hd, hl)[1]
r = sp_min(obj_holes, np.array(hp), method='L-BFGS-B',
           bounds=[(hole_lo[i], hole_hi[i]) for i in range(len(hp))],
           options={"maxiter": 200, "ftol": 1e-8})
hp = r.x.tolist()

# Stage 4: Simultaneous fine-tune
all_bounds = [(bore_length*0.85, bore_length*1.15)]
all_bounds += [(3.0, 15.0)] * n_cp
all_bounds += [(hole_lo[i], hole_hi[i]) for i in range(len(hp))]

def obj_all(x):
    L_i = x[0]
    rad_i = np.maximum(x[1:1+n_cp], 3.0)
    hp_i = x[1+n_cp:1+n_cp+len(hp)]
    return eval_detail(rad_i, L_i, hp_i.tolist(), hd, hl)[1]

x0 = np.concatenate([[bore_length], radii, np.array(hp)])
r = sp_min(obj_all, x0, method='L-BFGS-B',
           bounds=all_bounds,
           options={"maxiter": 300, "ftol": 1e-10})
bore_length = r.x[0]
radii = np.maximum(r.x[1:1+n_cp], 3.0)
hp = r.x[1+n_cp:].tolist()

ca, median_rms, absolute_rms, freqs = eval_detail(radii, bore_length, hp, hd, hl)
print(f"\nRefined result (n_cp=6):")
print(f"  Median-corrected RMS: {median_rms:.2f}c")
print(f"  Absolute RMS:         {absolute_rms:.2f}c")
print(f"  Per-note cents:       {[f'{x:.1f}' for x in ca]}")
print(f"  Bore radii (mm):      {[f'{x:.1f}' for x in radii]}")
print(f"  Hole positions (mm):  {[f'{x:.1f}' for x in hp]}")


# Test 3: Refinement with n_cp=0 (fixed bore)
print("\n" + "=" * 70)
print("TEST 3: Full refinement (n_cp=0, FIXED bore)")
print("=" * 70)

radii_0 = np.full(8, cfg["bore_radius"])
hp_0 = list(hp)
bore_length_0 = bore_length

# Stage 1: Bore length only
def obj_bore_length_0(x):
    return eval_detail(radii_0, x[0], hp_0, hd, hl)[1]
r = sp_min(obj_bore_length_0, [bore_length_0], method='L-BFGS-B',
           bounds=[(bore_length_0*0.85, bore_length_0*1.15)],
           options={"maxiter": 100, "ftol": 1e-8})
bore_length_0 = r.x[0]

# Stage 2: Hole positions only
def obj_holes_0(x):
    return eval_detail(radii_0, bore_length_0, x.tolist(), hd, hl)[1]
r = sp_min(obj_holes_0, np.array(hp_0), method='L-BFGS-B',
           bounds=[(hole_lo[i], hole_hi[i]) for i in range(len(hp_0))],
           options={"maxiter": 200, "ftol": 1e-8})
hp_0 = r.x.tolist()

# Stage 3: Simultaneous fine-tune
all_bounds_0 = [(bore_length_0*0.85, bore_length_0*1.15)]
all_bounds_0 += [(hole_lo[i], hole_hi[i]) for i in range(len(hp_0))]

def obj_all_0(x):
    L_i = x[0]
    hp_i = x[1:1+len(hp_0)]
    return eval_detail(radii_0, L_i, hp_i.tolist(), hd, hl)[1]

x0_0 = np.concatenate([[bore_length_0], np.array(hp_0)])
r = sp_min(obj_all_0, x0_0, method='L-BFGS-B',
           bounds=all_bounds_0,
           options={"maxiter": 300, "ftol": 1e-10})
bore_length_0 = r.x[0]
hp_0 = r.x[1:].tolist()

ca, median_rms, absolute_rms, freqs = eval_detail(radii_0, bore_length_0, hp_0, hd, hl)
print(f"\nRefined result (n_cp=0, fixed bore):")
print(f"  Median-corrected RMS: {median_rms:.2f}c")
print(f"  Absolute RMS:         {absolute_rms:.2f}c")
print(f"  Per-note cents:       {[f'{x:.1f}' for x in ca]}")
print(f"  Bore radii (mm):      {[f'{x:.1f}' for x in radii_0]}")
print(f"  Hole positions (mm):  {[f'{x:.1f}' for x in hp_0]}")


# Test 4: How does the closed-open chalumeau compare with n_cp=0?
print("\n" + "=" * 70)
print("TEST 4: Chalumeau (closed-open) with n_cp=0 for comparison")
print("=" * 70)

cfg_c = {
    "desc": "Chalumeau in C",
    "closed_top": True,
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
    "names": ["C4", "D4", "E4", "F4", "G4", "A4"],
    "bore_radius": 7.25, "outer_diameter": 22.0,
    "hole_diameter": 7.0, "hole_length": 3.75,
    "fingerings": [
        ["closed"] * 6,
        ["open", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "closed", "closed"],
        ["open", "open", "open", "open", "open", "closed"],
    ],
}

def eval_c(radii, bore_length, hp, hd, hl):
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg_c["outer_diameter"], cfg_c["closed_top"], 0.5,
    )
    tw = [c / f for f in cfg_c["targets"]]
    freqs = inst.compute_fingered_frequencies(tw, cfg_c["fingerings"], 1)
    cents = []
    for a, t in zip(freqs, cfg_c["targets"]):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
    ca = np.array(cents)
    return ca, float(np.sqrt(np.mean((ca - np.median(ca)) ** 2))), float(np.sqrt(np.mean(ca ** 2)))

radii_c = np.full(8, cfg_c["bore_radius"])
targets_c = sorted(cfg_c["targets"])
fund_c = min(targets_c)
L_c = c / (4.0 * fund_c)

# Phase 1
def bore_obj_c(L):
    try:
        inst = tmm_instrument_from_radii(radii_c, L, [], [], [],
            cfg_c["outer_diameter"], cfg_c["closed_top"], 0.5)
        wl = inst.find_resonance(c / fund_c, [], 1)
        f = inst.frequency_from_wavelength(wl)
        if f <= 0 or not math.isfinite(f): return 1e10
        return abs(1200.0 * math.log2(f / fund_c))
    except: return 1e10
r = sp_min(bore_obj_c, [L_c], method='L-BFGS-B',
           bounds=[(L_c * 0.7, L_c * 1.3)], options={"maxiter": 50, "ftol": 1e-8})
bore_length_c = r.x[0]

hp_c, hd_c, hl_c = [], [], []
for k, target in enumerate(targets_c[1:]):
    min_p = hp_c[-1] + 15 if hp_c else 30
    max_p = bore_length_c - 30
    if min_p >= max_p: break
    best_pos, best_err = 0, 1e10
    for pos in np.linspace(min_p, max_p, 60):
        try:
            inst = tmm_instrument_from_radii(radii_c, bore_length_c,
                [pos], [cfg_c["hole_diameter"]], [cfg_c["hole_length"]],
                cfg_c["outer_diameter"], cfg_c["closed_top"], 0.5)
            wl = inst.find_resonance(c / target, ["open"], 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
            if err < best_err:
                best_err, best_pos = err, pos
        except: pass
    hp_c.append(best_pos)
    hd_c.append(cfg_c["hole_diameter"])
    hl_c.append(cfg_c["hole_length"])

idx_c = np.argsort(hp_c)
hp_c = [hp_c[j] for j in idx_c]
ca_c, median_c, abs_c = eval_c(radii_c, bore_length_c, hp_c, hd_c, hl_c)
print(f"Chalumeau sequential (n_cp=0):")
print(f"  Median-corrected RMS: {median_c:.2f}c")
print(f"  Absolute RMS:         {abs_c:.2f}c")
print(f"  Per-note cents:       {[f'{x:.1f}' for x in ca_c]}")
print(f"  Hole positions (mm):  {[f'{x:.1f}' for x in hp_c]}")
