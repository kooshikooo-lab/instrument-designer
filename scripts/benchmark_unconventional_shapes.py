#!/usr/bin/env python3
"""
Benchmark unconventional bore shapes against cylindrical baseline.

Tests 5 bore shapes (cylindrical, conical, parabolic, bessel, exponential)
across all instruments in benchmark_all.INSTRUMENTS using Dask parallelization.

Usage:
    python scripts/benchmark_unconventional_shapes.py
    python scripts/benchmark_unconventional_shapes.py --quick
    python scripts/benchmark_unconventional_shapes.py --no-dask
    python scripts/benchmark_unconventional_shapes.py --shapes cylindrical conical
    python scripts/benchmark_unconventional_shapes.py --instruments chalumeau soprano_sax
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Any

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DASK_SCHEDULER = "tcp://127.0.0.1:8786"
N_CP = 6  # control points, matches benchmark_all.sequential_refined
FLARE_BELL = 1.5  # bell radius multiplier relative to bore_radius (default)

# Per-shape flare multipliers — tuned for each bore geometry
SHAPE_FLARE = {
    "cylindrical": 1.5,
    "conical": 1.5,
    "parabolic": 1.5,
    "bessel": 1.5,
    "exponential": 1.5,
    "sinusoidal": 1.4,
    "stepped": 1.3,
    "inverse_taper": 1.0,
    "trumpet": 1.8,
}

SHAPES = {
    "cylindrical": {"desc": "Uniform radius (baseline)"},
    "conical": {"desc": "Linear taper, narrow→wide"},
    "parabolic": {"desc": "Quadratic flare"},
    "bessel": {"desc": "Power-law flare (exponent 0.5)"},
    "exponential": {"desc": "Exponential flare"},
    "sinusoidal": {"desc": "Conical taper + 2-cycle sine ripple"},
    "stepped": {"desc": "Three discrete radius steps"},
    "inverse_taper": {"desc": "Narrowing bore (wide mouth, narrow bell)"},
    "trumpet": {"desc": "Cubic flare (slow then rapid expansion)"},
}


SHAPE_TO_BORE = {
    "cylindrical": "cylinder", "conical": "cone", "parabolic": "parabolic",
    "bessel": "bessel", "exponential": "exponential",
    "sinusoidal": "sinusoidal", "stepped": "stepped",
    "inverse_taper": "inverse_taper", "trumpet": "trumpet",
}


def _make_shape_radii(shape: str, length: float, r_mouth: float, r_bell: float) -> np.ndarray:
    from backend.spline_bore import analytical_bore
    bore_shape = SHAPE_TO_BORE[shape]
    bore = analytical_bore(bore_shape, length, r_bell, r_mouth, flare=0.5, n_control=N_CP, n_samples=N_CP)
    return bore.to_radii_array(N_CP)


def eval_one(instrument_name: str, shape: str, verbose: bool = False) -> dict[str, Any]:
    from backend.benchmark_all import INSTRUMENTS, sequential_refined, eval_multi

    cfg = dict(INSTRUMENTS[instrument_name])
    if cfg.get("_chromatic"):
        return {"instrument": instrument_name, "shape": shape, "error": "chromatic not supported", "rms": 1e10}

    r_mouth = cfg["bore_radius"]
    flare = SHAPE_FLARE.get(shape, FLARE_BELL)
    r_bell = r_mouth * flare
    length_est = 600.0

    if shape == "cylindrical":
        initial_radii = None
    else:
        try:
            initial_radii = _make_shape_radii(shape, length_est, r_mouth, r_bell)
        except Exception as e:
            return {"instrument": instrument_name, "shape": shape, "error": str(e), "rms": 1e10}

    t0 = time.time()
    try:
        result = sequential_refined(cfg, initial_radii=initial_radii)
        rms, L, hp, hd, bore_radii, elapsed = result
    except Exception as e:
        return {"instrument": instrument_name, "shape": shape, "error": str(e), "rms": 1e10, "time": time.time() - t0}

    multi = eval_multi(bore_radii, L, hp, hd, [cfg["hole_length"]] * len(hp), cfg)

    return {
        "instrument": instrument_name,
        "shape": shape,
        "rms": float(rms),
        "bore_length_mm": float(L),
        "n_holes": len(hp),
        "hole_positions": hp,
        "hole_diameters": hd,
        "bore_radii": bore_radii.tolist(),
        "multi": multi,
        "time_s": time.time() - t0,
        "error": "",
    }


def run_dask(instrument_names: list[str], shapes: list[str], scheduler: str = DASK_SCHEDULER) -> list[dict[str, Any]]:
    from dask.distributed import Client, as_completed

    client = Client(scheduler, timeout="30s")
    try:
        tasks = [(inst, shape) for inst in instrument_names for shape in shapes]
        futures = {client.submit(eval_one, inst, shape): (inst, shape) for inst, shape in tasks}

        results = []
        for future in as_completed(futures):
            inst, shape = futures[future]
            try:
                res = future.result()
                results.append(res)
                status = f"RMS={res['rms']:.2f}c" if res.get("rms", 1e10) < 1e5 else f"ERR: {res.get('error', '?')}"
                print(f"  {inst:22s} / {shape:12s}  {status}  ({res.get('time_s', 0):.1f}s)")
            except Exception as e:
                print(f"  {inst:22s} / {shape:12s}  FAILED: {e}")
                results.append({"instrument": inst, "shape": shape, "error": str(e), "rms": 1e10, "time_s": 0})
        return results
    finally:
        client.close()


def run_local(instrument_names: list[str], shapes: list[str]) -> list[dict[str, Any]]:
    results = []
    total = len(instrument_names) * len(shapes)
    idx = 0
    for inst in instrument_names:
        for shape in shapes:
            idx += 1
            print(f"  [{idx}/{total}] {inst:22s} / {shape:12s}...", end=" ", flush=True)
            res = eval_one(inst, shape, verbose=False)
            status = f"RMS={res['rms']:.2f}c" if res.get("rms", 1e10) < 1e5 else f"ERR: {res.get('error', '?')}"
            print(f"{status}  ({res.get('time_s', 0):.1f}s)")
            results.append(res)
    return results


def print_table(results: list[dict[str, Any]]):
    inst_names = sorted(set(r["instrument"] for r in results))
    shape_names = sorted(set(r["shape"] for r in results))

    print()
    col_w = 16
    print("=" * (18 + col_w * len(shape_names)))
    print(f"{'Instrument':<18}", end="")
    for s in shape_names:
        print(f"{s:>{col_w}}", end="")
    print()
    print("=" * (18 + col_w * len(shape_names)))

    for inst in inst_names:
        print(f"{inst:<18}", end="")
        for s in shape_names:
            matches = [r for r in results if r["instrument"] == inst and r["shape"] == s]
            if not matches:
                print(f"{'---':>{col_w}}", end="")
            else:
                rms = matches[0].get("rms", 1e10)
                if rms < 1e5:
                    print(f"{rms:>{col_w-3}.2f}c ", end="      ")
                else:
                    print(f"{'FAIL':>{col_w}}", end="")
        print()
    print()

    print("SHAPE AVERAGES:")
    for s in shape_names:
        vals = [r["rms"] for r in results if r["shape"] == s and r.get("rms", 1e10) < 1e5]
        if vals:
            print(f"  {s:12s}: avg={np.mean(vals):.2f}c  min={np.min(vals):.2f}c  max={np.max(vals):.2f}c")

    print()
    print("MULTI-OBJECTIVE METRICS (average across instruments):")
    metric_labels = {
        "rms": "RMS (cents)",
        "timbre_consistency": "Timbre Consistency",
        "playability": "Playability (smoothness)",
        "register_break": "Register Break",
        "max_error": "Max Error (cents)",
    }
    for metric_key, metric_label in metric_labels.items():
        print(f"\n  {metric_label}:")
        for s in shape_names:
            vals = []
            for r in results:
                if r["shape"] == s and r.get("multi") and r["multi"].get(metric_key, 1e10) < 1e5:
                    vals.append(r["multi"][metric_key])
            if vals:
                print(f"    {s:12s}: avg={np.mean(vals):.2f}c  min={np.min(vals):.2f}c  max={np.max(vals):.2f}c")

    print()
    print("BEST SHAPE PER INSTRUMENT (lowest RMS):")
    recs = []
    for inst in inst_names:
        inst_results = [r for r in results if r["instrument"] == inst and r.get("rms", 1e10) < 1e5]
        if inst_results:
            best = min(inst_results, key=lambda r: r["rms"])
            cyl = [r for r in inst_results if r["shape"] == "cylindrical"]
            cyl_rms = cyl[0]["rms"] if cyl else None
            delta = f"(vs cyl: {best['rms'] - cyl_rms:+.2f}c)" if cyl_rms else ""
            multi = best.get("multi", {})
            extra = ""
            if multi:
                extra = f"  timbre={multi.get('timbre_consistency',0):.2f}c  play={multi.get('playability',0):.2f}c  max_err={multi.get('max_error',0):.2f}c"
            print(f"  {inst:22s}: {best['shape']:12s}  RMS={best['rms']:.2f}c  {delta}{extra}")
            recs.append({"instrument": inst, "recommended_shape": best["shape"],
                         "rms": best["rms"], "improvement": best["rms"] - cyl_rms if cyl_rms else 0,
                         "timbre_consistency": multi.get("timbre_consistency", 0),
                         "hole_positions": best.get("hole_positions", []),
                         "hole_diameters": best.get("hole_diameters", [])})

    # Recommendation summary
    print()
    print("=" * 70)
    print("RECOMMENDATION REPORT")
    print("=" * 70)
    print(f"{'Instrument':<22} {'Shape':<14} {'RMS':>8} {'vs Cyl':>8} {'Holes':>6}")
    print("-" * 70)
    for r in sorted(recs, key=lambda x: x["improvement"]):
        imp = r["improvement"]
        imp_str = f"{imp:+.2f}c" if imp != 0 else "best"
        print(f"{r['instrument']:<22} {r['recommended_shape']:<14} {r['rms']:>6.2f}c {imp_str:>8} {len(r['hole_positions']):>4}")
    print("-" * 70)
    non_cyl = [r for r in recs if r["recommended_shape"] != "cylindrical"]
    print(f"Recommend non-cylindrical bore for {len(non_cyl)}/{len(recs)} instruments.")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark unconventional bore shapes")
    parser.add_argument("--quick", action="store_true", help="Quick test: 2 instruments, 3 shapes")
    parser.add_argument("--no-dask", action="store_true", help="Run locally without Dask")
    parser.add_argument("--scheduler", default=DASK_SCHEDULER, help="Dask scheduler address")
    parser.add_argument("--shapes", nargs="+", default=list(SHAPES.keys()), choices=list(SHAPES.keys()),
                        help="Shapes to test")
    parser.add_argument("--instruments", nargs="+", default=None, help="Instruments (default: all non-chromatic)")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    from backend.benchmark_all import INSTRUMENTS
    all_inst = sorted(k for k, v in INSTRUMENTS.items() if not v.get("_chromatic"))
    instrument_names = args.instruments or all_inst
    shapes = args.shapes

    if args.quick:
        instrument_names = instrument_names[:2]
        shapes = [s for s in shapes if s in ("cylindrical", "conical", "exponential")][:3]

    scheduler = args.scheduler

    print(f"Instruments ({len(instrument_names)}): {instrument_names}")
    print(f"Shapes ({len(shapes)}): {shapes}")
    print(f"Total tasks: {len(instrument_names) * len(shapes)}")
    print(f"Dask: {'disabled' if args.no_dask else f'enabled ({DASK_SCHEDULER})'}")

    if args.no_dask:
        results = run_local(instrument_names, shapes)
    else:
        results = run_dask(instrument_names, shapes, scheduler=scheduler)

    print_table(results)

    output_path = args.output or os.path.join("scripts",
        f"benchmark_unconventional_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    failures = [r for r in results if r.get("rms", 0) >= 1e5]
    if failures:
        print(f"\n{len(failures)} failures:")
        for f in failures:
            print(f"  {f['instrument']:22s} / {f['shape']:12s}: {f.get('error', '?')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
