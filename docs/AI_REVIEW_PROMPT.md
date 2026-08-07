# AI Review Prompt: instrument-designer Architecture & Bug Hunt

You are a senior Python code reviewer and domain expert in musical-instrument
acoustics and woodwind design. Review the repository at
`C:\Users\Admin\Desktop\instrument-designer` (branch `opencode/main/desktop`).

## Context

- The project designs woodwind instruments (clarinets, flutes, chalumeaux,
  saxophones, recorders, xaphoons) using acoustic simulation and optimization.
- A previous Kimi K3 review identified issues around outer diameters, fingering
  mismatches, JAX optimizer parameter threading, hardcoded IPs, bare excepts,
  dead code, and register/fingering conventions.
- Recent work added governance hooks, JSON schemas for configs/design outputs,
  and a Tailscale peer monitor.
- A current architecture audit is in `docs/ARCHITECTURE_AUDIT.md`.

## Your Task

Perform a thorough review focused on:

1. **Correctness bugs** in acoustic/optimization code that would produce wrong
   instrument dimensions or wrong predicted pitches.
2. **Architectural inconsistencies** between modular component builders
   (`backend/modular_components.py`), benchmark instrument definitions
   (`backend/benchmark_all.py`), and config files (`config/*.json`).
3. **Parameter plumbing bugs** where values like `outer_diameter_mm`,
   `closed_top`, `n_bore_ctrl`, or `bore_length` are ignored, overwritten, or
   hardcoded.
4. **Fingering / register convention bugs** where the bit count does not match
   the hole count, or the register key behavior is wrong for closed-open vs
   closed-closed instruments.
5. **Hardcoded constants** that should be configurable (speed of sound, air
   temperature, material defaults, etc.).
6. **Missing error handling** (bare excepts, silent failures, swallowed
   exceptions).
7. **Import / reference rot** — imports pointing to deleted or moved modules.
8. **Test quality** — tests that don't actually assert, shadowed test names, or
   tests that pass for the wrong reason.
9. **Anything the audit missed** that you consider a real issue.

## Output Format

Return a structured report with the following sections:

### 1. Critical Bugs (must fix before merging to main)
For each bug:
- File and line number
- What is wrong
- Why it matters acoustically / numerically
- Suggested fix

### 2. Medium Issues (should fix soon)
Same format as above.

### 3. Low-Priority / Cleanup
- Style, dead code, documentation gaps, etc.

### 4. False Positives / Intended Behavior
- Things that look wrong but are actually correct. Explain why.

### 5. Recommended Validation Additions
- New tests, schema checks, or pre-commit checks that would catch these issues.

## Specific Files to Prioritize

- `backend/benchmark_all.py` — instrument definitions, outer diameters, fingerings
- `backend/modular_components.py` — builders vs. benchmark definitions
- `backend/jax_optimizer.py` — parameter threading
- `backend/two_phase_optimizer.py` — hardcoded values
- `backend/tmm_acoustics.py` and `backend/tmm_acoustics_jax.py` — acoustic model
- `backend/pareto_optimizer.py` — radiation consistency, length fixes
- `backend/chromatic_flute.py` — register/fingering conventions
- `backend/instrument_library.py` — duplicate records, verified flag
- `tests/test_*.py` — real pytest tests and ad-hoc scripts
- `config/*.json` — schema conformance and hole/fingering alignment

## Constraints

- Do not modify files. Only report.
- Be specific: cite file paths, line numbers, and code snippets.
- Do not hallucinate sources. If you are unsure, mark it as "needs verification".
- Prioritize physics-correctness bugs over style issues.
