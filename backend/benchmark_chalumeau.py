"""
Benchmark all optimizers on chalumeau and bass chalumeau instruments.

Chalumeau: simple cylindrical closed-open pipe, 6 holes, odd harmonics.
Bass chalumeau: larger bore, lower range, prototype for bass clarinet.
Tests TMM baseline L-BFGS-B, Powell+v2, multi-start.
"""

import sys, os, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.tmm_optimizer import TMMBoreOptimizer
from backend.tmm_optimizer_v2 import TMMBoreOptimizerJAX
from backend.tmm_optimizer_multi import MultiStartOptimizer


# ============================================================================
# Instrument configurations
# ============================================================================

INSTRUMENTS = {
    "chalumeau": {
        "targets": [261.6, 277.2, 293.7, 311.1, 329.6, 349.2],
        "names": ["C4", "C#4", "D4", "Eb4", "E4", "F4"],
        "bore_length": 300.0,
        "bore_radius": 7.25,
        "outer_diameter": 22.0,
        "n_holes": 6,
        "hole_positions": [50.0, 90.0, 130.0, 170.0, 210.0, 250.0],
        "hole_diameters": [7.0] * 6,
        "hole_lengths": [3.75] * 6,
        "fingering_sets": [
            ["closed", "closed", "closed", "closed", "closed", "closed"],
            ["open",   "closed", "closed", "closed", "closed", "closed"],
            ["open",   "open",   "closed", "closed", "closed", "closed"],
            ["open",   "open",   "open",   "closed", "closed", "closed"],
            ["open",   "open",   "open",   "open",   "closed", "closed"],
            ["open",   "open",   "open",   "open",   "open",   "closed"],
        ],
        "n_register": 1,
    },
    "bass_chalumeau": {
        "targets": [233.1, 246.9, 261.6, 277.2, 293.7, 311.1, 329.6, 349.2],
        "names": ["Bb2", "B2", "C3", "C#3", "D3", "Eb3", "E3", "F3"],
        "bore_length": 600.0,
        "bore_radius": 9.5,
        "outer_diameter": 28.0,
        "n_holes": 8,
        "hole_positions": [60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 520.0],
        "hole_diameters": [8.0] * 8,
        "hole_lengths": [4.0] * 8,
        "fingering_sets": [
            ["closed"] * 8,
            ["open",   "closed", "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open",   "open",   "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open",   "open",   "open",   "closed", "closed", "closed", "closed", "closed"],
            ["open",   "open",   "open",   "open",   "closed", "closed", "closed", "closed"],
            ["open",   "open",   "open",   "open",   "open",   "closed", "closed", "closed"],
            ["open",   "open",   "open",   "open",   "open",   "open",   "closed", "closed"],
            ["open",   "open",   "open",   "open",   "open",   "open",   "open",   "closed"],
        ],
        "n_register": 1,
    },
}


# ============================================================================
# Helpers
# ============================================================================

