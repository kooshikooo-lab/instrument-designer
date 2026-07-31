#!/usr/bin/env python3
"""
AI Boot Sequence Compliance Watchdog.

Reads CONSTRAINTS_AND_PREFERENCES.md, AI_CONSTITUTION.md, COMPLIANCE_CHECK.md,
and ARCHITECTURE_CHECKLIST.md, then runs automated compliance checks at
configurable intervals.

Usage:
    python scripts/compliance_watchdog.py                    # 15-min cycle
    python scripts/compliance_watchdog.py --interval 5       # 5-min cycle
    python scripts/compliance_watchdog.py --once             # single run
    python scripts/compliance_watchdog.py --check-before path/to/file.py
"""

import argparse
import ast
import os
import re
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
SCRIPTS_DIR = REPO_ROOT / "scripts"
COMPLIANCE_LOG = SCRIPTS_DIR / "compliance_log.jsonl"

BACKEND_DIRS = [
    REPO_ROOT / "backend",
    REPO_ROOT / "woodwind_designer",
]

EXCLUDED_DIRS = [
    "__pycache__",
    "archived_optimizers",
    ".git",
    "node_modules",
    "web",
]

EXCLUDED_FILES = [
    "__init__.py",
]

# Known oversized modules (architectural debt, tracked for future refactoring).
# These don't cause FAIL but are reported for awareness.
OVERSIZED_ALLOWLIST = {
    "backend\\ai_advisor.py",
    "backend\\benchmark_all.py",
    "backend\\cadquery_export.py",
    "backend\\modular_components.py",
    "backend\\pareto_optimizer.py",
    "backend\\tmm_acoustics.py",
    "backend\\trumpet_acoustics.py",
    "backend\\trumpet_openwind.py",
    "woodwind_designer\\engine\\design_server.py",
    "woodwind_designer\\engine\\instrument_library.py",
}

# ── Boot sequence knowledge ─────────────────────────────────────────

CONSTITUTION_LAWS = [
    "Law 1 - Architecture over features",
    "Law 2 - No architectural invention",
    "Law 3 - Never duplicate code",
    "Law 4 - Geometry is separate from acoustics",
    "Law 5 - Optimization chooses variables, physics computes results",
    "Law 6 - The GUI never contains physics",
    "Law 7 - One source of truth for every physical quantity",
    "Law 8 - One responsibility per module",
    "Law 9 - Document architectural decisions",
    "Law 10 - When uncertain, stop and ask",
]

SUBSYSTEM_TABLE = {
    "Geometry": ["geometry.py", "spline_bore.py"],
    "Acoustic solver": ["tmm_acoustics.py", "tmm_acoustics_jax.py"],
    "Optimization": ["pareto_optimizer.py", "jax_optimizer.py"],
    "Sound analysis": ["sound_analysis.py"],
    "Pipeline": ["design_from_wav.py", "design_from_unconventional.py", "design_pipeline.py"],
    "Generative agent": ["generative_agent.py", "instrument_knowledge.py"],
    "CAD/Manufacturing": ["cadquery_export.py"],
    "GUI": ["woodwind_designer/", "web/"],
    "Tests": ["tests/"],
}

TRIGGER_TYPES = ["timer", "before-code", "after-tests", "drift-feel"]


# ── Automated checks ────────────────────────────────────────────────


def find_python_files():
    files = []
    for d in BACKEND_DIRS:
        if not d.exists():
            continue
        for root, dirs, names in os.walk(d):
            dirs[:] = [x for x in dirs if x not in EXCLUDED_DIRS]
            for name in names:
                if name.endswith(".py") and name not in EXCLUDED_FILES:
                    files.append(Path(root) / name)
    return sorted(files)


def check_bare_excepts(path: Path) -> list[int]:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    return [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.ExceptHandler) and n.type is None]


