# AGENTS.md — Working Agreement for instrument-designer

You are an agent working in this repository on behalf of one of two machines:
- **desktop** (`TEAM_MACHINE=desktop`) — the human's primary machine
- **laptop** (`TEAM_MACHINE=laptop`)

Both machines build this repo with AI agents. Coordination happens over GitHub
**Discussion #23** (the "team channel"). A human is sometimes present but must
NOT be used to relay messages between machines.

## MANDATORY — Step 0: sync the team channel

The FULL communications protocol is hard-coded in
`docs/CONSTRAINTS_AND_PREFERENCES.md` under **Step 0**. Read it. It survives
context drops.

Also reload the live session state from
`docs/session-logs/BOOT_STATE.md` — this is the versioned snapshot of current
goal, progress, next steps, decisions, and sync context. It survives context
drops; update it at the end of every session.

Also read `docs/REMINDERS.md` — the standing compliance checklist plus the list
of pending cross-machine threads. It is a living file both machines edit; check
it at session start right after `team_chat.py sync`. If any pending thread is
waiting on the other machine and has gone stale (no reply for a while), post a
brief nudge to #23 so requests never silently drop.

**Mid-session context loss:** if your context has been compacted, summarized,
or you notice you can no longer recall this session's earlier details, STOP and
RE-READ this file plus `docs/session-logs/BOOT_STATE.md` before doing anything
else. This happens frequently mid-session — it is the #1 recurring failure.
Highlights:

```
python scripts/team_chat.py sync      # at session start AND before you stop
python scripts/team_chat.py post --file path\to\msg.md   # to send (use --file)
python scripts/team_chat.py post --important "..."       # tag a READ-REQUIRED message
python scripts/team_chat.py remind "..."                 # follow up if not acknowledged
```

- Post when you start/finish a task affecting shared state, make a decision, or
  are blocked.
- **READING is mandatory (Law 12).** After `sync`, actually read and restate what
  the other machine posted. Re-check at least every 30 min (`watch --interval 30`).
  If you posted something important and got no acknowledgment, `remind` — never
  assume it was read.
- Reply in-channel; never silently drop a request.
- **The human answers questions directly from the desktop.** If a question needs
  the human's input, post it to #23 and the desktop will surface it and post the
  answer back. Resolve machine-to-machine issues yourselves first; only escalate
  to the human when a real decision is needed.
- Channel is canonical — decisions in #23 win.
- Provisional changes: mark `AUDIT:` in the commit message.
- Don't commit regenerable artifacts (STLs, JSON dumps, logs).

## MANDATORY — enable the governance guard (once per clone)

The governance file (`docs/CONSTRAINTS_AND_PREFERENCES.md`) is instruction-only
and protected. Enable the guard on this clone so your commits can't accidentally
rewrite it:

```
powershell -ExecutionPolicy Bypass -File scripts\install_hooks.ps1
```

This sets `core.hooksPath` to the versioned hooks inside the repo (nothing is
copied into `.git/hooks`), so hook updates merge with the repo. After that, any
commit touching a protected governance file requires `GOVERNANCE-UPDATE` in the
commit message; CI (`governance-guard.yml`) enforces the same rule on every push.
If you see a BLOCKED message from the hook, you were about to rewrite the boot
sequence without authorization — re-read the file instead of editing it.

**Law 16 (system self-audit)** — the guards must not be trusted on faith. Before
committing to a canonical branch or `main`, run:

```
python scripts/system_audit.py      # all enforcement layers active + correct
```

Before any cross-machine merge, run `python scripts/merge_gate.py <base> <head>`;
if it predicts conflicts, rehearse on a `merge/<topic>` branch — never merge blind.
The pre-push hook (`scripts/git-hooks/pre-push`) blocks canonical-branch
deletion/force-push unless explicitly approved via `GUARD_BRANCH_ALLOW_DELETE=<branch>`
or `GUARD_BRANCH_ALLOW_FORCE=<branch>` (Law 15.8 / Law 16.2).

## Environment

- Repo: `kooshikooo-lab/instrument-designer` (remote: `origin`)
- Branch naming: Law 15 in `docs/AI_CONSTITUTION.md` governs branches. Only
  four namespaces exist: `main` (trunk), `opencode/main/<machine>` (canonical,
  permanent), `opencode/<topic>/<machine>` (feature, ephemeral), and
  `merge/<topic>` (cross-machine merge staging, ephemeral). Nothing else is a
  valid branch name.
- Channel: Discussion #23 (GraphQL id `D_kwDOTOg0Rs4AoFZO`)
- Git identity: `Admin <kooshikooo@gmail.com>`; `gh` authed as `kooshikooo-lab`.
- Set `TEAM_MACHINE` to your machine name so sync output is self-identifying.

## If things go wrong

- `team_chat.py sync` fails: check `gh auth status` and network.
- Merge conflict: prefer `main`'s structure where `main` intentionally refactored,
  then commit and post the outcome to #23.
- Other machine unresponsive: post your message anyway, note the expected action,
  and proceed with what is safe on your side.
