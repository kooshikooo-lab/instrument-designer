"""
Alto sax 2nd register: bore shape optimization.

Key insight from Lefebvre (2011): straight cones don't work well for saxophones.
The bore shape itself must be optimized alongside hole positions.

We parameterize the bore as a linear cone with optimizable r_in, angle, L,
and test whether the TMM model can match the target frequencies.
"""
import sys, os, time, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from scipy.optimize import minimize as sp_min, differential_evolution

c = SPEED_OF_SOUND

targets = [349.2, 392.0, 415.3, 466.2, 523.3, 587.3]
names = ['F4','G4','Ab4','Bb4','C5','D5']

fingerings = [
    ['closed','closed','closed','closed','closed','closed'],  # F4
    ['closed','closed','closed','closed','closed','open'],    # G4
    ['closed','closed','closed','closed','open','open'],      # Ab4
    ['closed','closed','closed','open','open','open'],        # Bb4
    ['closed','closed','open','open','open','open'],          # C5
    ['closed','open','open','open','open','open'],            # D5
]

OD = 26.0; HD = 7.5; HL = 3.5; N_REG = 3

def make_cone_radii(r_in, angle_deg, L, n=12):
    angle_rad = math.radians(angle_deg)
    r_out = r_in + L * math.tan(angle_rad)
    return np.linspace(r_in, r_out, n)

def eval_cum(radii, L, hp):
    hd = [HD]*len(hp); hl = [HL]*len(hp)
    inst = tmm_instrument_from_radii(radii, L, hp, hd, hl, OD, False, 0.5)
    cents = []
    for fing, tgt in zip(fingerings, targets):
        wl = inst.find_resonance(c/tgt, fing, n_register=N_REG)
        f = inst.frequency_from_wavelength(wl)
        cents.append(1200*math.log2(f/tgt) if f>0 and math.isfinite(f) else 1e10)
    return cents

def show(radii, L, hp, label=""):
    cents = eval_cum(radii, L, hp)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5): print(f"  {label}: FAIL"); return 999
    even = float(np.sqrt(np.mean((ca-np.median(ca))**2)))
    absr = float(np.sqrt(np.mean(ca**2)))
    med = float(np.median(ca))
    print(f"  {label}: Even={even:.1f}c Abs={absr:.1f}c Off={med:+.1f}c")
    for n,fr,ct in zip(names,targets,cents):
        print(f"    {n:>5} ({fr:.0f}Hz): {ct:>+7.1f}c")
    return even

def cost_fn(radii, L, hp):
    cents = eval_cum(radii, L, hp)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5): return 1e10
    med = float(np.median(ca))
    return float(np.sqrt(np.mean((ca-med)**2))) + 0.1*float(np.sqrt(np.mean(ca**2)))

print("=== ALTO SAX: BORE SHAPE + HOLES OPTIMIZATION ===")
print(f"n_register=3 (2nd register)")
print()

# First: sanity check the Lefebvre cone
R_IN = 6.25; ANGLE = 3.0; L_REF = 965.2
radii_ref = make_cone_radii(R_IN, ANGLE, L_REF)
hp_ref = sorted([c/(2.0*t) for t in reversed(targets)])
print(f"Lefebvre cone: r_in={R_IN}mm, angle={ANGLE}°, L={L_REF}mm")
show(radii_ref, L_REF, hp_ref, "Lefebvre ref cone")

# Now: sweep bore length to find the best L for the cone
print(f"\n--- Sweep bore length (r_in=6.25, angle=3.0) ---")
best_cost = 1e10
best_L = L_REF
for L_try in range(500, 1500, 25):
    radii = make_cone_radii(R_IN, ANGLE, L_try)
    # Theory positions for this L
    hp = sorted([min(c/(2.0*t), L_try-20) for t in reversed(targets)])
    if hp[0] < 20: continue
    cost = cost_fn(radii, L_try, hp)
    if cost < best_cost:
        best_cost = cost
        best_L = L_try
