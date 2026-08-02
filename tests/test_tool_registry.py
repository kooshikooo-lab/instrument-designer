"""Registry guard: every third-party import in the live pipeline must be
declared in pyproject.toml. See scripts/toolcheck.py for the checker.

This is the "integrated in a pipeline" enforcement for tool adoption: installing
a package is not a step — declaring it and being importable by the whitelisted
test suite is.
"""
import importlib.util
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLCHECK = ROOT / "scripts" / "toolcheck.py"

import importlib.util


def _load_toolcheck():
    spec = importlib.util.spec_from_file_location("toolcheck_mod", TOOLCHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _declared_packages() -> set[str]:
    with open(ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    deps = list(data["project"].get("dependencies", []))
    for extra in data.get("project", {}).get("optional-dependencies", {}).values():
        deps.extend(extra)
    out = set()
    for dep in deps:
        dep = dep.strip().split("[")[0].strip()
        dep = dep.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
        out.add(dep.lower().replace("_", "-"))
    return out


def test_all_imported_tools_are_declared():
    mod = _load_toolcheck()
    declared = _declared_packages()
    imported_roots = mod._imported()
    undeclared = sorted(
        pkg for root in imported_roots
        if (pkg := mod._resolve_pkg(root)) not in declared
    )
    assert not undeclared, (
        "Third-party imports not declared in pyproject.toml:\n"
        + "\n".join(f"  {r} -> {mod._resolve_pkg(r)}" for r in sorted(imported_roots) if mod._resolve_pkg(r) in undeclared)
        + "\nDeclare them in pyproject.toml, or fix the alias in scripts/toolcheck.py."
    )
