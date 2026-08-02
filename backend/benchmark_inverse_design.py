"""Benchmark inverse design from WAV: Tier 1 (sound analysis) + Tier 3 (timbre matching).

Tier 2 (generative_agent scale design) is PLANNED and unavailable on main, so
the benchmark exercises the self-contained stages:
  1. synthesize known harmonic WAVs (clarinet-like odd harmonics, flute-like all harmonics)
  2. analyze_wav -> verify f0 recovery accuracy
  3. match_timbre -> verify bore-radius optimization reduces harmonic-envelope cost
"""
import os, sys, json, time, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.inverse_design import (
    synthesize_harmonic, save_synthetic_wav, analyze_wav,
    build_target_envelope, estimate_harmonic_magnitudes, match_timbre,
)


def _candidate(bore_length=600.0, closed_top=False):
    n_holes = 6
    positions = [float(bore_length * (i + 1) / (n_holes + 1)) for i in range(n_holes)]
    return {
        "bore_length_mm": bore_length,
        "hole_positions_mm": positions,
        "hole_diameters_mm": [8.0] * n_holes,
        "hole_lengths_mm": [3.0] * n_holes,
        "closed_top": closed_top,
    }


def run():
    results = {}
    out_dir = os.path.join(os.path.dirname(__file__), "..", "test_output", "inverse_design")
    os.makedirs(out_dir, exist_ok=True)

    cases = [
        {"name": "clarinet_odd", "f0": 220.0, "odd_only": True, "n_harm": 10},
        {"name": "flute_all", "f0": 261.63, "odd_only": False, "n_harm": 12},
    ]
    tier1_results = []
    for case in cases:
        t0 = time.time()
        sig = synthesize_harmonic(case["f0"], n_harmonics=case["n_harm"], odd_only=case["odd_only"])
        path = os.path.join(out_dir, f"{case['name']}.wav")
        save_synthetic_wav(path, sig)
        analysis = analyze_wav(path)
        dt = time.time() - t0
        f0 = analysis["fundamental_hz"]
        cents_err = 1200.0 * math.log2(f0 / case["f0"]) if f0 > 0 else float("nan")
        n_harm = len(analysis["harmonic_frequencies"])
        tier1_results.append({
            "case": case["name"], "expected_f0": case["f0"], "recovered_f0": round(f0, 3),
            "cents_error": round(cents_err, 3), "n_harmonics_recovered": n_harm,
            "analyze_time_s": round(dt, 4),
        })
        print(f"[Tier1] {case['name']}: f0={f0:.3f}Hz (expected {case['f0']}), "
              f"err={cents_err:+.1f}c, harmonics={n_harm}, {dt:.2f}s")

    # Tier 3: timbre matching on one case
    analysis = analyze_wav(os.path.join(out_dir, "flute_all.wav"))
    candidate = _candidate(bore_length=600.0, closed_top=False)
    t0 = time.time()
    tier3 = match_timbre(candidate, analysis, n_gen=15, pop_size=20)
    dt = time.time() - t0
    print(f"[Tier3] initial cost={tier3['tier3_cost_initial']:.6f} "
          f"optimized={tier3['tier3_cost_optimized']:.6f} "
          f"improved={tier3['tier3_success']} ({dt:.1f}s)")
    tier3_result = {
        "cost_initial": tier3["tier3_cost_initial"],
        "cost_optimized": tier3["tier3_cost_optimized"],
        "success": bool(tier3["tier3_success"]),
        "time_s": round(dt, 2),
    }

    results = {"tier1": tier1_results, "tier3": tier3_result, "timestamp": time.time()}
    report_path = os.path.join(out_dir, "benchmark_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    run()
