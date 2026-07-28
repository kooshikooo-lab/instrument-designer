"""Cross-fingerings: start from best-known 47c chart, optimize with L-BFGS-B."""
import sys, time
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Cross-fingering chart from test_final_correct.py (best known: 47c)
chart = [
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
chart_str = [["open" if x else "closed" for x in row] for row in chart]

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
        freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    except:
        return 1000.0
    errs = []
    for t, f in zip(targets, freqs):
        c = 1200 * np.log2(f/t) if f > 0 else 1e10
        errs.append(c)
    e = np.array(errs)
    off = np.median(e)
    return np.sqrt(np.mean((e - off)**2))

# Start from best-known initial positions
initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]
print("=== Cross-fingering optimization ===")
print("Initial cost: %.2fc" % evaluate(initial))

# Wider bounds
bounds = [
    (100, 300),
    (200, 400),
    (280, 480),
    (350, 550),
    (450, 650),
    (530, 710),
    (580, 750),
    (630, 830),
    (700, 900),
    (770, 970),
    (840, 1050),
    (910, 1150),
]

t0 = time.time()
r = minimize(evaluate, initial, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 300, 'ftol': 1e-8})
dt = time.time() - t0

print("Optimized: %.2fc (%.0fs)" % (r.fun, dt))
print("Positions: %s" % [round(p) for p in sorted(r.x)])

# Detailed eval
all_pos = sorted(list(r.x) + [REG_POS])
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)

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
