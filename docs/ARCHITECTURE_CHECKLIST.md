# Architecture Checklist

Pre-flight and pre-commit checklist for AI agents. Run this before writing code and again before finishing.

---

## BOOT SEQUENCE (summary)

Every session/agent must run these 6 steps before writing code. Full version: `docs/CONSTRAINTS_AND_PREFERENCES.md`.

1. **Read the AI Constitution** (`docs/AI_CONSTITUTION.md`) — state which laws apply to your task.
2. **Read architecture docs** — `ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `CODING_STANDARDS.md`, `PHYSICS_PRINCIPLES.md`.
3. **Identify your subsystem** — from the table in `CONSTRAINTS_AND_PREFERENCES.md`.
4. **Search before building** — reuse existing functions/classes/tests; never duplicate.
5. **Produce an implementation plan** — files, interfaces, tests, docs, ADRs.
6. **Implement** — follow `CODING_STANDARDS.md`; run `ARCHITECTURE_CHECKLIST.md` and `COMPLIANCE_CHECK.md` on every trigger.

---

## Pre-Flight (before writing code)

- [ ] Read `docs/AI_CONSTITUTION.md` and identify applicable laws
- [ ] Read `docs/ARCHITECTURE.md` — understand coordinate systems and conventions
- [ ] Read `docs/ARCHITECTURE_DECISIONS.md` — understand why the architecture is what it is
- [ ] Identify the subsystem you are modifying
- [ ] Search existing code for what you need (function, class, utility)
- [ ] Search existing tests
- [ ] Search existing documentation
- [ ] Search existing interfaces
- [ ] Produce a short implementation plan

## Pre-Commit (before finishing)

### No duplication
- [ ] No duplicate code created
- [ ] No duplicate interfaces created
- [ ] No duplicate data structures (coordinate systems, units, fingerings)

### Architecture integrity
- [ ] No new coordinate systems introduced
- [ ] No hidden physics (physics belongs in `backend.physics`, not in optimizers or pipelines)
- [ ] No mixing of GUI concerns with backend concerns
- [ ] Module boundaries respected (one responsibility per file)
- [ ] Public APIs preserved or explicitly deprecated

### Quality
- [ ] Tests updated or added
- [ ] Documentation updated
- [ ] No hardcoded instrument-specific assumptions in general code
- [ ] All functions have type hints
- [ ] All functions have NumPy-style docstrings
- [ ] Error handling uses sentinel values (1e10) for optimization failures, not exceptions
- [ ] No bare `except:` clauses

### If a mistake was made
- [ ] Log it in `docs/AI_FAILURE_PATTERNS.md` so it is not repeated
- [ ] Fix the mistake before committing
