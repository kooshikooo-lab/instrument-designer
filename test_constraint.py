import sys, numpy as np
sys.path.insert(0, '.')
from backend.optimizer import BoreOptimizationProblem, MonotonicRepair, _IMPEDANCE_CACHE
_IMPEDANCE_CACHE.clear()

freqs = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]
problem = BoreOptimizationProblem(target_frequencies=freqs, n_control_points=12)
repair = MonotonicRepair()

# Test PAVA repair on random samples
np.random.seed(42)
print('PAVA repair test:')
for trial in range(3):
    x = np.random.uniform(0.003, 0.025, 12)
    print('\n  Before: ', ['{:.4f}'.format(v) for v in x])
    X = x.reshape(1, -1)
    X_repaired = repair._do(problem, X.copy())
    r = X_repaired[0]
    print('  After:  ', ['{:.4f}'.format(v) for v in r])
    mono_ok = all(r[i] <= r[i+1] for i in range(len(r)-1))
    print('  Monotonic: {} | Range: {:.4f} to {:.4f}'.format(mono_ok, r[0], r[-1]))

# Now run a larger optimization: pop=20, gen=15 with constraint
print('\n\n=== Running optimizer (pop=20, gen=15) ===')
from backend.optimizer import BoreOptimizer
_IMPEDANCE_CACHE.clear()
import time
t0 = time.time()
opt = BoreOptimizer(
    target_frequencies=freqs,
    n_control_points=12,
    pop_size=20,
    n_generations=15,
    n_workers=1,
)
result = opt.run(verbose=False)
t = time.time() - t0
print('Time: {:.1f}s'.format(t))
if result.get('best_candidates'):
    best = result['best_candidates'][0]
    print('Best RMS: {:.2f} cents'.format(best['objectives']['frequency_accuracy']))
    for m in best['matched_frequencies'][:8]:
        print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m['target'], m['actual'], m['error_cents']))
else:
    print('No valid candidates')
