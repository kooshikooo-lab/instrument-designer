import sys; sys.path.insert(0,'.')
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'

from backend.v2_scipy_optimizer import ScipyBoreOptimizer

targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
opt = ScipyBoreOptimizer(
    target_frequencies=targets,
    n_control_points=12,
    bore_length=0.65,
)
result = opt.run(verbose=True, method='L-BFGS-B', maxiter=50)
print(f'Final RMS: {result["final_rms_cents"]:.2f} cents')
print(f'Global offset: {result["global_offset_cents"]:.2f} cents')
print(f'Corrected errors: {[f"{e:.1f}" for e in result["corrected_errors_cents"]]}')
