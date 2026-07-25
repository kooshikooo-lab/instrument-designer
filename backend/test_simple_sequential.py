"""Simplest approach: reed-first sequential for 13 notes with 12 holes.

Each note opens one more hole from the reed end:
D2: all closed
D#2: H1
E2: H1+H2
...
D3: H1-H12 all open

This is the simplest possible chart. If this doesn't work, nothing will.
"""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Simplest chart: reed-first sequential, 13 notes, 12 holes
chart_raw = []
for i in range(13):
    row = [0]*12 + [0]  # 12 free + register
    for j in range(i):
        row[j] = 1
    chart_raw.append(row)
chart_str = [["open" if c else "closed" for c in row] for row in chart_raw]

print("Chart:")
for n, row in zip(names, chart_raw):
    pat = "".join("O" if x else "X" for x in row[:12])
    print("  %s: %s" % (n, pat))

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

# Even spacing initial guess
initial = [80 + i * 1130/13 for i in range(1, 13)]
print("\nInitial: %s" % [round(p) for p in initial])
print("Initial phase=%.6f freq=%.1fc" % (eval_phase(initial), eval_freq(initial)))

# Check individual phases
inst = make_inst(initial)
print("\nPhase check (initial):")
for i, (n, t) in enumerate(zip(names, targets)):
    wl = SPEED_OF_SOUND / t
    ph = inst.resonance_phase(wl, chart_str[i])
    print("  %s: phase=%.4f (want=1)" % (n, ph))

# Optimize
bounds = [(100, 1180)] * 12
for i in range(11):
    lo = max(100, initial[i] - 200)
    hi = min(1180, initial[i] + 200)
    if i > 0:
        lo = max(lo, bounds[i-1][0] + 10)
    bounds[i] = (lo, hi)

t0 = time.time()
de = differential_evolution(eval_phase, bounds, seed=42,
                             maxiter=50, popsize=12, tol=1e-6)
dt = time.time() - t0
print("\nDE: phase=%.6f freq=%.1fc (%.0fs)" % (de.fun, eval_freq(de.x), dt))
print("Holes: %s" % [round(p) for p in sorted(de.x)])

# L-BFGS-B
r = minimize(eval_phase, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-10})
dt2 = time.time() - t0
print("Final: phase=%.6f freq=%.1fc (%.0fs)" % (r.fun, eval_freq(r.x), dt2))
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
