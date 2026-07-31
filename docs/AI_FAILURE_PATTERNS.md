# AI Failure Patterns

Every time an AI makes a mistake, log the pattern here. This builds institutional memory so the same class of errors does not repeat across different models and sessions.

**When to log:** You made a mistake that cost >5 minutes to diagnose or fix. Don't log trivial typos; do log conceptual errors.

**Format:**
```
## Failure #N ÔÇö Short Title

Date: YYYY-MM-DD
Session: brief context

Problem:
What went wrong.

Root cause:
Why the AI made the mistake.

Solution:
How it was fixed.

Prevention:
What check or rule would catch this next time.
```

---

## Failure #1 ÔÇö Test file placed in test_output/ instead of tests/

Date: 2026-07-29
Session: Creating Tier 3 regression test

Problem:
A new test file `test_tier3.py` was written to `test_output/` instead of `tests/`. This violated the directory architecture rule that `test_output/` = output artifacts, `tests/` = test source files.

Root cause:
The AI searched for existing test files and found stale copies in `test_output/` (from a prior run), assumed that was the correct location, and placed the new test there.

Solution:
Moved `test_output/test_tier3.py` ÔåÆ `tests/test_tier3.py`.

Prevention:
- Search for `tests/` directory structure (not just any `.py` file matching the pattern) before placing test files.
- Rule in CODING_STANDARDS.md: "All test files go in `tests/`."
- ARCHITECTURE_CHECKLIST.md includes "No duplicate code" ÔÇö verify file placement against the directory map.

---

## Failure #2 ÔÇö PowerSpectrum imported but assumed to exist as module

Date: 2026-07-29
Session: Inverse design pipeline refactoring

Problem:
Code referenced `from backend.spectrum import PowerSpectrum` which did not exist as a file ÔÇö the class lived inside another module. The AI assumed a file existed based on a class name mentioned in documentation.

Root cause:
The AI searched for "PowerSpectrum" in imports but did not verify the actual file path. Documentation referenced the class in a design diagram but the refactoring to extract it had not been done yet.

Solution:
Used the correct import path. Created the extraction as a separate task.

Prevention:
- Always verify file existence before importing.
- Document planned-but-uncreated modules clearly (e.g., with a `# TODO: extract to backend/spectrum.py` comment).
- Add "Search for actual file path" to ARCHITECTURE_CHECKLIST.md.

---

## Failure #3 ÔÇö Unused imports left in refactored modules

Date: 2026-07-29
Session: Creating design_from_wav.py, geometry.py

Problem:
After extracting `sound_analysis.py` and `design_from_wav.py` from `inverse_design.py`, several imports (Sequence, validate_physical_series, pareto_sweep, numpy) were left in the new modules but never used. These were not caught until a static analysis pass.

Root cause:
The AI copied blocks of code from the original monolithic file and did not verify which imports were actually consumed by the extracted functions.

Solution:
Ran a static import-use analysis script (`check_unused_imports.py`) and removed unused imports.

Prevention:
- Run `import` verification after every refactoring extraction.
- Add "No unused imports" to ARCHITECTURE_CHECKLIST.md.
- The `from __future__ import annotations` false-positive is harmless; ignore it.

---

## Failure #4 ÔÇö Zip used wrong file inclusion method, missing docs/ directory

Date: 2026-07-29
Session: Creating architecture review zip

Problem:
PowerShell's `-Include "docs\*.md"` was used with `Get-ChildItem -Recurse`, but `-Include` in PowerShell filters on the **filename**, not the path. This caused all `docs/*.md` files to be silently excluded from the zip.

Root cause:
The AI was unfamiliar with PowerShell's `-Include` behavior with `-Recurse`. It assumed `"docs\*.md"` would match files in the `docs/` subdirectory, but PowerShell matched against the literal filename pattern `docs\*.md`.

Solution:
Switched to a Python script using `os.walk()` which has intuitive path filtering.

