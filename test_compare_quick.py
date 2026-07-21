"""Quick optimizer comparison: 6 control points, small evals."""
import sys
sys.path.insert(0, '.')
import time
import numpy as np
from backend.bore_optimizer_lbfgs import _pava_isotonic, _compute_impedance, _match_peaks
from scipy.optimize import minimize, differential_evolution

TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
N_CP = 6
MIN_R = 0.003
MAX_R = 0.025
FREQ_RANGE = (50, 3000)

v = 331.3 + 0.606 * 20.0
BORE_LEN = v / (4 * min(TARGETS))
positions = np.linspace(0, BORE_LEN, N_CP)
print("Bore length: {:.0f}mm, {} control points".format(BORE_LEN * 1000, N_CP))


def objective(radii):
    radii = np.clip(radii, MIN_R, MAX_R)
    radii = _pava_isotonic(radii)
    bore = list(zip(positions.tolist(), radii.tolist()))
    peak_freqs, _ = _compute_impedance(bore, FREQ_RANGE, 5000, 20.0)
    if len(peak_freqs) < 2:
        return 1e10
    matched = _match_peaks(peak_freqs, TARGETS)
    raw_cents = np.array([m[3] for m in matched])
    offset = np.median(raw_cents)
    corrected = np.abs(raw_cents - offset)
    return float(np.sqrt(np.mean(corrected ** 2)))


bounds = [(MIN_R, MAX_R)] * N_CP
x0 = np.full(N_CP, 0.010)

# Test 1: L-BFGS-B (25 evals/iter for 12 vars, now 13 for 6)
print("\n--- L-BFGS-B (maxiter=30) ---")
t0 = time.time()
r1 = minimize(objective, x0, method='L-BFGS-B', jac='2-point', bounds=bounds,
              options={'maxiter': 30, 'ftol': 1e-12})
t1 = time.time() - t0
radii1 = _pava_isotonic(np.clip(r1.x, MIN_R, MAX_R))
print("  {:.4f} cents, {} evals, {:.1f}s".format(r1.fun, r1.nfev, t1))
print("  Bore: entry={:.2f}mm exit={:.2f}mm".format(radii1[0]*1000, radii1[-1]*1000))

# Test 2: CMA-ES (pop=10, 300 evals max)
print("\n--- CMA-ES (pop=10, maxfevals=300) ---")
import cma
t0 = time.time()
res = cma.fmin2(objective, [0.010]*N_CP, 0.003, {
    'bounds': [MIN_R, MAX_R], 'verbose': -9,
    'maxfevals': 300, 'popsize': 10,
})
t2 = time.time() - t0
radii2 = _pava_isotonic(np.clip(np.array(res[0]), MIN_R, MAX_R))
print("  {:.4f} cents, {} evals, {:.1f}s".format(res[1].fbest, res[1].countevals, t2))
print("  Bore: entry={:.2f}mm exit={:.2f}mm".format(radii2[0]*1000, radii2[-1]*1000))

# Test 3: DE (popsize=8, maxiter=10)
print("\n--- DE (popsize=8, maxiter=10) ---")
t0 = time.time()
r3 = differential_evolution(objective, bounds, strategy='best1bin',
                            maxiter=10, popsize=8, tol=1e-8, seed=42, polish=False)
t3 = time.time() - t0
radii3 = _pava_isotonic(np.clip(r3.x, MIN_R, MAX_R))
print("  {:.4f} cents, {} evals, {:.1f}s".format(r3.fun, r3.nfev, t3))
print("  Bore: entry={:.2f}mm exit={:.2f}mm".format(radii3[0]*1000, radii3[-1]*1000))

# Summary
print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
results = [
    ("L-BFGS-B (30 iter)", r1.fun, r1.nfev, t1),
    ("CMA-ES (300 evals)", res[1].fbest, res[1].countevals, t2),
    ("DE (10 iter)", r3.fun, r3.nfev, t3),
]
print("  {:<25} {:>12} {:>8} {:>8}".format("Method", "RMS(cents)", "Evals", "Time(s)"))
print("  " + "-" * 53)
for name, rms, ev, t in sorted(results, key=lambda x: x[1]):
    print("  {:<25} {:>12.4f} {:>8} {:>8.1f}".format(name, rms, ev, t))
