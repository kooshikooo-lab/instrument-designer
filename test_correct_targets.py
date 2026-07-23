import sys, time, numpy as np
sys.path.insert(0, '.')
from backend.optimizer import BoreOptimizer
from backend.mp_cache import cache_clear
cache_clear()

clarinet_targets = [261.6 * i for i in [1, 3, 5, 7, 9, 11]]
print('Targets:', ['{:.1f}'.format(f) for f in clarinet_targets])

# pop=15, gen=10 = 150 evals, ~4 min
print('\n=== Test (pop=15, gen=10) ===')
t0 = time.time()
opt = BoreOptimizer(
    target_frequencies=clarinet_targets,
    n_control_points=12,
    pop_size=15,
    n_generations=10,
    n_workers=1,
)
result = opt.run(verbose=False)
t = time.time() - t0
print('Time: {:.1f}s'.format(t))

if result.get('best_candidates'):
    best = result['best_candidates'][0]
    print('Best RMS: {:.2f} cents'.format(best['objectives']['frequency_accuracy']))
    bore = best['bore_profile']
    radii = [p['radius'] for p in bore]
    print('Bore radii:', ['{:.4f}'.format(r) for r in radii])
    print()
    for m in best['matched_frequencies'][:8]:
        print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m['target'], m['actual'], m['error_cents']))
else:
    print('No valid candidates found')
