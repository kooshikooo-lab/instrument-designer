"""7-hole diatonic optimization — fast version, single DE + L-BFGS-B."""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 82.407, 87.307, 98.000, 110.000, 123.471, 146.832]
names = ['D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'D3']

def evaluate(hole_positions_7):
    all_pos = sorted([80.0] + list(hole_positions_7))
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
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart, n_register=1)
    except:
        return 1000.0
    errs = []
    for t, f in zip(targets, freqs):
        c = 1200 * np.log2(f/t) if f > 0 else 1e10
        errs.append(c)
    e = np.array(errs)
    off = np.median(e)
    return np.sqrt(np.mean((e - off)**2))

# Initial: spread along bore
initial = [200, 400, 550, 700, 850, 1000, 1150]
print("=== 7-hole diatonic optimization ===")
print("Initial cost: %.2fc" % evaluate(initial))

t0 = time.time()

# Narrow bounds per hole
bounds = [
    (150, 350),
    (300, 500),
    (450, 650),
    (600, 800),
    (750, 950),
    (900, 1100),
    (1050, 1200),
]

# Single DE, small population
de = differential_evolution(
    evaluate, bounds, seed=42,
    maxiter=20, popsize=10,
    tol=1e-6, mutation=(0.5, 1.0), recombination=0.7,
    polish=False,
)
print("DE cost: %.2fc (%.0fs)" % (de.fun, time.time()-t0))

# L-BFGS-B refinement
r = minimize(evaluate, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-9})
dt = time.time() - t0
print("L-BFGS-B cost: %.2fc (total %.0fs)" % (r.fun, dt))
print("Positions: %s" % [round(p) for p in r.x])

# Detailed eval
all_pos = sorted([80.0] + list(r.x))
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
