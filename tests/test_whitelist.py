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


def _find_whitelisted(name: str) -> bool:
    for root, _dirs, files in os.walk(TESTS_DIR):
        if name in files:
            return True
    return False


def _open_whitelisted(name: str):
    for root, _dirs, files in os.walk(TESTS_DIR):
        if name in files:
            return open(os.path.join(root, name), encoding="utf-8")
    raise FileNotFoundError(name)


def test_whitelist_files_exist():
    missing = [n for n in _whitelist() if not _find_whitelisted(n)]
    assert not missing, f"whitelisted test files missing: {missing}"


def test_whitelist_no_duplicates():
    wl = _whitelist()
    assert len(wl) == len(set(wl)), "duplicate entries in python_files whitelist"


def test_whitelist_files_contain_tests():
    empty = [
        n
        for n in _whitelist()
        if "def test_" not in _open_whitelisted(n).read()
    ]
    assert not empty, f"whitelisted files without test functions: {empty}"


def test_whitelist_files_parse():
    bad = []
    for n in _whitelist():
        try:
            _open_whitelisted(n).close()
            with _open_whitelisted(n) as f:
                ast.parse(f.read(), filename=n)
        except SyntaxError as exc:
            bad.append(f"{n}: {exc}")
    assert not bad, f"syntax errors in whitelisted files: {bad}"
