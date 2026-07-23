"""Bass clarinet full chromatic scale (D2-D3, 12 holes)."""
import sys, os, math, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Chromatic targets D2 to D3 (13 notes, 12 holes)
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0

# Step 1: Run SequentialBoreOptimizer for 12 holes (no register hole)
print("="*70)
print("SEQUENTIAL BORE OPTIMIZER — Chromatic D2-D3 (12 holes)")
print("="*70)

# Dummy fingering sets (Phase 3 uses these, but for closed-top Phase 2 ignores them)
# We'll generate proper ones after optimization
dummy_fs = [["closed"]*12]*13

opt = SequentialBoreOptimizer(
    target_frequencies=targets,
    fingering_sets=dummy_fs,
    bore_radius=BORE_RADIUS,
    outer_diameter=OUTER_DIAMETER,
    closed_top=True,
    hole_diameter=HOLE_DIAMETER,
    hole_length=HOLE_LENGTH,
    n_bore_cp=0,
)
opt.bore_length_bounds = (900, 1500)

print(f"\nPhase 1: Finding bore length for {targets[0]:.1f} Hz")
print(f"  Initial: {SPEED_OF_SOUND/(4*targets[0]):.0f}mm")

result = opt.run(verbose=True)

bore_length = result["bore_length_mm"]
holes_no_reg = result["hole_positions"]
rms = result["final_rms_cents"]

print(f"\n{'='*70}")
print(f"Phase 2: Add register hole and re-optimize")
print(f"{'='*70}")

REGISTER_POS = 80.0
REGISTER_DIAM = 2.5
REGISTER_LENGTH = 3.0

from scipy.optimize import minimize

# Build fingerings with register hole
def build_all_holes(hp):
    all_pos = list(hp) + [REGISTER_POS]
    all_dia = [HOLE_DIAMETER]*len(hp) + [REGISTER_DIAM]
    all_len = [HOLE_LENGTH]*len(hp) + [REGISTER_LENGTH]
    idx = np.argsort(all_pos)
    return ([all_pos[i] for i in idx], [all_dia[i] for i in idx],
            [all_len[i] for i in idx], list(idx).index(len(hp)))

def make_fingerings(n, ri):
    th = sorted([j for j in range(n) if j != ri])
    fs = []
    for k in range(len(targets)):
        f = ["closed"] * n
        f[ri] = "closed"
        for j in th[:k]: f[j] = "open"
        fs.append(f)
    return fs

