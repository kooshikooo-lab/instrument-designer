"""GitHub Monitor — polls Discussion #23, issues, PRs, and commits every 60s.

Usage:
    python scripts/github_monitor.py

Writes updates to scripts/github_updates.log.
"""

import json
import subprocess
import time
import os
from datetime import datetime, timezone

REPO = "kooshikooo-lab/instrument-designer"
DISCUSSION_NUM = 23
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_updates.log")
POLL_INTERVAL = 60


def gh(*args):
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def fetch_discussion_comments():
    raw = gh("api", f"repos/{REPO}/discussions/{DISCUSSION_NUM}/comments",
             "--paginate", "--jq",
             ".[] | {user: .user.login, date: .created_at, body: .body}")
    comments = []
    for line in raw.strip().split("\n"):
        if line.strip():
            try:
                comments.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return comments


def fetch_prs():
    raw = gh("pr", "list", "--repo", REPO, "--state", "all",
             "--json", "number,title,state,updatedAt", "--limit", "10")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return []


def fetch_issues():
    raw = gh("issue", "list", "--repo", REPO, "--state", "all",
             "--json", "number,title,state,updatedAt", "--limit", "10")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return []


def fetch_commits():
    raw = gh("api", f"repos/{REPO}/commits?per_page=5",
             "--jq", ".[] | {sha: .sha[0:7], msg: .commit.message[0:80], date: .commit.author.date, author: .commit.author.name}")
    commits = []
    for line in raw.strip().split("\n"):
        if line.strip():
            try:
                commits.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return commits


def log(msg):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def poll_once(last_discussion_count, last_pr_update, last_issue_update, last_commit_sha):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Discussion
    try:
        comments = fetch_discussion_comments()
        if len(comments) > last_discussion_count:
            for c in comments[last_discussion_count:]:
                log(f"DISCUSSION #{DISCUSSION_NUM}: {c['user']}: {c['body'][:200]}")
            last_discussion_count = len(comments)
    except Exception as e:
        log(f"ERROR fetching discussion: {e}")

    # PRs
    try:
        prs = fetch_prs()
        for pr in prs:
            if pr.get("updatedAt", "") > last_pr_update:
                log(f"PR #{pr['number']}: {pr['title']} [{pr['state']}]")
        if prs:
            max_update = max(pr.get("updatedAt", "") for pr in prs)
            if max_update > last_pr_update:
                last_pr_update = max_update
    except Exception as e:
        log(f"ERROR fetching PRs: {e}")

    # Issues
    try:
        issues = fetch_issues()
        for iss in issues:
            if iss.get("updatedAt", "") > last_issue_update:
                log(f"ISSUE #{iss['number']}: {iss['title']} [{iss['state']}]")
        if issues:
            max_update = max(iss.get("updatedAt", "") for iss in issues)
            if max_update > last_issue_update:
                last_issue_update = max_update
    except Exception as e:
        log(f"ERROR fetching issues: {e}")

    # Commits
    try:
        commits = fetch_commits()
        for c in commits:
            if c["sha"] != last_commit_sha:
                log(f"COMMIT {c['sha']}: {c['msg']} ({c['author']})")
                break  # Only report newest unseen
        if commits:
            last_commit_sha = commits[0]["sha"]
    except Exception as e:
        log(f"ERROR fetching commits: {e}")

    return last_discussion_count, last_pr_update, last_issue_update, last_commit_sha


def main():
    log("=== GitHub Monitor started ===")

    # Initial state
    comments = fetch_discussion_comments()
    last_discussion_count = len(comments)
    last_pr_update = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    last_issue_update = last_pr_update
    commits = fetch_commits()
    last_commit_sha = commits[0]["sha"] if commits else ""

    log(f"Initial state: {last_discussion_count} discussion comments, {len(commits)} recent commits")

    while True:
        try:
            time.sleep(POLL_INTERVAL)
            last_discussion_count, last_pr_update, last_issue_update, last_commit_sha = \
                poll_once(last_discussion_count, last_pr_update, last_issue_update, last_commit_sha)
        except KeyboardInterrupt:
            log("=== Monitor stopped ===")
            break
        except Exception as e:
            log(f"POLL ERROR: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
