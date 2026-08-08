"""Interruption status report - where did the last turn leave off?

Read-only summary used by Step 0.5 (docs/CONSTRAINTS_AND_PREFERENCES.md):
on any session start or after an interrupted turn, run this to see exactly
what is unfinished before resuming. Never mutates state.

Usage:
    python scripts/resume_check.py              # full report
    python scripts/resume_check.py --cursor     # task cursor block only
    python scripts/resume_check.py --log        # opencode log failure counts only
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOT_STATE = os.path.join(REPO_ROOT, "docs", "session-logs", "BOOT_STATE.md")
TEAM_STATE = os.path.join(REPO_ROOT, "scripts", ".team_state.json")
OPENCODE_LOG = os.path.join(
    os.path.expanduser("~"), ".local", "share", "opencode", "log", "opencode.log"
)

FAILURE_PATTERNS = {
    "Nvidia 502 ResourceExhausted": "Worker local total request limit",
    "DNS ENOTFOUND opencode.ai": "getaddrinfo ENOTFOUND opencode.ai",
    "Internal server error": "Internal server error",
    "Streaming response failed": "Streaming response failed",
    "Rate limit exceeded": "Rate limit exceeded",
}


def read_cursor():
    """Extract the '## Current Task Cursor' block from BOOT_STATE.md."""
    if not os.path.exists(BOOT_STATE):
        return None
    try:
        with open(BOOT_STATE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return None
    out, in_block = [], False
    for line in lines:
        if line.startswith("## Current Task Cursor"):
            in_block = True
            continue
        if in_block and line.startswith("## "):
            break
        if in_block:
            out.append(line.rstrip("\n"))
    while out and (not out[-1].strip() or out[-1].strip() == "---"):
        out.pop()
    text = "\n".join(out).strip()
    return text if text else None


def log_counts():
    """Count known failure patterns in the opencode log (last 24h + total)."""
    if not os.path.exists(OPENCODE_LOG):
        return {"log": None, "recent": {}, "total": {}}
    now = datetime.now(timezone.utc)
    recent, total = {}, {}
    try:
        with open(OPENCODE_LOG, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                for label, pat in FAILURE_PATTERNS.items():
                    if pat in line:
                        total[label] = total.get(label, 0) + 1
                        m = re.match(r"timestamp=([^ ]+)", line)
                        if m:
                            try:
                                ts = datetime.fromisoformat(m.group(1))
                            except ValueError:
                                ts = None
                            if ts is not None and (now - ts).total_seconds() <= 86400:
                                recent[label] = recent.get(label, 0) + 1
                        break
    except OSError:
        return {"log": OPENCODE_LOG, "error": "unreadable", "recent": {}, "total": {}}
    return {"log": OPENCODE_LOG, "recent": recent, "total": total}


def git_status():
    """Short porcelain status of the repo working tree."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def team_state():
    """Per-machine cursor from team_chat state (if present)."""
    if not os.path.exists(TEAM_STATE):
        return None
    try:
        with open(TEAM_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cursor", action="store_true", help="task cursor only")
    parser.add_argument("--log", action="store_true", help="log counts only")
    args = parser.parse_args()

    if args.log:
        counts = log_counts()
        if counts.get("error"):
            print(f"[log] {counts['error']}: {counts['log']}")
        elif counts["log"] is None:
            print("[log] opencode log not found (this machine is not running opencode)")
        else:
            print(f"[log] {counts['log']}")
            if counts["total"]:
                for label in FAILURE_PATTERNS:
                    print(f"  last24h={counts['recent'].get(label, 0):>5}  "
                          f"total={counts['total'].get(label, 0):>6}  {label}")
            else:
                print("  no known failure patterns found")
        return

    cursor = read_cursor()
    print("=== TASK CURSOR (docs/session-logs/BOOT_STATE.md) ===")
    print(cursor if cursor else "(none - BOOT_STATE missing or no cursor block)")
    print()
    print("=== GIT STATUS ===")
    status = git_status()
    print(status if status else "(clean)")
    print()
    print("=== OPENCODE LOG FAILURES ===")
    counts = log_counts()
    if counts.get("error"):
        print(f"[log] {counts['error']}: {counts['log']}")
    elif counts["log"] is None:
        print("[log] opencode log not found (this machine is not running opencode)")
    else:
        print(f"[log] {counts['log']}")
        if counts["total"]:
            for label in FAILURE_PATTERNS:
                print(f"  last24h={counts['recent'].get(label, 0):>5}  "
                      f"total={counts['total'].get(label, 0):>6}  {label}")
        else:
            print("  no known failure patterns found")
    print()
    print("=== TEAM STATE (scripts/.team_state.json) ===")
    ts = team_state()
    print(json.dumps(ts, indent=2) if ts else "(none)")


if __name__ == "__main__":
    main()
