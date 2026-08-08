"""Metamaterial design-knob optimization benchmark for low clarinets.

Runs the MetamaterialOptimizer across the low clarinet family and
compares optimized designs against the baseline tuned designs from
the family benchmark.

Run: python scripts/benchmark_metamaterial_optimization.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.optimization.metamaterial_optimizer import (
    optimize_family,
    print_family_results,
)
from backend.metamaterial_low_clarinets import LOW_CLARINETS

OUT = os.path.join("test_output", "metamaterial_optimization_results.json")


def compare_with_baseline(optimized):
    """Compare optimized designs with the baseline from the family benchmark."""
    baseline_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test_output", "metamaterial_low_clarinet_benchmark_results.json",
    )
    if not os.path.exists(baseline_path):
        print("  No baseline found; skipping comparison.")
        return

    with open(baseline_path) as fh:
        baseline = json.load(fh)

    print()
    print("=" * 90)
    print("COMPARISON: baseline tuned designs vs optimized designs")
    print("=" * 90)
    print(f"{'key':<16} {'metric':<20} {'baseline':>10} {'optimized':>10} {'delta':>10}")
    print("-" * 90)
    for key, opt in optimized.items():
        b = baseline.get("tuned", {}).get(key, {})
        if not b:
            continue
        # f1 accuracy
        b_f1 = b.get("f1_l1", 0)
        o_f1 = opt.achieved_f1
        b_cents = b.get("cents", 0)
        o_cents = opt.cents_error
        print(f"{key:<16} {'f1 (Hz)':<20} {b_f1:>10.2f} {o_f1:>10.2f} {o_f1 - b_f1:>+10.2f}")
        print(f"{key:<16} {'f1 cents err':<20} {b_cents:>+10.1f} {o_cents:>+10.1f} {o_cents - b_cents:>+10.1f}")
        # 12th deviation
        b_12th = b.get("twelfth_cents", 0)
        o_12th = opt.twelfth_cents
        print(f"{key:<16} {'12th cents':<20} {b_12th:>+10.1f} {o_12th:>+10.1f} {o_12th - b_12th:>+10.1f}")
        # cavity volume
        b_cav = b.get("cavity_v_mm3", 0)
        o_cav = opt.cavity_v_mm3
        print(f"{key:<16} {'cavity V(mm3)':<20} {b_cav:>10.0f} {o_cav:>10.0f} {o_cav - b_cav:>+10.0f}")
        # coverage
        b_lo = b.get("sb_lo")
        b_hi = b.get("sb_hi")
        b_cov = (b_hi - b_lo) if (b_lo and b_hi) else 0
        o_cov = opt.coverage_hz
        print(f"{key:<16} {'stopband Hz':<20} {b_cov:>10.0f} {o_cov:>10.0f} {o_cov - b_cov:>+10.0f}")
        print()


def main():
    print("Running metamaterial optimization across the low clarinet family...")
    print("(DE global + L-BFGS-B refinement, ~2 min per instrument)")
    print()

    optimized = optimize_family(max_time_seconds=60.0)
    print_family_results(optimized)
    compare_with_baseline(optimized)

    out = {}
    for key, r in optimized.items():
        out[key] = {
            "target_hz": r.target_hz,
            "achieved_f1": r.achieved_f1,
            "cents_error": r.cents_error,
            "twelfth_cents": r.twelfth_cents,
            "coverage_hz": r.coverage_hz,
            "cavity_v_mm3": r.cavity_v_mm3,
            "n_resonators": r.n_resonators,
            "best_f0": r.best_f0,
            "best_spacing": r.best_spacing,
            "best_neck_r": r.best_neck_r,
            "best_neck_l": r.best_neck_l,
            "best_start_frac": r.best_start_frac,
            "stopband_lo": r.stopband_lo,
            "stopband_hi": r.stopband_hi,
            "cost": r.cost,
            "rms_cents": r.rms_cents,
            "wall_time": r.wall_time,
            "n_evaluations": r.n_evaluations,
        }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n  JSON -> {OUT}")


if __name__ == "__main__":
    main()