"""Tests for scripts/validate_imports.py."""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate_imports.py"


def run_validator_on(source: str) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", encoding="utf-8", dir=REPO_ROOT / "scripts", delete=False
    ) as f:
        f.write(source)
        tmp_path = Path(f.name)
    try:
        rel = tmp_path.relative_to(REPO_ROOT).as_posix()
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--path", rel],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=REPO_ROOT,
        )
        return result.returncode, result.stdout
    finally:
        tmp_path.unlink(missing_ok=True)


def test_valid_imports_pass():
    source = "from backend.metrics import rms_cents\n"
    rc, stdout = run_validator_on(source)
    assert rc == 0, stdout


def test_legacy_optimizer_blocked():
    source = "from backend.legacy_optimizer import staged_optimize\n"
    rc, stdout = run_validator_on(source)
    assert rc == 1, stdout
    assert "deleted module" in stdout


def test_nonexistent_module_blocked():
    source = "import backend.this_module_does_not_exist\n"
    rc, stdout = run_validator_on(source)
    assert rc == 1, stdout
    assert "cannot be resolved" in stdout


def test_relative_unresolved_blocked():
    source = "from .nonexistent import x\n"
    rc, stdout = run_validator_on(source)
    assert rc == 1, stdout
    assert "relative import" in stdout
