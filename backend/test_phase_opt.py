"""Optimize 12-hole cross-fingerings using phase_cost_with_offset (smooth, reliable)."""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Cross-fingering chart from test_final_correct.py
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
chart_str = [["open" if x else "closed" for x in row] for row in chart_raw]

REG_POS = 80.0
REG_DIA = 2.5
REG_LEN = 3.0

def evaluate_phase(x):
    """Phase-based cost (smooth, reliable, no resonance tracking)."""
    free_pos = sorted(x)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    return inst.phase_cost_with_offset(targets, chart_str, n_register=1)

def evaluate_freq(x):
    """Frequency-based cost (for final evaluation only)."""
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
    errs = [1200*np.log2(f/t) if f>0 else 1e10 for t, f in zip(targets, freqs)]
    e = np.array(errs)
    off = np.median(e)
    return np.sqrt(np.mean((e - off)**2))

initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]
print("=== Phase-cost optimization (smooth) ===")
print("Initial phase_cost: %.6f" % evaluate_phase(initial))
print("Initial freq_cost: %.2fc" % evaluate_freq(initial))

# DE with small population (phase_cost is ~10x faster than freq)
t0 = time.time()
bounds = [(100, 1180)] * 12
for i in range(11):
    lo = max(100, initial[i] - 200)
    hi = min(1180, initial[i] + 200)
    if i > 0:
        lo = max(lo, bounds[i-1][0] + 10)
    bounds[i] = (lo, hi)

print("\nPhase 1: DE (12 vars, phase cost)")
de = differential_evolution(
    evaluate_phase, bounds, seed=42,
    maxiter=50, popsize=15,
    tol=1e-6, mutation=(0.5, 1.0), recombination=0.7,
    polish=False,
)
print("  DE phase_cost: %.6f (%.0fs)" % (de.fun, time.time()-t0))
print("  DE freq_cost: %.2fc" % evaluate_freq(de.x))
print("  Holes: %s" % [round(p) for p in sorted(de.x)])

# L-BFGS-B refinement
print("\nPhase 2: L-BFGS-B refinement")
r = minimize(evaluate_phase, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-10})
dt = time.time() - t0
print("  Final phase_cost: %.6f (%.0fs total)" % (r.fun, dt))
print("  Final freq_cost: %.2fc" % evaluate_freq(r.x))
print("  Holes: %s" % [round(p) for p in sorted(r.x)])

# Detailed frequency evaluation
free_pos = sorted(r.x)
all_pos = sorted(free_pos + [REG_POS])
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
