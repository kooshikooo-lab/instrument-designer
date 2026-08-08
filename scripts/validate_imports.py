"""Check Python imports for references to deleted modules and unresolved names.

Usage:
    python scripts/validate_imports.py                    # check staged files (pre-commit)
    python scripts/validate_imports.py --path file.py     # check single file
    python scripts/validate_imports.py --all              # scan entire repo (CI)

Exit codes:
    0 = all imports resolvable
    1 = deleted/unresolved imports or dead-path references detected
"""

import argparse
import ast
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path


# Modules that are known to have been deleted/moved. Keep in sync with repo history.
DELETED_MODULES = {
    "backend.archived_optimizers",
    "backend.legacy_optimizer",
    "backend.bore_optimizer",
    "backend.stage1_optimizer",
    "backend.stage2_optimizer",
    "backend_old",
    "woodwind_designer",
}

# Branch names that have been deleted and should not be referenced in code/config.
# Adding a reference to a deleted branch can accidentally resurrect it.
DELETED_BRANCHES = {
    "kalles-main-branch",
    "kalles-rebased",
    "test/kalles-into-main",
    "port/main-2026-08-01",
    "perf/tmm-refactor-copilot",
    "perf/tmm-medium-refactor-copilot",
    "audit/merge-main-into-desktop",
    "audit/sim-laptop-merge",
    "benchmarking-experiments",
}

# Deleted directory prefixes. Re-adding files under these paths is a dead-path resurrection.
DELETED_DIRS = {
    "backend/archived_optimizers",
    "backend/legacy_optimizer",
    "backend/stage1_optimizer",
    "backend/stage2_optimizer",
}

REPO_ROOT = Path(__file__).resolve().parent.parent


def staged_files():
    """Return staged Python files (relative to repo root)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".py")]


def all_python_files():
    """Return all Python files in the repo (excluding .git, __pycache__, test_output)."""
    excluded = {".git", "__pycache__", "test_output", ".pytest_cache", "build", "dist",
                ".venv", ".venv-wsl", "venv", "node_modules"}
    files = []
    for root, dirs, fnames in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in excluded]
        for fname in fnames:
            if fname.endswith(".py"):
                rel = Path(root).relative_to(REPO_ROOT) / fname
                files.append(str(rel))
    return files


def resolve_module(name):
    """Try to resolve a module/import name. Returns True if resolvable."""
    repo_root = str(REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        spec = importlib.util.find_spec(name)
        return spec is not None
    except (ModuleNotFoundError, ImportError):
        return False


def check_deleted_branch_refs(source: str, rel: str) -> list[str]:
    """Scan source for references to deleted branch names."""
    errors = []
    for branch in DELETED_BRANCHES:
        if branch in source:
            errors.append(f"{rel}: reference to deleted branch '{branch}'")
    return errors


def check_imports(path: Path, rel: str) -> list[str]:
    """Return list of error messages for imports in the given Python file."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError as e:
        return [f"{rel}: cannot read file — {e}"]

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel}:{e.lineno}: syntax error — {e.msg}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in DELETED_MODULES or name.split(".")[0] in DELETED_MODULES:
                    errors.append(f"{rel}:{node.lineno}: import from deleted module '{name}'")
                elif not resolve_module(name):
                    errors.append(f"{rel}:{node.lineno}: import '{name}' cannot be resolved")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level
            if level > 0:
                parent = (REPO_ROOT / rel).parent
                parts = module.split(".") if module else []
                for _ in range(level - 1):
                    parent = parent.parent
                candidate = parent
                for part in parts:
                    candidate = candidate / part
                if candidate.with_suffix(".py").is_file() or (candidate.is_dir() and (candidate / "__init__.py").is_file()):
                    continue
                mod_name = "." * level + module
                errors.append(f"{rel}:{node.lineno}: relative import '{mod_name}' cannot be resolved")
            else:
                full = module
                if full in DELETED_MODULES or full.split(".")[0] in DELETED_MODULES:
                    errors.append(f"{rel}:{node.lineno}: import from deleted module '{full}'")
                elif not resolve_module(full):
                    errors.append(f"{rel}:{node.lineno}: import '{full}' cannot be resolved")

    # Also scan for deleted-branch references (skip registry file itself)
    if not rel.endswith("validate_imports.py"):
        errors.extend(check_deleted_branch_refs(path.read_text(encoding="utf-8", errors="replace"), rel))

    return errors


def check_deleted_dir_readd(rel: str) -> list[str]:
    """Check if a staged file is being added under a deleted directory."""
    errors = []
    for d in DELETED_DIRS:
        if rel.startswith(d + "/") or rel == d:
            errors.append(f"{rel}: re-adding file under deleted directory '{d}' (deleted per ARCHIVED_OPTIMIZERS.md)")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Check Python imports for deleted/unresolved references")
    parser.add_argument("--path", type=str, help="check a single file (relative to repo root)")
    parser.add_argument("--all", action="store_true", help="scan all Python files in repo (CI mode)")
    args = parser.parse_args()

    if args.path:
        rels = [args.path]
    elif args.all:
        rels = all_python_files()
    else:
        rels = staged_files()
        if not rels:
            print("No staged Python files to check.")
            return 0

    all_errors = []
    for rel in rels:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue

        # Check for deleted-dir re-add (only for staged files, not --all)
        if not args.all and not args.path:
            all_errors.extend(check_deleted_dir_readd(rel))

        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        all_errors.extend(check_imports(path, rel))

    if all_errors:
        print("DEAD PATH ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"OK: imports resolvable for {len(rels)} Python file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())