"""Run Pareto sweep on all 12 instruments via Dask."""
import sys, os, json, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from distributed import Client
from backend.benchmark_all import INSTRUMENTS
from backend.pareto_optimizer import pareto_sweep


def _pareto_task(args):
    """Run Pareto sweep on a single instrument."""
    inst_name, cfg = args
    try:
        results = pareto_sweep(cfg, n_weights=8, maxiter=100, verbose=False)
        return {
            "instrument": inst_name,
            "desc": cfg.get("desc", ""),
            "closed_top": cfg["closed_top"],
            "results": [
                {"w_int": w, "intonation": inton, "timbre": timb, "bore_length": bore}
                for w, inton, timb, bore in results
            ],
            "error": None,
        }
    except Exception as e:
        return {
            "instrument": inst_name,
            "desc": cfg.get("desc", ""),
            "closed_top": cfg["closed_top"],
            "results": [],
            "error": str(e),
        }


def main():
    scheduler = "tcp://127.0.0.1:8786"
    print("=" * 70)
    print("  PARETO SWEEP — ALL INSTRUMENTS")
    print("=" * 70)

    # Use scheduler if available, otherwise local
    try:
        client = Client(scheduler, timeout=5)
        info = client.scheduler_info()
        n_workers = len(info["workers"])
        print(f"  Workers: {n_workers}, Threads: {info['total_threads']}")
        use_dask = n_workers > 0
    except Exception:
        use_dask = False
        client = None
        print("  Running locally (no Dask scheduler)")
    print()

    # Skip chromatic
    tasks = [
        (name, cfg) for name, cfg in INSTRUMENTS.items()
        if not cfg.get("_chromatic", False)
    ]

    print(f"  Running Pareto sweep on {len(tasks)} instruments...")
    t0 = time.time()
    if use_dask:
        futures = client.map(_pareto_task, tasks)
        results = client.gather(futures)
    else:
        results = [_pareto_task(t) for t in tasks]
    total_time = time.time() - t0
    print(f"  Completed in {total_time:.1f}s")
    print()

    # Summary table
    print(f"  {'Instrument':<22} {'Type':<10} {'Int@w=1':>8} {'Int@w=0':>8} {'Tim@w=0':>8} {'Tradeoff':>10}")
    print(f"  {'-'*22} {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")

    all_results = {}
    for r in sorted(results, key=lambda x: x["instrument"]):
        inst = r["instrument"]
        ctype = "closed" if r["closed_top"] else "open"
        if r["error"]:
            print(f"  {inst:<22} {ctype:<10} FAIL: {r['error'][:40]}")
            continue

        pts = r["results"]
        if not pts:
            print(f"  {inst:<22} {ctype:<10} NO DATA")
            continue

        # w_int=1.0 is intonation-only, w_int=0.0 is timbre-only
        int_only = pts[-1]["intonation"]  # w=1.0
        timbre_only_int = pts[0]["intonation"]  # w=0.0
        timbre_only_tim = pts[0]["timbre"]

        # Tradeoff = how much intonation degrades when maximizing timbre
        tradeoff = timbre_only_int - int_only
        tradeoff_str = f"{tradeoff:.2f}c" if tradeoff > 0.01 else "flat"

        print(f"  {inst:<22} {ctype:<10} {int_only:>7.2f}c {timbre_only_int:>7.2f}c {timbre_only_tim:>8.4f} {tradeoff_str:>10}")

        all_results[inst] = {
            "type": ctype,
            "desc": r["desc"],
            "int_only_rms": int_only,
            "timbre_only_intonation": timbre_only_int,
            "timbre_only_cost": timbre_only_tim,
            "tradeoff": tradeoff,
            "points": pts,
        }

    # Save
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).parent / f"pareto_sweep_{ts}.json"
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Saved to: {out}")

    if client:
        client.close()
    return all_results


if __name__ == "__main__":
    main()
