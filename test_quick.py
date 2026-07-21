"""Quick test of improved optimizer."""
import sys
sys.path.insert(0, r"C:\instrument-designer")
from backend.optimizer import BoreOptimizer

target = [277.4, 841.4, 1402.5, 1966.5]
opt = BoreOptimizer(target_frequencies=target, n_control_points=8, bore_length=0.300, pop_size=10, n_generations=5, seed=42)
result = opt.run(verbose=False)
print(f"Designs: {len(result['designs'])}")
for i, c in enumerate(result["best_candidates"][:2]):
    print(f"\nCandidate {i+1}: freq_err={c['objectives']['frequency_accuracy']:.1f}")
    for m in c["matched_frequencies"]:
        print(f"  {m['target']:7.1f} -> {m['actual']:7.1f} Hz ({m['error_cents']:+.1f} cents)")
