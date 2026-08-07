"""Run pre-commit checks on all tracked files."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from validate_pre_commit import (
    check_regenerable, check_placement, check_bare_excepts,
    check_hardcoded_ips, check_module_size,
)

root = Path(__file__).resolve().parent.parent

result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=root)
files = result.stdout.splitlines()

errors = []
warnings = []

for rel in files:
    p = root / rel
    if not p.is_file():
        continue

    msg = check_regenerable(rel)
    if msg:
        errors.append(msg)

    msg = check_placement(rel)
    if msg:
        errors.append(msg)

    if rel.endswith(".py"):
        bare = check_bare_excepts(p)
        for line in bare:
            errors.append(f"{rel}:{line}: bare except clause")

        ips = check_hardcoded_ips(p)
        if ips:
            errors.append(f"{rel}: hardcoded IP(s) {', '.join(set(ips))}")

        size_msg = check_module_size(p, root)
        if size_msg:
            warnings.append(size_msg)

print("ERRORS:")
for e in errors:
    print(f"  - {e}")
print("\nWARNINGS:")
for w in warnings:
    print(f"  - {w}")

# Dependency drift check (non-blocking here; run with --warn to fail)
dep_result = subprocess.run(
    [sys.executable, str(root / "scripts" / "check_local_dependencies.py")],
    capture_output=True, text=True, cwd=root,
)
print("\nDEPENDENCY CHECK:")
print(dep_result.stdout.strip())
print(dep_result.stderr.strip())

print(f"\nTotal errors: {len(errors)}, warnings: {len(warnings)}")
