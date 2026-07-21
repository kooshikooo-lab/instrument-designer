"""Test improved bore optimizer."""
import sys
sys.path.insert(0, r"C:\instrument-designer")

from backend.optimizer import BoreOptimizer
import numpy as np

# Test 1: Penny Whistle D (simplest case)
print("=" * 60)
print("TEST 1: Penny Whistle D")
print("=" * 60)

# Cylindrical bore, fundamental ~277 Hz (first peak of closed-open 300mm pipe)
target_freqs = [277.4, 841.4, 1402.5, 1966.5]

optimizer = BoreOptimizer(
    target_frequencies=target_freqs,
    n_control_points=8,
    bore_length=0.300,
    min_radius=0.005,
    max_radius=0.012,
    pop_size=30,
    n_generations=30,
    seed=42,
)

print(f"Bore length: {optimizer.bore_length:.3f} m")
print(f"Freq range: {optimizer.freq_range}")
print(f"Running...")
result = optimizer.run(verbose=False)

print(f"\nResults: {len(result['designs'])} designs, {result['n_evaluations']} evaluations")
for i, c in enumerate(result["best_candidates"]):
    obj = c["objectives"]
    print(f"\nCandidate {i+1}:")
    print(f"  freq_err={obj['frequency_accuracy']:.1f} cents, evenness={obj['scale_evenness']:.4f}, projection={obj['projection']:.2f}")
    for m in c["matched_frequencies"]:
        print(f"  {m['target']:7.1f} Hz -> {m['actual']:7.1f} Hz  ({m['error_cents']:+.1f} cents)")

# Test 2: Clarinet Bb (harder - needs more control points)
print("\n" + "=" * 60)
print("TEST 2: Clarinet Bb")
print("=" * 60)

target_freqs2 = [129.7, 389.6, 649.4, 909.3, 1166.2]

optimizer2 = BoreOptimizer(
    target_frequencies=target_freqs2,
    n_control_points=12,
    bore_length=0.660,
    min_radius=0.005,
    max_radius=0.012,
    pop_size=30,
    n_generations=30,
    seed=42,
)

print(f"Bore length: {optimizer2.bore_length:.3f} m")
print(f"Running...")
result2 = optimizer2.run(verbose=False)

print(f"\nResults: {len(result2['designs'])} designs")
for i, c in enumerate(result2["best_candidates"][:2]):
    obj = c["objectives"]
    print(f"\nCandidate {i+1}:")
    print(f"  freq_err={obj['frequency_accuracy']:.1f} cents, evenness={obj['scale_evenness']:.4f}")
    for m in c["matched_frequencies"]:
        print(f"  {m['target']:7.1f} Hz -> {m['actual']:7.1f} Hz  ({m['error_cents']:+.1f} cents)")
