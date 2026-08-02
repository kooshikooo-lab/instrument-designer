"""Run chalumier designs for all presets in parallel via a local Dask cluster.

Each preset design (JDK 17 + chalumier shadow JAR) is dispatched to a worker
process. Results are serialized to JSON for downstream comparison with our TMM.

Usage:
    python scripts/benchmark_chalumier_dask.py                 # all presets, 3 workers
    python scripts/benchmark_chalumier_dask.py --workers 2 --presets d_whistle,recorder
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from distributed import Client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PRESETS = [
    "d_whistle",
    "d_major_flute",
    "e_minor_flute",
    "recorder",
    "folk_shawm",
    "simple_shawm",
]


def _design_one(preset: str, output_root: str) -> dict:
    from woodwind_designer.engine.chalumier_wrapper import ChalumierDesigner

    out = os.path.join(output_root, preset)
    d = ChalumierDesigner()
    t0 = time.time()
    r = d.design(preset, output_dir=out)
    return {
        "preset": preset,
        "success": r.success,
        "elapsed_s": round(time.time() - t0, 1),
        "svg": r.svg_path,
        "json": r.json_path,
        "length_m": r.length,
        "n_bore": len(r.bore_profile),
        "n_holes": len(r.hole_positions),
        "bore": r.bore_profile,
        "hole_positions": r.hole_positions,
        "hole_diameters": r.hole_diameters,
        "log_tail": (r.log or "")[-300:],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--output-root", default=str(ROOT / "chalumier" / "test-output" / "dask-designs"))
    ap.add_argument("--presets", default=",".join(PRESETS))
    args = ap.parse_args()

    presets = [p.strip() for p in args.presets.split(",") if p.strip()]
    os.makedirs(args.output_root, exist_ok=True)

    client = Client(processes=True, n_workers=args.workers, threads_per_worker=1)
    info = client.scheduler_info()
    print(f"[dask] workers: {len(info.get('workers', {}))}", flush=True)

    futures = {p: client.submit(_design_one, p, args.output_root) for p in presets}
    results = {}
    for p, fut in futures.items():
        try:
            results[p] = fut.result(timeout=2400)
        except Exception as e:  # noqa: BLE001 - report per-preset failures
            results[p] = {"preset": p, "success": False, "error": str(e)}

    out_path = os.path.join(args.output_root, "results.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    for p, r in results.items():
        status = "OK" if r.get("success") else "FAIL"
        print(
            f"[dask] {p}: {status} len={r.get('length_m', 0.0):.3f}m "
            f"n_bore={r.get('n_bore', 0)} n_holes={r.get('n_holes', 0)} "
            f"{r.get('elapsed_s', 0):.0f}s",
            flush=True,
        )
    print(f"[dask] WROTE {out_path}", flush=True)
    client.close()


if __name__ == "__main__":
    main()
