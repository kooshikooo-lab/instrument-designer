"""Optimize with phase_cost (NOT phase_cost_with_offset) to prevent register mismatch."""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Best chart from earlier tests
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
REG_DIA = 2.5
REG_LEN = 3.0

def make_inst(x):
    free_pos = sorted(x)
    all_pos = sorted(free_pos + [REG_POS])
    return tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )

def eval_phase(x):
    inst = make_inst(x)
    return inst.phase_cost(targets, chart_str, n_register=1)

def eval_freq(x):
    inst = make_inst(x)
    wl = [SPEED_OF_SOUND/t for t in targets]
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    except:
        return 1000.0
    errs = [1200*np.log2(f/t) if f>0 else 1e10 for t, f in zip(targets, freqs)]
    e = np.array(errs)
    off = np.median(e)
    return np.sqrt(np.mean((e - off)**2))

# Test: verify that phase_cost distinguishes registers
print("=== Register check ===")
initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]
p1 = eval_phase(initial)
f1 = eval_freq(initial)
print("Initial: phase_cost=%.6f freq_cost=%.1fc" % (p1, f1))

# Check individual phases
inst = make_inst(initial)
for n, t in zip(names, targets):
    wl = SPEED_OF_SOUND / t
    ph = inst.resonance_phase(wl, chart_str[names.index(n)])
    print("  %s: target=%.1fHz phase=%.4f (want=1)" % (n, t, ph))

print("\n=== Optimization with phase_cost (register-aware) ===")
bounds = [(100, 1180)] * 12
for i in range(11):
    lo = max(100, initial[i] - 200)
    hi = min(1180, initial[i] + 200)
    if i > 0:
        lo = max(lo, bounds[i-1][0] + 10)
    bounds[i] = (lo, hi)

t0 = time.time()
de = differential_evolution(eval_phase, bounds, seed=42,
                             maxiter=30, popsize=10, tol=1e-6)
dt = time.time() - t0
print("DE: phase=%.6f freq=%.1fc (%.0fs)" % (de.fun, eval_freq(de.x), dt))
print("Holes: %s" % [round(p) for p in sorted(de.x)])

r = minimize(eval_phase, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-10})
dt2 = time.time() - t0
print("L-BFGS-B: phase=%.6f freq=%.1fc (%.0fs)" % (r.fun, eval_freq(r.x), dt2))
print("Holes: %s" % [round(p) for p in sorted(r.x)])

# Detailed
inst = make_inst(r.x)
wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
errs = []
for n, t, f in zip(names, targets, freqs):
    c = 1200*np.log2(f/t) if f>0 else 0
    errs.append(c)
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, f, c))
e = np.array(errs)
off = np.median(e)
rms = np.sqrt(np.mean((e - off)**2))
print("\nRMS=%.2fc offset=%+.1fc" % (rms, off))
