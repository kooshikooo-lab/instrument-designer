"""Refine bass clarinet with fixed Bessel bell using sequential Bordeaux method."""
import sys, os, math, time
import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
REGISTER_POS = 80.0
REGISTER_DIAM = 2.5
REGISTER_LENGTH = 3.0
BELL_LENGTH = 220.0
BELL_END_RADIUS = 26.0
n_bessel = math.log2(BELL_END_RADIUS / BORE_RADIUS)

targets_1st = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]

def build_profile(L_cyl, n_seg=80):
    L_tot = L_cyl + BELL_LENGTH
    radii = np.zeros(n_seg)
    for i in range(n_seg):
        x = i * L_tot / n_seg
        radii[i] = BORE_RADIUS if x < L_cyl else BORE_RADIUS * (1 + (x-L_cyl)/BELL_LENGTH)**n_bessel
    return radii, L_tot

def make_all_holes(hp):
    all_pos = list(hp) + [REGISTER_POS]
    all_dia = [HOLE_DIAMETER]*len(hp) + [REGISTER_DIAM]
    all_len = [HOLE_LENGTH]*len(hp) + [REGISTER_LENGTH]
    idx = np.argsort(all_pos)
    return ([all_pos[i] for i in idx], [all_dia[i] for i in idx],
            [all_len[i] for i in idx], list(idx).index(len(hp)))

def make_fingerings(n, reg_idx):
    th = sorted([j for j in range(n) if j != reg_idx])
    fs = []
    for i in range(8):
        f = ["closed"] * n
        f[reg_idx] = "closed"
        for j in th[:i]:
            f[j] = "open"
        fs.append(f)
    return fs

# ===== Phase 1: Find L_cyl =====
print("="*70)
print("Phase 1: Find L_cyl for all-closed fundamental")
print("="*70)

INITIAL_HOLES = [175.9, 292.9, 337.5, 444.6, 532.0, 609.8, 636.4]

