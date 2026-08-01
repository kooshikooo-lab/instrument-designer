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

Recite the 10 laws from `docs/AI_CONSTITUTION.md` from memory. If you cannot remember all 10, re-read the file.

State which laws apply to your current activity and which do not.

**PASS:** You can state each law and explain relevance.
**FAIL:** You skipped or cannot recall the laws.

---

### CHECK 2 — Subsystem check

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