Prevention:
- When zip/archive operations are needed, use Python (zipfile module) instead of PowerShell.
- The `-Filter` parameter works correctly with path patterns in PowerShell ÔÇö use `-Filter "*.md"` with `-Path "docs\*"` instead of `-Include`.

---

## Failure #5 ÔÇö Attempted to import from non-existent file based on class name

Date: 2026-07-29
Session: Creating sound_analysis.py

Problem:
The code `from backend.spectrum import PowerSpectrum` was written because the architecture diagram showed a `PowerSpectrum` component. No `backend/spectrum.py` existed yet ÔÇö it was a planned extraction.

Root cause:
The AI treated architecture diagrams as current-state documentation when they were actually future-state plans. The diagram showed a refactoring target, not the current file layout.

Solution:
Imported the class from its actual current location (`backend.sound_analysis`).

Prevention:
- Architecture diagrams in docs/ must clearly annotate what is implemented vs planned.
- Mark planned modules with `(PLANNED)` in architecture docs.
- When reading architecture docs, cross-reference against actual file listing.

---

## Failure #6 — Created new module that duplicated existing backend code

Date: 2026-07-31
Session: CadQuery STL pipeline replacement for demakein Makers

Problem:
Created `woodwind_designer/engine/stl_generator.py` with CadQuery-based STL generation that duplicated logic already present in `backend/cadquery_export.py::generate_variable_bore_instrument`. Wrote ~100 lines of new code instead of importing the existing function.

Root cause:
The AI searched for "CadQuery" in the engine directory only and didn't find it. It failed to search the `backend/` directory where CAD utilities live. The subsystem table in CONSTRAINTS_AND_PREFERENCES.md lists CAD/Manufacturing → `cadquery_export.py` but the AI didn't cross-reference this during Step 4.

Solution:
Deleted `stl_generator.py`. Modified `demakein_wrapper.py` to import from `backend.cadquery_export` instead. Sampled the demakein Instrument profile into the `[(pos, diam)]` format that `generate_variable_bore_instrument` expects.

Prevention:
- In Step 4 of boot sequence, explicitly search BOTH `woodwind_designer/` AND `backend/` directories.
- The subsystem table in CONSTRAINTS_AND_PREFERENCES.md is authoritative — check it during Step 3.
- Before creating any new `.py` file, grep for the core function signature across the entire project.

---

## Failure #7 — Declared governance docs "non-existent" while working in the wrong repo and branch

Date: 2026-07-31
Session: Deep governance audit

Problem:
I claimed the project's governance docs (`AI_CONSTITUTION.md`, `ARCHITECTURE_DECISIONS.md`, `CONSTRAINTS_AND_PREFERENCES.md`, etc.) "did not exist" and that the user had "corrected me" on this — a correction that never happened. In reality the docs exist on `main` (added in commit `c3ba5ee`, 2026-07-29). I was working in a checkout on branch `experiment/unconventional-shapes` at `e3e1a64`, which predates the governance commit and is a different lineage from `main`. I also audited the entire codebase from that wrong branch, producing findings invalid for `main`.

Root cause:
I never verified the git branch/checkout state before making claims about file existence. I searched only the local working tree of the wrong branch, treated that partial search as exhaustive, and then asserted the user was wrong based on my incorrect repo state.

Solution:
- Checked `git branch --show-current` and `git rev-parse origin/main` — established the repo was on the wrong branch and behind.
- Confirmed via `git ls-tree origin/main` that the governance docs and a committed routes package exist on `main`.
- Stashed the divergent uncommitted refactor (`git stash -u`), checked out `main`, fast-forwarded to `origin/main` (`38782b1`).
- Re-read all governance docs from their canonical `docs/` location and re-anchored the audit to `main`.

Prevention:
- Before ANY claim that a file "does not exist": run `git branch --show-current`, `git rev-parse origin/main`, `git ls-tree -r origin/main -- <path>`, and `git log --all -- <path>`.
- Every audit finding must state the branch and commit SHA it was produced against.
- Never claim the user "corrected me" about a fact unless that correction is present in the visible conversation.
