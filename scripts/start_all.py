"""Start all session services: Dask scheduler + worker, GitHub monitor, LAN chat server."""
import subprocess, sys, os, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PY = sys.executable

def background(cmd_args, log_name):
    log_path = os.path.join(SCRIPT_DIR, log_name)
    proc = subprocess.Popen(
        [PY] + cmd_args,
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return proc

print("Starting session services...")

# 1. Dask scheduler
proc_sched = background(
    ["-m", "distributed.cli.dask_scheduler", "--port", "9797", "--dashboard-address", ":9798"],
    "dask_scheduler.log"
)
print(f"  Dask scheduler: PID {proc_sched.pid}")

# 2. Dask worker (local, 2 workers)
time.sleep(3)
proc_worker = subprocess.Popen(
    [PY, "-m", "distributed.cli.dask_worker", "tcp://100.69.113.41:9797",
     "--nworkers", "2", "--nthreads", "8"],
    stdout=open(os.path.join(SCRIPT_DIR, "dask_worker.log"), "w"),
    stderr=subprocess.STDOUT,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
print(f"  Dask worker:   PID {proc_worker.pid}")

# 3. GitHub monitor
proc_mon = background(
    [os.path.join(SCRIPT_DIR, "github_monitor.py")],
    "github_monitor.log"
)
print(f"  GitHub monitor: PID {proc_mon.pid}")

# 4. LAN chat server
proc_chat = background(
    [os.path.join(SCRIPT_DIR, "lan_chat.py"), "server"],
    "lan_chat.log"
)
print(f"  LAN chat:       PID {proc_chat.pid}")

print("\nAll services started. Run startup_check.py to verify.")
