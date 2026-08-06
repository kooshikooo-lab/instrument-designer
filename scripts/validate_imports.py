"""Pre-commit import-consistency checker.

Scans staged Python files for import statements and verifies that every
imported module actually exists in the repository. Flags:
  - imports from deleted/archived modules (e.g. backend/archived_optimizers)
  - imports from modules that do not exist
  - relative imports that leave the repository

Used by the pre-commit hook in scripts/git-hooks/pre-commit.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

# Modules/packages that are explicitly forbidden to import.
DELETED_PREFIXES = (
    "backend.archived_optimizers",
    "archived_optimizers",
)

# External packages and stdlib modules that we never try to resolve in-repo.
# This is intentionally incomplete; anything not matching a repo package and
# not resolvable is reported.
KNOWN_EXTERNAL = {
    "ast", "argparse", "base64", "collections", "copy", "csv", "datetime",
    "functools", "glob", "hashlib", "importlib", "inspect", "io", "itertools",
    "json", "logging", "math", "numbers", "numpy", "os", "pathlib", "pickle",
    "pprint", "random", "re", "shutil", "subprocess", "sys", "tempfile", "time",
    "traceback", "typing", "unittest", "uuid", "warnings",
    # common third-party
    "cv2", "fastapi", "flask", "jax", "jinja2", "matplotlib", "numba", "numpy",
    "pandas", "pydantic", "pymoo", "pytest", "requests", "scipy", "sklearn",
    "starlette", "uvicorn", "yaml",
}


def repo_root() -> Path:
    return Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip())


def staged_python_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        return []
    return [
        line.strip() for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    ]


def extract_imports(source: str) -> list[tuple[str, int]]:
    """Return list of (module_name, line_number) for top-level imports.

    For relative imports, the module name is reconstructed with leading dots so
    the resolver can determine the relative level.
    """
    imports = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            if node.module is None:
                # from . import x
                imports.append(("." * level, node.lineno))
            else:
                imports.append(("." * level + node.module, node.lineno))
    return imports


def is_external(module: str) -> bool:
    top = module.split(".")[0]
    return top in KNOWN_EXTERNAL


def module_exists(root: Path, module: str) -> bool:
    """Check whether a dotted module path resolves to an existing file or package."""
    parts = module.split(".")
    candidate_py = root / "/".join(parts[:-1]) / f"{parts[-1]}.py"
    candidate_pkg = root / "/".join(parts) / "__init__.py"
    return candidate_py.exists() or candidate_pkg.exists()


def resolve_relative(root: Path, file_rel: str, module: str) -> bool:
    """Resolve a relative import (e.g. '.foo.bar') against the file location."""
    file_path = root / file_rel
    level = 0
    for ch in module:
        if ch == ".":
            level += 1
        else:
            break
    rel_parts = module[level:].split(".") if module[level:] else []
    base = file_path.parent
    for _ in range(level - 1):
        base = base.parent
        if not root in [base, *base.parents]:
            return False  # goes outside repo
    candidate_py = base / f"{rel_parts[-1]}.py" if rel_parts else base / "__init__.py"
    candidate_pkg = base / "/".join(rel_parts) / "__init__.py"
    return candidate_py.exists() or candidate_pkg.exists()


def check_file(root: Path, file_rel: str) -> list[str]:
    """Return list of error messages for a single staged Python file."""
    errors = []
    path = root / file_rel
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError as e:
        return [f"{file_rel}: cannot read — {e}"]

    source = source.lstrip("\ufeff")  # strip UTF-8 BOM before parsing
    imports = extract_imports(source)
    for module, lineno in imports:
        # Block imports from deleted modules.
        if any(module == prefix or module.startswith(prefix + ".") for prefix in DELETED_PREFIXES):
            errors.append(
                f"{file_rel}:{lineno}: import from deleted module '{module}' "
                f"(see docs/ARCHIVED_OPTIMIZERS.md; use SystemExit guard if intentional)"
            )
            continue

        # Skip external packages and stdlib.
        if is_external(module):
            continue

        # Skip empty/relative markers handled below.
        if module == ".":
            continue

        # Resolve absolute repo imports.
        if module.startswith("."):
            if not resolve_relative(root, file_rel, module):
                errors.append(f"{file_rel}:{lineno}: relative import '{module}' cannot be resolved")
        else:
            # Only check modules whose top-level package is one of the repo packages.
            top = module.split(".")[0]
            if (root / top).is_dir():
                if not module_exists(root, module):
                    errors.append(f"{file_rel}:{lineno}: import '{module}' cannot be resolved")

    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check Python imports for consistency")
    parser.add_argument("--path", type=str, help="check a single file (relative to repo root)")
    args = parser.parse_args()

    root = repo_root()

    if args.path:
        files = [args.path]
    else:
        files = staged_python_files()

    if not files:
        print("No staged Python files to check.")
        return 0

    all_errors = []
    for rel in files:
        all_errors.extend(check_file(root, rel))

    if all_errors:
        print("IMPORT CONSISTENCY ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"Import consistency OK for {len(files)} Python file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
