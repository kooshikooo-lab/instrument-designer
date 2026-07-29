# Instrument Designer — AI Boot Sequence

**Read this file first.** It is the initialization procedure every AI agent must follow before writing code.

Never begin coding until every step below is complete.

---

## BOOT SEQUENCE

### ☐ Step 1 — Read the AI Constitution

Write down in your notes the **10 laws** from the AI Constitution, deleting those that are irrelevant to your current task. Refer back to these throughout the session.

Read `docs/AI_CONSTITUTION.md` completely. After reading, state aloud which laws apply to your current task and how you will follow them. Do not skip this.

### ☐ Step 2 — Read architecture documentation

Read the following files in order:

1. `docs/ARCHITECTURE.md` — system organization, coordinate systems, fingering conventions
2. `docs/ARCHITECTURE_DECISIONS.md` — why the architecture looks the way it does
3. `docs/CODING_STANDARDS.md` — implementation practices
4. `docs/PHYSICS_PRINCIPLES.md` — acoustic modeling assumptions

### ☐ Step 3 — Identify your subsystem

Determine which subsystem you are modifying:

| Subsystem | Key files |
|-----------|-----------|
| **Geometry** | `geometry.py`, `spline_bore.py` |
| **Acoustic solver** | `tmm_acoustics.py`, `tmm_acoustics_jax.py` |
| **Optimization** | `pareto_optimizer.py`, `jax_optimizer.py` |
| **Sound analysis** | `sound_analysis.py` |
| **Pipeline** | `design_from_wav.py`, `design_from_unconventional.py`, `design_pipeline.py` |
| **Generative agent** | `generative_agent.py`, `instrument_knowledge.py` |
| **CAD/Manufacturing** | `cadquery_export.py` |
| **GUI** | `woodwind_designer/`, `web/` |
| **Tests** | `tests/` |

Never modify an unrelated subsystem.

### ☐ Step 4 — Search before building

Search the codebase for:
- Existing function that does what you need
- Existing class that models what you need
- Existing test you should extend

Never create duplicate functionality.

### ☐ Step 5 — Produce an implementation plan

Before writing code, write a short plan identifying:
- Files to modify
- Interfaces affected
- Tests to update
- Documentation to update
- Any ADRs that apply

### ☐ Step 6 — Implement

Write code. Follow `docs/CODING_STANDARDS.md`. Run `docs/ARCHITECTURE_CHECKLIST.md` when done.

**During implementation:** run `docs/COMPLIANCE_CHECK.md` on every trigger:
- Every 15 minutes of active work
- Before every file modification or creation
- After every test run
- Whenever you feel stuck or uncertain

---

## FINAL CHECK

Before finishing:

- [ ] All tests pass
- [ ] Documentation updated
- [ ] No duplicated code
- [ ] Architecture preserved (no new coordinate systems, no hidden physics)
- [ ] `ARCHITECTURE_CHECKLIST.md` completed
- [ ] `COMPLIANCE_CHECK.md` run at least once in this session
- [ ] If you made a mistake, log it in `AI_FAILURE_PATTERNS.md`

## CONSTRAINTS & PREFERENCES

Non-negotiable constraints are defined in `docs/AI_CONSTITUTION.md` (10 laws). Read it before coding.

### Preferences (strongly preferred, not absolute)
- Python 3.11+ type hints on all functions
- NumPy-style docstrings on all functions
- Error handling uses sentinel values (1e10) for optimization failures, not exceptions
- No bare `except:` clauses — always specify exception type
- Tests in `tests/`, not `test_output/`
- Pipelines are thin orchestrators (<300 lines)
- Public APIs preserved or explicitly deprecated
- Architecture diagrams annotate planned vs implemented
