"""GitHub Update Checker — polls issues, discussions, and the wiki at defined intervals.

Complements scripts/github_monitor.py (main: issues/PRs/commits + Discussion #23 only).
This script adds wiki page tracking, all-discussion coverage, and configurable
poll intervals.

Usage:
    python scripts/github_updates_check.py [--interval SECONDS] [--once]

Flags:
    --interval SECONDS   Poll interval (default 300; min 60)
    --once               Poll once and exit (useful for cron / Task Scheduler)

Writes updates to scripts/github_updates_check.log.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = "kooshikooo-lab/instrument-designer"
DISCUSSIONS = [23, 46]
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_updates_check.log")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_updates_check_state.json")


def gh(*args):
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _lines(raw):
    for line in raw.strip().split("\n"):
        if line.strip():
            yield line


def fetch_discussion_comments(num):
    raw = gh("api", f"repos/{REPO}/discussions/{num}/comments",
             "--paginate", "--jq",
             ".[] | {user: .user.login, date: .created_at, body: .body}")
    out = []
    for line in _lines(raw):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def fetch_issues():
    raw = gh("issue", "list", "--repo", REPO, "--state", "open",
             "--json", "number,title,state,updatedAt", "--limit", "50")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    return []


def fetch_wiki_pages():
    """List wiki pages. The wiki is a git repo: <REPO>.wiki.git."""
    raw = gh("api", f"repos/{REPO}/contents/wiki", "--jq", ".[] | {name: .name, path: .path}")
    out = []
    for line in _lines(raw):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def log(msg):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("utf-8", errors="replace").decode("utf-8"))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except OSError:
        pass


def poll_once(state):
    # Issues
    try:
        issues = fetch_issues()
        for iss in issues:
            key = f"issue-{iss['number']}"
            prev = state.get(key)
            if prev != iss.get("updatedAt"):
                state[key] = iss.get("updatedAt")
                if prev is None:
                    log(f"ISSUE #{iss['number']}: {iss['title']} [open] (seen)")
                else:
                    log(f"ISSUE #{iss['number']} updated: {iss['title']}")
    except Exception as e:
        log(f"ERROR fetching issues: {e}")

    # Discussions
    for num in DISCUSSIONS:
        try:
            comments = fetch_discussion_comments(num)
            key = f"disc-{num}"
            count = len(comments)
            prev = state.get(key, 0)
            if count > prev:
                for c in comments[prev:]:
                    log(f"DISCUSSION #{num}: {c['user']}: {c['body'][:200]}")
                state[key] = count
        except Exception as e:
            log(f"ERROR fetching discussion #{num}: {e}")

    # Wiki
    try:
        pages = fetch_wiki_pages()
        names = {p["name"] for p in pages}
        prev = state.get("wiki-pages")
        prev_set = set(prev) if isinstance(prev, list) else prev
        if prev_set is not None and names != prev_set:
            added = sorted(names - prev_set)
            removed = sorted(prev_set - names)
            if added:
                log(f"WIKI page(s) added: {', '.join(added)}")
            if removed:
                log(f"WIKI page(s) removed: {', '.join(removed)}")
        state["wiki-pages"] = sorted(names)
        state["wiki-count"] = len(names)
    except Exception as e:
        log(f"ERROR fetching wiki: {e}")

    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    interval = max(args.interval, 60)
    state = _load_state()
    fresh = not state
    log("=== GitHub Update Checker started ===")
    log(f"Polling: issues + discussions {DISCUSSIONS} + wiki every {interval}s"
        f" (fresh run: {fresh})")

    state = poll_once(state)
    _save_state(state)
    if fresh:
        log("Initial state captured: "
            f"{state.get('wiki-count', 0)} wiki pages, "
            f"{state.get('disc-23', 0)} comments in #23, "
            f"{state.get('disc-46', 0)} comments in #46")
    else:
        log(f"State refreshed: {len(state)} tracked keys")

    if args.once:
        log("=== Update Checker done (--once) ===")
        return

    while True:
        try:
            time.sleep(interval)
            state = poll_once(state)
            _save_state(state)
        except KeyboardInterrupt:
            log("=== Update Checker stopped ===")
            break
        except Exception as e:
            log(f"POLL ERROR: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    main()
