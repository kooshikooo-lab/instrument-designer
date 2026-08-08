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
    "backend.legacy_optimizer",
    "backend.bore_optimizer",
    "backend.stage1_optimizer",
    "backend.stage2_optimizer",
    "backend_old",
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
    except (ModuleNotFoundError, ImportError, ValueError):
        return False


REPO_LOCAL_ROOTS = {"backend", "woodwind_designer", "tests", "scripts", "chalumier", "launchers", "blender_addon"}


def is_repo_local(name: str) -> bool:
    """True if the dotted name belongs to a repo-local package (first segment)."""
    return name.split(".")[0] in REPO_LOCAL_ROOTS


def local_module_exists(name: str) -> bool:
    """Static existence check for a repo-local dotted module (no import, so
    missing optional third-party deps cannot produce false failures)."""
    parts = name.split(".")
    candidate = REPO_ROOT
    for part in parts:
        candidate = candidate / part
    return candidate.with_suffix(".py").is_file() or (candidate.is_dir() and (candidate / "__init__.py").is_file())


def check_deleted_branch_refs(source: str, rel: str) -> list[str]:
    """Scan source for references to deleted branch names."""
    errors = []
    for branch in DELETED_BRANCHES:
        if branch in source:
            errors.append(f"{rel}: reference to deleted branch '{branch}'")
    return errors


def _guarded_import_nodes(tree) -> set:
    """Import nodes inside a try/except ModuleNotFoundError|ImportError block.

    These are the documented quarantine pattern (ARCHIVED_OPTIMIZERS.md):
    the import is guarded at runtime with a SystemExit message, so the static
    check must not block it.
    """
    guarded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            def _matches(h):
                t = h.type
                if t is None:
                    return False
                names = set()
                if isinstance(t, ast.Name):
                    names.add(t.id)
                elif isinstance(t, ast.Attribute):
                    names.add(t.attr)
                elif isinstance(t, ast.Tuple):
                    names.update(e.id for e in t.elts if isinstance(e, ast.Name))
                return bool(names & {"ModuleNotFoundError", "ImportError"})
            if any(_matches(h) for h in node.handlers):
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.Import, ast.ImportFrom)):
                        guarded.add(id(sub))
    return guarded


def check_imports(path: Path, rel: str) -> tuple[list[str], list[str]]:
    """Return (hard_errors, warnings) for imports in the given Python file.

    Hard errors: deleted-module imports, repo-local imports whose file is gone,
    unresolvable relative imports. Warnings: third-party imports not installed
    in the current environment (optional deps — env-dependent, not dead paths).
    """
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError as e:
        return [f"{rel}: cannot read file — {e}"], []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel}:{e.lineno}: syntax error — {e.msg}"], []

    guarded = _guarded_import_nodes(tree)

    def _check(name: str, lineno: int):
        if name in DELETED_MODULES or name.split(".")[0] in DELETED_MODULES:
            errors.append(f"{rel}:{lineno}: import from deleted module '{name}'")
        elif is_repo_local(name):
            if not local_module_exists(name):
                errors.append(f"{rel}:{lineno}: import '{name}' cannot be resolved")
        elif not resolve_module(name):
            warnings.append(f"{rel}:{lineno}: third-party import '{name}' not installed here (optional?)")

    for node in ast.walk(tree):
        if id(node) in guarded:
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                _check(alias.name, node.lineno)
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
                _check(module, node.lineno)

    # Also scan for deleted-branch references (skip registry file itself)
    if not rel.endswith("validate_imports.py"):
        errors.extend(check_deleted_branch_refs(source, rel))

    return errors, warnings


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

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for rel in rels:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue

        # Check for deleted-dir re-add (only for staged files, not --all)
        if not args.all and not args.path:
            all_errors.extend(check_deleted_dir_readd(rel))

        errs, warns = check_imports(path, rel)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    if all_warnings:
        print(f"WARNINGS ({len(all_warnings)} third-party imports not installed here — non-blocking):")
        for w in all_warnings[:20]:
            print(f"  - {w}")
        if len(all_warnings) > 20:
            print(f"  ... and {len(all_warnings) - 20} more")

    if all_errors:
        print("DEAD PATH ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"OK: imports resolvable for {len(rels)} Python file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())