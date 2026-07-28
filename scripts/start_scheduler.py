"""Start Dask scheduler on port 9797."""
import subprocess, sys, os

log_path = os.path.join(os.path.dirname(__file__), "dask_scheduler.log")
proc = subprocess.Popen(
    [sys.executable, "-m", "distributed.cli.dask_scheduler",
     "--port", "9797", "--dashboard-address", ":9798"],
    stdout=open(log_path, "w"),
    stderr=subprocess.STDOUT,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)

pid_path = os.path.join(os.path.dirname(__file__), "dask_scheduler.pid")
with open(pid_path, "w") as f:
    f.write(str(proc.pid))

print(f"Scheduler started (PID {proc.pid}), log: {log_path}")
