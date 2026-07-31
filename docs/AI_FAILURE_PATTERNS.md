# AI Failure Patterns

Every time an AI makes a mistake, log the pattern here. This builds institutional memory so the same class of errors does not repeat across different models and sessions.

**When to log:** You made a mistake that cost >5 minutes to diagnose or fix. Don't log trivial typos; do log conceptual errors.

**Format:**
```
## Failure #N — Short Title

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

## Failure #1 — Test file placed in test_output/ instead of tests/

Date: 2026-07-29
Session: Creating Tier 3 regression test

Problem:
A new test file `test_tier3.py` was written to `test_output/` instead of `tests/`. This violated the directory architecture rule that `test_output/` = output artifacts, `tests/` = test source files.

Root cause:
The AI searched for existing test files and found stale copies in `test_output/` (from a prior run), assumed that was the correct location, and placed the new test there.

Solution:
Moved `test_output/test_tier3.py` → `tests/test_tier3.py`.

Prevention:
- Search for `tests/` directory structure (not just any `.py` file matching the pattern) before placing test files.
- Rule in CODING_STANDARDS.md: "All test files go in `tests/`."
- ARCHITECTURE_CHECKLIST.md includes "No duplicate code" — verify file placement against the directory map.

---

## Failure #2 — PowerSpectrum imported but assumed to exist as module

Date: 2026-07-29
Session: Inverse design pipeline refactoring

Problem:
Code referenced `from backend.spectrum import PowerSpectrum` which did not exist as a file — the class lived inside another module. The AI assumed a file existed based on a class name mentioned in documentation.

Root cause:
The AI searched for "PowerSpectrum" in imports but did not verify the actual file path. Documentation referenced the class in a design diagram but the refactoring to extract it had not been done yet.

Solution:
Used the correct import path. Created the extraction as a separate task.

Prevention:
- Always verify file existence before importing.
- Document planned-but-uncreated modules clearly (e.g., with a `# TODO: extract to backend/spectrum.py` comment).
- Add "Search for actual file path" to ARCHITECTURE_CHECKLIST.md.

---

## Failure #3 — Unused imports left in refactored modules

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

---

## Failure #4 — Zip used wrong file inclusion method, missing docs/ directory

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
- The `-Filter` parameter works correctly with path patterns in PowerShell — use `-Filter "*.md"` with `-Path "docs\*"` instead of `-Include`.

---

## Failure #5 — Attempted to import from non-existent file based on class name

Date: 2026-07-29
Session: Creating sound_analysis.py

Problem:
The code `from backend.spectrum import PowerSpectrum` was written because the architecture diagram showed a `PowerSpectrum` component. No `backend/spectrum.py` existed yet — it was a planned extraction.

Root cause:
The AI treated architecture diagrams as current-state documentation when they were actually future-state plans. The diagram showed a refactoring target, not the current file layout.

Solution:
Imported the class from its actual current location (`backend.sound_analysis`).

Prevention:
- Architecture diagrams in docs/ must clearly annotate what is implemented vs planned.
- Mark planned modules with `(PLANNED)` in architecture docs.
- When reading architecture docs, cross-reference against actual file listing.

---

## Failure #7 — design_server.py violated Law 8 (single responsibility)

Date: 2026-07-31
Session: Post-audit compliance sweep

Problem:
`woodwind_designer/engine/design_server.py` was 973 lines with ~40 endpoints, models, and background jobs
all in one file. Law 8 requires one responsibility per module.

Root cause:
Organic growth: new endpoints were appended to the same file across multiple sessions without
refactoring into separate route modules.

Solution:
No immediate refactor (risk of breaking running server). Deferred — needs planned split into:
- `routers/design.py` — design endpoints
- `routers/optimization.py` — all optimization variants
- `routers/export.py` — STL/STEP/SVG export
- `routers/advisor.py` — advisor endpoints
- `routers/cache.py` — cache management

Prevention:
- Check file size (target <500 lines) before every modification.
- If a file exceeds 500 lines, split before adding new endpoints.
- Add to CONSTRAINTS_AND_PREFERENCES.md: "No module >500 lines except generated code."
