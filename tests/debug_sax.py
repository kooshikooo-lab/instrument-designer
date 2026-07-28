"""Debug soprano sax sequential placement."""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

cfg = {
    'targets': [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
    'closed_top': False,
    'bore_radius': 6.0,
    'outer_diameter': 20.0,
    'hole_diameter': 6.5,
    'hole_length': 3.0,
}
targets = sorted(cfg['targets'])
fundamental = min(targets)
L_est = c / (2.0 * fundamental)
print(f'Bore length estimate: {L_est:.0f} mm')

bore_radii = np.full(8, cfg['bore_radius'])
bore_length = L_est
hp, hd, hl = [], [], []

for i, target in enumerate(targets):
    best_pos, best_err = 0, 1e10
    min_p = hp[-1] + 15 if hp else 30
    max_p = bore_length - 30
    if min_p >= max_p:
        max_p = min_p + 1

    for pos in np.linspace(min_p, max_p, 80):
        pl = hp + [pos]
        dl = hd + [cfg['hole_diameter']]
        ll = hl + [cfg['hole_length']]
        idx = np.argsort(pl)
        pl_s = [pl[j] for j in idx]
        dl_s = [dl[j] for j in idx]
        ll_s = [ll[j] for j in idx]
        fing = ['closed'] * len(pl)
        fing[list(idx).index(i)] = 'open'
        try:
            inst = tmm_instrument_from_radii(
                bore_radii, bore_length, pl_s, dl_s, ll_s,
                cfg['outer_diameter'], cfg['closed_top'], 0.5,
            )
            wl = inst.find_resonance(c / target, fing, 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
            if err < best_err:
                best_err, best_pos = err, pos
        except:
            pass
    hp.append(best_pos)
    hd.append(cfg['hole_diameter'])
    hl.append(cfg['hole_length'])
    print(f'  Hole {i} ({target:.1f} Hz): pos={best_pos:.1f}mm, err={best_err:.1f}c')

idx = np.argsort(hp)
hp = [hp[j] for j in idx]
hd = [hd[j] for j in idx]
hl = [hl[j] for j in idx]

print(f'\nHoles sorted: {[f"{p:.0f}" for p in hp]}')
print(f'Bore length: {bore_length:.0f} mm')

# Evaluate final
inst = tmm_instrument_from_radii(bore_radii, bore_length, hp, hd, hl, 20.0, False, 0.5)
fingerings = [
    ['closed']*7,
    ['open','closed','closed','closed','closed','closed','closed'],
    ['open','open','closed','closed','closed','closed','closed'],
    ['open','open','open','closed','closed','closed','closed'],
    ['open','open','open','open','closed','closed','closed'],
    ['open','open','open','open','open','closed','closed'],
    ['open','open','open','open','open','open','closed'],
]
print('\nFinal evaluation:')
for fing, t in zip(fingerings, cfg['targets']):
    wl = inst.find_resonance(c/t, fing, 1)
    actual = inst.frequency_from_wavelength(wl)
    err = 1200*math.log2(actual/t)
    print(f'  {t:.1f} Hz -> {actual:.1f} Hz (err={err:+.1f}c)')

# Also check: what does the bore-length optimization give for sax?
print('\n--- Bore length optimization for sax ---')
from scipy.optimize import minimize as sp_min

def bore_obj(L):
    radii = np.full(6, cfg['bore_radius'])
    try:
        inst = tmm_instrument_from_radii(radii, L, [], [], [], cfg['outer_diameter'], False, 0.5)
        wl = inst.find_resonance(c/fundamental, [], 1)
        actual = inst.frequency_from_wavelength(wl)
        if actual <= 0 or not math.isfinite(actual):
            return 1e10
        return abs(1200.0 * math.log2(actual / fundamental))
    except:
        return 1e10

r = sp_min(bore_obj, [L_est], method='L-BFGS-B', bounds=[(L_est*0.7, L_est*1.3)])
print(f'Optimized bore length: {r.x[0]:.1f} mm (err: {r.fun:.1f}c)')
print(f'Ratio L/diameter: {r.x[0]/(cfg["bore_radius"]*2):.1f}')
