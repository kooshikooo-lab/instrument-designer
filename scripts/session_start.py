"""
Session startup — one command to sync with GitHub, review activity, and
connect infrastructure before starting work.

Usage:
    python scripts/session_start.py

Performs:
    1. GitHub auth check
    2. Fetch recent commits (since last session)
    3. List changed/new docs since last session
    4. List open issues
    5. Read latest discussion thread
    6. Post daily status to discussion
    7. Connect Dask workers to scheduler
"""

import json, os, shutil, socket, subprocess, sys, time, urllib.request, urllib.error

if sys.stdout.encoding and sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = "kooshikooo-lab/instrument-designer"
DASK_SCHEDULER = "tcp://100.69.113.41:9797"
DISCUSSION_NUMBER = 29
DISCUSSION_ID = "D_kwDOTOg0Rs4AoH1M"
LAST_COMMIT_FILE = os.path.join(os.path.dirname(__file__), ".last_commit_seen")


def gh(*args):
    result = subprocess.run(["gh"] + list(args), capture_output=True, encoding="utf-8", errors="replace")
    out = result.stdout.strip() if result.returncode == 0 else ""
    return out.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def step(num, title):
    print(f"\n[{num}/7] {title}")
    print("-" * 60)


def ok(msg):
    print(f"  OK  {msg}")


def warn(msg):
    print(f"  WRN {msg}")


def info(msg):
    print(f"  .. {msg}")


def main():
    print("=" * 60)
    print("  SESSION START")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}  |  {REPO}")
    print("=" * 60)

    # ── 1. GitHub auth ──────────────────────────────────────────────
    step(1, "GitHub Auth")
    raw = gh("auth", "status")
    if "Logged in" in raw:
        ok("Authenticated")
    else:
        warn("Not logged in — run `gh auth login`")
        return

    # ── 2. Recent commits ───────────────────────────────────────────
    step(2, "Recent Commits")
    gh("repo", "sync", REPO, "--force")
    commits_raw = gh("api", f"repos/{REPO}/commits?per_page=10",
                     "--jq", ".[] | {sha: .sha[0:8], msg: .commit.message[0:80], author: .commit.author.name, date: .commit.author.date}")
    commits = []
    for line in commits_raw.strip().split("\n"):
        line = line.strip()
        if line:
            try:
                commits.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if commits:
        last_seen = ""
        if os.path.exists(LAST_COMMIT_FILE):
            last_seen = open(LAST_COMMIT_FILE).read().strip()
        new_count = 0
        for c in commits:
            is_new = last_seen and c["sha"] != last_seen
            if is_new or not last_seen:
                new_count += 1
                tag = " NEW" if is_new else ""
                info(f"  {c['sha']} {c['msg'][:72]} ({c['author']}){tag}")
        if last_seen and new_count == 0:
            ok("No new commits since last session")
        with open(LAST_COMMIT_FILE, "w") as f:
            f.write(commits[0]["sha"])
    else:
        warn("Could not fetch commits")

    # ── 3. New / changed docs ──────────────────────────────────────
    step(3, "Docs Changes")
    if shutil.which("git"):
        result = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", "-5", "--", "docs/"],
            capture_output=True, encoding="utf-8", errors="replace",
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        if files:
            seen = set()
            for f in files:
                if f not in seen:
                    seen.add(f)
                    info(f)
        else:
            ok("No recent docs changes")
    else:
        warn("git not available, skipping")

    # ── 4. Open issues ──────────────────────────────────────────────
    step(4, "Open Issues")
    issues_raw = gh("issue", "list", "--repo", REPO, "--state", "open",
                    "--json", "number,title,labels,updatedAt")
    try:
        issues = json.loads(issues_raw) if issues_raw else []
    except json.JSONDecodeError:
        issues = []
    if issues:
        for i in issues:
            labels = ", ".join(l["name"] for l in i.get("labels", []))
            lbl = f" [{labels}]" if labels else ""
            info(f"  #{i['number']}: {i['title']}{lbl}")
    else:
        ok("No open issues")

    # ── 5. Read discussion ──────────────────────────────────────────
    step(5, "Discussion Thread")
    disc_raw = gh("api", f"repos/{REPO}/discussions/{DISCUSSION_NUMBER}",
                  "--jq", "{title: .title, comments: (.comments | length), updated: .updated_at}")
    if disc_raw:
        try:
            d = json.loads(disc_raw)
            info(f"  Title: {d['title']}")
            info(f"  Comments: {d['comments']}")
            info(f"  Updated: {d.get('updated', '?')[:19]}")
        except json.JSONDecodeError:
            warn("Could not parse discussion data")
    else:
        warn("Discussion not accessible — use `gh api` to debug")

    # ── 6. Post status ──────────────────────────────────────────────
    step(6, "Post Daily Status")
    commit_msg = commits[0]["msg"][:60] if commits else "(no commits)"
    author = commits[0]["author"] if commits else "?"
    body = (
        f"## Daily Start — {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"### Status\n"
        f"- Ready to work\n"
        f"- Last commit: {commit_msg} ({author})\n"
        f"- Open issues: {len(issues)}\n\n"
        f"### Plan for today\n"
        f"- [ ] Review latest commits and docs\n"
        f"- [ ] Check open issues\n"
        f"- [ ] Run pipeline / fix bugs / iterate\n"
        f"- [ ] Push updates and report results\n"
    )
    gql = json.dumps({
        "query": "mutation($input: AddDiscussionCommentInput!) { addDiscussionComment(input: $input) { comment { id } } }",
        "variables": {"input": {"discussionId": DISCUSSION_ID, "body": body}},
    })
    proc = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=gql, capture_output=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode == 0:
        try:
            j = json.loads(proc.stdout.strip())
            cid = j.get("data", {}).get("addDiscussionComment", {}).get("comment", {}).get("id", "?")
            ok(f"Posted comment ({cid})")
        except json.JSONDecodeError:
            ok("Posted comment")
    else:
        err = proc.stderr.strip()[:120] if proc.stderr else "unknown"
        warn(f"Could not post ({err})")

    # ── 7. Dask workers ────────────────────────────────────────────
    step(7, "Dask Workers")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    host, port_str = DASK_SCHEDULER.replace("tcp://", "").split(":")
    port = int(port_str)
    try:
        sock.connect((host, port))
        sock.close()
        ok(f"Scheduler reachable at {host}:{port}")
        info("Connect workers with:")
        info(f"  python -m distributed.cli.dask_worker {DASK_SCHEDULER} --nworkers 2 --nthreads 8")
        info("Or run:  scripts\\start_desktop.ps1")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        warn(f"Scheduler not reachable ({e})")
        info("Start scheduler with:")
        info(f"  python -m distributed.cli.dask_scheduler --port {port} --dashboard-address :{port+1}")

    # ── Done ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SESSION START COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
