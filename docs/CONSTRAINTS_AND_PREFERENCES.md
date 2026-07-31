# AI Constraints & Preferences

**Read this file first.** It is the initialization procedure every AI agent must follow before writing code.

Never begin coding until every step below is complete.

---

## Subsystem Reference

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

---

## BOOT SEQUENCE

### □ Step 1 — Read the AI Constitution

Write down in your notes the **10 laws** from `docs/AI_CONSTITUTION.md`, deleting those irrelevant to your current task. Refer back throughout the session.

### □ Step 2 — Read architecture documentation

Read in order:
1. `docs/ARCHITECTURE.md` — system organization, coordinate systems, fingering conventions
2. `docs/ARCHITECTURE_DECISIONS.md` — why the architecture looks the way it does
3. `docs/CODING_STANDARDS.md` — implementation practices
4. `docs/PHYSICS_PRINCIPLES.md` — acoustic modeling assumptions

### □ Step 3 — Identify your subsystem

Determine which subsystem you are modifying from the table above.

### □ Step 4 — Search before building

Search the codebase for:
- Existing function that does what you need
- Existing class that models what you need
- Existing test you should extend

### □ Step 5 — Produce an implementation plan

Before writing code, write a short plan identifying:
- Files to modify
- Interfaces affected
- Tests to update
- Documentation to update
- Any ADRs that apply

### □ Step 6 — Implement

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
- [ ] If you made a mistake, log it in `docs/AI_FAILURE_PATTERNS.md`
