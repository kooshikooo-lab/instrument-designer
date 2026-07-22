"""Quick test: alto sax with correct n_register=2 evaluation."""
import sys, os, time, math
import numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from scipy.optimize import minimize as sp_min

c = SPEED_OF_SOUND
cfg = {
    'targets': [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3],
    'names': ['Eb4','F4','G4','Ab4','Bb4','C5','D5'],
    'closed_top': False,
    'outer_diameter': 26.0,
    'bore_radius': 8.5,
    'hole_diameter': 7.5,
    'hole_length': 3.5,
    'fingerings': [
        ['closed']*7,
        ['open','closed','closed','closed','closed','closed','closed'],
        ['open','open','closed','closed','closed','closed','closed'],
        ['open','open','open','closed','closed','closed','closed'],
        ['open','open','open','open','closed','closed','closed'],
        ['open','open','open','open','open','closed','closed'],
        ['open','open','open','open','open','open','closed'],
    ],
}

def eval_abs(radii, L, hp, n_reg):
    hd = [cfg['hole_diameter']]*len(hp)
    hl = [cfg['hole_length']]*len(hp)
    inst = tmm_instrument_from_radii(radii, L, hp, hd, hl, cfg['outer_diameter'], False, 0.5)
    tw = [c/f for f in cfg['targets']]
    cents = []
    for twl, fing in zip(tw, cfg['fingerings']):
        wl = inst.find_resonance(twl, fing, n_register=n_reg)
        f = inst.frequency_from_wavelength(wl)
        if f > 0 and math.isfinite(f):
            cents.append(1200.0*math.log2(f / cfg['targets'][cfg['fingerings'].index(fing)]))
        else:
            cents.append(1e10)
    return cents

def eval_evenness(radii, L, hp, n_reg):
    cents = eval_abs(radii, L, hp, n_reg)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5): return 1e10
    return float(np.sqrt(np.mean((ca - np.median(ca))**2)))

def eval_abs_rms(radii, L, hp, n_reg):
    cents = eval_abs(radii, L, hp, n_reg)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5): return 1e10
    return float(np.sqrt(np.mean(ca**2)))

# Step 1: Place holes with n_reg=2
print("="*60)
print("ALTO SAX Eb - Sequential hole placement (n_reg=2)")
print("="*60)

L_est = c / (2.0 * min(cfg['targets']))
bore_radii = np.full(8, cfg['bore_radius'])

# Bore length
def bore_obj(L):
    try:
        inst = tmm_instrument_from_radii(bore_radii, L, [], [], [], cfg['outer_diameter'], False, 0.5)
        wl = inst.find_resonance(c/min(cfg['targets']), [], n_register=2)
        f = inst.frequency_from_wavelength(wl)
        if f<=0 or not math.isfinite(f): return 1e10
        return abs(1200*math.log2(f/min(cfg['targets'])))
    except: return 1e10

r = sp_min(bore_obj, [L_est], method='L-BFGS-B', bounds=[(L_est*0.7, L_est*1.3)], options={"maxiter":50})
L = r.x[0]
print(f"  Bore length: {L:.0f}mm")

# Place holes sequentially
hp = []
sorted_targets = sorted(cfg['targets'])
hole_targets = sorted_targets[1:]
for k, target in enumerate(hole_targets):
    min_p = hp[-1] + 15 if hp else 30
    max_p = L - 30
    if min_p >= max_p: break

    best_pos, best_err = 0, 1e10
    for pos in np.linspace(min_p, max_p, 40):
        try:
            pl = list(hp) + [pos]
            idx = np.argsort(pl)
            pl_s = [pl[j] for j in idx]
            fing = ['closed'] * len(pl)
            for j in range(k+1):
                fing[list(idx).index(j)] = 'open'
            inst = tmm_instrument_from_radii(bore_radii, L, pl_s,
                [cfg['hole_diameter']]*len(pl), [cfg['hole_length']]*len(pl),
                cfg['outer_diameter'], False, 0.5)
            wl = inst.find_resonance(c/target, fing, n_register=2)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200*math.log2(f/target)) if f>0 else 1e10
            if err < best_err:
                best_err, best_pos = err, pos
        except: pass
    hp.append(best_pos)
    print(f"  Hole {k}: pos={best_pos:.0f}mm, target={target:.1f}Hz, err={best_err:.1f}c")

# Evaluate with cumulative fingering (real playing)
print(f"\n  Cumulative fingering evaluation (n_reg=2):")
cents = eval_abs(bore_radii, L, hp, 2)
ca = np.array(cents)
print(f"  Abs RMS={np.sqrt(np.mean(ca**2)):.1f}c, Median={np.median(ca):+.1f}c")
for name, freq, ct in zip(cfg['names'], cfg['targets'], cents):
    print(f"    {name:>5} ({freq:.1f}Hz): {ct:>+8.1f}c")

# Now optimize bore profile
print(f"\n  Optimizing bore profile (6 control points)...")
n_cp = 6
radii0 = np.full(n_cp, cfg['bore_radius'])
hd = [cfg['hole_diameter']]*len(hp)
hl = [cfg['hole_length']]*len(hp)

def obj(x):
    return eval_abs_rms(np.maximum(x, 3.0), L, hp, 2)

res = sp_min(obj, radii0, method='L-BFGS-B', bounds=[(3,15)]*n_cp, options={"maxiter":300, "ftol":1e-10})
radii_opt = np.maximum(res.x, 3.0)

print(f"  Radii: {' '.join(f'{x:.1f}' for x in radii_opt)}")
cents = eval_abs(radii_opt, L, hp, 2)
ca = np.array(cents)
print(f"  After bore opt: Abs RMS={np.sqrt(np.mean(ca**2)):.1f}c, Median={np.median(ca):+.1f}c")
for name, freq, ct in zip(cfg['names'], cfg['targets'], cents):
    print(f"    {name:>5} ({freq:.1f}Hz): {ct:>+8.1f}c")
