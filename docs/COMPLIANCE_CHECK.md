# Compliance Check Script

Run this at **session start**, then on every **trigger event**:

## BOOT SEQUENCE (summary)

Every session/agent must run these 6 steps before writing code. Full version: `docs/CONSTRAINTS_AND_PREFERENCES.md`.

1. **Read the AI Constitution** (`docs/AI_CONSTITUTION.md`) — state which laws apply to your task.
2. **Read architecture docs** — `ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `CODING_STANDARDS.md`, `PHYSICS_PRINCIPLES.md`.
3. **Identify your subsystem** — from the table in `CONSTRAINTS_AND_PREFERENCES.md`.
4. **Search before building** — reuse existing functions/classes/tests; never duplicate.
5. **Produce an implementation plan** — files, interfaces, tests, docs, ADRs.
6. **Implement** — follow `CODING_STANDARDS.md`; run `ARCHITECTURE_CHECKLIST.md` and `COMPLIANCE_CHECK.md` on every trigger.

---

| Trigger | When |
|---------|------|
| **Timer** | Every 15 minutes of active work |
| **Before code** | Before every file modification or creation |
| **After tests** | After every test run |
| **Drift feel** | Whenever you feel unsure or stuck |

Do not skip triggers. If you are in the middle of a code change when a trigger fires, complete the change (max 5 more minutes) then run this check.

---

## PASS / FAIL procedure

For each check below, answer PASS or FAIL.

- **PASS** → continue to next check
- **FAIL** → stop, fix the issue, re-run the check
- If you cannot fix immediately, log the failure in `AI_FAILURE_PATTERNS.md` and document the issue in the session

---

### CHECK 1 — Constitution refresh

Recite the laws from `docs/AI_CONSTITUTION.md` from memory. If you cannot remember them all, re-read the file.

State which laws apply to your current activity and which do not.

**PASS:** You can state each law and explain relevance.
**FAIL:** You skipped or cannot recall the laws.

---

### CHECK 1b — Dependency integrity (Law 13)

For every declared dependency (`pyproject.toml` extras, `requirements*.txt`) required by your subsystem: verify it is installed and importable, and check there is no `importorskip`/`skip` masking a missing package that production code relies on.

```
python -m pip check
python -m pytest tests -q -rs    # review every SKIPPED line — is the skip justified?
```

**PASS:** All required dependencies import; every skip is genuinely optional/declared-off.
**FAIL:** A declared dependency is missing — that is a bug (Law 13). Install it and re-run the skipped tests until they pass.

---

### CHECK 1c — Pre-commit audit (Law 14)

Before every commit touching `.py` files, verify the work you are about to commit:

1. **Constitution re-read** — agents forget the constitution because of lack of context size, so re-read `docs/AI_CONSTITUTION.md` and state which laws apply to this change (from the file, not from memory). If you cannot quote them, you have not read them.
2. **Tests ran and passed** — the tests covering the change passed (or you added coverage for new code).
3. **Diff reviewed** — `git diff --cached` was read line-by-line and checked against the laws and coding standards from step 1; you can explain every hunk.
4. **No silent killers** — scan for wrong enum names, unit swaps, hardcoded physics constants, off-by-one, copy-paste edits.
5. **No scratch files** — `git status` shows no `fix_*.py` / debug / one-off files staged.
6. **Verification declared** — the commit message carries a `Tests:` or `Verification:` line (enforced by the commit-msg hook). If verification was skipped, declare `AUDIT: unverified` explicitly.

**PASS:** All six points checked and recorded in the commit message.
**FAIL:** You are about to commit unverified work. Stop — run the tests / fix the environment first.

---

### CHECK 1e — System self-audit (Law 16)

The enforcement system must itself be verified — a broken guard is worse than no guard, because it gives false confidence. Before committing to a canonical branch or `main`:

```
python scripts/system_audit.py          # all enforcement layers active + correct
python -m pytest tests/test_guard_scripts.py -q   # the guards' own tests (Law 16.5)
```

And before any cross-machine merge:

```
python scripts/merge_gate.py <base> <head>   # predicts conflicts WITHOUT touching the worktree
```

**PASS:** `system_audit.py` exits 0 and the merge gate reports a clean merge (or you have rehearsed the conflicts on a `merge/<topic>` branch per Law 15.3).
**FAIL:** Any check exits non-zero — fix the guard or the violation before proceeding. Do not commit around a failing audit.

---

### CHECK 1d — Compliance watchdog (Law 14)

The watchdog automates what agents forget. Run it, and trust its exit code over your memory:

```
python scripts/compliance_watchdog.py --check-laws       # laws match AI_CONSTITUTION.md?
python scripts/compliance_watchdog.py --check-baseline   # no NEW violations vs baseline?
python scripts/compliance_watchdog.py --once             # full scan (session start)
```

- The pre-commit hook already runs `--check-baseline` — a new violation blocks the commit.
- The baseline (`scripts/compliance_baseline.json`) is versioned: when you *intentionally* fix
  debt, regenerate it with `--baseline` so the fix becomes the new baseline.
- If you introduce a real violation, the regression check blocks — do not work around it by
  re-baselining unless the change is deliberate and reviewed.

**PASS:** `--check-laws` and `--check-baseline` both exit 0.
**FAIL:** A new violation or stale law list — fix it before committing (do not bypass).

---

State which single subsystem you are modifying (from the table in `docs/CONSTRAINTS_AND_PREFERENCES.md`).

**PASS:** You name exactly one subsystem.
**FAIL:** You are touching multiple subsystems — split the task.

---

### CHECK 3 — Drift detection

Compare your next action against the implementation plan from Step 5 of the boot sequence.

**PASS:** Current action matches the plan.
**FAIL:** You drifted — stop, re-plan, discard unfinished drift work.

---

### CHECK 4 — Duplication guard

Identify the code you are about to write. Now search the codebase for existing implementations.

**PASS:** Code does not exist elsewhere.
**FAIL:** Code exists — reuse it.

---

### CHECK 5 — Self-test (every 3rd cycle only)

Ask: *"Have I introduced any architecture violations since the last compliance check?"*

Specific violations to watch for:
- New coordinate system without documentation
- Physics logic inside an optimizer or pipeline module
- Duplicate data structures (units, frequencies, fingerings)
- Module over ~500 lines that should be split
- Non-thin orchestrator (custom NSGA-II, CMA-ES in pipeline code)

**PASS:** No violations introduced.
**FAIL:** Document the violation in `AI_FAILURE_PATTERNS.md` and fix it.

---

## Logging

After all checks pass, append one line to the session context:

```
COMPLIANCE: passed at <timestamp> | subsystem: <name> | cycle: <N> | trigger: <timer|before-code|after-tests>
```

If any check failed, append:

```
COMPLIANCE: FAILED at <timestamp> | check: <N> | reason: <brief> | fix: <applied|deferred>
```

---

## Violation of this procedure

Skipping compliance checks is itself a compliance failure. Log it in `AI_FAILURE_PATTERNS.md` under "Failure — Compliance skipped."
