"""Test the bore optimizer with auto-calculated bore length."""
import sys
sys.path.insert(0, r"C:\instrument-designer")

from backend.optimizer import BoreOptimizer

# C major scale starting at C4
target_freqs = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]

optimizer = BoreOptimizer(
    target_frequencies=target_freqs,
    n_control_points=6,
    bore_length=None,  # auto-calculate from fundamental
    pop_size=15,
    n_generations=5,
    seed=42,
)

print(f"Auto-calculated bore length: {optimizer.bore_length:.3f} m")
print(f"Speed of sound: {331.3 + 0.606 * 20:.1f} m/s")
print(f"Fundamental target: {min(target_freqs):.1f} Hz")
print()

result = optimizer.run(verbose=False)
print(f"Pareto front size: {len(result['pareto_front'])}")
print(f"Total designs: {len(result['designs'])}")
print(f"Best candidates: {len(result['best_candidates'])}")
print()
for i, c in enumerate(result["best_candidates"]):
    obj = c["objectives"]
    print(f"Candidate {i+1}: freq_err={obj['frequency_accuracy']:.2f}, evenness={obj['scale_evenness']:.6f}, projection={obj['projection']:.2f}")
print()
print(f"Evaluations: {result['n_evaluations']}")
