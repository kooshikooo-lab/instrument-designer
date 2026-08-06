"""Tests for schemas/instrument_config.schema.json and validate_instrument_configs.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "instrument_config.schema.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_instrument_configs.py"
CONFIG_DIR = REPO_ROOT / "config"


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), "instrument config schema is missing"


def test_validator_script_exists():
    assert VALIDATOR_PATH.exists(), "validate_instrument_configs.py is missing"


def test_schema_is_valid_json():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema.get("$schema") is not None
    assert schema.get("title", "").lower() == "instrument designer — instrument config"


def test_all_config_files_validate():
    """All committed config/*.json files must pass schema validation."""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"config validation failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_validator_reports_invalid_config(tmp_path):
    """A deliberately invalid config file is rejected."""
    bad_config = tmp_path / "bad.json"
    bad_config.write_text(json.dumps({"name": "Bad", "description": "Missing bore"}))
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--path", str(bad_config)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1
    assert "FAILED" in result.stdout
