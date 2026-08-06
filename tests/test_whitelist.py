"""Whitelist health checks for [tool.pytest.ini_options].python_files.

Guards the pytest collection whitelist in pyproject.toml: every listed file
must exist, be unique, contain test functions, and parse as valid Python.
"""

import ast
import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(__file__))
TESTS_DIR = os.path.join(ROOT, "tests")


def _whitelist() -> list[str]:
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
        cfg = tomllib.load(f)
    entries = cfg["tool"]["pytest"]["ini_options"]["python_files"]
    return [e for e in entries if e.startswith("test_")]


def test_whitelist_files_exist():
    missing = [n for n in _whitelist() if not os.path.exists(os.path.join(TESTS_DIR, n))]
    assert not missing, f"whitelisted test files missing: {missing}"


def test_whitelist_no_duplicates():
    wl = _whitelist()
    assert len(wl) == len(set(wl)), "duplicate entries in python_files whitelist"


def test_whitelist_files_contain_tests():
    empty = [
        n
        for n in _whitelist()
        if "def test_" not in open(os.path.join(TESTS_DIR, n), encoding="utf-8").read()
    ]
    assert not empty, f"whitelisted files without test functions: {empty}"


def test_whitelist_files_parse():
    bad = []
    for n in _whitelist():
        try:
            with open(os.path.join(TESTS_DIR, n), encoding="utf-8") as f:
                ast.parse(f.read(), filename=n)
        except SyntaxError as exc:
            bad.append(f"{n}: {exc}")
    assert not bad, f"syntax errors in whitelisted files: {bad}"
