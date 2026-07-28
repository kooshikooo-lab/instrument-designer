"""Cross-branch Dask benchmark: runs instrument optimization in parallel.

Usage:
    python scripts/dask_benchmark.py [--scheduler tcp://HOST:8786] [--branch BRANCH] [--instruments all]

Examples:
    # Run all instruments on current branch with local Dask
    python scripts/dask_benchmark.py

    # Run with remote scheduler (desktop workers)
    python scripts/dask_benchmark.py --scheduler tcp://100.100.66.117:8786

    # Run specific instruments
    python scripts/dask_benchmark.py --instruments chalumeau_C,soprano_sax_Bb
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from distributed import Client, get_client, progress


# ============================================================================
# Import benchmark from current branch
# ============================================================================

def get_instruments():
    """Import INSTRUMENTS from benchmark_all.py on current branch."""
    from backend.benchmark_all import INSTRUMENTS
    return INSTRUMENTS


def get_optimizers():
    """Return dict of optimizer_name -> (fn, needs_jax) on current branch."""
    optimizers = {}

    from backend.benchmark_all import sequential, sequential_refined
    optimizers["sequential"] = (sequential, False)
    optimizers["seq_refined"] = (sequential_refined, False)

    # Try to import JAX optimizer (only on experiment/ai-tier1)
    try:
        from backend.jax_optimizer import jax_two_phase_optimize
        optimizers["jax_two_phase"] = (jax_two_phase_optimize, True)
    except ImportError:
        pass

    return optimizers


# ============================================================================
# Dask-parallelized benchmark task
# ============================================================================

def _run_instrument_task(args):
    """Run a single instrument + optimizer combination. Designed for Dask scatter."""
    instrument_name, instrument_cfg, optimizer_name, optimizer_fn, use_jax_bore = args

    import time, math, numpy as np

    result = {
        "instrument": instrument_name,
        "optimizer": optimizer_name,
        "desc": instrument_cfg.get("desc", ""),
    }

    try:
        t0 = time.time()

        if optimizer_name in ("sequential", "seq_refined"):
            out = optimizer_fn(instrument_cfg)
            if len(out) == 5:
                rms, bore_length, hp, hd, dt = out
            else:
                rms, bore_length, hp, dt = out
            result["rms"] = rms
            result["bore_length"] = bore_length
            result["n_holes"] = len(hp)
            result["time"] = dt

        elif optimizer_name == "jax_two_phase":
            cfg = instrument_cfg
            result_opt = optimizer_fn(
                targets=cfg["targets"],
                bore_radius=cfg["bore_radius"],
                outer_diameter=cfg["outer_diameter"],
                hole_diameter=cfg["hole_diameter"],
                hole_length=cfg["hole_length"],
                closed_top=cfg["closed_top"],
                use_jax_bore=use_jax_bore,
                verbose=False,
            )
            result["rms"] = result_opt.get("final_cost", result_opt.get("rms", 1e10))
            result["bore_length"] = result_opt.get("bore_length", 0)
            hp_list = result_opt.get("hole_positions", [])
            result["n_holes"] = len(hp_list) if hp_list else 0
            result["time"] = time.time() - t0

        else:
            result["error"] = f"Unknown optimizer: {optimizer_name}"
            result["rms"] = 1e10
            result["time"] = 0

    except Exception as e:
        result["error"] = str(e)
        result["rms"] = 1e10
        result["time"] = 0

    return result


# ============================================================================
# Main benchmark runner
# ============================================================================

def run_benchmark(scheduler_address, instrument_filter=None, branch_name=None, optimizer_filter=None):
    """Run full cross-branch benchmark via Dask."""
    print("=" * 70)
    print("  CROSS-BRANCH DASK BENCHMARK")
    print("=" * 70)
    print(f"  Scheduler: {scheduler_address}")
    print(f"  Branch: {branch_name or 'current'}")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # Connect to Dask
    client = Client(scheduler_address, timeout=30)
    info = client.scheduler_info()
    print(f"  Workers: {len(info['workers'])}")
    print(f"  Threads: {info['total_threads']}")
    print(f"  Memory:  {info.get('total_memory', 0) / 1e9:.1f} GB")
    print()

    # Get instruments and optimizers from current branch
    INSTRUMENTS = get_instruments()
    optimizers = get_optimizers()

    print(f"  Instruments: {len(INSTRUMENTS)}")
    print(f"  Optimizers:  {list(optimizers.keys())}")
    print()

    # Filter instruments if requested
    if instrument_filter:
        names = [n.strip() for n in instrument_filter.split(",")]
        INSTRUMENTS = {k: v for k, v in INSTRUMENTS.items() if k in names}
        print(f"  Filtered instruments to: {list(INSTRUMENTS.keys())}")
        print()

    # Filter optimizers if requested
    if optimizer_filter:
        opt_names = [n.strip() for n in optimizer_filter.split(",")]
        optimizers = {k: v for k, v in optimizers.items() if k in opt_names}
        print(f"  Filtered optimizers to: {list(optimizers.keys())}")
        print()

    # Build task list: (instrument, optimizer) pairs
    tasks = []
    for inst_name, inst_cfg in INSTRUMENTS.items():
        # Skip chromatic instruments for sequential optimizer
        if inst_cfg.get("_chromatic", False):
            continue
        for opt_name, (opt_fn, needs_jax) in optimizers.items():
            tasks.append((inst_name, inst_cfg, opt_name, opt_fn, needs_jax))

    print(f"  Total tasks: {len(tasks)}")
    print()

    # Submit to Dask
    print("  Submitting tasks...")
    t0 = time.time()
    futures = client.map(_run_instrument_task, tasks)
    results = client.gather(futures)
    total_time = time.time() - t0

    print(f"  Completed in {total_time:.1f}s")
    print()

    # Organize results
    by_instrument = {}
    for r in results:
        inst = r["instrument"]
        if inst not in by_instrument:
            by_instrument[inst] = {"desc": r["desc"], "results": {}}
        by_instrument[inst]["results"][r["optimizer"]] = r

    # Print summary table
    print("=" * 90)
    print("  RESULTS SUMMARY")
    print("=" * 90)
    print(f"\n  {'Instrument':<22} {'Optimizer':<14} {'RMS (c)':>8} {'Time':>8} {'Holes':>6}")
    print(f"  {'-'*22} {'-'*14} {'-'*8} {'-'*8} {'-'*6}")

    all_results = {}
    for inst_name in sorted(by_instrument.keys()):
        data = by_instrument[inst_name]
        for opt_name in ["sequential", "seq_refined", "jax_two_phase"]:
            if opt_name in data["results"]:
                r = data["results"][opt_name]
                rms = r.get("rms", 1e10)
                rms_str = f"{rms:.2f}" if rms < 1e5 else "FAIL"
                t_str = f"{r.get('time', 0):.1f}s"
                holes = r.get("n_holes", "-")
                print(f"  {inst_name:<22} {opt_name:<14} {rms_str:>8} {t_str:>8} {str(holes):>6}")

                key = f"{inst_name}_{opt_name}"
                all_results[key] = {
                    "instrument": inst_name,
                    "optimizer": opt_name,
                    "rms": rms,
                    "time": r.get("time", 0),
                    "n_holes": r.get("n_holes", 0),
                    "bore_length": r.get("bore_length", 0),
                    "desc": r.get("desc", ""),
                }
        print()

    # Save results
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    branch_tag = (branch_name or "current").replace("/", "_")
    result_file = PROJECT_ROOT / "scripts" / f"benchmark_{branch_tag}_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"  Results saved to: {result_file}")

    client.close()
    return all_results


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-branch Dask benchmark")
    parser.add_argument("--scheduler", default="tcp://127.0.0.1:8786",
                        help="Dask scheduler address")
    parser.add_argument("--instruments", default=None,
                        help="Comma-separated instrument names to benchmark")
    parser.add_argument("--optimizers", default=None,
                        help="Comma-separated optimizers to run (sequential,seq_refined,jax_two_phase)")
    parser.add_argument("--branch", default=None,
                        help="Branch name label for results file")
    args = parser.parse_args()

    run_benchmark(args.scheduler, args.instruments, args.branch, args.optimizers)
