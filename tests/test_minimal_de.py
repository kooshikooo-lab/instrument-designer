"""GlobalFingeringOptimizer with minimal DE: popsize=8, maxiter=5."""
import sys, time
import numpy as np
sys.path.insert(0, '.')
from optimizer_global import GlobalFingeringOptimizer

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

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

initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart_str,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=[(80.0, 2.5, 3.0)],
    register_weights=(0.15, 1.0),
    optimize_grad=True,
    grad_bounds=(6.0, 12.0, 16.0, 22.0),
)

# Manually run DE with smaller params
from scipy.optimize import differential_evolution

n_free = 12
bounds = []
for i in range(n_free):
    lo = max(8, initial[i] - 200)
    if i > 0:
        lo = max(lo, bounds[-1][0] + 8)
    hi = min(1211.3 - 8, initial[i] + 200)
    if i < n_free - 1:
        hi = min(hi, initial[i+1] + 200 - 8)
    bounds.append((lo, hi))

# Graduated diameters bounds
bounds.append((6.0, 12.0))
bounds.append((16.0, 22.0))
initial_ext = list(initial) + [9.0, 19.0]

print("=== Minimal DE: popsize=8, maxiter=10 ===")
print("Variables: %d (12 holes + 2 diameters)" % len(bounds))
t0 = time.time()
de = differential_evolution(
    opt._objective, bounds, x0=initial_ext,
    seed=42, maxiter=10, popsize=8,
    tol=1e-4, mutation=(0.5, 1.0), recombination=0.7,
    polish=False,
)
dt = time.time() - t0
print("DE done: cost=%.4f (%.0fs)" % (de.fun, dt))

# L-BFGS-B refinement
from scipy.optimize import minimize
r = minimize(opt._objective, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-8})
dt2 = time.time() - t0
print("L-BFGS-B done: cost=%.4f (total %.0fs)" % (r.fun, dt2))

# Extract results
free_pos = sorted(r.x[:-2])
grad_d = r.x[-2:]
print("Holes: %s" % [round(p) for p in free_pos])
print("Diameters: d_min=%.1f d_max=%.1f" % (grad_d[0], grad_d[1]))

# Full eval with both registers
all_pos = sorted(free_pos + [80.0])
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
d_min, d_max = grad_d
n_free = 12
dias = [d_min + (d_max - d_min) * i / (n_free - 1) for i in range(n_free)]
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [d/2.0 for d in dias] + [2.5/2.0],
    [5.0]*12 + [3.0], 37.0, closed_top=True, cone_step=0.5
)
chal_chart = [row[:12] + ["closed"] for row in chart_str]
wl = [SPEED_OF_SOUND/t for t in targets]
freqs1 = inst.compute_fingered_frequencies(wl, chal_chart, n_register=1)

print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
errs = []
for n, t, f in zip(names, targets, freqs1):
    c = 1200*np.log2(f/t) if f>0 else 0
    errs.append(c)
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, f, c))
e = np.array(errs)
off = np.median(e)
rms = np.sqrt(np.mean((e - off)**2))
print("\nReg1 RMS=%.2fc offset=%+.1fc" % (rms, off))
