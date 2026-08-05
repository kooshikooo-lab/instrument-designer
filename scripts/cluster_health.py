"""Probe a Dask scheduler and print JSON health (reachable + worker count).

Used by sync.ps1 / start-cluster.ps1 to fold cluster status into the
tailscale health verdict. Exits 1 when the scheduler is unreachable.

    python scripts/cluster_health.py [--scheduler tcp://100.69.113.41:8786] [--timeout 5]
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheduler", default="tcp://100.69.113.41:8786")
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()

    try:
        from distributed import Client
    except ImportError as e:
        print(json.dumps({"reachable": False, "error": f"distributed not installed: {e}",
                          "workers": 0, "addresses": []}))
        sys.exit(1)

    try:
        c = Client(a.scheduler, timeout=a.timeout)
        try:
            info = c.scheduler_info()
            workers = info.get("workers", {})
            addrs = sorted(workers.keys())
            print(json.dumps({"reachable": True, "workers": len(workers), "addresses": addrs}))
        finally:
            c.close()
    except Exception as e:
        print(json.dumps({"reachable": False, "error": str(e),
                          "workers": 0, "addresses": []}))
        sys.exit(1)


if __name__ == "__main__":
    main()