print(f"  Best L={best_L}mm (cost={best_cost:.1f})")
radii = make_cone_radii(R_IN, ANGLE, best_L)
hp = sorted([min(c/(2.0*t), best_L-20) for t in reversed(targets)])
show(radii, best_L, hp, "Best L sweep")

# L-BFGS-B from best sweep
print(f"\n--- L-BFGS-B from best sweep ---")
radii_best = make_cone_radii(R_IN, ANGLE, best_L)
def obj(x):
    hp = list(x)
    for i in range(1, len(hp)):
        if hp[i] <= hp[i-1]+5: return 1e6
    if hp[0]<20 or hp[-1]>best_L-20: return 1e6
    return cost_fn(radii_best, best_L, hp)

bounds = [(30, best_L-20)]*6
t0 = time.time()
res = sp_min(obj, np.array(hp), method='L-BFGS-B', bounds=bounds,
             options={"maxiter":200, "ftol":1e-10})
print(f"  [{time.time()-t0:.1f}s] cost={res.fun:.1f}")
show(radii_best, best_L, list(res.x), "L-BFGS-B holes")

# Joint: r_in + angle + L + holes using differential_evolution
print(f"\n--- Differential Evolution: r_in + angle + L + holes ---")
def obj_de(x):
    r_in, angle, L = x[0], x[1], x[2]
    hp = sorted(x[3:])
    if r_in<3 or r_in>12 or angle<0.5 or angle>5.0 or L<500 or L>1500: return 1e6
    for i in range(1, len(hp)):
        if hp[i] <= hp[i-1]+5: return 1e6
    if hp[0]<20 or hp[-1]>L-20: return 1e6
    radii = make_cone_radii(r_in, angle, L, n=12)
    return cost_fn(radii, L, hp)

# Build bounds: r_in, angle, L, then 6 hole positions
de_bounds = [(4,12),(1.0,5.0),(600,1500)] + [(30,1400)]*6
t0 = time.time()
res_de = differential_evolution(obj_de, de_bounds, seed=42, maxiter=50, tol=1e-8,
                                polish=True, workers=1)
print(f"  [{time.time()-t0:.1f}s] cost={res_de.fun:.1f}")
ri,angle,L = res_de.x[0], res_de.x[1], res_de.x[2]
hp = sorted(res_de.x[3:])
print(f"  r_in={ri:.2f}mm, angle={angle:.2f}°, L={L:.0f}mm")
radii = make_cone_radii(ri, angle, L, n=12)
show(radii, L, hp, "DE best")

# L-BFGS-B polish from DE result
print(f"\n--- L-BFGS-B polish from DE ---")
def obj2(x):
    r_in, angle, L = x[0], x[1], x[2]
    hp = list(x[3:])
    if r_in<3 or r_in>12 or angle<0.5 or angle>5.0 or L<500 or L>1500: return 1e6
    for i in range(1, len(hp)):
        if hp[i] <= hp[i-1]+5: return 1e6
    if hp[0]<20 or hp[-1]>L-20: return 1e6
    radii = make_cone_radii(r_in, angle, L, n=12)
    return cost_fn(radii, L, hp)

bounds2 = [(4,12),(1.0,5.0),(600,1500)] + [(30,1400)]*6
t0 = time.time()
res2 = sp_min(obj2, res_de.x, method='L-BFGS-B', bounds=bounds2,
              options={"maxiter":200, "ftol":1e-12})
print(f"  [{time.time()-t0:.1f}s] cost={res2.fun:.1f}")
ri2,angle2,L2 = res2.x[0], res2.x[1], res2.x[2]
hp2 = list(res2.x[3:])
print(f"  r_in={ri2:.2f}mm, angle={angle2:.2f}°, L={L2:.0f}mm")
radii2 = make_cone_radii(ri2, angle2, L2, n=12)
show(radii2, L2, hp2, "Polished")