best_Lc, best_err = None, 1e10
for Lc in range(600, 1200, 10):
    radii, L_tot = build_profile(Lc)
    all_pos_s, all_dia_s, all_len_s, ri = make_all_holes(INITIAL_HOLES)
    try:
        inst = tmm_instrument_from_radii(radii, L_tot, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
        wl = inst.find_resonance(SPEED_OF_SOUND/73.416, ["closed"]*8, n_register=1)
        f = inst.frequency_from_wavelength(wl)
        e = abs(1200*math.log2(f/73.416)) if f>0 else 1e10
        if e < best_err: best_err, best_Lc = e, Lc
    except:
        pass
print(f"  L_cyl={best_Lc}mm err={best_err:.1f}c")

# ===== Phase 2: Sequential hole placement =====
print(f"\n{'='*70}")
print(f"Phase 2: Sequential hole placement (Bordeaux)")
print(f"{'='*70}")

L_cyl = best_Lc
existing_holes = []
t_start = time.time()

def eval_single_hole(pos, target, existing_holes):
    hp = sorted(existing_holes + [pos])
    radii, L_tot = build_profile(L_cyl)
    all_pos_s, all_dia_s, all_len_s, ri = make_all_holes(hp)
    n = len(all_pos_s)
    fing = ["closed"] * n
    fing[all_pos_s.index(pos)] = "open"
    fing[ri] = "closed"
    try:
        inst = tmm_instrument_from_radii(radii, L_tot, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
        wl = inst.find_resonance(SPEED_OF_SOUND/target, fing, n_register=1)
        f = inst.frequency_from_wavelength(wl)
        if f<=0: return 1e10
        return abs(1200*math.log2(f/target))
    except:
        return 1e10

for i, target in enumerate(targets_1st[1:], 1):
    lo = (existing_holes[-1]+10) if existing_holes else 20
    hi = L_cyl - 20
    if lo >= hi: lo, hi = hi-1, hi+1
    
    # L-BFGS-B
    def obj(x):
        return eval_single_hole(float(x[0]), target, existing_holes)
    
    r = minimize(obj, [(lo+hi)/2], method='L-BFGS-B', bounds=[(lo, hi)], options={"maxiter":50,"ftol":1e-4})
    best_pos, best_err = float(r.x[0]), float(r.fun)
    
    # Random starts
    for _ in range(3):
        xt = np.random.uniform(lo, hi)
        r2 = minimize(obj, [xt], method='L-BFGS-B', bounds=[(lo, hi)], options={"maxiter":30,"ftol":1e-4})
        if r2.fun < best_err: best_err, best_pos = r2.fun, float(r2.x[0])
    
    existing_holes.append(best_pos)
    print(f"  Hole {i} ({target:.0f}Hz): pos={best_pos:.1f}mm err={best_err:.1f}c")

holes_p2 = sorted(existing_holes)
dt = time.time()-t_start
print(f"  Time: {dt:.0f}s")
print(f"  Holes: {[f'{h:.0f}' for h in holes_p2]}")

# ===== Phase 3: All-hole + L_cyl refinement =====
print(f"\n{'='*70}")
print(f"Phase 3: Simultaneous refinement")
print(f"{'='*70}")

GAP = 8
def make_bounds(hp, Lc):
    bounds = [(Lc*0.85, Lc*1.15)]
    for i in range(len(hp)):
        lo = GAP if i==0 else hp[i-1]+GAP
        lo = max(lo, hp[i]-15)
        hi = (Lc*1.15-GAP) if i==len(hp)-1 else hp[i+1]-GAP
        hi = min(hi, hp[i]+15)
        if lo>=hi: lo,hi=hi-5,hi+5
        bounds.append((lo,hi))
    return bounds

def joint_obj(x):
    Lc = float(x[0])
    hp = sorted(x[1:].tolist())
    if Lc < hp[-1]+20 or Lc < 300: return 1e10
    hp = sorted(hp)
    radii, L_tot = build_profile(Lc)
    aps, ads, als, ri = make_all_holes(hp)
    fs = make_fingerings(len(aps), ri)
    try:
        inst = tmm_instrument_from_radii(radii, L_tot, aps, ads, als, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
        f1 = inst.compute_fingered_frequencies([SPEED_OF_SOUND/f for f in targets_1st], fs, n_register=1)
        cents = []
        for a,t in zip(f1, targets_1st):
            if a>0 and math.isfinite(a): cents.append(1200*math.log2(a/t))
            else: cents.append(1e10)
        c = np.array(cents); off = np.median(c); return float(np.sqrt(np.mean((c-off)**2)))
    except: return 1e10

cb = make_bounds(holes_p2, L_cyl)
x0 = [L_cyl] + holes_p2
r3 = minimize(joint_obj, x0, method='L-BFGS-B', bounds=cb, options={"maxiter":100,"ftol":1e-8})
L_cyl_f = r3.x[0]
holes_f = sorted(r3.x[1:].tolist())
print(f"  cost={r3.fun:.4f}")
print(f"  L_cyl={L_cyl_f:.1f} L_tot={L_cyl_f+BELL_LENGTH:.0f}")
print(f"  Holes: {[f'{h:.0f}' for h in holes_f]}")

# ===== Final =====
print(f"\n{'='*70}")
print(f"FINAL 1ST REGISTER")
print(f"{'='*70}")

hp = sorted(holes_f)
radii, L_tot = build_profile(L_cyl_f)
aps, ads, als, ri = make_all_holes(hp)
fs = make_fingerings(len(aps), ri)
inst = tmm_instrument_from_radii(radii, L_tot, aps, ads, als, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
f1 = inst.compute_fingered_frequencies([SPEED_OF_SOUND/f for f in targets_1st], fs, n_register=1)

cents1 = []
for n,t,a in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"],targets_1st,f1):
    c = 1200*math.log2(a/t) if a>0 else 0
    cents1.append(c)
    print(f"  {n}: t={t:.1f} a={a:.1f} err={c:+.0f}c")
c1 = np.array(cents1); off1 = np.median(c1); rms1 = np.sqrt(np.mean((c1-off1)**2))
print(f"  Offset: {off1:+.0f}c RMS(rel): {rms1:.2f}c")

print(f"\n{'='*70}")
print(f"2ND REGISTER")
print(f"{'='*70}")
targets_2nd = [t*3 for t in targets_1st]
reg2_fs = [list(f) for f in fs]
for f in reg2_fs: f[ri] = "open"
f2 = inst.compute_fingered_frequencies([SPEED_OF_SOUND/f for f in targets_2nd], reg2_fs, n_register=2)

cents2 = []
for n,t,a in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"],targets_2nd,f2):
    c = 1200*math.log2(a/t) if a and a>0 else 0
    cents2.append(c)
    print(f"  {n}: t={t:.1f} a={a:.1f} err={c:+.0f}c")
c2 = np.array(cents2); off2 = np.median(c2); rms2 = np.sqrt(np.mean((c2-off2)**2))
print(f"  Offset: {off2:+.0f}c RMS(rel): {rms2:.1f}c")

print(f"\n{'='*70}")
print(f"TWELFTHS")
print(f"{'='*70}")
twelfths = []
for n,f1v,f2v in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"],f1,f2):
    r = f2v/f1v; e = 1200*math.log2(r/3.0); twelfths.append(e)
    print(f"  {n}: f1={f1v:.1f} f2={f2v:.1f} ratio={r:.3f} err={e:+.0f}c")
rms12 = np.sqrt(np.mean(np.array(twelfths)**2))
print(f"  Twelfths RMS: {rms12:.1f}c")