def verify_instrument(radii_mm, cfg, label=""):
    """Verify an optimized bore profile and print detailed results."""
    inst = tmm_instrument_from_radii(
        radii_mm, cfg["bore_length"],
        cfg["hole_positions"], cfg["hole_diameters"], cfg["hole_lengths"],
        cfg["outer_diameter"], closed_top=True, cone_step=0.5,
    )
    target_wavelengths = [SPEED_OF_SOUND / f for f in cfg["targets"]]
    freqs = inst.compute_fingered_frequencies(target_wavelengths, cfg["fingering_sets"], cfg["n_register"])

    print(f"\n  {label}")
    print(f"  {'Note':<8} {'Target':>10} {'Actual':>10} {'Error':>10} {'Cents':>8}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

    cents_errors = []
    for name, target, actual in zip(cfg["names"], cfg["targets"], freqs):
        err = 1200.0 * np.log2(actual / target) if actual > 0 else 1e10
        cents_errors.append(err)
        print(f"  {name:<8} {target:>10.1f} {actual:>10.1f} {actual-target:>+10.1f} {err:>+8.1f}")

    cents_arr = np.array(cents_errors)
    if np.any(np.abs(cents_arr) > 1e5):
        print(f"  FAILED - some notes didn't resonate")
        return 1e10, 1e10

    offset = np.median(cents_arr)
    corrected = cents_arr - offset
    rms = float(np.sqrt(np.mean(corrected ** 2)))
    peak = float(np.max(np.abs(corrected)))
    print(f"\n  Median offset: {offset:+.1f} cents")
    print(f"  RMS intonation: {rms:.2f} cents")
    print(f"  Peak error: {peak:.2f} cents")
    return rms, peak


def run_optimizers(cfg, label):
    """Run all three TMM optimizers on a given instrument config."""
    print("\n" + "#" * 70)
    print(f"# {label}")
    print(f"# Bore: {cfg['bore_length']:.0f}mm x {cfg['bore_radius']:.1f}mm radius")
    print(f"# {cfg['n_holes']} holes, {len(cfg['targets'])} target notes")
    print("#" * 70)

    results = {}
    min_r = cfg["bore_radius"] * 0.5
    max_r = cfg["bore_radius"] * 1.5

    # --- 1. Baseline L-BFGS-B ---
    print(f"\n{'='*70}")
    print(f"1. BASELINE L-BFGS-B ({label})")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        opt1 = TMMBoreOptimizer(
            target_frequencies=cfg["targets"],
            fingering_sets=cfg["fingering_sets"],
            n_control_points=12,
            bore_length=cfg["bore_length"],
            min_radius=min_r,
            max_radius=max_r,
            hole_positions=cfg["hole_positions"],
            hole_diameters=cfg["hole_diameters"],
            hole_lengths=cfg["hole_lengths"],
            closed_top=True,
            outer_diameter=cfg["outer_diameter"],
            n_register=cfg["n_register"],
        )
        r1 = opt1.run(verbose=True, maxiter=300)
        t1 = time.time()
        radii1 = np.array(r1["best_radii"])
        rms1, peak1 = verify_instrument(radii1, cfg, "Baseline L-BFGS-B")
    except Exception as e:
        t1 = time.time()
        print(f"  FAILED: {e}")
        rms1, peak1 = 1e10, 1e10

    # --- 2. Powell + L-BFGS-B v2 ---
    print(f"\n{'='*70}")
    print(f"2. POWELL + L-BFGS-B v2 ({label})")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        opt2 = TMMBoreOptimizerJAX(
            target_frequencies=cfg["targets"],
            fingering_sets=cfg["fingering_sets"],
            n_control_points=20,
            bore_length=cfg["bore_length"],
            min_radius=min_r,
            max_radius=max_r,
            hole_positions=cfg["hole_positions"],
            hole_diameters=cfg["hole_diameters"],
            hole_lengths=cfg["hole_lengths"],
            closed_top=True,
            outer_diameter=cfg["outer_diameter"],
            n_register=cfg["n_register"],
        )
        r2 = opt2.run(verbose=True, maxiter=600)
        t2 = time.time()
        rms2, peak2 = verify_instrument(np.array(r2["best_radii"]), cfg, "Powell+v2")
    except Exception as e:
        t2 = time.time()
        print(f"  FAILED: {e}")
        rms2, peak2 = 1e10, 1e10

    # --- 3. Multi-start ---
    print(f"\n{'='*70}")
    print(f"3. MULTI-START ({label})")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        opt3 = MultiStartOptimizer(
            target_frequencies=cfg["targets"],
            fingering_sets=cfg["fingering_sets"],
            n_control_points=20,
            bore_length=cfg["bore_length"],
            min_radius=min_r,
            max_radius=max_r,
            hole_positions=cfg["hole_positions"],
            hole_diameters=cfg["hole_diameters"],
            hole_lengths=cfg["hole_lengths"],
            closed_top=True,
            outer_diameter=cfg["outer_diameter"],
            n_register=cfg["n_register"],
            n_starts=5,
            maxiter_per_start=200,
        )
        r3 = opt3.run(verbose=True)
        t3 = time.time()
        rms3, peak3 = verify_instrument(np.array(r3["best_radii"]), cfg, "Multi-start")
    except Exception as e:
        t3 = time.time()
        print(f"  FAILED: {e}")
        rms3, peak3 = 1e10, 1e10

    results[label] = {
        "baseline": {"rms": rms1, "peak": peak1},
        "powell_v2": {"rms": rms2, "peak": peak2},
        "multi_start": {"rms": rms3, "peak": peak3},
    }
    return results


# ============================================================================
# Main
# ============================================================================

all_results = {}
for name, cfg in INSTRUMENTS.items():
    results = run_optimizers(cfg, name)
    all_results.update(results)

# Summary
print("\n" + "#" * 70)
print("# FINAL SUMMARY")
print("#" * 70)
print(f"\n  {'Instrument':<20} {'Optimizer':<25} {'RMS (cents)':>12} {'Peak':>8}")
print(f"  {'-'*20} {'-'*25} {'-'*12} {'-'*8}")
for inst_name, res in all_results.items():
    for opt_name, data in res.items():
        rms = data["rms"]
        peak = data["peak"]
        rms_str = f"{rms:.3f}" if rms < 1e5 else "FAILED"
        peak_str = f"{peak:.1f}" if peak < 1e5 else "—"
        print(f"  {inst_name:<20} {opt_name:<25} {rms_str:>12} {peak_str:>8}")
    print()

# Bass chalumeau assessment
if "bass_chalumeau" in all_results:
    bc = all_results["bass_chalumeau"]
    best_bc = min(r["rms"] for r in bc.values())
    print(f"  Bass chalumeau best RMS: {best_bc:.3f} cents")
    print(f"  {'PASS' if best_bc < 3.0 else 'NEEDS MORE ITERATIONS / HOLES'}")
    print()
    print("  NOTE: Bass chalumeau is a prototype path toward bass clarinet.")
    print("  The 8-hole layout + 600mm bore models a simplified bass instrument.")
    print("  Real bass clarinets use 17-21 keys with a 1800mm bore + U-bend.")
    print("  This prototype validates the TMM model at lower frequencies")
    print("  before tackling full bass clarinet complexity.")
