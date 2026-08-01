# Coding Standards

Implementation practices for the Instrument Designer project. Follow these whenever writing or modifying code. Read after `ARCHITECTURE.md` and `ARCHITECTURE_DECISIONS.md` (Step 2 of the boot sequence).

---

## BOOT SEQUENCE (summary)

Every session/agent must run these 6 steps before writing code. Full version: `docs/CONSTRAINTS_AND_PREFERENCES.md`.

1. **Read the AI Constitution** (`docs/AI_CONSTITUTION.md`) — state which laws apply to your task.
2. **Read architecture docs** — `ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `CODING_STANDARDS.md`, `PHYSICS_PRINCIPLES.md`.
3. **Identify your subsystem** — from the table in `CONSTRAINTS_AND_PREFERENCES.md`.
4. **Search before building** — reuse existing functions/classes/tests; never duplicate.
5. **Produce an implementation plan** — files, interfaces, tests, docs, ADRs.
6. **Implement** — follow this file; run `ARCHITECTURE_CHECKLIST.md` and `COMPLIANCE_CHECK.md` on every trigger.

---

## File Placement

- `backend/` root: ONLY core source modules (no test/debug files).
- `tests/`: ALL test files (from any location).
- `scripts/`: ALL utility/debug/benchmark scripts.
- `docs/`: ALL documentation, prompts, session logs.
- `test_output/`: OUTPUT ARTIFACTS ONLY — never place source or test files there.
- Root: ONLY config files (`pyproject.toml`, `README.md`, etc.).

## Search Before Building

- Search the codebase for existing functions, classes, tests, and docs BEFORE writing new code (Law 3, boot sequence Step 4).
- Search BOTH `woodwind_designer/` AND `backend/` directories (Failure #6) — CAD/geometry utilities often live in `backend/`.
- The subsystem table in `CONSTRAINTS_AND_PREFERENCES.md` is authoritative for where code lives.
- Before creating any new `.py` file, grep for the core function signature across the entire project.

## Imports

- Never import from a module without first verifying the file actually exists (Failures #2, #5).
- Before importing, check for a same-named package directory: `git ls-files <name>.py <name>/` — a package `__init__.py` shadows a same-named module (Failure #8).
- No unused imports. Run import-use verification after every refactor/extraction.
- `from __future__ import annotations` false-positives are harmless; ignore them.
- Package `__init__.py` files must NOT eagerly import modules that have import-time side effects (e.g., running benchmarks) or broken dependencies (Failure #8).

## Verification Discipline

- "Importable" means: `python -c "import <module>"` in a fresh interpreter, with a timeout (Failure #8).
- Before claiming a file "does not exist": check `git branch --show-current`, `git rev-parse origin/main`, `git ls-tree -r origin/main -- <path>`, and `git log --all -- <path>` (Failure #7).
- Every audit finding must state the branch and commit SHA it was produced against.

## File Encoding

- Never write tracked source files through PowerShell `Set-Content`/`Out-File` (defaults to UTF-16 — corrupts git blobs, Failure #8).
- Write source bytes via UTF-8 (e.g., `git show <sha>:<path>` or a Python file write with `encoding="utf-8"`).
- If a file shows mojibake (e.g., `ÔÇö` instead of `—`), it was UTF-8 misread as a legacy codepage — restore clean UTF-8.

## Code Quality

- All functions have type hints and NumPy-style docstrings.
- One responsibility per module; split files that exceed ~500 lines or mix concerns (Law 8).
- No bare `except:` clauses.
- Error handling uses sentinel values (e.g., `1e10`) for optimization failures, not exceptions.
- No hardcoded instrument-specific assumptions in general code.
- No new coordinate systems without documentation (Law 7) — document conversions at function entry points.
- No hidden physics: physics belongs in `backend.physics`, not in optimizers or pipelines (Law 4, Law 5).
- The GUI (`woodwind_designer/`, `web/`) never contains physics (Law 6).
