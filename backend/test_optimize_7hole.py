"""Optimize 7-hole diatonic bass clarinet from scratch.

Forget the unverified 0.45c claim. Start fresh and find actual optimal positions.
"""
import sys, time
import numpy as np
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# 7 diatonic targets
targets = [73.416, 82.407, 87.307, 98.000, 110.000, 123.471, 146.832]
names = ['D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'D3']

# Fingering: reed-end-first sequential (hole nearest reed opens first)
# Register hole at 80mm always closed
# Hole index 0 = register, holes 1-7 = primary (sorted by position)

def evaluate(hole_positions_7):
    """Evaluate 7-hole diatonic with reed-first sequential fingering."""
    all_pos = sorted([80.0] + list(hole_positions_7))
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [2.5/2] + [11.0/2]*7, [3.0] + [5.0]*7, 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
    
    # Reed-first sequential: hole 1 opens first, then 1+2, etc.
    chart = []
    for i in range(7):
        row = ['closed'] * 8  # 8 holes total
        if i == 0:
            pass  # D2: all closed
        else:
            for j in range(1, i + 1):
                row[j] = 'open'
        chart.append(row)
    
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart, n_register=1)
    except Exception:
        return 1000.0
    
    errs = []
    for t, f in zip(targets, freqs):
        c = 1200 * np.log2(f/t) if f > 0 else 1e10
        errs.append(c)
    err_arr = np.array(errs)
    offset = np.median(err_arr)
    rms = np.sqrt(np.mean((err_arr - offset)**2))
    return rms

# Initial guess: evenly spread along bore
initial = [i * 1211.3 / 8 for i in range(1, 8)]
print("=== 7-hole diatonic optimization ===")
print("Initial: %s" % [round(p) for p in initial])
print("Initial cost: %.2fc" % evaluate(initial))

# Multi-start optimization
best_rms = 1e10
best_pos = None

for start_idx in range(5):
    if start_idx == 0:
        init = initial
    else:
        init = sorted(np.random.uniform(100, 1100, 7).tolist())
    
    t0 = time.time()
    bounds = [(100, 1150)] * 7
    for i in range(6):
        bounds[i] = (max(100, init[i] - 200), min(init[i+1] - 10, init[i] + 200))
    
    from scipy.optimize import differential_evolution, minimize
    
    # DE phase
    de = differential_evolution(evaluate, bounds, seed=start_idx,
                                 maxiter=40, popsize=15, tol=1e-6,
                                 mutation=(0.5, 1.0), recombination=0.7)
    
    # L-BFGS-B refinement
    r = minimize(evaluate, de.x, method='L-BFGS-B', bounds=bounds,
                 options={'maxiter': 200, 'ftol': 1e-9})
    
    dt = time.time() - t0
    if r.fun < best_rms:
        best_rms = r.fun
        best_pos = r.x
    print("  Start %d: cost=%.2fc in %.0fs" % (start_idx, r.fun, dt))

print("\nBest: %.2fc" % best_rms)
print("Positions: %s" % [round(p) for p in best_pos])

# Detailed evaluation
all_pos = sorted([80.0] + list(best_pos))
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [2.5/2] + [11.0/2]*7, [3.0] + [5.0]*7, 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]
chart = []
for i in range(7):
    row = ['closed'] * 8
    if i > 0:
        for j in range(1, i + 1):
            row[j] = 'open'
    chart.append(row)

freqs = inst.compute_fingered_frequencies(wl, chart, n_register=1)
print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
errs = []
for n, t, f in zip(names, targets, freqs):
    c = 1200 * np.log2(f/t) if f > 0 else 0
    errs.append(c)
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, f, c))
e = np.array(errs)
off = np.median(e)
rms = np.sqrt(np.mean((e - off)**2))
print("\nRMS=%.2fc offset=%+.1fc" % (rms, off))
print("Max err: %.1fc" % max(abs(e - off)))
