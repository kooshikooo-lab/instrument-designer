import sys, os, time
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

print("Step 1: Import numpy...")
t0 = time.time()
import numpy as np
print(f"  Done ({time.time()-t0:.1f}s)")

print("Step 2: Import scipy...")
t0 = time.time()
from scipy.optimize import minimize
print(f"  Done ({time.time()-t0:.1f}s)")

print("Step 3: Import openwind...")
t0 = time.time()
from openwind import ImpedanceComputation
print(f"  Done ({time.time()-t0:.1f}s)")

print("Step 4: Create bore and compute...")
t0 = time.time()
freqs = np.linspace(50, 10500, 5000)
bore_str = "test_bore.csv"
with open(bore_str, 'w') as f:
    for i in range(12):
        f.write(f"{i * 0.65/11} 0.0074\n")
ic = ImpedanceComputation(freqs, bore_str, unit="m", diameter=False, temperature=20.0)
freq = np.array(ic.frequencies)
Z = np.array(ic.impedance)
print(f"  Done ({time.time()-t0:.1f}s), shape={Z.shape}")

print("Step 5: Import PAVA...")
t0 = time.time()
from backend.v2_scipy_optimizer import _pava_isotonic
print(f"  Done ({time.time()-t0:.1f}s)")

print("Step 6: Test PAVA...")
t0 = time.time()
x = np.random.uniform(0.003, 0.025, 12)
result = _pava_isotonic(x)
print(f"  Done ({time.time()-t0:.1f}s), result shape={result.shape}")

print("Step 7: Test objective function...")
t0 = time.time()
from backend.v2_scipy_optimizer import _objective_cents, _compute_impedance_from_bore
target_freqs = np.array([261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6])
bore_length = 0.65
freq_range = (50, 10500)
n_freqs = 5000
temperature = 20.0
n_cp = 12
max_radius_jump = (0.025 - 0.003) * 0.3
val = _objective_cents(x, bore_length, target_freqs, freq_range, n_freqs, temperature, n_cp, max_radius_jump)
print(f"  Done ({time.time()-t0:.1f}s), value={val:.2f}")

print("\nAll steps passed!")
os.remove(bore_str)
