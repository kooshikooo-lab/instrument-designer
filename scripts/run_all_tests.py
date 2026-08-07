"""Resource-aware, category-organized test runner.

Runs the test matrix (docs/TEST_MATRIX.md) category by category, sequentially,
with a health gate so test batches never starve other tasks on this machine
(16 cores / 16 GB, shared with the GitHub monitor and Dask work).

Categories are organized by subsystem (server, tmm, physics, optimizer, ...)
and each has a tier:

    low      -> safe to run any time, sequential
    medium   -> sequential, limited; one batch at a time
    heavy    -> ON-DEMAND ONLY (never auto-run)

A health gate checks CPU load, free RAM, and other heavy processes before each
command and skips the run unless --force is given. Every command has a hard
subprocess timeout so nothing hangs the machine.

Usage:
    python scripts/run_all_tests.py --tier low            # scheduled daily sweep
    python scripts/run_all_tests.py --category server     # one category
    python scripts/run_all_tests.py --tier heavy --force  # explicit heavy run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "test_output" / "testing"

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

PY = sys.executable
PYTEST = [PY, "-m", "pytest"]


def _pyt(*files, extra=()):
    return PYTEST + [str(ROOT / "tests" / f) for f in files] + list(extra) + ["-q", "--tb=short"]


# name -> (tier, description, [commands])  each command is a list of argv
CATEGORIES = {
    "server": {
        "tier": "low",
        "desc": "Design server REST endpoints (optimize/start, status, evaluate, presets, cache).",
        "commands": [
            _pyt("test_server_routes.py"),
            [PY, "-c", "from woodwind_designer.engine.design_server import app; print('server import OK')"],
        ],
    },
    "tmm": {
        "tier": "low",
        "desc": "TMM acoustics engine (chalumier port): impedance/register behavior.",
        "commands": [_pyt("test_tmm.py")],
    },
    "physics": {
        "tier": "low",
        "desc": "Physics modules + coordinate conventions (chalumier/internal/OpenWind).",
        "commands": [_pyt("test_properties.py")],
    },
    "architecture": {
        "tier": "low",
        "desc": "Regression/structure: basic functionality, speed of sound, median-correction removal.",
        "commands": [_pyt("test_architecture.py")],
    },
    "instruments": {
        "tier": "low",
        "desc": "Instrument library save/load + registry integrity smoke.",
        "commands": [
            [PY, "-c",
             "from woodwind_designer.engine.instrument_library import LIBRARY, save_novel_instrument; "
             "print(f'instrument_library OK: {len(LIBRARY)} entries')"],
        ],
    },
    "chalumier": {
        "tier": "low",
        "desc": "chalumier JVM availability + preset discovery (no JVM design).",
        "commands": [
            [PY, "-c",
             "from woodwind_designer.engine.chalumier_wrapper import ChalumierDesigner; "
             "d = ChalumierDesigner(); print('is_available:', d.is_available(), 'presets:', len(d.list_presets()))"],
        ],
    },
    "jax": {
        "tier": "low",
        "desc": "JAX optimizer import + tiny evaluation smoke.",
        "commands": [
            [PY, "-c", "import backend.jax_optimizer; print('jax_optimizer import OK')"],
        ],
    },
    "comparison": {
        "tier": "medium",
        "desc": "AI/ML optimization family comparison (Bayesian, neural, RL, gradient-free).",
        "commands": [
            _pyt("test_ai_methods_comparison.py", extra=["-m", "comparison", "-s"]),
        ],
    },
    "optimizer": {
        "tier": "medium",
        "desc": "Two-phase / Phase-2 objective tests + optional quick smoke (slow).",
        "commands": [
            _pyt("test_phase2_objective.py"),
        ],
    },
    "openwind": {
        "tier": "medium",
        "desc": "OpenWind FEM vs TMM validation (register+1, reed agreement, register vent).",
        "commands": [_pyt("test_openwind_solver.py")],
    },
    "stl": {
        "tier": "medium",
        "desc": "CadQuery STL export: cylindrical/conical/parametric bore with holes.",
        "commands": [_pyt("test_cadquery_instrument.py")],
    },
    "regression": {
        "tier": "medium",
        "desc": "run_tests.py full regression (pytest + benchmark smoke + dask help + server import + part5).",
        "commands": [[PY, str(ROOT / "run_tests.py")]],
    },
    "unconventional": {
        "tier": "heavy",
        "desc": "Full unconventional bore-shape benchmark (serial). On-demand only.",
        "commands": [[PY, str(ROOT / "backend" / "benchmark_unconventional_shapes.py")]],
    },
    "chalumier-design": {
        "tier": "heavy",
        "desc": "chalumier design sweep, all 6 presets, 1 worker (JVM). On-demand only.",
        "commands": [[PY, str(ROOT / "scripts" / "benchmark_chalumier_dask.py"), "--workers", "1"]],
    },
    "pareto": {
        "tier": "heavy",
        "desc": "Pareto sweep across instruments. On-demand only.",
        "commands": [[PY, str(ROOT / "scripts" / "pareto_sweep_all.py")]],
    },
}

TIER_TIMEOUT_S = {"low": 900, "medium": 1800, "heavy": 7200}


def branch_and_commit() -> tuple[str, str]:
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, cwd=ROOT)
        b = r.stdout.strip()
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, cwd=ROOT)
        c = r.stdout.strip()
        return b, c
    except Exception:
        return "unknown", "unknown"


def health_check(force: bool) -> tuple[bool, str]:
    """Return (ok, reason). If psutil missing, assume ok."""
    if psutil is None:
        return True, "psutil missing; health gate disabled"
    load = psutil.cpu_percent(interval=0.5)
    avail = psutil.virtual_memory().available / (1024 ** 3)
    heavy = []
    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            if p.info["name"] in ("java.exe", "node.exe", "python.exe") and p.info["pid"] != os.getpid():
                if p.info["memory_info"] and p.info["memory_info"].rss > 300 * 1024 * 1024:
                    heavy.append(f"{p.info['name']} pid={p.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if force:
        return True, f"force (load={load:.0f}% ram_free={avail:.1f}G heavy={heavy or 'none'})"
    if load > 30:
        return False, f"CPU load {load:.0f}% > 30%"
    if avail < 4.0:
        return False, f"free RAM {avail:.1f}G < 4G"
    if heavy:
        return False, f"heavy process(es) running: {heavy}"
    return True, f"ok (load={load:.0f}% ram_free={avail:.1f}G)"


def run_command(cmd: list[str], timeout_s: int) -> dict:
    t0 = time.time()
    note = ""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=ROOT)
        rc = r.returncode
        if rc != 0:
            note = (r.stdout + "\n" + r.stderr).strip()[-500:]
        return {"cmd": " ".join(cmd), "status": "PASS" if rc == 0 else "FAIL",
                "rc": rc, "elapsed_s": round(time.time() - t0, 1), "note": note}
    except subprocess.TimeoutExpired:
        return {"cmd": " ".join(cmd), "status": "TIMEOUT", "rc": -1,
                "elapsed_s": round(time.time() - t0, 1), "note": f"killed after {timeout_s}s"}
    except Exception as e:  # noqa: BLE001
        return {"cmd": " ".join(cmd), "status": "ERROR", "rc": -1,
                "elapsed_s": round(time.time() - t0, 1), "note": str(e)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", choices=["low", "medium", "heavy", "all"], default="all",
                    help="Filter categories by tier. Default: all (auto-run uses low/medium).")
    ap.add_argument("--category", nargs="*", choices=sorted(CATEGORIES),
                    help="Run only these categories (overrides --tier).")
    ap.add_argument("--force", action="store_true", help="Run even if health gate says busy.")
    ap.add_argument("--timeout-per-cmd", type=int, default=0,
                    help="Override per-command timeout in seconds (0 = tier default).")
    ap.add_argument("--output-dir", default=str(REPORT_DIR))
    args = ap.parse_args()

    if args.category:
        names = args.category
    else:
        names = [n for n, c in CATEGORIES.items() if args.tier == "all" or c["tier"] == args.tier]

    os.makedirs(args.output_dir, exist_ok=True)
    branch, commit = branch_and_commit()
    started = datetime.now(timezone.utc).isoformat()

    ok, reason = health_check(args.force)
    print(f"[gate] {reason}")
    if not ok:
        print("[gate] SKIPPING run (pass --force to override).")
        sys.exit(2)

    results = {"run": {"branch": branch, "commit": commit, "started_utc": started,
                       "finished_utc": None, "host": os.environ.get("COMPUTERNAME", "")},
               "categories": []}
    overall_status = "PASS"
    for name in names:
        cat = CATEGORIES[name]
        print(f"\n== {name} [{cat['tier']}] ==")
        t0 = time.time()
        cmd_results = []
        for cmd in cat["commands"]:
            ok2, reason2 = health_check(args.force)
            if not ok2:
                print(f"  [gate] busy mid-batch ({reason2}); skipping {cmd[0]}...")
                cmd_results.append({"cmd": " ".join(cmd), "status": "SKIP", "rc": -2,
                                    "elapsed_s": 0.0, "note": f"busy: {reason2}"})
                continue
            timeout = args.timeout_per_cmd or TIER_TIMEOUT_S[cat["tier"]]
            print(f"  -> {' '.join(cmd[:4])}... (timeout {timeout}s)")
            cmd_results.append(run_command(cmd, timeout))
            r = cmd_results[-1]
            print(f"     {r['status']} ({r['elapsed_s']}s)" + (f" note={r['note'][:120]}" if r["note"] else ""))
        cat_status = "PASS" if all(r["status"] == "PASS" for r in cmd_results) else "FAIL"
        if cat_status == "FAIL":
            overall_status = "FAIL"
        results["categories"].append({"name": name, "tier": cat["tier"], "desc": cat["desc"],
                                      "status": cat_status,
                                      "elapsed_s": round(time.time() - t0, 1),
                                      "commands": cmd_results})

    results["run"]["finished_utc"] = datetime.now(timezone.utc).isoformat()
    results["run"]["overall_status"] = overall_status
    out_path = os.path.join(args.output_dir, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"TEST RUN {overall_status}  (branch={branch} @ {commit})")
    for c in results["categories"]:
        print(f"  {c['status']:4s} {c['name']:20s} {c['elapsed_s']:7.1f}s")
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()
