"""Pre-commit validation helpers.

Checks staged files for:
  - regenerable artifacts (STL, JSON dumps, logs, test_output/)
  - UTF-16 encoded text files
  - file placement violations (source/tests/scripts/docs boundaries)
  - Python basics for staged .py files (bare excepts, hardcoded IPs, oversized modules)

Used by the pre-commit hook in scripts/git-hooks/pre-commit.
"""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

# These are the directory boundaries from docs/ARCHITECTURE.md and CODING_STANDARDS.md.
PLACEMENT_RULES = {
    "backend/": {
        "allowed": {".py"},
        "message": "backend/ root must contain ONLY core source modules (.py)",
    },
    "tests/": {
        "allowed": {".py"},
        "message": "tests/ must contain ONLY test files (.py)",
    },
    "scripts/": {
        "allowed": {".py", ".ps1", ".sh", ".bat"},
        "message": "scripts/ must contain ONLY utility/debug/benchmark scripts",
    },
    "docs/": {
        "allowed": {".md", ".txt", ".docx", ".pdf"},
        "message": "docs/ must contain ONLY documentation",
    },
}

# Regenerable artifacts that should never be committed.
REGENERABLE_SUFFIXES = {
    ".stl", ".step", ".stp", ".obj", ".ply", ".3mf",
    ".json", ".jsonl", ".dat", ".log", ".txt", 
    ".png", ".jpg", ".jpeg", ".svg", 
}
REGENERABLE_PATHS = {"test_output/", "designs/", "chat-logs/", "wiki/"}

# Known oversized modules (architectural debt, tracked). These are reported but not blocked.
OVERSIZED_ALLOWLIST = {
    "backend/ai_advisor.py",
    "backend/benchmark_all.py",
    "backend/cadquery_export.py",
    "backend/modular_components.py",
    "backend/pareto_optimizer.py",
    "backend/tmm_acoustics.py",
    "backend/trumpet_acoustics.py",
    "backend/trumpet_openwind.py",
    "woodwind_designer/engine/design_server.py",
    "woodwind_designer/engine/instrument_library.py",
}


def staged_files():
    """Return list of staged file paths (relative to repo root)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_binary(path: Path) -> bool:
    """Cheap binary check: read first 8KB and look for null bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


def check_utf16(path: Path) -> bool:
    """Detect UTF-16 by BOM."""
    try:
        with open(path, "rb") as f:
            bom = f.read(2)
        return bom in (b"\xff\xfe", b"\xfe\xff")
    except OSError:
        return False


def check_regenerable(path: str) -> str | None:
    """Return violation message if path is a regenerable artifact."""
    low = path.lower()
    for suffix in REGENERABLE_SUFFIXES:
        if low.endswith(suffix):
            # JSON logs/reports under test_output/ or designs/ are always regenerable.
            for prefix in REGENERABLE_PATHS:
                if path.startswith(prefix):
                    return f"{path}: regenerable artifact in {prefix} (do not commit)"
            # JSON config files in config/ are allowed.
            if path.startswith("config/") and suffix == ".json":
                return None
            if suffix in {".log", ".txt", ".jsonl"}:
                return f"{path}: log/dump file should not be committed"
    return None


def check_placement(path: str) -> str | None:
    """Return violation message if path violates directory placement rules."""
    for prefix, rule in PLACEMENT_RULES.items():
        if path.startswith(prefix):
            suffix = Path(path).suffix.lower()
            if suffix and suffix not in rule["allowed"]:
                return f"{path}: {rule['message']}"
    return None


def check_bare_excepts(path: Path) -> list[int]:
    """Return line numbers of bare except handlers in a Python file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read())
    except SyntaxError:
        return []
    return [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is None
    ]


def check_hardcoded_ips(path: Path) -> list[str]:
    """Return list of hardcoded non-loopback IPs."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return []
    ips = re.findall(r"(?<!\d)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)", content)
    safe = {"0.0.0.0", "127.0.0.1", "255.255.255.255"}
    return [ip for ip in ips if ip not in safe]


def check_module_size(path: Path, root: Path) -> str | None:
    """Return warning message if .py file exceeds ~500 lines and is not allowlisted."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = len(f.readlines())
    except OSError:
        return None
    if lines <= 500:
        return None
    rel = path.relative_to(root).as_posix()
    if rel in OVERSIZED_ALLOWLIST:
        return None
    return f"{rel}: {lines} lines (exceeds 500; split or add to OVERSIZED_ALLOWLIST)"


def main():
    repo_root = Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip())

    files = staged_files()
    if not files:
        print("No staged files to validate.")
        return 0

    errors = []
    warnings = []
    for rel in files:
        path = repo_root / rel
        if not path.is_file():
            continue

        # 1. Regenerable artifacts
        msg = check_regenerable(rel)
        if msg:
            errors.append(msg)

        # 2. UTF-16
        if check_utf16(path):
            errors.append(f"{rel}: UTF-16 encoding detected — save as UTF-8")

        # 3. Placement
        msg = check_placement(rel)
        if msg:
            errors.append(msg)

        # 4. Python-specific checks
        if rel.endswith(".py"):
            bare = check_bare_excepts(path)
            for line in bare:
                errors.append(f"{rel}:{line}: bare except clause")

            ips = check_hardcoded_ips(path)
            if ips:
                errors.append(f"{rel}: hardcoded IP(s) {', '.join(set(ips))}")

            size_msg = check_module_size(path, repo_root)
            if size_msg:
                warnings.append(size_msg)

    if warnings:
        print("WARNINGS (non-blocking):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("BLOCKED — fix these before committing:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Pre-commit validation passed for {len(files)} staged file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
