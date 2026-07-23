"""Quick test of phase-based resonance detection and L-BFGS-B optimizer."""
import sys
sys.path.insert(0, '.')
import time
from backend.v2_scipy_optimizer import (
    ScipyBoreOptimizer, _compute_impedance_from_bore, 
    _compute_phase_resonances, _match_peaks_to_targets, _pava_isotonic
)
import numpy as np

print("=" * 60)
print("TEST 1: Phase-based resonance detection")
print("=" * 60)

# Simple cylindrical bore
bore = [(0, 0.0074), (0.3, 0.0074), (0.65, 0.0074)]
result = _compute_impedance_from_bore(bore, freq_range=(50, 2000), n_freqs=1000, temperature=20.0)

freqs = np.asarray(result["frequencies"])
Z_complex = np.asarray(result["impedance_complex"])
peak_freqs = result["peak_frequencies"]

print(f"Peak frequencies: {peak_freqs[:6]}")

# Test with correct targets (odd harmonics)
targets = np.array([131.0, 393.0, 655.0])
phase_cost = _compute_phase_resonances(freqs, Z_complex, targets)
matched = _match_peaks_to_targets(peak_freqs, targets)
raw_cents = np.array([m[3] for m in matched])
print(f"Targets: {targets}")
print(f"Phase cost: {phase_cost:.6e}")
print(f"Cents errors: {raw_cents}")

# Test with wrong targets
bad_targets = np.array([200.0, 500.0, 800.0])
phase_cost_bad = _compute_phase_resonances(freqs, Z_complex, bad_targets)
matched_bad = _match_peaks_to_targets(peak_freqs, bad_targets)
raw_cents_bad = np.array([m[3] for m in matched_bad])
print(f"\nBad targets: {bad_targets}")
print(f"Phase cost: {phase_cost_bad:.6e}")
print(f"Cents errors: {raw_cents_bad}")

print("\n" + "=" * 60)
print("TEST 2: L-BFGS-B (5 iterations)")
print("=" * 60)

targets_opt = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
opt = ScipyBoreOptimizer(
    target_frequencies=targets_opt,
    n_control_points=12,
    bore_length=0.65,
    n_freqs=1000,
)

t0 = time.time()
result = opt.run(verbose=True, method='L-BFGS-B', maxiter=5, initial_guess='cylindrical')
wall_time = time.time() - t0

print(f"\nFinal RMS: {result['final_rms_cents']:.2f} cents")
print(f"Objective: {result['best_objective']:.4f}")
print(f"Function evals: {result['function_evaluations']}")
print(f"Wall time: {wall_time:.1f}s")
print(f"Matched peaks:")
for m in result["matched_frequencies"]:
    print(f"  {m['target']:.1f} -> {m['actual']:.1f} Hz ({m['error_cents']:.1f} cents)")
