"""Run chalumier designs on a remote Dask cluster (Kalle's workers).

Ships OUR fixed wrapper (1800 s timeout, -Xmx2g) to each worker at runtime so
designs do not hit the old 600 s cap in the worker's own checkout. It never
modifies the remote repo.

Usage:
    python scripts/chalumier_design_remote.py --probe
    python scripts/chalumier_design_remote.py --presets d_whistle
    python scripts/chalumier_design_remote.py --presets d_whistle,recorder
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from distributed import Client

ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "woodwind_designer" / "engine" / "chalumier_wrapper.py"


def _wrapper_source() -> str:
    return WRAPPER.read_text(encoding="utf-8")


def probe(worker_address: str, wrapper_src: str) -> dict:
    """On a remote worker: ship the wrapper, verify jar/java/presets."""
    import shutil
    import os
    from pathlib import Path

    tmp = tempfile.mkdtemp(prefix="wdw_")
    try:
        mod_path = os.path.join(tmp, "chalumier_wrapper.py")
        Path(mod_path).write_text(wrapper_src, encoding="utf-8")
        sys.path.insert(0, tmp)
        import importlib.util

        spec = importlib.util.spec_from_file_location("chalumier_wrapper", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        chalumier_dir = os.path.join(os.getcwd(), "chalumier")
        d = mod.ChalumierDesigner(chalumier_dir=chalumier_dir)
        jar = d._find_jar()
        return {
            "worker": worker_address,
            "cwd": os.getcwd(),
            "jar_found": str(jar) if jar else None,
            "available": d.is_available(),
            "presets": sorted(d.list_presets().keys()),
        }
    except Exception as e:  # noqa: BLE001 - report probe failures per worker
        return {"worker": worker_address, "error": str(e)[:200]}
    finally:
        try:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass


def design_one(preset: str, output_dir: str, wrapper_src: str) -> dict:
    """On a remote worker: ship the wrapper and run one design."""
    import os
    import shutil
    from pathlib import Path

    tmp = tempfile.mkdtemp(prefix="wdw_")
    try:
        mod_path = os.path.join(tmp, "chalumier_wrapper.py")
        Path(mod_path).write_text(wrapper_src, encoding="utf-8")
        sys.path.insert(0, tmp)
        import importlib.util
        import time

        spec = importlib.util.spec_from_file_location("chalumier_wrapper", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        chalumier_dir = os.path.join(os.getcwd(), "chalumier")
        d = mod.ChalumierDesigner(chalumier_dir=chalumier_dir)
        t0 = time.time()
        r = d.design(preset, output_dir=output_dir)
        return {
            "preset": preset,
            "success": r.success,
            "elapsed_s": round(time.time() - t0, 1),
            "length_m": r.length,
            "n_bore": len(r.bore_profile),
            "n_holes": len(r.hole_positions),
            "svg": r.svg_path,
            "json": r.json_path,
            "log_tail": (r.log or "")[-200:],
        }
    except Exception as e:  # noqa: BLE001 - report per-preset failures
        return {"preset": preset, "success": False, "error": str(e)[:200]}
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scheduler", default="tcp://100.100.66.117:8786")
    ap.add_argument("--presets", default="d_whistle")
    ap.add_argument("--probe", action="store_true", help="Capability check only")
    ap.add_argument("--output-root", default=None,
                    help="Remote output root (default: <worker cwd>/chalumier/test-output/dask-designs)")
    args = ap.parse_args()

    client = Client(args.scheduler, timeout=30)
    workers = sorted(client.scheduler_info()["workers"].keys())
    print(f"[remote] scheduler={args.scheduler} workers={len(workers)}", flush=True)
    wrapper_src = _wrapper_source()

    if args.probe:
        futures = {w: client.submit(probe, w, wrapper_src, workers=[w]) for w in workers}
        for w, f in futures.items():
            try:
                res = f.result(timeout=60)
                print(f"[probe] {w}: {res}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[probe] {w}: FAILED {e}", flush=True)
        client.close()
        return

    presets = [p.strip() for p in args.presets.split(",") if p.strip()]
    out_root = args.output_root or "chalumier/test-output/dask-designs"

    futures = {}
    for p in presets:
        out = os.path.join(out_root, p)
        futures[p] = client.submit(design_one, p, out, wrapper_src)
        print(f"[remote] submitted {p} -> {out}", flush=True)

    results = {}
    for p, f in futures.items():
        try:
            results[p] = f.result(timeout=7200)
        except Exception as e:  # noqa: BLE001
            results[p] = {"preset": p, "success": False, "error": str(e)[:200]}

    for p, r in results.items():
        st = "OK" if r.get("success") else "FAIL"
        print(f"[remote] {p}: {st} len={r.get('length_m', 0.0):.3f}m "
              f"n_bore={r.get('n_bore', 0)} n_holes={r.get('n_holes', 0)} "
              f"{r.get('elapsed_s', 0):.0f}s", flush=True)
    client.close()


if __name__ == "__main__":
    main()
