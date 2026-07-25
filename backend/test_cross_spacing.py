"""Cross-fingering optimization with minimum spacing penalty to prevent hole collapse."""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

chart_raw = [
    [0,0,0,0,0,0,0,0,0,0,0,0, 0],
    [1,0,0,0,0,0,0,0,0,0,0,0, 0],
    [1,1,0,0,0,0,0,0,0,0,0,0, 0],
    [1,1,1,0,0,0,0,0,0,0,0,0, 0],
    [1,1,1,1,0,0,0,0,0,0,0,0, 0],
    [1,1,1,0,1,0,0,0,0,0,0,0, 0],
    [1,1,1,1,1,0,0,0,0,0,0,0, 0],
    [1,1,0,0,1,0,0,0,0,0,0,0, 0],
    [1,0,0,0,1,0,0,1,0,0,0,0, 0],
    [1,0,0,0,1,1,0,0,0,0,0,0, 0],
    [1,0,0,0,1,1,1,0,0,0,0,0, 0],
    [1,0,0,0,1,1,1,1,0,0,0,0, 0],
    [1,1,1,1,1,1,1,1,0,0,0,0, 0],
]
chart_str = [["open" if c else "closed" for c in row] for row in chart_raw]

REG_POS = 80.0
MIN_GAP = 30  # minimum hole spacing in mm
PENALTY_WEIGHT = 100.0

def spacing_penalty(x):
    """Penalize holes closer than MIN_GAP."""
    pos = sorted(x)
    penalty = 0.0
    for i in range(len(pos) - 1):
        gap = pos[i+1] - pos[i]
        if gap < MIN_GAP:
            penalty += (MIN_GAP - gap)**2
    return penalty

def eval_obj(x):
    """Phase cost + spacing penalty."""
    free_pos = sorted(x)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [2.5/2], [5.0]*12 + [3.0], 37.0,
        closed_top=True, cone_step=0.5
    )
    phase = inst.phase_cost(targets, chart_str, n_register=1)
    return phase + PENALTY_WEIGHT * spacing_penalty(x)

def eval_freq(x):
    free_pos = sorted(x)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [2.5/2], [5.0]*12 + [3.0], 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    except:
        return 1000.0, []
    errs = [1200*np.log2(f/t) if f>0 else 1e10 for t, f in zip(targets, freqs)]
    e = np.array(errs)
    off = np.median(e)
    return np.sqrt(np.mean((e - off)**2)), errs

# Evenly spaced initial positions
initial = [80 + i * (1130/13) for i in range(1, 13)]
print("=== Cross-fingering with spacing penalty (min %dmm) ===" % MIN_GAP)
print("Initial: %s" % [round(p) for p in initial])

bounds = [(100, 1180)] * 12

t0 = time.time()
de = differential_evolution(eval_obj, bounds, seed=42,
                             maxiter=50, popsize=15, tol=1e-6,
                             mutation=(0.5, 1.0), recombination=0.7)
dt = time.time() - t0

print("DE: obj=%.6f freq=%.1fc (%.0fs)" % (de.fun, eval_freq(de.x)[0], dt))
print("Holes: %s" % [round(p) for p in sorted(de.x)])

# Check spacing
holes = sorted(de.x)
gaps = [holes[i+1] - holes[i] for i in range(len(holes)-1)]
print("Gaps: %s" % [round(g) for g in gaps])
print("Min gap: %.0fmm" % min(gaps))

# L-BFGS-B refinement
r = minimize(eval_obj, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-10})
dt2 = time.time() - t0
print("\nFinal: obj=%.6f freq=%.1fc (%.0fs)" % (r.fun, eval_freq(r.x)[0], dt2))
holes = sorted(r.x)
gaps = [holes[i+1] - holes[i] for i in range(len(holes)-1)]
print("Holes: %s" % [round(p) for p in holes])
print("Gaps: %s" % [round(g) for g in gaps])
print("Min gap: %.0fmm" % min(gaps))

# Detailed eval
freq, errs = eval_freq(r.x)
print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
for n, t, c in zip(names, targets, errs):
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, t * 2**(c/1200), c))
e = np.array(errs)
off = np.median(e)
rms = np.sqrt(np.mean((e - off)**2))
print("\nRMS=%.2fc offset=%+.1fc" % (rms, off))
