# Instrument Designer — AI Boot Sequence & Governance Index

> ## IMMUTABLE — INSTRUCTION-ONLY FILE
> This file is the source of **instructions**, not a scratchpad for assumptions.
> It is protected by a pre-commit hook and a CI check (`.github/workflows/governance-guard.yml`).
> **Do not edit it unless you are following an explicit, direct instruction to do so**
> (from a human or an existing instruction in this repo), and you must keep the
> BOOT SEQUENCE section byte-for-byte intact unless the instruction is about the
> boot sequence itself.
>
> If you are an agent and you "assumed" this file should change: STOP. Do not
> rewrite, summarize, truncate, or rephrase it. If the boot sequence or protocol
> is missing from your context, re-read this file — do not re-create it from memory.
> Violations are blocked by the commit hook and fail CI.
>
> Authorized edits (e.g. a human asked you to update governance) must include
> `GOVERNANCE-UPDATE` in the commit message, otherwise the hook blocks the commit.

**Read this file first.** It is the initialization procedure every AI agent must follow before writing code.

**Never begin coding until every step below is complete.**

**IMPORTANT — The confirmation requirement:** You must begin your next response with: *"I have read the AI Constitution and will follow it."* followed by a summary of which laws apply to your current task. This is not optional. If you do not include this statement, you have skipped Step 1.

---

## BOOT SEQUENCE

### [Step 0] - Sync with the team channel (MANDATORY, do this first)

This project runs on TWO machines (laptop and desktop) that must coordinate through
GitHub **Discussion #23**. Do not start any other work until you have checked it.

Run **twice per session**: once at the start, once at the end (before you stop):

```
python scripts/team_chat.py sync
```

- If it prints new messages, READ every one of them, then **state in your response**
  what the other machine said and whether it is waiting on you.
- `sync` keeps a per-machine cursor (scripts/.team_state.json), so it only shows NEW messages.

Skipping this step is the #1 cause of the human having to mediate. It is not optional.
The rest of this section is the complete communications protocol — it is hard-coded here
so it survives context drops. You do not need another file to know how to communicate.

#### When to post to the channel

Post a message to Discussion #23 whenever you:
- start a task that affects shared state (repo, artifacts, runs, decisions),
- finish a task the other machine needs to know about,
- make a decision or change a convention the other machine relies on,
- are blocked and need the other machine to do something.

Post with:

```
python scripts/team_chat.py post --file path\to\message.md
```

Use `--file` (not inline text) for anything longer than a single short line.
For other threads (e.g. Discussion #46), pass `--discussion N`.

#### Replying to messages

- Reply inside Discussion #23 to the relevant comment via `gh`:

  ```
  gh api repos/kooshikooo-lab/instrument-designer/discussions/23/comments \
    -f body="your reply" -f reply_to_id=<parent_comment_id>
  ```

- Answer what was asked; if you cannot fully act, state exactly what you did and
  what remains. Do not silently drop a request.

#### Protocol rules

1. **Never relay through the human.** If the other machine posted something, act
   on it directly. The human must never be the message bus between the two computers.
2. **Keep the channel canonical.** Decisions made in #23 win. If a conversation
   also happens in a doc or another thread, mirror the binding decision back to #23.
3. **Never lose work.** If you cannot finish something, leave a checkpoint commit
   or a clearly marked stub, and say so in the channel.
4. **Prefer direct-to-main, then audit.** Commits go to `main`; work lives in
   feature branches that merge into `main`. If a change is provisional, mark it
   for audit in the commit message (e.g. `AUDIT:` prefix) and say so in the channel.
5. **Do not commit regenerable artifacts** (STLs, large JSON dumps, logs). The
   `.gitignore` covers most; check with `git status` before committing.

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
