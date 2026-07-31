# Instrument Designer ÔÇö AI Boot Sequence

**Read this file first.** It is the initialization procedure every AI agent must follow before writing code.

**Never begin coding until every step below is complete.**

**IMPORTANT ÔÇö The confirmation requirement:** You must begin your next response with: *"I have read the AI Constitution and will follow it."* followed by a summary of which laws apply to your current task. This is not optional. If you do not include this statement, you have skipped Step 1.

---

## BOOT SEQUENCE

### Ôûí Step 1 ÔÇö Read the AI Constitution

Read `docs/AI_CONSTITUTION.md` completely.

**Then explicitly state in your response:** *"I have read the AI Constitution and will follow it."*

Also list which laws apply to your current task and how you will follow them. This forces you to refresh the architectural constraints in your working context before touching any code.

Do not skip this confirmation. If you do not state it, you have not completed Step 1.

### Ôûí Step 2 ÔÇö Read architecture documentation

Read the following files in order:

1. `docs/ARCHITECTURE.md` ÔÇö system organization, coordinate systems, fingering conventions
2. `docs/ARCHITECTURE_DECISIONS.md` ÔÇö why the architecture looks the way it does
3. `docs/CODING_STANDARDS.md` ÔÇö implementation practices
4. `docs/PHYSICS_PRINCIPLES.md` ÔÇö acoustic modeling assumptions

### Ôûí Step 3 ÔÇö Identify your subsystem

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

### Ôûí Step 4 ÔÇö Search before building

Search the codebase for:
- Existing function that does what you need
- Existing class that models what you need
- Existing test you should extend

Never create duplicate functionality.

### Ôûí Step 5 ÔÇö Produce an implementation plan

Before writing code, write a short plan identifying:
- Files to modify
- Interfaces affected
- Tests to update
- Documentation to update
- Any ADRs that apply

### Ôûí Step 6 ÔÇö Implement

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