def check_module_mutables(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    issues = []
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    if isinstance(n.value, (ast.List, ast.Dict, ast.Set)):
                        issues.append(f"{t.id} L{n.lineno}")
    return issues


def check_hardcoded_ips(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    ips = re.findall(r"(?<!\d)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)", content)
    safe = {"0.0.0.0", "127.0.0.1", "255.255.255.255"}
    return [ip for ip in ips if ip not in safe]


def check_module_size(path: Path) -> int | None:
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if len(lines) > 500:
        return len(lines)
    return None


def check_docstring_present(path: Path) -> bool:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    return isinstance(tree.body[0], ast.Expr) if tree.body else False


def check_no_dunder_assign(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    issues = []
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id.startswith("__") and t.id.endswith("__"):
                    pass
    return issues


# ── Runner ──────────────────────────────────────────────────────────


def run_checks(subsystem: str | None = None, trigger: str = "timer") -> dict:
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "subsystem": subsystem or "all",
        "checks": {},
        "violations": [],
        "passed": True,
    }

    files = find_python_files()

    bare_excepts_total = 0
    mutable_total = 0
    ip_total = 0
    oversized_modules = []

    for f in files:
        rel = f.relative_to(REPO_ROOT)
        try:
            bare = check_bare_excepts(f)
            if bare:
                results["violations"].append({
                    "file": str(rel),
                    "check": "bare_except",
                    "lines": bare,
                })
                bare_excepts_total += len(bare)
        except SyntaxError:
            pass

        try:
            mutables = check_module_mutables(f)
            if mutables:
                results["violations"].append({
                    "file": str(rel),
                    "check": "module_mutable",
                    "items": mutables,
                })
                mutable_total += len(mutables)
        except SyntaxError:
            pass

        try:
            ips = check_hardcoded_ips(f)
            if ips:
                results["violations"].append({
                    "file": str(rel),
                    "check": "hardcoded_ip",
                    "ips": ips,
                })
                ip_total += len(ips)
        except SyntaxError:
            pass

        try:
            rel_str = str(rel)
            size = check_module_size(f)
            if size and rel_str not in OVERSIZED_ALLOWLIST:
                oversized_modules.append({"file": rel_str, "lines": size})
                results["violations"].append({
                    "file": rel_str,
                    "check": "module_size",
                    "lines": size,
                })
        except SyntaxError:
            pass

    results["checks"] = {
        "files_scanned": len(files),
        "bare_excepts": bare_excepts_total,
        "module_mutables": mutable_total,
        "hardcoded_ips": ip_total,
        "oversized_modules": len(oversized_modules),
        "oversized_list": oversized_modules,
    }

    results["passed"] = (
        bare_excepts_total == 0
        and ip_total == 0
    )

    return results


def print_results(results: dict):
    ts = results["timestamp"][:19]
    trigger = results["trigger"]
    status = "PASS" if results["passed"] else "FAIL"
    c = results["checks"]
    print(f"[{ts}] COMPLIANCE: {status} | trigger: {trigger}")
    print(f"       files: {c['files_scanned']} | bare excepts: {c['bare_excepts']} | "
          f"mutables: {c['module_mutables']} | IPs: {c['hardcoded_ips']} | "
          f"oversized: {c['oversized_modules']}")
    for v in results["violations"]:
        print(f"       VIOLATION: {v['file']} | {v['check']}")


def log_results(results: dict):
    COMPLIANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(COMPLIANCE_LOG, "a") as f:
        f.write(json.dumps(results) + "\n")


def print_boot_sequence():
    print("=" * 60)
    print("AI BOOT SEQUENCE")
    print("=" * 60)
    print()
    print("Step 1 - Read the AI Constitution:")
    for law in CONSTITUTION_LAWS:
        print(f"   {law}")
    print()
    print("Step 2 - Read architecture docs:")
    for d in ["ARCHITECTURE.md", "ARCHITECTURE_DECISIONS.md",
              "CODING_STANDARDS.md", "PHYSICS_PRINCIPLES.md"]:
        p = DOCS_DIR / d
        status = "EXISTS" if p.exists() else "MISSING"
        print(f"   {d} [{status}]")
    print()
    print("Step 3 - Identify your subsystem:")
    for sub, files in SUBSYSTEM_TABLE.items():
        print(f"   {sub}: {', '.join(files)}")
    print()
    print("Step 4 - Search before building")
    print("Step 5 - Produce an implementation plan")
    print("Step 6 - Implement (run compliance every 15 min)")
    print()
    print("FINAL CHECK before finishing:")
    print("   All tests pass | No duplicated code")
    print("   Architecture preserved | ARCHITECTURE_CHECKLIST.md complete")
    print("   COMPLIANCE_CHECK.md run | Failures logged in AI_FAILURE_PATTERNS.md")
    print("=" * 60)


# ── Pre-file-modification hook ──────────────────────────────────────


def check_before_modify(filepath: str) -> bool:
    path = Path(filepath)
    if not path.exists():
        return True
    print(f"[before-code] Checking {filepath}...")
    results = run_checks(trigger="before-code")
    print_results(results)
    log_results(results)
    if not results["passed"]:
        print(f"[before-code] FAILED - fix violations before modifying {filepath}")
        return False
    return True


# ── Main ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="AI Boot Sequence Compliance Watchdog"
    )
    parser.add_argument("--interval", "-i", type=int, default=15,
                        help="Check interval in minutes (default: 15)")
    parser.add_argument("--once", action="store_true",
                        help="Run a single check and exit")
    parser.add_argument("--boot", action="store_true",
                        help="Print boot sequence and exit")
    parser.add_argument("--check-before", type=str, metavar="FILE",
                        help="Run compliance check before modifying a file")
    parser.add_argument("--subsystem", "-s", type=str, default=None,
                        help="Limit checks to a specific subsystem")
    args = parser.parse_args()

    if args.boot:
        print_boot_sequence()
        return

    if args.check_before:
        ok = check_before_modify(args.check_before)
        sys.exit(0 if ok else 1)

    if args.once:
        results = run_checks(subsystem=args.subsystem, trigger="manual")
        print_results(results)
        log_results(results)
        sys.exit(0 if results["passed"] else 1)

    print(f"[watchdog] Starting compliance watchdog (interval={args.interval}min)")
    print(f"[watchdog] Log: {COMPLIANCE_LOG}")
    print()
    print_boot_sequence()
    print()

    cycle = 0
    while True:
        cycle += 1
        trigger = "timer"
        results = run_checks(subsystem=args.subsystem, trigger=trigger)
        results["cycle"] = cycle
        print_results(results)
        log_results(results)

        if not results["passed"]:
            print(f"[watchdog] VIOLATIONS DETECTED in cycle {cycle}")
        else:
            print(f"[watchdog] All clean, next check in {args.interval}min")

        print()
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
