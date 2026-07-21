import sys, os, time
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from backend.v2_scipy_optimizer import ScipyBoreOptimizer, _objective_cents

targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]

print("=" * 60)
print("TEST 1: L-BFGS-B (n_freqs=1000)")
print("=" * 60)

opt = ScipyBoreOptimizer(
    target_frequencies=targets,
    n_control_points=12,
    bore_length=0.65,
    n_freqs=1000,
)

# Time a single objective eval
x0 = opt._make_initial_guess("cylindrical")
t0 = time.time()
val = _objective_cents(x0, opt.bore_length, opt.target_freqs, opt.freq_range, opt.n_freqs, opt.temperature, opt.n_cp, opt.max_radius_jump)
print(f"Single eval: {time.time()-t0:.3f}s (objective={val:.2f})")

# L-BFGS-B with finite differences: 12 vars = 13 evals per iteration
print(f"Est. per iteration: ~{13 * (time.time()-t0):.1f}s")

t0 = time.time()
result = opt.run(verbose=True, method='L-BFGS-B', maxiter=20)
print(f"\nL-BFGS-B 20 iters: {result['final_rms_cents']:.2f} cents, "
      f"{result['function_evaluations']} evals, {time.time()-t0:.1f}s")

# Save result
import json
with open("chat-logs/v2-lbfgsb-result.json", "w") as f:
    json.dump({
        "method": "L-BFGS-B",
        "rms_cents": result['final_rms_cents'],
        "global_offset": result['global_offset_cents'],
        "corrected_errors": result['corrected_errors_cents'],
        "iterations": result['iterations'],
        "evaluations": result['function_evaluations'],
        "wall_time": time.time()-t0,
        "n_freqs": 1000,
        "n_cp": 12,
    }, f, indent=2)
