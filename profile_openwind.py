"""Profile single OpenWInD evaluation time."""
import sys, os, time
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from backend.v2_scipy_optimizer import _compute_impedance_from_bore, _pava_isotonic

bore_length = 0.65
n_cp = 12
positions = np.linspace(0, bore_length, n_cp)
radii = np.full(n_cp, 0.0074)  # cylindrical bore
bore = list(zip(positions.tolist(), radii.tolist()))

freq_range = (50, 10500)
n_freqs = 5000

print("Profiling single OpenWInD evaluation...")
print(f"  Bore: {n_cp} control points, {bore_length*1000:.0f}mm length")
print(f"  Freq range: {freq_range}, {n_freqs} points")

# Warm up
_compute_impedance_from_bore(bore, freq_range=freq_range, n_freqs=n_freqs)

# Time 5 evaluations
times = []
for i in range(5):
    t0 = time.time()
    result = _compute_impedance_from_bore(bore, freq_range=freq_range, n_freqs=n_freqs)
    t1 = time.time()
    dt = t1 - t0
    times.append(dt)
    print(f"  Eval {i+1}: {dt:.3f}s, {len(result['peak_frequencies'])} peaks found")

avg = np.mean(times)
print(f"\nAverage: {avg:.3f}s per evaluation")
print(f"L-BFGS-B (12 CP, forward diff): {13*avg:.1f}s per iteration")
print(f"L-BFGS-B 10 iters: {10*13*avg:.1f}s total")
print(f"L-BFGS-B 50 iters: {50*13*avg:.1f}s total")
print(f"Nelder-Mead 100 iters (~200 evals): {200*avg:.1f}s total")
print(f"differential_evolution (pop=15, 50 gen): {15*50*avg:.1f}s total")
