#!/usr/bin/env python3
"""Session startup check — run at beginning of each session.

Usage:
    python scripts/startup_check.py [--verbose]

Checks:
  1. GitHub auth + Discussion #23, recent PRs, issues, commits
  2. Dask scheduler alive (100.69.113.41:9797)
  3. HTTP messaging server on Kalle's machine (100.100.66.117:9124)
  4. GitHub monitor daemon running
  5. Desktop's own HTTP messaging server (100.69.113.41:9124)
"""
import sys, subprocess, json, socket, os, time, urllib.request, urllib.error

REPO = "kooshikooo-lab/instrument-designer"
DASK_ADDR = ("100.69.113.41", 9797)
TWITCHY_MSG = "http://100.69.113.41:9124/ping"
KALLE_MSG = "http://100.100.66.117:9124/ping"

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

def gh(*args):
    result = subprocess.run(["gh"] + list(args), capture_output=True, encoding="utf-8", errors="replace")
    stdout = result.stdout or ""
    return stdout.strip() if result.returncode == 0 else ""

def safe(text):
    if isinstance(text, str):
        return text.encode("ascii", errors="replace").decode("ascii")
    return text

def http_ping(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def check_github_auth():
    raw = gh("auth", "status")
    if "Logged in" in raw:
        return PASS, "gh authenticated"
    return FAIL, "not logged in"

def check_discussion():
    raw = gh("api", f"repos/{REPO}/discussions/23", "--jq", "{title: .title, comments: .comments, updated: .updated_at}")
    if raw:
        try:
            d = json.loads(raw)
            updated = d.get("updated") or "unknown"
            return PASS, f"Discussion #23: {d['comments']} comments, last updated {updated[:10]}"
        except json.JSONDecodeError:
            pass
    return FAIL, "could not fetch Discussion #23"

def check_recent_activity():
    commits_raw = gh("api", f"repos/{REPO}/commits?per_page=3",
                     "--jq", ".[] | {sha: .sha[0:7], msg: .commit.message[0:60], author: .commit.author.name}")
    commits = []
    for line in commits_raw.strip().split("\n"):
        if line.strip():
            try:
                commits.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    prs_raw = gh("pr", "list", "--repo", REPO, "--state", "open", "--json", "number,title,headRefName")
    prs = json.loads(prs_raw) if prs_raw else []
    issues_raw = gh("issue", "list", "--repo", REPO, "--state", "open", "--json", "number,title")
    issues = json.loads(issues_raw) if issues_raw else []

    lines = []
    if commits:
        for c in commits[:2]:
            lines.append(f"  commit {c['sha']}: {safe(c['msg'])} ({c['author']})")
    if prs:
        for p in prs:
            lines.append(f"  PR #{p['number']}: {safe(p['title'])} [{p['headRefName']}]")
    if issues:
        for i in issues:
            lines.append(f"  Issue #{i['number']}: {safe(i['title'])}")

    status = PASS if (commits or prs or issues) else WARN
    return status, f"{len(commits)} recent commits, {len(prs)} open PRs, {len(issues)} open issues", lines

def check_tcp(addr, label, timeout=3):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(addr)
        sock.close()
        return PASS, f"{label} reachable at {addr[0]}:{addr[1]}"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return WARN if "refused" in str(e).lower() else FAIL, f"{label} unreachable: {e}"
    finally:
        sock.close()

def check_dask():
    return check_tcp(DASK_ADDR, "Dask scheduler")

def check_own_msg():
    result = http_ping(TWITCHY_MSG)
    if result and result.get("pong"):
        return PASS, "Desktop HTTP messaging server up (port 9124)"
    return FAIL, "Desktop HTTP messaging server DOWN"

def check_kalle_msg():
    result = http_ping(KALLE_MSG)
    if result and result.get("pong"):
        return PASS, "Kalle HTTP messaging server up (port 9124)"
    return WARN, "Kalle HTTP messaging server unreachable (not started yet?)"

def check_monitor():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "github_updates.log")
    if os.path.exists(log_path):
        age = time.time() - os.path.getmtime(log_path)
        if age < 300:
            return PASS, f"Monitor active (log updated {age:.0f}s ago)"
        else:
            return WARN, f"Monitor log stale ({age:.0f}s since last update)"
    return FAIL, "Monitor log not found"

def result_tag(status):
    return f"[{status}]"

def main():
    verbose = "--verbose" in sys.argv
    print("=" * 64)
    print("  SESSION STARTUP CHECK")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 64)

    checks = []
    for name, fn in [
        ("GitHub Auth", check_github_auth),
        ("Discussion #23", check_discussion),
        ("Recent Activity", check_recent_activity),
        ("Dask Scheduler", check_dask),
        ("Msg Server (Desktop)", check_own_msg),
        ("Msg Server (Kalle)", check_kalle_msg),
        ("GitHub Monitor", check_monitor),
    ]:
        result = fn()
        checks.append((name, result[0], result[1], result[2] if len(result) > 2 else []))

    all_pass = True
    for name, status, msg, detail_lines in checks:
        tag = result_tag(status)
        if status == FAIL:
            all_pass = False
        print(f"  {tag} {name}: {safe(msg)}")
        if detail_lines and verbose:
            for dl in detail_lines:
                print(f"      {dl}")

    print("-" * 64)
    if all_pass:
        print("  ALL CHECKS PASSED")
    else:
        print("  STATUS: ", end="")
        if any(s == FAIL for _, s, _, _ in checks):
            print("SOME CHECKS FAILED")
        if any(s == WARN for _, s, _, _ in checks):
            print("(warnings are OK - expected if Kalle hasn't started services yet)")
    print("=" * 64)
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
