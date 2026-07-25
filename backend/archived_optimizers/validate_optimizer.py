"""
Validation: Test optimizer against known instrument designs.

For each reference instrument:
1. Compute its impedance peaks (ground truth)
2. Feed those peaks as targets to the optimizer
3. Compare the optimized bore to the original
4. Report accuracy metrics

Intonation targets (phased):
- Phase 1: <20 cents (achievable now)
- Phase 2: <10 cents (with good SLA printing)
- Phase 3: <5 cents (Noreland-level, excellent SLA + calibration)
- Phase 4: <3 cents (stretch goal, best-case everything)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import numpy as np
from scipy.signal import find_peaks
from backend.optimizer import _compute_impedance_from_bore, BoreOptimizer


REFERENCE_DIR = Path(__file__).parent / "reference_instruments"


def load_bore_csv(filepath):
    """Load a bore profile from CSV. Returns list of (position, radius)."""
    bore = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                bore.append((float(parts[0]), float(parts[1])))
    return bore


def get_ground_truth_peaks(bore, freq_range=(50, 3000), n_freqs=1000):
    """Compute impedance peaks for a bore profile."""
    result = _compute_impedance_from_bore(bore, freq_range=freq_range, n_freqs=n_freqs)
    return result["peak_frequencies"], result["peak_magnitudes"]


def validate_instrument(name, bore, target_note_count=8):
    """
    Validate the optimizer against a known bore profile.
    
    Steps:
    1. Compute ground truth peaks
    2. Select the lowest N peaks as targets
    3. Run optimizer to reconstruct the bore
    4. Compare results
    """
    print(f"\n{'='*60}")
    print(f"  VALIDATING: {name}")
    print(f"{'='*60}")
    print(f"  Bore points: {len(bore)}")
    print(f"  Bore length: {bore[-1][0]:.3f} m")
    print(f"  Mouthpiece radius: {bore[0][1]*1000:.1f} mm")
    print(f"  Bell radius: {bore[-1][1]*1000:.1f} mm")
    
    # Step 1: Ground truth
    peak_freqs, peak_mags = get_ground_truth_peaks(bore)
    print(f"\n  Ground truth peaks: {len(peak_freqs)}")
    for i, (f, m) in enumerate(zip(peak_freqs[:10], peak_mags[:10])):
        print(f"    Peak {i+1}: {f:.1f} Hz (|Z|={m:.2e})")
    
    # Step 2: Select target frequencies (lowest N peaks)
    n_targets = min(target_note_count, len(peak_freqs))
    target_freqs = peak_freqs[:n_targets]
    print(f"\n  Using {n_targets} peaks as optimization targets:")
    for f in target_freqs:
        print(f"    {f:.1f} Hz")
    
    # Step 3: Run optimizer
    print(f"\n  Running optimizer (pop=40, gen=20)...")
    optimizer = BoreOptimizer(
        target_frequencies=target_freqs,
        n_control_points=max(6, len(bore)),  # match original complexity
        bore_length=bore[-1][0],  # same length as original
        min_radius=0.003,
        max_radius=0.020,
        pop_size=40,
        n_generations=20,
        seed=42,
    )
    
    result = optimizer.run(verbose=False)
    
    # Step 4: Evaluate best candidate
    best = result["best_candidates"][0]
    best_vars = best["variables"]
    
    # Get detailed evaluation
    detailed = optimizer.evaluate_single(best_vars)
    
    print(f"\n  Optimization result (best candidate):")
    print(f"    Frequency accuracy: {best['objectives']['frequency_accuracy']:.2f}")
    print(f"    Scale evenness: {best['objectives']['scale_evenness']:.6f}")
    print(f"    Projection: {best['objectives']['projection']:.2f}")
    
    # Compare matched frequencies
    print(f"\n  Frequency matching (target vs optimized):")
    total_error_cents = 0
    for match in detailed["matched_frequencies"]:
        error_cents = match["error_cents"]
        total_error_cents += abs(error_cents)
        status = "OK" if abs(error_cents) < 20 else "WARN"
        print(f"    {match['target']:7.1f} Hz -> {match['actual']:7.1f} Hz  "
              f"(error: {error_cents:+6.1f} cents) [{status}]")
    
    avg_error_cents = total_error_cents / len(detailed["matched_frequencies"])
    print(f"\n  Average absolute error: {avg_error_cents:.1f} cents")
    
    # Compare bore profiles
    print(f"\n  Bore profile comparison:")
    orig_radii = [r for _, r in bore]
    opt_radii = [p["radius"] for p in detailed["bore_profile"]]
    
    # Interpolate original to match optimized points
    orig_positions = [p for p, _ in bore]
    opt_positions = [p["position"] for p in detailed["bore_profile"]]
    
    orig_interp = np.interp(opt_positions, orig_positions, orig_radii)
    
    radius_errors = [(opt_r - orig_r) * 1000 for opt_r, orig_r in zip(opt_radii, orig_interp)]
    max_error_mm = max(abs(e) for e in radius_errors)
    avg_error_mm = np.mean([abs(e) for e in radius_errors])
    
    print(f"    Max radius error: {max_error_mm:.2f} mm")
    print(f"    Avg radius error: {avg_error_mm:.2f} mm")
    
    return {
        "name": name,
        "avg_error_cents": avg_error_cents,
        "max_radius_error_mm": max_error_mm,
        "avg_radius_error_mm": avg_error_mm,
        "n_targets": n_targets,
        "peak_count": len(peak_freqs),
    }


def main():
    print("INSTRUMENT DESIGN VALIDATION")
    print("Testing optimizer against known reference instruments")
    print("\nIntonation targets:")
    print("  Phase 1: <20 cents (achievable now)")
    print("  Phase 2: <10 cents (with good SLA printing)")
    print("  Phase 3: <5 cents (Noreland-level, excellent SLA + calibration)")
    print("  Phase 4: <3 cents (stretch goal, best-case everything)")
    
    results = []
    
    for filename in sorted(os.listdir(REFERENCE_DIR)):
        if filename.endswith(".csv"):
            name = filename.replace(".csv", "").replace("_", " ").title()
            bore = load_bore_csv(REFERENCE_DIR / filename)
            if len(bore) >= 3:
                r = validate_instrument(name, bore)
                results.append(r)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Instrument':<25} {'Avg Error':>10} {'Max Radius':>12} {'Avg Radius':>12}")
    print(f"  {'-'*25} {'(cents)':>10} {'(mm)':>12} {'(mm)':>12}")
    for r in results:
        print(f"  {r['name']:<25} {r['avg_error_cents']:>10.1f} {r['max_radius_error_mm']:>12.2f} {r['avg_radius_error_mm']:>12.2f}")
    
    # Pass/fail criteria with phased targets
    print(f"\n  Pass criteria:")
    print(f"    Phase 1: avg error < 20 cents, max radius error < 1mm")
    print(f"    Phase 2: avg error < 10 cents, max radius error < 0.5mm")
    print(f"    Phase 3: avg error < 5 cents, max radius error < 0.25mm")
    print(f"    Phase 4: avg error < 3 cents, max radius error < 0.1mm")
    
    for r in results:
        passed_p1 = r["avg_error_cents"] < 20 and r["max_radius_error_mm"] < 1.0
        passed_p2 = r["avg_error_cents"] < 10 and r["max_radius_error_mm"] < 0.5
        passed_p3 = r["avg_error_cents"] < 5 and r["max_radius_error_mm"] < 0.25
        passed_p4 = r["avg_error_cents"] < 3 and r["max_radius_error_mm"] < 0.1
        
        if passed_p4:
            status = "PASS (Phase 4 - 3 cents)"
        elif passed_p3:
            status = "PASS (Phase 3 - 5 cents)"
        elif passed_p2:
            status = "PASS (Phase 2 - 10 cents)"
        elif passed_p1:
            status = "PASS (Phase 1 - 20 cents)"
        else:
            status = "FAIL"
        
        print(f"  {r['name']}: {status}")


if __name__ == "__main__":
    main()
