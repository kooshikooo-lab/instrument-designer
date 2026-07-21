"""
Minimal computation analysis — isolate what works and what doesn't.
"""
import sys, os, time
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from backend.v2_scipy_optimizer import (
    _objective_cents, _pava_isotonic,
    _compute_impedance_from_bore, _match_peaks_to_targets
)

TARGETS = np.array([261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6])
BORE_LEN = 0.65
N_CP = 12
N_FREQS = 1000
MRJ = (0.025 - 0.003) * 0.3
BOUNDS = [(0.003, 0.025)] * N_CP

R13 = np.array([0.00740, 0.00735, 0.00730, 0.00725, 0.00715, 0.00720,
                0.00725, 0.00730, 0.00735, 0.00740, 0.00745, 0.00750])

def obj(x):
    return _objective_cents(x, BORE_LEN, TARGETS, (50, 10500), N_FREQS, 20.0, N_CP, MRJ)

def report(x, label):
    radii = _pava_isotonic(x)
    bore = [(i * BORE_LEN/(N_CP-1), radii[i]) for i in range(N_CP)]
    result = _compute_impedance_from_bore(bore, (50, 10500), N_FREQS, 20.0)
    pf = result["peak_frequencies"]
    if isinstance(pf, np.ndarray): pf = pf.tolist()
    matched = _match_peaks_to_targets(np.array(pf), TARGETS)
    raw = np.array([m[3] for m in matched])
    off = np.median(raw)
    corr = np.abs(raw - off)
    rms = np.sqrt(np.mean(corr**2))
    print(f"  {label}: RMS={rms:.2f}c, offset={off:.1f}c, cost={obj(x):.1f}")
    for tf, act, _, c in matched:
        print(f"    {tf:.0f} -> {act:.0f} ({c:+.1f}c)")
    return rms

print("=" * 60)
print("STEP 1: Baseline costs")
print("=" * 60)
print(f"  Cylindrical (0.0074 uniform): {obj(np.full(N_CP, 0.0074)):.1f}")
print(f"  Buffet R13:                   {obj(R13):.1f}")

print("\n" + "=" * 60)
print("STEP 2: Baseline RMS")
print("=" * 60)
report(np.full(N_CP, 0.0074), "Cylindrical")
report(R13, "Buffet R13")

print("\n" + "=" * 60)
print("STEP 3: L-BFGS-B from R13 (maxiter=30)")
print("=" * 60)
from scipy.optimize import minimize
t0 = time.time()
r = minimize(obj, R13, method='L-BFGS-B', bounds=BOUNDS,
             options={'maxiter': 30, 'ftol': 1e-8, 'gtol': 1e-6})
dt = time.time() - t0
print(f"  Time: {dt:.1f}s, Evals: {r.nfev}, Iters: {r.nit}")
report(r.x, "L-BFGS-B from R13")

print("\n" + "=" * 60)
print("STEP 4: Nelder-Mead from R13 (maxiter=50)")
print("=" * 60)
t0 = time.time()
r2 = minimize(obj, R13, method='Nelder-Mead',
              options={'maxiter': 50, 'xatol': 1e-7, 'fatol': 1e-7})
dt = time.time() - t0
print(f"  Time: {dt:.1f}s, Evals: {r2.nfev}, Iters: {r2.nit}")
report(r2.x, "Nelder-Mead from R13")

print("\n" + "=" * 60)
print("COMPUTE REQUIREMENTS SUMMARY")
print("=" * 60)
print("  Each OpenWInD eval: ~1.9s (unique), ~0.0s (cached)")
print("  L-BFGS-B per iter: 25 evals = 47.5s (uncached)")
print("  Nelder-Mead per iter: ~13 evals = ~25s (uncached)")
print("  Key finding: initialization matters more than algorithm")
