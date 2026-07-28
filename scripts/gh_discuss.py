"""Post comments to GitHub Discussions via GraphQL (REST POST returns 404 for this repo).

Usage:
    python scripts/gh_discuss.py <number> "<body>"       # Post inline
    python scripts/gh_discuss.py <number> --file path.txt  # Post from file
    python scripts/gh_discuss.py --list-comments <number>   # List comments via GET
"""
import sys, json, subprocess, os

REPO = "kooshikooo-lab/instrument-designer"

def gh(*args):
    result = subprocess.run(["gh"] + list(args), capture_output=True, encoding="utf-8", errors="replace")
    return (result.stdout or "").strip() if result.returncode == 0 else ""

def fetch_node_id(disc_num):
    raw = gh("api", f"repos/{REPO}/discussions/{disc_num}", "--jq", ".node_id")
    if not raw:
        print(f"ERROR: Discussion #{disc_num} not found")
        sys.exit(1)
    return raw.strip()

def post_comment(node_id, body):
    import tempfile
    query = {
        "query": f'mutation {{ addDiscussionComment(input: {{discussionId: "{node_id}", body: {json.dumps(body)}}}) {{ comment {{ id url }} }} }}'
    }
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(query, tmp)
    tmp.close()
    result = subprocess.run(
        ["gh", "api", "graphql", "--input", tmp.name],
        capture_output=True, encoding="utf-8", errors="replace"
    )
    os.unlink(tmp.name)
    raw = (result.stdout or "").strip() if result.returncode == 0 else ""
    try:
        data = json.loads(raw)
        if "errors" in data:
            safe_print(f"ERROR: {data['errors']}")
            return None
        return data["data"]["addDiscussionComment"]["comment"]
    except (json.JSONDecodeError, KeyError) as e:
        safe_print(f"ERROR parsing response: {e}")
        safe_print(f"Raw: {raw[:500]}")
        return None

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))

def list_comments(disc_num):
    raw = gh("api", f"repos/{REPO}/discussions/{disc_num}/comments", "--paginate",
             "--jq", ".[] | {user: .user.login, date: .created_at, body: .body[0:200]}")
    for line in raw.strip().split("\n"):
        if line.strip():
            try:
                c = json.loads(line)
                safe_print(f"[{c['date']}] {c['user']}: {c['body']}")
                safe_print("")
            except json.JSONDecodeError:
                pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--list-comments" and len(sys.argv) > 2:
        list_comments(int(sys.argv[2]))
        sys.exit(0)

    disc_num = int(sys.argv[1])
    if len(sys.argv) >= 4 and sys.argv[2] == "--file":
        path = sys.argv[3]
        with open(path, "r", encoding="utf-8") as f:
            body = f.read()
    elif len(sys.argv) >= 3:
        body = sys.argv[2]
    else:
        print("Usage: python scripts/gh_discuss.py <number> \"<body>\"")
        sys.exit(1)

    safe_print(f"Fetching node_id for Discussion #{disc_num}...")
    node_id = fetch_node_id(disc_num)
    safe_print(f"Node ID: {node_id}")

    safe_print("Posting comment...")
    result = post_comment(node_id, body)
    if result:
        safe_print(f"Posted: {result['url']}")
    else:
        safe_print("Failed to post comment")
        sys.exit(1)
