"""
Laptop startup script -- follows Desktop's coordination workflow.

Starts LAN chat, verifies imports, checks Tailscale/Dask, and broadcasts
startup status to Desktop per the coordination protocol.

Usage:
    python scripts/startup.py
    python scripts/startup.py --desktop-ip 100.69.113.41
    python scripts/startup.py --skip-chat --skip-server
"""

import argparse, json, os, socket, subprocess, sys, threading, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_PORT = 9123
DESKTOP_IPS = ["100.69.113.41", "100.100.66.117", "192.168.1.100"]
MY_NAME = "laptop"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def banner():
    print("=" * 60)
    print(f"  LAPTOP STARTUP  --  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

# ---------------------------------------------------------------------------
# 1. Git
# ---------------------------------------------------------------------------

def check_git():
    log("[1] Git state")
    for cmd in [
        "git fetch origin",
        "git status --short",
        "git branch --show-current",
        "git log --oneline -3",
    ]:
        parts = cmd.split()
        try:
            r = subprocess.run(parts, capture_output=True, text=True, timeout=15)
            out = (r.stdout or "").strip()[:200]
            if out:
                log(f"  $ {cmd} -> {out.split(chr(10))[0]}")
        except Exception as e:
            log(f"  $ {cmd} -> ERROR: {e}")

# ---------------------------------------------------------------------------
# 2. Imports (from Coordination Workflow: import tests)
# ---------------------------------------------------------------------------

IMPORT_CHECKS = {
    "Current branch optimizers": [
        "from backend.jax_optimizer import refine_sequential",
        "from backend.pareto_optimizer import pareto_sweep",
    ],
    "Desktop architecture": [
        "from backend.core.network import AcousticNetwork",
        "from backend.physics.losses import KeefeLoss",
        "from backend.solvers.tmm_solver import TMMSolver",
        "from backend.two_phase_optimizer import two_phase_optimize",
    ],
    "STL + CadQuery": [
        "from backend.stl_export import make_capped_bore, export_bore_only",
        "from backend.cadquery_export import INSTRUMENTS, make_instrument_stl",
    ],
    "Dask": [
        "from distributed import Client, get_client",
    ],
}

def check_imports():
    log("[2] Import verification")
    ok = True
    for group, stmts in IMPORT_CHECKS.items():
        for stmt in stmts:
            try:
                exec(stmt, {}, {})
                log(f"  OK  [{group}] {stmt.split()[-1]}")
            except Exception as e:
                log(f"  --  [{group}] {stmt.split()[-1]} skipped ({short_err(e)})")
    return ok

def short_err(e):
    s = str(e)
    if "No module named" in s:
        return "no module"
    if "cannot import name" in s:
        return "not on this branch"
    return type(e).__name__

# ---------------------------------------------------------------------------
# 3. LAN Chat server
# ---------------------------------------------------------------------------

def start_server(port=DEFAULT_PORT):
    log(f"[3] Starting LAN chat server on port {port}")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind(("0.0.0.0", port))
        srv.listen(5)
    except OSError as e:
        log(f"  Port {port} unavailable: {e}")
        srv.close()
        return

    def handle(conn, addr):
        log(f"  Connection from {addr}")
        try:
            buf = ""
            while True:
                data = conn.recv(4096).decode()
                if not data: break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if not line.strip(): continue
                    m = json.loads(line)
                    log(f"  [{m.get('from','?')}] {m.get('text','')[:100]}")
                    conn.sendall((json.dumps({"from": MY_NAME, "text": "ACK"}) + "\n").encode())
        except: pass
        finally: conn.close()

    def serve():
        while True:
            try:
                conn, addr = srv.accept()
                threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
            except OSError:
                break

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    log("  Server listening")

# ---------------------------------------------------------------------------
# 4. Tailscale
# ---------------------------------------------------------------------------

def check_tailscale():
    log("[4] Tailscale")
    try:
        r = subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for line in r.stdout.strip().split("\n")[:3]:
                log(f"  {line}")
            return True
        else:
            log("  not available")
            return False
    except FileNotFoundError:
        log("  not installed")
        return False
    except Exception as e:
        log(f"  {e}")
        return False

# ---------------------------------------------------------------------------
# 5. Dask
# ---------------------------------------------------------------------------

def check_dask():
    log("[5] Dask")
    pidf = PROJECT_ROOT / "scripts" / "dask_scheduler.pid"
    if pidf.exists():
        pid = pidf.read_text().strip()
        try:
            os.kill(int(pid), 0)
            log(f"  scheduler running (PID {pid})")
        except: log(f"  stale PID file ({pid})")
    else:
        log("  no local scheduler (connect to desktop's)")

# ---------------------------------------------------------------------------
# 6. Broadcast to Desktop
# ---------------------------------------------------------------------------

def broadcast(ip, port=DEFAULT_PORT):
    log(f"[6] Notifying desktop at {ip}:{port}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((ip, port))
        msg = json.dumps({"from": MY_NAME, "text": "LAPTOP STARTUP"}) + "\n"
        s.sendall(msg.encode())
        buf = ""
        deadline = time.time() + 4
        while time.time() < deadline:
            try:
                chunk = s.recv(4096).decode()
                if not chunk: break
                buf += chunk
                if "ACK" in buf:
                    log("  desktop acknowledged")
                    s.close()
                    return
            except socket.timeout: break
        s.close()
        log("  no ACK from desktop")
    except ConnectionRefusedError:
        log("  desktop not reachable (server down?)")
    except socket.timeout:
        log("  connection timed out")
    except Exception as e:
        log(f"  {e}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--desktop-ip", default="", help="Desktop's Tailscale IP")
    parser.add_argument("--skip-chat", action="store_true", help="Skip LAN chat server")
    parser.add_argument("--skip-check", action="store_true", help="Skip connectivity check")
    args = parser.parse_args()

    banner()
    check_git()
    check_imports()

    if not args.skip_chat:
        start_server()
    else:
        log("[3] Skipping LAN chat server")

    ts_ok = check_tailscale()
    check_dask()

    if not args.skip_check:
        ip = args.desktop_ip or (DESKTOP_IPS[0] if ts_ok else "")
        if ip:
            broadcast(ip)
        else:
            log("[6] No desktop IP -- skipping broadcast")

    print()
    print("=" * 60)
    print("  Startup complete.")
    print("=" * 60)

if __name__ == "__main__":
    main()
