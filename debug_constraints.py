import sys, numpy as np
sys.path.insert(0, '.')
from backend.optimizer import BoreOptimizationProblem, _IMPEDANCE_CACHE
_IMPEDANCE_CACHE.clear()

freqs = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]

problem = BoreOptimizationProblem(
    target_frequencies=freqs,
    n_control_points=12,
)

print('n_ieq_constr:', problem.n_ieq_constr)
print('n_var:', problem.n_var)

# Test 1: manually create a valid monotonic bore
x_monotonic = np.linspace(0.005, 0.015, 12)
out = {}
problem._evaluate(x_monotonic, out)
print('\nMonotonic test:')
print('  F:', out['F'])
print('  G (should be <= 0):', out['G'])
print('  Any G > 0 (violations):', np.any(out['G'] > 0))

# Test 2: non-monotonic bore (should violate)
x_bad = np.array([0.015]*6 + [0.005]*6)
out2 = {}
problem._evaluate(x_bad, out2)
print('\nNon-monotonic test:')
print('  F:', out2['F'])
print('  G violations:', out2['G'][out2['G'] > 0])
print('  # violations:', np.sum(out2['G'] > 0))

# Test 3: what does random sampling produce?
from pymoo.operators.sampling.rnd import FloatRandomSampling
sampling = FloatRandomSampling()
X = sampling(problem, 5)
print('\nRandom samples (5):')
for i in range(5):
    x = X[i]
    violations = sum(1 for j in range(len(x)-1) if x[j] > x[j+1])
    jumps = [abs(x[j+1] - x[j]) for j in range(len(x)-1)]
    print('  sample {}: monotonic_violations={}, max_jump={:.4f}'.format(i, violations, max(jumps)))
