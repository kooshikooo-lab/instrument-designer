"""Start the desktop's Dask workers as compute on the shared (laptop) cluster.

The scheduler lives on the laptop (Kalle's machine, Tailscale 100.100.66.117).
These workers connect to it over Tailscale and register as tcp://100.69.113.41:*.
A reconnect loop keeps the desktop contributing even across laptop reboots
(scheduler downtime) or Tailscale blips.

Sizing matches the desktop (Ryzen 7 1800X, 16 GB):
    6 workers x 2 threads = 12 threads, memory-limit 2.5 GB each (15 GB max)

Each running design is a single JVM on one worker, so worker count = parallelism,
not single-design speed; RAM is the real ceiling (~2.5-3 GB per concurrent design).

Usage:
    python scripts/start_desktop_cluster.py [--workers 6] [--threads 2] [--mem 2.5GB]
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scheduler", default="tcp://100.100.66.117:8786")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--mem", default="2.5GB")
    ap.add_argument("--retry-s", type=float, default=15.0)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    logdir = root / "test_output" / "testing"
    logdir.mkdir(parents=True, exist_ok=True)

    print(
        f"[desktop-workers] scheduler={args.scheduler} "
        f"workers={args.workers}x{args.threads} mem={args.mem}",
        flush=True,
    )
    while True:
        log = open(logdir / "desktop_cluster_worker.log", "a", encoding="utf-8", buffering=1)
        p = subprocess.Popen(
            [
                sys.executable, "-m", "distributed.cli.dask_worker",
                args.scheduler,
                "--nworkers", str(args.workers),
                "--nthreads", str(args.threads),
                "--memory-limit", args.mem,
            ],
            cwd=str(root),
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        (logdir / "desktop_cluster.pid").write_text(
            f"workers={p.pid}\nscheduler={args.scheduler}\n", encoding="utf-8"
        )
        code = p.wait()
        log.close()
        print(f"[desktop-workers] worker-manager exited ({code}); "
              f"reconnecting in {args.retry_s:.0f}s", flush=True)
        time.sleep(args.retry_s)


if __name__ == "__main__":
    main()
