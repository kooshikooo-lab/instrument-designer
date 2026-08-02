"""Team channel CLI - sync/post messages with the other machine via GitHub Discussion #23.

The single source of truth for machine-to-machine communication. Run at the start
of every session (see docs/CONSTRAINTS_AND_PREFERENCES.md Step 0).

Usage:
    python scripts/team_chat.py sync              # fetch and print new comments since last read
    python scripts/team_chat.py post "message"    # post a comment to Discussion #23
    python scripts/team_chat.py sync --json       # machine-readable output

State: a per-machine cursor in scripts/.team_state.json (gitignored).
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = "kooshikooo-lab/instrument-designer"
DISCUSSION_NUM = 23
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".team_state.json")
MACHINE = os.environ.get("TEAM_MACHINE", "unknown")


def gh(*args):
    result = subprocess.run(
        ["gh"] + list(args), capture_output=True, text=True,
        encoding="utf-8", errors="replace"
    )
    return result.stdout, result.stderr, result.returncode


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fetch_comments():
    raw, err, code = gh(
        "api", f"repos/{REPO}/discussions/{DISCUSSION_NUM}/comments",
        "--paginate", "--jq",
        ".[] | {user: .user.login, date: .created_at, body: .body}")
    if code != 0:
        print(f"ERROR fetching comments: {err}", file=sys.stderr)
        sys.exit(1)
    comments = []
    for line in raw.strip().split("\n"):
        if line.strip():
            try:
                comments.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    comments.sort(key=lambda c: c["date"])
    return comments


def resolve_discussion_id(discussion_num=23):
    raw, err, code = gh(
        "api", "graphql", "-f",
        f"query={{repository(owner:\"kooshikooo-lab\",name:\"instrument-designer\")"
        f"{{discussion(number:{discussion_num}){{id}}}}}}")
    if code != 0:
        print(f"ERROR resolving discussion id: {err}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(raw)["data"]["repository"]["discussion"]["id"]
    except (KeyError, json.JSONDecodeError) as e:
        print(f"ERROR parsing discussion id: {e}", file=sys.stderr)
        sys.exit(1)


def post_comment(body, discussion_num=23):
    disc_id = resolve_discussion_id(discussion_num)
    mutation = (
        "mutation($id: ID!, $body: String!){"
        "addDiscussionComment(input:{discussionId:$id,body:$body})"
        "{comment{url}}}"
    )
    raw, err, code = gh(
        "api", "graphql",
        "-f", f"query={mutation}",
        "-f", f"id={disc_id}",
        "-f", f"body={body}")
    if code != 0:
        print(f"ERROR posting: {err}", file=sys.stderr)
        sys.exit(1)
    try:
        url = json.loads(raw)["data"]["addDiscussionComment"]["comment"]["url"]
    except (KeyError, json.JSONDecodeError):
        print(f"Unexpected response: {raw}", file=sys.stderr)
        sys.exit(1)
    state = load_state()
    try:
        comments = fetch_comments()
        state["last_comment_date"] = comments[-1]["date"] if comments else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        state["last_comment_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(state)
    print(f"POSTED: {url}")


def cmd_sync(as_json=False):
    state = load_state()
    last_seen = state.get("last_comment_date", "")
    comments = fetch_comments()

    new = [c for c in comments if c["date"] > last_seen] if last_seen else comments

    if as_json:
        print(json.dumps({"new_count": len(new), "machine": MACHINE, "messages": new}))
    elif not new:
        print(f"[{MACHINE}] No new team messages.")
    else:
        print(f"[{MACHINE}] {len(new)} NEW message(s) from the other machine:")
        for c in new:
            print("-" * 60)
            print(f"[{c['date']}] {c['user']}:")
            print(c["body"])
        print("-" * 60)

    if new:
        state["last_comment_date"] = comments[-1]["date"]
        save_state(state)


def main():
    parser = argparse.ArgumentParser(description="Team channel CLI (Discussion #23)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync", help="fetch new comments since last read")
    p_sync.add_argument("--json", action="store_true", help="machine-readable output")

    p_post = sub.add_parser("post", help="post a comment to a discussion")
    p_post.add_argument("message", nargs="?", help="message body (or use --file)")
    p_post.add_argument("--file", help="read message body from a file (avoids shell quoting issues)")
    p_post.add_argument("--discussion", type=int, default=23,
                        help="discussion number to post to (default 23)")

    args = parser.parse_args()

    if args.cmd == "sync":
        cmd_sync(as_json=args.json)
    elif args.cmd == "post":
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                body = f.read()
        elif args.message:
            body = args.message
        else:
            parser.error("post requires either a message argument or --file")
        post_comment(body, discussion_num=args.discussion)


if __name__ == "__main__":
    main()
