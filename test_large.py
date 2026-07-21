import sys, time, numpy as np
sys.path.insert(0, '.')
from backend.optimizer import BoreOptimizer
from backend.mp_cache import cache_clear
cache_clear()

clarinet_targets = [261.6 * i for i in [1, 3, 5, 7, 9, 11]]
print('Targets:', ['{:.1f}'.format(f) for f in clarinet_targets])

# Large test: pop=40, gen=50 = 2000 evals, serial
print('\n=== SERIAL: pop=40, gen=50 ===')
t0 = time.time()
opt = BoreOptimizer(
    target_frequencies=clarinet_targets,
    n_control_points=12,
    pop_size=40,
    n_generations=50,
    n_workers=1,
)
result = opt.run(verbose=False)
t_ser = time.time() - t0
print('Time: {:.1f}s ({:.1f} min)'.format(t_ser, t_ser/60))
if result.get('best_candidates'):
    best = result['best_candidates'][0]
    print('Best RMS: {:.2f} cents'.format(best['objectives']['frequency_accuracy']))
    for m in best['matched_frequencies'][:8]:
        print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m['target'], m['actual'], m['error_cents']))
else:
    print('No valid candidates')

# Now parallel test
from backend.mp_cache import cache_clear
cache_clear()
print('\n=== PARALLEL: pop=40, gen=50, 6 workers ===')
t0 = time.time()
opt2 = BoreOptimizer(
    target_frequencies=clarinet_targets,
    n_control_points=12,
    pop_size=40,
    n_generations=50,
    n_workers=6,
)
result2 = opt2.run(verbose=False)
t_par = time.time() - t0
print('Time: {:.1f}s ({:.1f} min)'.format(t_par, t_par/60))
if result2.get('best_candidates'):
    best2 = result2['best_candidates'][0]
    print('Best RMS: {:.2f} cents'.format(best2['objectives']['frequency_accuracy']))
    for m in best2['matched_frequencies'][:8]:
        print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m['target'], m['actual'], m['error_cents']))
else:
    print('No valid candidates')

print('\n=== SPEEDUP ===')
print('Serial: {:.1f} min'.format(t_ser/60))
print('Parallel: {:.1f} min'.format(t_par/60))
print('Speedup: {:.2f}x'.format(t_ser/t_par))
