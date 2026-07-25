"""12-hole sequential bell-first: L-BFGS-B only (skip slow DE)."""
import sys, time
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Bell-first: open from bell end toward reed
chart = []
for i in range(13):
    row = ["closed"] * (12 - i) + ["open"] * i + ["closed"]  # + register (closed)
    chart.append(row)

REG_POS = 80.0
REG_DIA = 2.5
REG_LEN = 3.0

def evaluate(x):
    free_pos = sorted(x)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
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

initial = [150, 250, 350, 450, 550, 650, 750, 850, 950, 1050, 1100, 1150]
print("=== 12-hole sequential bell-first (L-BFGS-B only) ===")
print("Initial cost: %.2fc" % evaluate(initial))

bounds = [(100, 1200)] * 12
for i in range(11):
    bounds[i] = (max(100, initial[i]-150), min(1200, initial[i]+150))

t0 = time.time()
r = minimize(evaluate, initial, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 300, 'ftol': 1e-8})
dt = time.time() - t0

print("Optimized: %.2fc (%.0fs)" % (r.fun, dt))
print("Positions: %s" % [round(p) for p in sorted(r.x)])

all_pos = sorted(list(r.x) + [REG_POS])
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]
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