def evaluate_with_reg(hp, L, verbose=False):
    hp = sorted(hp)
    aps, ads, als, ri = build_all_holes(hp)
    fs = make_fingerings(len(aps), ri)
    radii = np.full(10, BORE_RADIUS)
    try:
        inst = tmm_instrument_from_radii(radii, L, aps, ads, als, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
        f1 = inst.compute_fingered_frequencies([SPEED_OF_SOUND/f for f in targets], fs, n_register=1)
    except: return 1e10, []
    cents = []
    for a,t in zip(f1, targets):
        if a>0 and math.isfinite(a): cents.append(1200*math.log2(a/t))
        else: cents.append(1e10)
    c = np.array(cents); off = np.median(c)
    rms = float(np.sqrt(np.mean((c-off)**2)))
    if verbose:
        print(f"  L={L:.0f} RMS(rel)={rms:.2f}c offset={off:+.0f}c")
        for n,t,a,e in zip(names,targets,f1,cents):
            print(f"    {n}: t={t:.1f} a={a:.1f} err={e:+.0f}c")
    return rms, cents

# Initial eval with register hole
print(f"\nInitial holes from SequentialBoreOptimizer:")
rms_i, cents_i = evaluate_with_reg(holes_no_reg, bore_length, verbose=True)

# Phase 2a: Re-optimize bore length
print(f"\nPhase 2a: Re-optimize bore length")
def bore_obj(L):
    rms_v, _ = evaluate_with_reg(holes_no_reg, L, verbose=False)
    return rms_v + 1e-6 * abs(L - bore_length)

r = minimize(bore_obj, [bore_length], method='L-BFGS-B', bounds=[(bore_length*0.85, bore_length*1.15)], options={"maxiter":50})
L_opt = float(r.x[0])
print(f"  L={L_opt:.0f}mm cost={r.fun:.4f}")

# Phase 2b: Re-optimize hole positions (sequential)
print(f"\nPhase 2b: Sequential hole re-optimization with register hole")
GAP = 10
existing_holes = []
t0 = time.time()

for i, target in enumerate(targets[1:], 1):
    lo = (existing_holes[-1]+GAP) if existing_holes else 20
    hi = L_opt - 20
    if lo >= hi: lo, hi = hi-1, hi+1
    
    def ho(x):
        pos = float(x[0])
        hp = sorted(existing_holes + [pos])
        aps, ads, als, ri = build_all_holes(hp)
        n = len(aps)
        fing = ["closed"] * n
        fing[aps.index(pos)] = "open"
        fing[ri] = "closed"
        try:
            radii = np.full(10, BORE_RADIUS)
            inst = tmm_instrument_from_radii(radii, L_opt, aps, ads, als, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
            wl = inst.find_resonance(SPEED_OF_SOUND/target, fing, n_register=1)
            f = inst.frequency_from_wavelength(wl)
            return abs(1200*math.log2(f/target)) if f>0 else 1e10
        except: return 1e10
    
    r = minimize(ho, [(lo+hi)/2], method='L-BFGS-B', bounds=[(lo, hi)], options={"maxiter":50,"ftol":1e-4})
    bp, be = float(r.x[0]), float(r.fun)
    for _ in range(3):
        xt = np.random.uniform(lo, hi)
        r2 = minimize(ho, [xt], method='L-BFGS-B', bounds=[(lo, hi)], options={"maxiter":30,"ftol":1e-4})
        if r2.fun < be: be, bp = r2.fun, float(r2.x[0])
    existing_holes.append(bp)
    print(f"  Note {i} ({target:.0f}Hz): pos={bp:.1f}mm err={be:.1f}c")

holes_p2 = sorted(existing_holes)
print(f"  Holes: {[f'{h:.0f}' for h in holes_p2]}")

# Phase 3: Simultaneous refinement
print(f"\nPhase 3: Simultaneous refinement")
def joint_obj(x):
    L = float(x[0])
    hp = sorted(x[1:].tolist())
    if L < hp[-1]+GAP or L < 500: return 1e10
    rms_v, _ = evaluate_with_reg(hp, L)
    return rms_v

cb = [(L_opt*0.9, L_opt*1.1)]
for i in range(len(holes_p2)):
    lo = GAP if i==0 else holes_p2[i-1]+GAP
    lo = max(lo, holes_p2[i]-10)
    hi = (L_opt*1.1-GAP) if i==len(holes_p2)-1 else holes_p2[i+1]-GAP
    hi = min(hi, holes_p2[i]+10)
    if lo>=hi: lo,hi=hi-5,hi+5
    cb.append((lo,hi))

x0 = [L_opt] + holes_p2
r3 = minimize(joint_obj, x0, method='L-BFGS-B', bounds=cb, options={"maxiter":150,"ftol":1e-8})
L_f = r3.x[0]; holes_f = sorted(r3.x[1:].tolist())
print(f"  cost={r3.fun:.4f}")

# Final eval
print(f"\n{'='*70}")
print(f"FINAL CHROMATIC (1st register)")
print(f"{'='*70}")
rms_f, cents_f = evaluate_with_reg(holes_f, L_f, verbose=True)
print(f"\n  L={L_f:.1f}mm, Holes={[f'{h:.0f}' for h in holes_f]}")

# 2nd register
print(f"\n{'='*70}")
print(f"2ND REGISTER (register open)")
print(f"{'='*70}")
targets_2nd = [t*3 for t in targets]
aps, ads, als, ri = build_all_holes(holes_f)
fs = make_fingerings(len(aps), ri)
reg2_fs = [list(f) for f in fs]
for f in reg2_fs: f[ri] = "open"
radii = np.full(10, BORE_RADIUS)
inst = tmm_instrument_from_radii(radii, L_f, aps, ads, als, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
f2 = inst.compute_fingered_frequencies([SPEED_OF_SOUND/f for f in targets_2nd], reg2_fs, n_register=2)

cents2 = []
for n,t,a in zip(names,targets_2nd,f2):
    c = 1200*math.log2(a/t) if a and a>0 else 0
    cents2.append(c)
    print(f"  {n}: t={t:.1f} a={a:.1f} err={c:+.0f}c")
c2 = np.array(cents2); off2 = np.median(c2); rms2 = np.sqrt(np.mean((c2-off2)**2))
print(f"  Offset: {off2:+.0f}c RMS(rel): {rms2:.1f}c")

# Twelfths
print(f"\n{'='*70}")
print(f"TWELFTHS")
print(f"{'='*70}")
_, cents1 = evaluate_with_reg(holes_f, L_f)  # get 1st reg cents
twelfths = []
for i in range(13):
    f1v = targets[i] * 2**(cents1[i]/1200)
    f2v = targets_2nd[i] * 2**(cents2[i]/1200)
    r = f2v/f1v; e = 1200*math.log2(r/3.0); twelfths.append(e)
    print(f"  {names[i]}: f1={f1v:.1f} f2={f2v:.1f} ratio={r:.3f} err={e:+.0f}c")
rms12 = np.sqrt(np.mean(np.array(twelfths)**2))
print(f"  Twelfths RMS: {rms12:.1f}c")
print(f"  Time: {time.time()-t0:.0f}s")
