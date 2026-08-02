# Instrument Designer — AI Boot Sequence & Governance Index

**Read this file first.** It is the initialization procedure every AI agent must follow before writing code.

**Never begin coding until every step below is complete.**

**IMPORTANT — The confirmation requirement:** You must begin your next response with: *"I have read the AI Constitution and will follow it."* followed by a summary of which laws apply to your current task. This is not optional. If you do not include this statement, you have skipped Step 1.

---

## BOOT SEQUENCE

### [Step 0] - Sync with the team channel (MANDATORY, do this first)

This project runs on TWO machines (laptop and desktop) that must coordinate through
GitHub **Discussion #23**. Do not start any other work until you have checked it.

Run:

```
python scripts/team_chat.py sync
```

Rules:

- **If it prints new messages:** read every one of them, then **state in your response**
  what the other machine said and whether it is waiting on you.
- **If a message is addressed to you or asks for a decision:** reply in the SAME channel
  before continuing: `python scripts/team_chat.py post "your reply"`.
- **Never relay through the human.** If you need something from the other machine, post
  it to Discussion #23. The human must never be the message bus between the two computers.
- `sync` keeps a per-machine cursor (scripts/.team_state.json), so it only shows NEW messages.

Skipping this step is the #1 cause of the human having to mediate. It is not optional.

### ☐ Step 1 — Read the AI Constitution

Read `docs/AI_CONSTITUTION.md` completely.

**Then explicitly state in your response:** *"I have read the AI Constitution and will follow it."*

Also list which laws apply to your current task and how you will follow them. This forces you to refresh the architectural constraints in your working context before touching any code.

Do not skip this confirmation. If you do not state it, you have not completed Step 1.

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

## GOVERNANCE DOCUMENTS

All governance documents exist in **two places** — `docs/` in the repository (authoritative source) and the GitHub wiki (https://github.com/kooshikooo-lab/instrument-designer/wiki). Keep both in sync. Read them in the order listed here.

| # | File (`docs/`) | Wiki page | Purpose |
|---|----------------|-----------|---------|
| 1 | `AI_CONSTITUTION.md` | [Governance-Constitution](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Constitution) | The 10 non-negotiable laws all AI work must obey |
| 2 | `CONSTRAINTS_AND_PREFERENCES.md` | [Governance-Boot-Sequence](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Boot-Sequence) | This file — the boot sequence (Section 1) |
| 3 | `AI_FAILURE_PATTERNS.md` | [Governance-Failure-Patterns](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Failure-Patterns) | Known failure modes of AI work on this repo — read before every session; log new failures here |
| 4 | `COMPLIANCE_CHECK.md` | [Governance-Compliance](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Compliance) | Compliance triggers and checklist (15-min timer, before code, after tests, when stuck) |
| 5 | `CODING_STANDARDS.md` | — | Implementation practices |
| 6 | `ARCHITECTURE_CHECKLIST.md` | [Governance-Checklist](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Checklist) | Run at the end of every implementation |
| 7 | `ARCHITECTURE.md` | [Internal-Architecture](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Architecture) | System organization, coordinate systems, fingering conventions |
| 8 | `ARCHITECTURE_DECISIONS.md` | [Governance-ADRs](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-ADRs) | ADRs — why the architecture looks the way it does |
| 9 | `PHYSICS_PRINCIPLES.md` | — | Acoustic modeling assumptions and units |
| 10 | `WIKI.md` / `WIKI-INDEX.md` | [Home](https://github.com/kooshikooo-lab/instrument-designer/wiki) | Project wiki — deep reference for research and conventions |
| 11 | `PROJECT.md` / `STATUS.md` / `ROADMAP.md` | — | Project state, status, and roadmap |
| 12 | `ai_project_summary.md` | — | High-level project summary for context |

---

## FINAL CHECK

Before finishing:

- [ ] All tests pass
- [ ] Documentation updated
- [ ] No duplicated code
- [ ] Architecture preserved (no new coordinate systems, no hidden physics)
- [ ] `ARCHITECTURE_CHECKLIST.md` completed
- [ ] `COMPLIANCE_CHECK.md` run at least once in this session
- [ ] **Posted a session-status update to Discussion #23** via `python scripts/team_chat.py post "..."` (what you did, what you need, what's blocked)
- [ ] If you made a mistake, log it in `AI_FAILURE_PATTERNS.md`
