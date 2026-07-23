"""Refine bore and hole positions with register hole present (closed for 1st reg)."""
import sys, os, math, time
import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
REGISTER_DIAM = 2.5
REGISTER_LENGTH = 3.0
REGISTER_POS = 80.0  # best from scan

# Initial hole positions from SequentialBoreOptimizer (no register hole)
INITIAL_HOLES = [179.6, 299.5, 345.5, 455.0, 544.7, 624.2, 651.5]

targets_1st = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]

def build_all_holes_and_fingerings(hole_positions, bore_length):
    """Build sorted hole list and fingerings with register hole fixed."""
    all_pos = list(hole_positions) + [REGISTER_POS]
    all_dia = [HOLE_DIAMETER] * len(hole_positions) + [REGISTER_DIAM]
    all_len = [HOLE_LENGTH] * len(hole_positions) + [REGISTER_LENGTH]
    idx = np.argsort(all_pos)
    all_pos_s = [all_pos[i] for i in idx]
    all_dia_s = [all_dia[i] for i in idx]
    all_len_s = [all_len[i] for i in idx]
    reg_idx = all_pos_s.index(REGISTER_POS)
    
    n_total = len(all_pos_s)
    # Fingerings for 8 notes of D major diatonic:
    # All notes: register = closed
    # Note 0 (D2): all holes closed
    # Note 1 (E2): nearest hole to reed open
    # Note 2 (F#2): nearest 2 holes open
    # ... etc
    tonehole_indices = sorted([j for j in range(n_total) if j != reg_idx])
    fingering_sets = []
    for i in range(8):
        f = ["closed"] * n_total
        if i > 0:
            for j in tonehole_indices[:i]:
                f[j] = "open"
        f[reg_idx] = "closed"
        fingering_sets.append(f)
    
    return all_pos_s, all_dia_s, all_len_s, fingering_sets

