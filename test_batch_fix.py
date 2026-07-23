"""
Batch parallel test with BLAS thread fix.
MUST use if __name__ == '__main__': guard on Windows (spawn).
"""
import time
from backend.mp_cache import cache_clear
from backend.optimizer import BoreOptimizer


def main():
    cache_clear()
    targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]

    print("=== BATCH PARALLEL TEST (BLAS fix applied) ===")
    t0 = time.time()
    opt = BoreOptimizer(
        targets, n_control_points=8, pop_size=10, n_generations=3,
        n_workers=4, parallel_mode="batch",
    )
    r = opt.run(verbose=True)
    elapsed = time.time() - t0
    best = r["best_candidates"][0]["objectives"]
    rms = best["frequency_accuracy"]
    print(f"Done in {elapsed:.1f}s, RMS={rms:.2f} cents, mode={r['parallel_mode']}")


if __name__ == "__main__":
    main()
