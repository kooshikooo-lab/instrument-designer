"""Silent health check for team chat channels (GitHub Discussion #23 + Tailscale).

No pop-ups, no console output. Writes a JSON status log to
REPO_ROOT/scripts/check_team_chat.log and exits with a non-zero code when a
channel is unhealthy.

Usage:
    python scripts/check_team_chat.py           # one-shot check
    python scripts/check_team_chat.py --loop 60 # run every 60 seconds

Desktop shortcut:
    launchers/check_team_chat.bat runs this with pythonw (no window).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_ROOT / "scripts" / "check_team_chat.log"
STATE_FILE = REPO_ROOT / "scripts" / ".tailscale_monitor.json"


def _log(status):
    status["checked_at"] = datetime.now(timezone.utc).isoformat()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(status, ensure_ascii=False) + "\n")
    except Exception as e:
        # Last-resort fallback; still avoid pop-ups.
        try:
            with open(REPO_ROOT / "check_team_chat.error", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()} LOG_FAILED: {e}\n")
        except Exception:
            pass


def _run(cmd, timeout=30):
    """Run a subprocess silently and return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env.setdefault("TEAM_MACHINE", "desktop")
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def _monitor_processes():
    """Find pythonw.exe processes running tailscale_monitor.py."""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*tailscale_monitor.py*' } | Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        out = proc.stdout.strip()
        if not out:
            return []
        data = json.loads(out)
        if isinstance(data, dict):
            return [data]
        return data
    except Exception:
        return []


def _ensure_monitor_running():
    """Start the tailscale monitor in the background if it is not running."""
    procs = _monitor_processes()
    if procs:
        return True, [p.get("ProcessId") for p in procs]
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if not Path(pythonw).exists():
        return False, f"pythonw not found at {pythonw}"
    try:
        subprocess.Popen(
            [pythonw, "scripts/tailscale_monitor.py", "heartbeat"],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(1.0)
        procs = _monitor_processes()
        return bool(procs), [p.get("ProcessId") for p in procs] if procs else "started but not detected"
    except Exception as e:
        return False, str(e)


def _check_github_channel():
    """Check that Discussion #23 sync works."""
    rc, out, err = _run([sys.executable, "scripts/team_chat.py", "sync"], timeout=60)
    ok = rc == 0 and "Error" not in out and "error" not in err.lower()
    return {
        "channel": "github_discussion_23",
        "ok": ok,
        "returncode": rc,
        "error": err if not ok else "",
    }


def _check_tailscale_channel():
    """Check that the Tailscale peer is reachable."""
    rc, out, err = _run([sys.executable, "scripts/tailscale_monitor.py", "test"], timeout=15)
    reachable = rc == 0 and "FAIL" not in out
    return {
        "channel": "tailscale_peer",
        "ok": reachable,
        "returncode": rc,
        "error": out or err if not reachable else "",
    }


def _read_tailscale_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def run_check():
    status = {
        "ok": True,
        "channels": [],
        "monitor_running": {},
        "tailscale_state": _read_tailscale_state(),
    }

    monitor_ok, monitor_info = _ensure_monitor_running()
    status["monitor_running"] = {"ok": monitor_ok, "info": monitor_info}

    github = _check_github_channel()
    tailscale = _check_tailscale_channel()

    status["channels"] = [github, tailscale]
    status["ok"] = github["ok"] and tailscale["ok"] and monitor_ok

    _log(status)
    return status


def main():
    parser = argparse.ArgumentParser(description="Silent team-chat health check")
    parser.add_argument("--loop", type=int, default=0, help="Re-check every N seconds (0 = one-shot)")
    args = parser.parse_args()

    while True:
        status = run_check()
        if not args.loop:
            sys.exit(0 if status["ok"] else 1)
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
