"""Tests for schemas/design_output.schema.json."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "design_output.schema.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_json_schema.py"
SAMPLE_DIR = REPO_ROOT / "test_output" / "unconventional" / "novel_instruments"


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), "design output schema is missing"


def test_schema_is_valid_json():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema.get("$schema") is not None
    assert schema.get("title", "").lower() == "instrument designer — design output"


def test_sample_design_outputs_validate():
    """All existing design-output JSON files pass schema validation."""
    if not SAMPLE_DIR.exists():
        pytest.skip("No sample design outputs present")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(SCHEMA_PATH), str(SAMPLE_DIR)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"design output validation failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_validator_rejects_bad_design_output(tmp_path):
    """A design output missing required fields is rejected."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"name": "Bad", "label": "Missing bore"}))
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(SCHEMA_PATH), str(bad)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1
    assert "FAILED" in result.stdout
