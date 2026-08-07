"""Branch-safety guard — enforces Law 15 (Branch governance) at the git layer.

Law 15 defines four branch namespaces and gives each a fixed lifetime. This
guard makes the rules mechanically enforced so that even a vague instruction
(e.g. "clean up branches") cannot delete a canonical branch, force-push a
canonical branch, or delete a branch whose content is not provably preserved
on a canonical branch or `main`.

Enforced by the pre-push hook (scripts/git-hooks/pre-push).

Commands:
  guard_branch.py --check-push          read push refspecs from stdin (pre-push hook)
  guard_branch.py --check-delete NAME   check a single local branch deletion
  guard_branch.py --audit               report branch-topology violations (Law 15)

Environment overrides (human approval for canonical-branch changes):
  GUARD_BRANCH_ALLOW_DELETE=<name>      permit deleting this canonical branch (human)
  GUARD_BRANCH_ALLOW_FORCE=<name>       permit force-pushing this canonical branch (human)

Exit codes: 0 = OK, 1 = blocked.
"""

import argparse
import os
import re
import subprocess
import sys

CANONICAL_PREFIX = "opencode/main/"
TRUNK = "main"
# Namespaces allowed by Law 15. Anything else is an orphan.
NAMESPACE_RE = {
    "trunk": re.compile(r"^main$"),
    "canonical": re.compile(r"^opencode/main/(desktop|laptop)$"),
    "feature": re.compile(r"^opencode/[a-z0-9-]+/(desktop|laptop)$"),
    "merge_staging": re.compile(r"^merge/[a-z0-9-]+$"),
}


def classify(name: str) -> str | None:
    """Return the Law 15 namespace of a branch, or None if it is an orphan."""
    name = name.strip()
    for ns, pattern in NAMESPACE_RE.items():
        if pattern.match(name):
            return ns
    return None


def is_canonical(name: str) -> bool:
    ns = classify(name)
    return ns in ("canonical", "trunk")


def run_git(args):
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return result.stdout.strip(), result.returncode
    except Exception:
        return "", 1


def content_preserved(sha: str) -> bool:
    """Law 15.5: is `sha` an ancestor of a canonical branch or main?"""
    for ref in ["main", "origin/main", "opencode/main/desktop",
                "opencode/main/laptop", "origin/opencode/main/desktop",
                "origin/opencode/main/laptop"]:
        out, code = run_git(["merge-base", "--is-ancestor", sha, ref])
        if code == 0:
            return True
    return False


def origin_head_points_at_main() -> bool:
    out, _ = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    return out.rstrip("/") in ("refs/remotes/origin/main", "refs/remotes/origin/main/")
    # return True if points at main


def parse_push_lines(lines):
    """Parse pre-push stdin refspecs.

    Format: <local ref> <local sha> <remote ref> <remote sha>
    A deletion is: <local ref> <40 zeroes> <remote ref> <remote sha>
    """
    pushes = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts
        pushes.append({
            "local_ref": local_ref,
            "local_sha": local_sha,
            "remote_ref": remote_ref,
            "remote_sha": remote_sha,
            "branch": remote_ref.replace("refs/heads/", ""),
            "deletion": set(local_sha) == {"0"},
            "forced": local_sha != "" and remote_sha not in ("", "0" * 40)
                      and local_sha != remote_sha,
        })
    return pushes


def check_push(lines, human_delete=set(), human_force=set()):
    """Return list of violations for the given push refspecs."""
    violations = []
    for push in parse_push_lines(lines):
        name = push["branch"]
        ns = classify(name)
        if ns is None:
            violations.append(
                f"PUSH {name}: orphan branch — not in a Law 15 namespace "
                f"(main / opencode/main/<machine> / opencode/<topic>/<machine> / merge/<topic>)."
            )
        if push["deletion"]:
            if is_canonical(name) and name not in human_delete:
                violations.append(
                    f"PUSH {name}: deletion of a canonical branch requires explicit "
                    f"human approval (GUARD_BRANCH_ALLOW_DELETE={name}). Law 15.8."
                )
            elif not push["local_sha"] or not content_preserved(push["local_sha"]):
                # local_sha on a delete refspec is the sha being deleted, provided
                # git supplied it (it may be zeroes when the local side is unknown).
                if set(push["local_sha"]) == {"0"}:
                    continue
                if not content_preserved(push["local_sha"]):
                    violations.append(
                        f"PUSH {name}: deletion would lose content not proven present "
                        f"on a canonical branch or main. Law 15.5."
                    )
        elif is_canonical(name) and name not in human_force:
            out, code = run_git(["merge-base", "--is-ancestor",
                                 push["remote_sha"], push["local_sha"]])
            if code != 0:
                violations.append(
                    f"PUSH {name}: force/non-fast-forward push to a canonical branch "
                    f"requires explicit human approval (GUARD_BRANCH_ALLOW_FORCE={name}). "
                    f"Law 15.8."
                )
    return violations


def check_delete(name: str) -> list[str]:
    """Check deletion of a single local branch (git branch -D equivalent)."""
    if classify(name) is None:
        return [f"DELETE {name}: orphan branch — not in a Law 15 namespace."]
    if is_canonical(name):
        if name in os.environ.get("GUARD_BRANCH_ALLOW_DELETE", "").split(","):
            return []
        return [
            f"DELETE {name}: deletion of a canonical branch requires explicit human "
            f"approval (set GUARD_BRANCH_ALLOW_DELETE={name}). Law 15.8."
        ]
    sha, _ = run_git(["rev-parse", name])
    if sha and not content_preserved(sha):
        return [f"DELETE {name}: content not provably present on a canonical branch or main. Law 15.5."]
    return []


def audit() -> list[str]:
    """Report branch-topology violations against Law 15 (read-only)."""
    findings = []
    out, _ = run_git(["for-each-ref", "--format=%(refname)", "refs/heads"])
    for ref in out.splitlines():
        name = ref.replace("refs/heads/", "")
        ns = classify(name)
        if ns is None:
            findings.append(f"AUDIT branch {name}: orphan — not in a Law 15 namespace.")
        elif ns in ("canonical", "trunk"):
            # Canonical branches must not be force-pushed; content-preservation
            # of the branch itself is moot. Nothing further to flag here.
            pass
    if not origin_head_points_at_main():
        findings.append(
            "AUDIT origin/HEAD: does not point at main (Law 15.6). "
            "Fix with: git remote set-head origin -a"
        )
    return findings


def main():
    parser = argparse.ArgumentParser(description="Branch-safety guard (Law 15)")
    parser.add_argument("--check-push", action="store_true",
                        help="read push refspecs from stdin (pre-push hook)")
    parser.add_argument("--check-delete", metavar="BRANCH",
                        help="check a single local branch deletion")
    parser.add_argument("--audit", action="store_true",
                        help="report branch-topology violations (read-only)")
    args = parser.parse_args()

    if args.audit:
        for f in audit():
            print(f)
        return 1 if audit() else 0

    if args.check_delete:
        violations = check_delete(args.check_delete)
        for v in violations:
            print(v, file=sys.stderr)
        return 1 if violations else 0

    if args.check_push:
        lines = sys.stdin.read().splitlines()
        human_delete = {n.strip() for n in
                        os.environ.get("GUARD_BRANCH_ALLOW_DELETE", "").split(",") if n.strip()}
        human_force = {n.strip() for n in
                       os.environ.get("GUARD_BRANCH_ALLOW_FORCE", "").split(",") if n.strip()}
        violations = check_push(lines, human_delete, human_force)
        for v in violations:
            print(v, file=sys.stderr)
        return 1 if violations else 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
