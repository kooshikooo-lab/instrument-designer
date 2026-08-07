"""Spawn a detached Dask worker attached to a scheduler.

Mirrors start_scheduler.py: subprocess.Popen with an argv list avoids the
shell/Start-Process mangling of `tcp://` scheduler addresses on Windows.

    python scripts/spawn_worker.py [tcp://host:8786] [suffix]
"""
import os
import subprocess
import sys

scheduler = sys.argv[1] if len(sys.argv) > 1 else "tcp://100.69.113.41:8786"
suffix = sys.argv[2] if len(sys.argv) > 2 else "1"

here = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(here, f"dask_worker_{suffix}.log")
proc = subprocess.Popen(
    [sys.executable, os.path.join(here, "start_worker.py"), scheduler],
    stdout=open(log_path, "w"),
    stderr=subprocess.STDOUT,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
pid_path = os.path.join(here, f"dask_worker_{suffix}.pid")
with open(pid_path, "w") as f:
    f.write(str(proc.pid))

print(f"Worker {suffix} started (PID {proc.pid}), log: {log_path}")
