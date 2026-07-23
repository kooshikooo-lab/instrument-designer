"""
Bass clarinet TMM optimization benchmark.

Compares with existing chalumeau and bass-chalumeau results:
- Chalumeau C: 6 holes, 300mm x 7.25mm, ~4.46c RMS
- Bass chalumeau Bb: 8 holes, 600mm x 9.5mm, ~3-5c RMS
- Bass clarinet Bb: 7-9 holes, 1200mm x 12.5mm, ??? (this test)

Tests:
1. Uniform bore, 7 holes, sequential optimizer
2. Bell-flare bore (exponential), 7 holes, sequential + bell profile in Phase 3
3. Extended (low-C) 1470mm version for comparison
"""

import sys, os, time, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer, optimize_bore_length


def verify_instrument(radii_mm, bore_length, positions, diameters, lengths,
                      outer_diameter, target_freqs, names, fingering_sets,
                      n_register=1, closed_top=True, label=""):
    """Verify an optimized instrument and print detailed results."""
    inst = tmm_instrument_from_radii(
        radii_mm, bore_length, positions, diameters, lengths,
        outer_diameter, closed_top=closed_top, cone_step=0.5,
    )
    target_wavelengths = [SPEED_OF_SOUND / f for f in target_freqs]
    freqs = inst.compute_fingered_frequencies(
        target_wavelengths, fingering_sets, n_register)

    print(f"\n  {label}")
    print(f"  {'Note':<8} {'Target':>10} {'Actual':>10} {'Error':>10} {'Cents':>8}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

    cents_errors = []
    for name, target, actual in zip(names, target_freqs, freqs):
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


# ============================================================================
# Instrument configurations
# ============================================================================

# Standard bass clarinet: 1200mm, ~D2 fundamental (sounding)
# Bb major diatonic scale: D2 E2 F#2 G2 A2 B2 C#3 D3
BASS_CLARINET_STANDARD = {
    "description": "Bass clarinet Bb (standard) — diatonic D major, 7 holes",
    "targets": [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8],
    "names": ["D2", "E2", "F#2", "G2", "A2", "B2", "C#3", "D3"],
    "bore_length": 1200.0,
    "bore_radius": 12.5,   # 25mm diameter
    "outer_diameter": 37.0,
    "n_holes": 7,
    "hole_diameter": 11.0,  # Scaled from bass chalumeau 8mm * 12.5/9.5
    "hole_length": 5.0,     # Scaled from bass chalumeau 4mm * 12.5/9.5
    "initial_positions": [100, 200, 300, 400, 500, 600, 700],
    "fingering_sets": [
        ["closed"] * 7,
        ["open",   "closed", "closed", "closed", "closed", "closed", "closed"],
        ["open",   "open",   "closed", "closed", "closed", "closed", "closed"],
        ["open",   "open",   "open",   "closed", "closed", "closed", "closed"],
        ["open",   "open",   "open",   "open",   "closed", "closed", "closed"],
        ["open",   "open",   "open",   "open",   "open",   "closed", "closed"],
        ["open",   "open",   "open",   "open",   "open",   "open",   "closed"],
        ["open"] * 7,
    ],
    "n_register": 1,
}

# Extended bass clarinet: 1470mm, ~Bb1 fundamental (sounding)
# Bb major diatonic: Bb1 C2 D2 Eb2 F2 G2 A2 Bb2
BASS_CLARINET_EXTENDED = {
    "description": "Bass clarinet Bb (extended low-C) — diatonic Bb major, 7 holes",
    "targets": [58.3, 65.4, 73.4, 77.8, 87.3, 98.0, 110.0, 116.5],
    "names": ["Bb1", "C2", "D2", "Eb2", "F2", "G2", "A2", "Bb2"],
    "bore_length": 1470.0,
    "bore_radius": 12.5,
    "outer_diameter": 37.0,
    "n_holes": 7,
    "hole_diameter": 11.0,
    "hole_length": 5.0,
    "initial_positions": [120, 240, 360, 480, 600, 720, 840],
    "fingering_sets": [
        ["closed"] * 7,
        ["open",   "closed", "closed", "closed", "closed", "closed", "closed"],
        ["open",   "open",   "closed", "closed", "closed", "closed", "closed"],
        ["open",   "open",   "open",   "closed", "closed", "closed", "closed"],
        ["open",   "open",   "open",   "open",   "closed", "closed", "closed"],
        ["open",   "open",   "open",   "open",   "open",   "closed", "closed"],
        ["open",   "open",   "open",   "open",   "open",   "open",   "closed"],
        ["open"] * 7,
    ],
    "n_register": 1,
}


# ============================================================================
# Test runner
# ============================================================================

def run_test(cfg, label, use_bell=False, n_bore_cp=0):
    """Run sequential optimizer on a given instrument config."""
    print("\n" + "#" * 70)
    print(f"# {cfg['description']}")
    print(f"# Bore: {cfg['bore_length']:.0f}mm x {cfg['bore_radius']:.1f}mm radius")
    print(f"# {cfg['n_holes']} holes, {len(cfg['targets'])} target notes")
    print(f"# Bell flare: {'YES' if use_bell else 'NO'}")
    print(f"# Bore control points: {n_bore_cp if n_bore_cp > 0 else 'uniform'}")
    print("#" * 70)

    # Build bell-flare profile if requested
    bore_radii = None
    bore_length = cfg["bore_length"]
    if use_bell:
        # Create bell profile: cylinder + exponential flare
        bell_start = bore_length - 280  # 280mm bell length
        n_cp = 15
        positions_pct = np.linspace(0, 1, n_cp)
        radii = []
        for pct in positions_pct:
            pos = pct * bore_length
            if pos < bell_start:
                radii.append(cfg["bore_radius"])
            else:
                # Exponential flare
                t = (pos - bell_start) / 280.0
                r_start = cfg["bore_radius"]
                r_end = 55.0  # Bell radius
                r = r_start + (r_end - r_start) * t ** 2
                radii.append(r)
        bore_radii = np.array(radii)

    # Run SequentialBoreOptimizer
    t0 = time.time()
    opt = SequentialBoreOptimizer(
        target_frequencies=cfg["targets"],
        fingering_sets=cfg["fingering_sets"],
        bore_radius=cfg["bore_radius"],
        outer_diameter=cfg["outer_diameter"],
        closed_top=True,
        hole_diameter=cfg["hole_diameter"],
        hole_length=cfg["hole_length"],
        bore_length_bounds=(bore_length * 0.7, bore_length * 1.3),
        n_bore_cp=n_bore_cp,
        bore_radius_bounds=(cfg["bore_radius"] * 0.5, cfg["bore_radius"] * 1.5),
        n_register=cfg["n_register"],
    )
    result = opt.run(verbose=True)
    dt = time.time() - t0

    # Extract results
    best_radii = np.array(result["bore_radii"])
    best_L = result["bore_length_mm"]
    best_positions = result["hole_positions"]

    print(f"\n  Total time: {dt:.0f}s")
    print(f"  Optimized length: {best_L:.1f} mm")

    # Verify with bell flare if requested
    verify_radii = best_radii
    verify_L = best_L
    if use_bell and bore_radii is not None:
        # Use bell flare for final bore profile
        # Interpolate best_radii onto bell-flare positions
        n_cp = len(bore_radii)
        old_pos = np.linspace(0, best_L, len(best_radii))
        new_pos = np.linspace(0, best_L, n_cp)
        verify_radii = np.interp(new_pos, old_pos, best_radii)
        # Apply bell flare at the end
        bell_start = best_L - 280
        for i, pos in enumerate(new_pos):
            if pos > bell_start:
                t = (pos - bell_start) / 280.0
                verify_radii[i] = cfg["bore_radius"] + (55.0 - cfg["bore_radius"]) * t ** 2

    rms, peak = verify_instrument(
        verify_radii, verify_L, best_positions,
        [cfg["hole_diameter"]] * cfg["n_holes"],
        [cfg["hole_length"]] * cfg["n_holes"],
        cfg["outer_diameter"], cfg["targets"], cfg["names"],
        cfg["fingering_sets"], cfg["n_register"],
        label="Optimized result",
    )

    return {"rms": rms, "peak": peak, "time": dt, "result": result}


# ============================================================================
# Direct comparison with bass chalumeau
# ============================================================================

def compare_bass_chalumeau():
    """Run the same optimizer on bass chalumeau for fair comparison."""
    print("\n\n" + "=" * 70)
    print("= COMPARISON: Bass chalumeau (same optimizer)")
    print("=" * 70)

    cfg = {
        "description": "Bass chalumeau in Bb — benchmark comparison",
        "targets": [233.1, 246.9, 261.6, 277.2, 293.7, 311.1, 329.6, 349.2],
        "names": ["Bb2", "B2", "C3", "C#3", "D3", "Eb3", "E3", "F3"],
        "bore_length": 600.0,
        "bore_radius": 9.5,
        "outer_diameter": 28.0,
        "n_holes": 8,
        "hole_diameter": 8.0,
        "hole_length": 4.0,
        "initial_positions": [60, 120, 180, 240, 300, 360, 420, 520],
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
    }

    t0 = time.time()
    opt = SequentialBoreOptimizer(
        target_frequencies=cfg["targets"],
        fingering_sets=cfg["fingering_sets"],
        bore_radius=cfg["bore_radius"],
        outer_diameter=cfg["outer_diameter"],
        closed_top=True,
        hole_diameter=cfg["hole_diameter"],
        hole_length=cfg["hole_length"],
        bore_length_bounds=(400, 800),
        n_bore_cp=0,
        n_register=cfg["n_register"],
    )
    result = opt.run(verbose=False)
    dt = time.time() - t0

    rms, peak = verify_instrument(
        np.array(result["bore_radii"]), result["bore_length_mm"],
        result["hole_positions"],
        [cfg["hole_diameter"]] * cfg["n_holes"],
        [cfg["hole_length"]] * cfg["n_holes"],
        cfg["outer_diameter"], cfg["targets"], cfg["names"],
        cfg["fingering_sets"], cfg["n_register"],
        label="Bass chalumeau (same optimizer)",
    )
    return {"rms": rms, "peak": peak, "time": dt}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    all_results = {}

    # Test 1: Bass clarinet standard, uniform bore
    all_results["bass_clarinet_uniform"] = run_test(
        BASS_CLARINET_STANDARD, "Uniform bore", use_bell=False)

    # Test 2: Bass clarinet standard, with bell flare + bore profile optimization
    all_results["bass_clarinet_bell"] = run_test(
        BASS_CLARINET_STANDARD, "Bell flare + bore profile", use_bell=True, n_bore_cp=6)

    # Test 3: Bass clarinet extended (low-C), uniform bore
    all_results["bass_clarinet_extended"] = run_test(
        BASS_CLARINET_EXTENDED, "Extended low-C", use_bell=False)

    # Test 4: Bass chalumeau for comparison
    all_results["bass_chalumeau_sequential"] = compare_bass_chalumeau()

    # Summary
    print("\n" + "#" * 70)
    print("# FINAL SUMMARY")
    print("#" * 70)
    print(f"\n  {'Test':<35} {'RMS (c)':>10} {'Peak (c)':>10} {'Time (s)':>10}")
    print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10}")
    for name, data in all_results.items():
        rms_str = f"{data['rms']:.2f}" if data['rms'] < 1e5 else "FAILED"
        peak_str = f"{data['peak']:.1f}" if data['peak'] < 1e5 else "—"
        print(f"  {name:<35} {rms_str:>10} {peak_str:>10} {data['time']:>10.0f}")

    # Cross-reference with known chalumeau results
    print("\n\n  Reference benchmarks from earlier runs:")
    print(f"  {'Instrument':<35} {'RMS (c)':>10}")
    print(f"  {'-'*35} {'-'*10}")
    print(f"  {'Chalumeau C (TMMBoreOptimizer)':<35} {'~4.46':>10}")
    print(f"  {'Bass chalumeau (TMMBoreOptimizer)':<35} {'~3-5':>10}")
    print(f"  {'Diatonic chalumeau (v2 JAX)':<35} {'~0.3':>10}")
    print(f"  {'All 7 TMM instruments (Phase 2b DE)':<35} {'<1.0':>10}")

    # Also consult AI for analysis
    print("\n\n  === AI ANALYSIS ===")
    best_rms = min(v['rms'] for v in all_results.values() if v['rms'] < 1e5)
    print(f"  Best RMS across tests: {best_rms:.2f} cents")
    if best_rms < 1.0:
        print("  STATUS: Excellent intonation (< 1c RMS)")
    elif best_rms < 3.0:
        print("  STATUS: Good intonation (1-3c RMS)")
    elif best_rms < 10.0:
        print("  STATUS: Acceptable intonation (3-10c RMS)")
    else:
        print("  STATUS: Needs improvement (> 10c RMS)")
