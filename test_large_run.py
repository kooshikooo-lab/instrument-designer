"""
Large accuracy test: pop=40, gen=50, batch parallel.
Requires if __name__ == '__main__': guard on Windows (spawn).
Uses BLAS thread fix from laptop's bore_optimizer.py update.
"""
import sys
sys.path.insert(0, '.')
import time


def main():
    from backend.mp_cache import cache_clear
    from backend.bore_optimizer import BoreOptimizer

    cache_clear()
    print("Cache cleared. Starting pop=40, gen=50 test...")
    targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
    opt = BoreOptimizer(
        targets, n_control_points=12, pop_size=40, n_generations=50,
        n_workers=6, parallel_mode='batch',
    )
    start = time.time()
    r = opt.run(verbose=True)
    elapsed = time.time() - start
    best = r['best_candidates'][0]
    obj = best['objectives']
    print()
    print("=== RESULT ===")
    print(f"Wall time: {elapsed:.1f}s")
    print(f"N evaluations: {r.get('n_evaluations', '?')}")
    print(f"RMS accuracy: {obj['frequency_accuracy']:.4f} cents")
    print(f"Scale evenness: {obj['scale_evenness']:.6f}")
    print(f"Projection: {obj['projection']:.4f}")
    print()
    for m in best['matched_frequencies']:
        print(f"  {m['target']:7.1f} -> {m['actual']:7.1f}  ({m['error_cents']:+.2f} cents)")
    print()
    print(f"Bore length: {r.get('bore_length', 0)*1000:.0f}mm")
    bp = best.get('bore_profile', [])
    if bp:
        print(f"Bore profile points: {len(bp)}")
        print(f"  Entry radius: {bp[0]['radius']*1000:.2f}mm")
        print(f"  Exit radius:  {bp[-1]['radius']*1000:.2f}mm")


if __name__ == '__main__':
    main()