def evaluate(hole_positions, bore_length, verbose=False):
    """Evaluate RMS error for 1st register with register hole."""
    all_pos_s, all_dia_s, all_len_s, fingering_sets = build_all_holes_and_fingerings(hole_positions, bore_length)
    
    radii = np.full(10, BORE_RADIUS)
    inst = tmm_instrument_from_radii(radii, bore_length, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
    
    target_wls = [SPEED_OF_SOUND / f for f in targets_1st]
    freqs = inst.compute_fingered_frequencies(target_wls, fingering_sets, n_register=1)
    
    cents = []
    for a, t in zip(freqs, targets_1st):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
    
    c = np.array(cents)
    offset = np.median(c)
    rms = float(np.sqrt(np.mean((c - offset) ** 2)))
    
    if verbose:
        print(f"  bore={bore_length:.1f}mm RMS(rel)={rms:.2f}c offset={offset:+.0f}c")
        for n, t, a, e in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"], targets_1st, freqs, cents):
            print(f"    {n}: target={t:.1f} actual={a:.1f} err={e:+.0f}c")
    
    return rms, offset, freqs

# Initial evaluation
print("="*70)
print("Initial: SequentialBoreOptimizer holes + register hole (closed)")
print("="*70)
bore_length = 1171.0  # from Phase 1
rms0, off0, freqs0 = evaluate(INITIAL_HOLES, bore_length, verbose=True)

# Phase 1: re-optimize bore length with register hole present
print(f"\n{'='*70}")
print(f"Phase 1: Re-optimize bore length with register hole")
print(f"{'='*70}")

def bore_obj(L):
    all_pos_s = list(INITIAL_HOLES) + [REGISTER_POS]
    all_dia_s = [HOLE_DIAMETER] * len(INITIAL_HOLES) + [REGISTER_DIAM]
    all_len_s = [HOLE_LENGTH] * len(INITIAL_HOLES) + [REGISTER_LENGTH]
    idx = np.argsort(all_pos_s)
    all_pos_s = [all_pos_s[i] for i in idx]
    all_dia_s = [all_dia_s[i] for i in idx]
    all_len_s = [all_len_s[i] for i in idx]
    
    try:
        inst = tmm_instrument_from_radii(np.full(10, BORE_RADIUS), L, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
        wl = inst.find_resonance(SPEED_OF_SOUND / 73.416, ["closed"]*len(all_pos_s), n_register=1)
        f = inst.frequency_from_wavelength(wl)
        if f <= 0:
            return 1e10
        return abs(1200*math.log2(f/73.416))
    except:
        return 1e10

r1 = minimize(bore_obj, [1171.0], method='L-BFGS-B', bounds=[(1000, 1500)], options={"maxiter": 100, "ftol": 1e-6})
bore_length_opt = r1.x[0]
print(f"  bore={bore_length_opt:.1f}mm err={r1.fun:.1f}c")

# Phase 2: Re-optimize hole positions with register hole present
print(f"\n{'='*70}")
print(f"Phase 2: Re-optimize hole positions with register hole")
print(f"{'='*70}")

def pos_obj(x):
    hp = sorted(x.tolist())
    rms_val, _, _ = evaluate(hp, bore_length_opt, verbose=False)
    return rms_val

n_h = len(INITIAL_HOLES)  # 7
# Bounds: maintain order, with gaps
GAP = 10

def make_bounds(holes, L):
    bounds = []
    for i in range(len(holes)):
        lo = GAP if i == 0 else holes[i-1] + GAP
        # Make lo slightly less than current position to allow movement
        lo = max(lo, holes[i] - 70)
        hi = L - GAP if i == len(holes)-1 else holes[i+1] - GAP
        hi = min(hi, holes[i] + 70)
        if lo > hi:
            lo, hi = hi - 5, hi + 5
        bounds.append((lo, hi))
    return bounds

bounds = make_bounds(INITIAL_HOLES, bore_length_opt)

r2 = minimize(pos_obj, np.array(INITIAL_HOLES), method='L-BFGS-B', bounds=bounds, options={"maxiter": 300, "ftol": 1e-6})
holes_opt = sorted(r2.x.tolist())
print(f"  cost={r2.fun:.4f}")

# Phase 3: Simultaneous
print(f"\n{'='*70}")
print(f"Phase 3: Simultaneous bore length + hole positions")
print(f"{'='*70}")

def joint_obj(x):
    L = x[0]
    hp = sorted(x[1:].tolist())
    rms_val, _, _ = evaluate(hp, L, verbose=False)
    return rms_val

joint_bounds = [(bore_length_opt*0.9, bore_length_opt*1.1)] + make_bounds(INITIAL_HOLES, bore_length_opt)
x0 = np.concatenate([[bore_length_opt], np.array(INITIAL_HOLES)])
r3 = minimize(joint_obj, x0, method='L-BFGS-B', bounds=joint_bounds, options={"maxiter": 300, "ftol": 1e-8})
bore_length_final = r3.x[0]
holes_final = sorted(r3.x[1:].tolist())
print(f"  cost={r3.fun:.4f}")

# Final evaluation
print(f"\n{'='*70}")
print(f"Final result with register hole (closed for 1st reg)")
print(f"{'='*70}")
rms_final, off_final, freqs_final = evaluate(holes_final, bore_length_final, verbose=True)

# Compare
print(f"\n{'='*70}")
print(f"Comparison: before vs after re-optimization")
print(f"{'='*70}")
print(f"  Initial: bore=1171mm holes={INITIAL_HOLES}")
print(f"  Final:   bore={bore_length_final:.1f}mm holes={[f'{h:.1f}' for h in holes_final]}")
print(f"  RMS: {rms0:.2f}c -> {rms_final:.2f}c")

# Now test 2nd register with final configuration
print(f"\n{'='*70}")
print(f"2nd register with final configuration")
print(f"{'='*70}")
all_pos_s, all_dia_s, all_len_s, _ = build_all_holes_and_fingerings(holes_final, bore_length_final)
radii = np.full(10, BORE_RADIUS)
inst = tmm_instrument_from_radii(radii, bore_length_final, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)

# Get the fingering sets for 2nd register (register hole OPEN)
_, _, _, reg1_fs = build_all_holes_and_fingerings(holes_final, bore_length_final)
reg2_fs = []
for fs in reg1_fs:
    f2 = list(fs)
    reg_idx = all_pos_s.index(REGISTER_POS)
    f2[reg_idx] = "open"
    reg2_fs.append(f2)

targets_2nd = [t * 3 for t in targets_1st]
target_wls2 = [SPEED_OF_SOUND / f for f in targets_2nd]
freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)

cents2 = []
for a, t in zip(freqs2, targets_2nd):
    if a and a > 0:
        cents2.append(1200*math.log2(a/t))
    else:
        cents2.append(1e10)
c2 = np.array(cents2)
off2 = np.median(c2)
rms2 = np.sqrt(np.mean((c2 - off2)**2))

print(f"  Offset: {off2:+.0f}c  RMS(rel): {rms2:.1f}c")
for n, t, a, e in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"], targets_2nd, freqs2, cents2):
    print(f"    {n}: target={t:.1f} actual={a:.1f} err={e:+.0f}c")

# Twelfths
twelfths = []
for n, f1, f2 in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"], freqs_final, freqs2):
    if f1 > 0 and f2 > 0:
        r = f2/f1
        e = 1200*math.log2(r/3.0)
        twelfths.append(e)
rms12 = np.sqrt(np.mean(np.array(twelfths)**2))
print(f"\n  Twelfths RMS: {rms12:.1f}c")
for n, f1, f2, e in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"], freqs_final, freqs2, twelfths):
    r = f2/f1
    print(f"    {n}: f1={f1:.1f} f2={f2:.1f} ratio={r:.3f} err={e:+.0f}c")
