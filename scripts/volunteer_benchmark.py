"""Volunteer-aware Dask benchmark runner.

Wraps the cross-branch benchmark (scripts/dask_benchmark.py) with volunteer idle/AC gating.
Designed to run on donor machines: only submits tasks when machine is idle + on AC power.

Usage:
    python scripts/volunteer_benchmark.py [--scheduler tcp://HOST:8786] [--check] [--once]

Modes:
  --check    Print gate state and exit (0 = donate, 1 = not donating)
  --once     Donate for one benchmark cycle then exit
  (default)  Continuous: run benchmark cycles while idle+AC, pause when active
"""
from __future__ import annotations

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# ---- Project path setup ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---- Volunteer gating (from volunteer_compute.py) ----
def _windows_input_idle_seconds() -> float:
    try:
        import ctypes
        from ctypes import wintypes

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

        last = LASTINPUTINFO()
        last.cbSize = ctypes.sizeof(LASTINPUTINFO)
        user32 = ctypes.windll.user32
        if not user32.GetLastInputInfo(ctypes.byref(last)):
            return -1.0
        ticks = user32.GetTickCount()
        return max(0.0, (ticks - last.dwTime) / 1000.0)
    except Exception:
        return -1.0


def on_ac_power() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class SYSTEM_POWER_STATUS(ctypes.Structure):
                _fields_ = [
                    ("ACLineStatus", wintypes.BYTE),
                    ("BatteryFlag", wintypes.BYTE),
                    ("BatteryLifePercent", wintypes.BYTE),
                    ("SystemStatusFlag", wintypes.BYTE),
                    ("BatteryLifeTime", wintypes.DWORD),
                    ("BatteryFullLifeTime", wintypes.DWORD),
                ]

            status = SYSTEM_POWER_STATUS()
            kernel32 = ctypes.windll.kernel32
            if kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                return status.ACLineStatus == 1
        except Exception:
            pass
    return True


def is_idle(min_idle_seconds: float = 300.0, require_ac: bool = True) -> tuple[bool, str]:
    if require_ac and not on_ac_power():
        return False, "on battery"
    idle = _windows_input_idle_seconds()
    if idle >= 0.0 and idle < min_idle_seconds:
        return False, f"active (last input {idle:.0f}s ago)"
    return True, "idle and on AC"


# ---- Volunteer benchmark runner ----
def run_benchmark_cycle(scheduler: str, instruments: str | None = None,
                        optimizers: str | None = None, branch: str | None = None) -> int:
    """Run one benchmark cycle via dask_benchmark.py."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "dask_benchmark.py"),
        "--scheduler", scheduler,
    ]
    if instruments:
        cmd += ["--instruments", instruments]
    if optimizers:
        cmd += ["--optimizers", optimizers]
    if branch:
        cmd += ["--branch", branch]

    print(f"[volunteer-benchmark] Running: {' '.join(cmd)}", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("[volunteer-benchmark] Benchmark cycle timed out (1h)", flush=True)
        return 1
    except Exception as e:
        print(f"[volunteer-benchmark] Benchmark cycle failed: {e}", flush=True)
        return 1


def run_surrogate_cycle(scheduler: str, n_samples: int = 500,
                        mode: str = "mixed", out_dir: str | None = None) -> int:
    """Run one surrogate data generation cycle via generate_surrogate_data_laptop.py
    (adapted for Dask if needed)."""
    # For now, run locally on the volunteer machine (no Dask scatter needed for this)
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "generate_surrogate_data_laptop.py"),
        "--n", str(n_samples),
        "--mode", mode,
    ]
    if out_dir:
        cmd += ["--out", out_dir]

    print(f"[volunteer-benchmark] Surrogate gen: {' '.join(cmd)}", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("[volunteer-benchmark] Surrogate cycle timed out (1h)", flush=True)
        return 1
    except Exception as e:
        print(f"[volunteer-benchmark] Surrogate cycle failed: {e}", flush=True)
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Volunteer-aware Dask benchmark runner")
    ap.add_argument("--scheduler", default=os.environ.get("VOLUNTEER_SCHEDULER", "tcp://127.0.0.1:8786"))
    ap.add_argument("--min-idle", type=float, default=float(os.environ.get("VOLUNTEER_MIN_IDLE", "300")))
    ap.add_argument("--no-ac", action="store_true", help="Disable AC power requirement")
    ap.add_argument("--check", action="store_true", help="Print gate state and exit")
    ap.add_argument("--once", action="store_true", help="Run one cycle then exit")
    ap.add_argument("--mode", choices=["benchmark", "surrogate", "both"], default="both",
                    help="What workload to run")
    ap.add_argument("--instruments", default=None, help="Comma-separated instruments for benchmark")
    ap.add_argument("--optimizers", default=None, help="Comma-separated optimizers for benchmark")
    ap.add_argument("--branch", default=None, help="Branch label for results")
    ap.add_argument("--surrogate-samples", type=int, default=500, help="Samples per surrogate cycle")
    ap.add_argument("--surrogate-mode", choices=["random", "mixed"], default="mixed")
    args = ap.parse_args()

    donate, reason = is_idle(args.min_idle, require_ac=not args.no_ac)
    print(f"[volunteer-benchmark] scheduler={args.scheduler} mode={args.mode} gate={donate} ({reason})", flush=True)

    if args.check:
        return 0 if donate else 1

    if not donate:
        print("[volunteer-benchmark] gates not met; not running", flush=True)
        return 0

    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\n[volunteer-benchmark] === Cycle {cycle_count} ===", flush=True)

            # Re-check gates at start of each cycle
            donate, reason = is_idle(args.min_idle, require_ac=not args.no_ac)
            if not donate:
                print(f"[volunteer-benchmark] gates no longer met: {reason}", flush=True)
                break

            if args.mode in ("benchmark", "both"):
                rc = run_benchmark_cycle(args.scheduler, args.instruments, args.optimizers, args.branch)
                if rc != 0:
                    print(f"[volunteer-benchmark] benchmark cycle exited with {rc}", flush=True)

            # Re-check before surrogate
            donate, reason = is_idle(args.min_idle, require_ac=not args.no_ac)
            if not donate:
                print(f"[volunteer-benchmark] gates no longer met before surrogate: {reason}", flush=True)
                break

            if args.mode in ("surrogate", "both"):
                rc = run_surrogate_cycle(args.scheduler, args.surrogate_samples, args.surrogate_mode)
                if rc != 0:
                    print(f"[volunteer-benchmark] surrogate cycle exited with {rc}", flush=True)

            if args.once:
                break

            # Brief pause between cycles, re-checking gates
            for _ in range(30):
                time.sleep(10)
                donate, reason = is_idle(args.min_idle, require_ac=not args.no_ac)
                if not donate:
                    print(f"[volunteer-benchmark] gates no longer met between cycles: {reason}", flush=True)
                    return 0

    except KeyboardInterrupt:
        print("\n[volunteer-benchmark] Interrupted", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())