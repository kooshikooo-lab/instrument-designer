"""Run benchmark matching laptop's 3.11 cent result."""
import sys
sys.path.insert(0, ".")
from backend.optimizer import BoreOptimizer

opt = BoreOptimizer(
    [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6],
    n_control_points=6, pop_size=15, n_generations=10,
    seed=42,
)
r = opt.run()
best = r["best_candidates"][0]
print("Accuracy:", best["objectives"])
print("Matches:")
for m in best["matched_frequencies"]:
    print(f'  {m["target"]:.1f} -> {m["actual"]:.1f} ({m["error_cents"]:+.1f} cents)')
