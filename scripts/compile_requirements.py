"""Regenerate pip-tools lock files from pyproject.toml.

Usage:
    python scripts/compile_requirements.py
    python scripts/compile_requirements.py --check

--check regenerates the lock files to a temporary directory and compares them
with the committed files, exiting non-zero if they are out of date.
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOCKS = [
    ("requirements.txt", []),
    ("requirements-dev.txt", ["--extra=dev", "--extra=test"]),
    ("requirements-cad.txt", ["--extra=cad"]),
    ("requirements-test.txt", ["--extra=test"]),
    ("requirements-chess.txt", ["--extra=chess"]),
]


def _compile(filename: str, extras: list[str], output_dir: Path) -> None:
    cmd = [
        "pip-compile",
        "--generate-hashes",
        "--output-file",
        str(output_dir / filename),
    ] + extras + ["pyproject.toml"]
    print(f"  {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def compile_all() -> None:
    for filename, extras in LOCKS:
        _compile(filename, extras, ROOT)
    print("\nLock files regenerated. Review the diffs and commit them.")


def _normalize_header(path: Path) -> str:
    """Read a lock file and canonicalize the header so paths don't cause false diffs."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#") and "pip-compile" in line:
            lines[i] = "#    pip-compile pyproject.toml"
    return "\n".join(lines)


def check_all() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for filename, extras in LOCKS:
            _compile(filename, extras, tmp_path)
        all_match = True
        for filename, _ in LOCKS:
            committed = ROOT / filename
            generated = tmp_path / filename
            if not committed.exists():
                print(f"Missing committed lock file: {committed}")
                all_match = False
                continue
            if _normalize_header(committed) != _normalize_header(generated):
                print(f"Out of date: {filename}")
                all_match = False
        if all_match:
            print("All lock files are up to date.")
            return 0
        print(
            "\nLock files are out of date. Run:\n"
            "    python scripts/compile_requirements.py\n"
            "then commit the regenerated files."
        )
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate pip-tools lock files")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that committed lock files are up to date (do not modify).",
    )
    args = parser.parse_args()

    if not shutil.which("pip-compile"):
        print("pip-compile not found. Install with: pip install pip-tools", file=sys.stderr)
        return 1

    return check_all() if args.check else compile_all()


if __name__ == "__main__":
    sys.exit(main() or 0)
