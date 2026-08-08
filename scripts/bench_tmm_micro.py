"""Micro-benchmark for TMM hot paths.

Place this script in scripts/ and run it on main and perf branches to compare
wall-clock timings for resonance evaluation. It intentionally avoids external
dependencies beyond numpy and the package itself.

Usage:
    python scripts/bench_tmm_micro.py

Output: prints timings for find_resonance and resonance_phase.
"""

import time
import numpy as np
import json
import random
from backend.tmm_acoustics import tmm_instrument_from_radii, Hole


def make_test_instrument():
    # Representative bore: 50 points from 3.5 mm to 7.0 mm radius
    radii = np.linspace(3.5, 7.0, 50)  # mm radius
    bore_length = 300.0  # mm
    # Example holes (positions in mm, diameters in mm, lengths in mm)
    hole_positions = [40, 80, 120, 160, 200, 240]
    hole_diams = [7.0] * len(hole_positions)
    hole_lens = [3.75] * len(hole_positions)
    inst = tmm_instrument_from_radii(
        radii_mm=radii,
        bore_length_mm=bore_length,
        hole_positions_mm=hole_positions,
        hole_diameters_mm=hole_diams,
        hole_lengths_mm=hole_lens,
        cone_step=0.5,
    )
    return inst


def random_fingerings(n_holes, n_notes):
    out = []
    for _ in range(n_notes):
        out.append([random.choice([Hole.OPEN, Hole.CLOSED]) for __ in range(n_holes)])
    return out


def bench_find_resonance(inst, fingerings, iterations=200):
    wl_guess = 400.0  # mm
    start = time.perf_counter()
    for i in range(iterations):
        fg = fingerings[i % len(fingerings)]
        _ = inst.find_resonance(wl_guess, fg, n_register=1)
    end = time.perf_counter()
    return end - start


def bench_resonance_phase(inst, fingerings, iterations=2000):
    wl = 400.0
    start = time.perf_counter()
    for i in range(iterations):
        fg = fingerings[i % len(fingerings)]
        _ = inst.resonance_phase(wl, fg)
    end = time.perf_counter()
    return end - start


def run_all(iterations_find=200, iterations_phase=2000, repeats=3):
    inst = make_test_instrument()
    fing_sets = random_fingerings(inst.n_holes, 20)
    results = {
        "find_resonance": [],
        "resonance_phase": [],
    }
    # Warm-up
    _ = inst.find_resonance(400.0, fing_sets[0], n_register=1)
    _ = inst.resonance_phase(400.0, fing_sets[0])

    for r in range(repeats):
        t1 = bench_find_resonance(inst, fing_sets, iterations=iterations_find)
        t2 = bench_resonance_phase(inst, fing_sets, iterations=iterations_phase)
        results["find_resonance"].append(t1)
        results["resonance_phase"].append(t2)
        print(f"repeat {r+1}/{repeats}: find_resonance x{iterations_find} = {t1:.6f}s, resonance_phase x{iterations_phase} = {t2:.6f}s")

    summary = {
        "find_resonance_mean": float(np.mean(results["find_resonance"])),
        "find_resonance_std": float(np.std(results["find_resonance"])),
        "resonance_phase_mean": float(np.mean(results["resonance_phase"])),
        "resonance_phase_std": float(np.std(results["resonance_phase"])),
        "iterations_find": iterations_find,
        "iterations_phase": iterations_phase,
        "repeats": repeats,
    }
    print("\nSummary:\n", json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run_all()
