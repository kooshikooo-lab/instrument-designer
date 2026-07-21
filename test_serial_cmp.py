"""Quick serial comparison test."""
import sys
sys.path.insert(0, '.')
import time


def main():
    from backend.mp_cache import cache_clear
    from backend.bore_optimizer import BoreOptimizer

    cache_clear()
    targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]

    print("=== SERIAL TEST (pop=15, gen=10) ===")
    t0 = time.time()
    opt = BoreOptimizer(
        targets, n_control_points=12, pop_size=15, n_generations=10,
        n_workers=1, parallel_mode='serial',
    )
    r = opt.run(verbose=True)
    elapsed = time.time() - t0
    best = r['best_candidates'][0]
    obj = best['objectives']
    print(f"\nSerial: {elapsed:.1f}s, RMS={obj['frequency_accuracy']:.4f} cents")
    for m in best['matched_frequencies']:
        print(f"  {m['target']:7.1f} -> {m['actual']:7.1f}  ({m['error_cents']:+.2f} cents)")


if __name__ == '__main__':
    main()
