"""
Compare NSGA-II vs scipy gradient-based optimization on clarinet Bb.

Tests:
1. Current NSGA-II approach (pymoo)
2. L-BFGS-B gradient-based approach (scipy.optimize)
3. Two-phase workflow (Noreland 2013)

Metrics: RMS cents error, wall time, convergence reliability
"""

import sys
import time
import numpy as np

sys.path.insert(0, ".")

# BLAS thread limits
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
BORE_LENGTH = 0.65  # ~650mm (Buffet R13 typical)


def test_scipy_lbfgsb():
    """Test L-BFGS-B gradient-based optimization."""
    from backend.v2_scipy_optimizer import ScipyBoreOptimizer
    
    print("\n" + "=" * 60)
    print("TEST: L-BFGS-B (gradient-based)")
    print("=" * 60)
    
    opt = ScipyBoreOptimizer(
        target_frequencies=TARGETS,
        n_control_points=12,
        bore_length=BORE_LENGTH,
    )
    
    t0 = time.time()
    result = opt.run(verbose=True, method="L-BFGS-B", maxiter=150)
    wall_time = time.time() - t0
    
    print(f"\n--- L-BFGS-B Results ---")
    print(f"  RMS cents: {result['final_rms_cents']:.2f}")
    print(f"  Global offset: {result['global_offset_cents']:.2f} cents")
    print(f"  Corrected errors: {[f'{e:.1f}' for e in result['corrected_errors_cents']]}")
    print(f"  Function evals: {result['function_evaluations']}")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Wall time: {wall_time:.1f}s")
    print(f"  Success: {result['success']}")
    
    return result


def test_scipy_nelder_mead():
    """Test Nelder-Mead (derivative-free but still single-objective)."""
    from backend.v2_scipy_optimizer import ScipyBoreOptimizer
    
    print("\n" + "=" * 60)
    print("TEST: Nelder-Mead (derivative-free)")
    print("=" * 60)
    
    opt = ScipyBoreOptimizer(
        target_frequencies=TARGETS,
        n_control_points=12,
        bore_length=BORE_LENGTH,
    )
    
    t0 = time.time()
    result = opt.run(verbose=True, method="Nelder-Mead", maxiter=300)
    wall_time = time.time() - t0
    
    print(f"\n--- Nelder-Mead Results ---")
    print(f"  RMS cents: {result['final_rms_cents']:.2f}")
    print(f"  Function evals: {result['function_evaluations']}")
    print(f"  Wall time: {wall_time:.1f}s")
    
    return result


def test_two_phase():
    """Test two-phase optimization (Noreland 2013)."""
    from backend.v2_scipy_optimizer import run_two_phase
    
    print("\n" + "=" * 60)
    print("TEST: Two-Phase Optimization (Noreland 2013)")
    print("=" * 60)
    
    t0 = time.time()
    result = run_two_phase(
        target_frequencies=TARGETS,
        n_control_points=12,
        bore_length=BORE_LENGTH,
        verbose=True,
    )
    wall_time = time.time() - t0
    
    print(f"\n--- Two-Phase Results ---")
    print(f"  RMS cents: {result['final_rms_cents']:.2f}")
    print(f"  Global offset: {result['global_offset_cents']:.2f} cents")
    print(f"  Wall time: {wall_time:.1f}s")
    
    return result


def test_nsga2():
    """Test current NSGA-II approach (for comparison)."""
    from backend.optimizer import BoreOptimizer
    
    print("\n" + "=" * 60)
    print("TEST: NSGA-II (current approach)")
    print("=" * 60)
    
    opt = BoreOptimizer(
        target_frequencies=TARGETS,
        n_control_points=12,
        bore_length=BORE_LENGTH,
        pop_size=30,
        n_generations=20,
        n_workers=1,
        parallel_mode="serial",
    )
    
    t0 = time.time()
    result = opt.run(verbose=True)
    wall_time = time.time() - t0
    
    # Extract best RMS from NSGA-II results
    if result.get("best_candidates"):
        best_rms = result["best_candidates"][0]["objectives"]["frequency_accuracy"]
    else:
        best_rms = float("inf")
    
    print(f"\n--- NSGA-II Results ---")
    print(f"  Best RMS cents: {best_rms:.2f}")
    print(f"  Wall time: {wall_time:.1f}s")
    print(f"  Evaluations: {result.get('n_evaluations', 'N/A')}")
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("OPTIMIZER COMPARISON: NSGA-II vs scipy.gradient vs Two-Phase")
    print("=" * 60)
    print(f"Target: Clarinet Bb (odd harmonics)")
    print(f"Targets: {TARGETS}")
    print(f"Bore length: {BORE_LENGTH*1000:.0f}mm")
    print(f"Control points: 12")
    
    # Run tests
    results = {}
    
    try:
        results["scipy_lbfgsb"] = test_scipy_lbfgsb()
    except Exception as e:
        print(f"L-BFGS-B FAILED: {e}")
        import traceback; traceback.print_exc()
    
    try:
        results["scipy_nelder"] = test_scipy_nelder_mead()
    except Exception as e:
        print(f"Nelder-Mead FAILED: {e}")
        import traceback; traceback.print_exc()
    
    try:
        results["two_phase"] = test_two_phase()
    except Exception as e:
        print(f"Two-phase FAILED: {e}")
        import traceback; traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, result in results.items():
        if result and "final_rms_cents" in result:
            print(f"  {name:20s}: {result['final_rms_cents']:.2f} cents, "
                  f"{result.get('wall_time', 0):.1f}s")
        elif result and "best_candidates" in result:
            best_rms = result["best_candidates"][0]["objectives"]["frequency_accuracy"]
            print(f"  {name:20s}: {best_rms:.2f} cents, "
                  f"{result.get('wall_time', 0):.1f}s")
