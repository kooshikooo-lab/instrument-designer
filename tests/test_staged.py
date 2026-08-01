import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

# QUARANTINED 2026-07-31: exercises backend.staged_optimizer, deleted from
# backend/archived_optimizers (docs/ARCHIVED_OPTIMIZERS.md). Superseded by
# backend/two_phase_optimizer.py. Kept for reference; not collected by pytest.
try:
    from backend.staged_optimizer import staged_optimize  # noqa: F401
except ModuleNotFoundError:
    raise SystemExit(
        "ARCHIVED: staged_optimizer.py was deleted on 2026-07-31 "
        "(see docs/ARCHIVED_OPTIMIZERS.md). Superseded by backend/two_phase_optimizer.py."
    )

from backend.target_frequencies import get_targets

# Test staged optimizer with KeefeLoss
targets = get_targets("clarinet_Bb", fundamental=233.1, n_notes=6)
print(f"Targets: {[f'{f:.1f}' for f in targets]}")

result = staged_optimize(
    target_frequencies=targets,
    n_control_points=12,
    pop_size=20,
    n_generations_per_stage=10,
    seed=42,
    verbose=True,
)

print(f"\nTotal evaluations: {result['total_evaluations']}")
if result["final_result"]:
    matched = result["final_result"]["matched_frequencies"]
    for m in matched:
        print(f"  {m['target']:.1f} Hz -> {m['actual']:.1f} Hz ({m['error_cents']:.1f} cents)")

print("\nStage history:")
for s in result["stages"]:
    print(f"  Stage {s['stage']}: {s['n_targets']} targets, {s['n_evaluations']} evals, {s['best_fitness']:.4f} cents")