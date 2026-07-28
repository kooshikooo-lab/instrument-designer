"""Actual compute measurement — no cache."""
import sys
sys.path.insert(0, '.')
import time
import numpy as np
from backend.mp_cache import cache_clear
from backend.bore_optimizer import _compute_impedance_from_bore

cache_clear()
v = 331.3 + 0.606 * 20.0
bl = v / (4 * 261.6)
print("Bore length: %.0fmm" % (bl * 1000))

# Warm up
print("Warming up OpenWInD (first import)...")
t0 = time.time()
r = np.full(6, 0.010)
p = np.linspace(0, bl, 6)
bore = list(zip(p.tolist(), r.tolist()))
_compute_impedance_from_bore(bore, (50, 3000), 5000, 20.0)
print("Warmup: %.1fs" % (time.time() - t0))

# Measure uncached evals
for n_cp in [6, 8, 12]:
    cache_clear()
    p = np.linspace(0, bl, n_cp)
    times = []
    for i in range(3):
        r = np.full(n_cp, 0.010)
        bore = list(zip(p.tolist(), r.tolist()))
        t0 = time.time()
        _compute_impedance_from_bore(bore, (50, 3000), 5000, 20.0)
        elapsed = time.time() - t0
        times.append(elapsed)
        print("  %d CP eval %d: %.3fs" % (n_cp, i+1, elapsed))
    avg = np.mean(times)
    print("%d CP: %.3fs avg per eval" % (n_cp, avg))

# Gradient cost estimate
print()
print("=== GRADIENT COST (centered finite differences) ===")
for n_cp in [6, 12]:
    # Cost per L-BFGS-B iteration = (2*n_cp + 1) evals
    evals_per_iter = 2 * n_cp + 1
    cache_clear()
    p = np.linspace(0, bl, n_cp)
    t0 = time.time()
    for i in range(evals_per_iter):
        r = np.random.uniform(0.005, 0.015, n_cp)
        bore = list(zip(p.tolist(), r.tolist()))
        _compute_impedance_from_bore(bore, (50, 3000), 5000, 20.0)
    iter_time = time.time() - t0
    print("%d CP: %d evals/iter = %.1fs per iteration" % (n_cp, evals_per_iter, iter_time))
