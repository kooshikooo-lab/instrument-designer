"""Registry guard: every third-party import in the live pipeline must be
declared in pyproject.toml. See scripts/toolcheck.py for the checker.

This is the "integrated in a pipeline" enforcement for tool adoption: installing
a package is not a step — declaring it and being importable by the whitelisted
test suite is.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLCHECK = ROOT / "scripts" / "toolcheck.py"


def _load_toolcheck():
    spec = importlib.util.spec_from_file_location("toolcheck_mod", TOOLCHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_all_imported_tools_are_declared():
    mod = _load_toolcheck()
    declared = mod._declared()
    declared_all = set().union(*declared.values()) if declared else set()
    imported = mod._imported()
    imported_pkgs = {mod._resolve_pkg(r) for r in imported}
    undeclared = mod.phantom_deps(declared_all, imported_pkgs)
    assert not undeclared, (
        "Third-party imports not declared in pyproject.toml:\n"
        + "\n".join(undeclared)
        + "\nDeclare them in pyproject.toml, or fix the alias in scripts/toolcheck.py."
    )
