# REMINDERS.md — Standing compliance + pending cross-machine threads

Living file, edited by **both** machines (desktop and laptop). It is the
"remind each other" mechanism: read it at the start of every session, right
after `python scripts/team_chat.py sync`, and update it whenever a pending
thread starts, moves, or resolves.

## Session-start ritual (after Step 0 sync)

1. Read `docs/CONSTRAINTS_AND_PREFERENCES.md` (Step 0) + `docs/session-logs/BOOT_STATE.md`.
2. Read this file.
3. If any pending thread below is waiting on the **other** machine and has gone
   stale (no reply for a while), post a brief nudge to Discussion #23.
4. If a thread resolved, delete its row here in the same commit as the reply.

## Standing compliance checklist

- [ ] Governance guard enabled on this clone (`scripts/install_hooks.ps1`).
- [ ] Commit touching `docs/CONSTRAINTS_AND_PREFERENCES.md` carries
      `GOVERNANCE-UPDATE` in the message (hook + CI enforce).
- [ ] Provisional / exploratory work tagged `AUDIT:` in the commit message.
- [ ] No regenerable artifacts committed (STLs, JSON dumps, logs, `test_output/`).
- [ ] `team_chat.py sync` at session start and before stopping.
- [ ] Reply in-channel; never silently drop a request from the other machine.
- [ ] Channel is canonical — decisions posted to #23 win over local ones.
- [ ] `TEAM_MACHINE` set (desktop / laptop) so sync output self-identifies.
- [ ] Branch naming: `opencode/main/<machine>` for per-machine integration,
      `opencode/<idea>/<machine>` for experiments (merge or scrap).
- [ ] No force-push to a shared/remote ref; keep per-machine `main` divergence
      from `main` minimal.
- [ ] Tests pass locally before committing (`pytest tests/`).

## Pending cross-machine threads

| # | Thread | Owner | Awaiting | Status | Last update |
|---|--------|-------|----------|--------|-------------|
| 1 | Topk integration table | desktop | laptop | **RESOLVED** — desktop posted the 5-family table + robustness to #23 (comment 17891204, 2026-08-04); laptop verified shared engine parity (5.902c @ maxiter=250) | 2026-08-04 |
| 2 | Numba wiring restore on `main` | both | merge of PR #62 | laptop keeps guarded skip; restore lands via PR #62 merge, then laptop merges `main` | 2026-08-04 |
| 3 | PR #62 head mirror `opencode-instrument-designer` | desktop | PR #62 merge | GitHub CLI cannot retarget PR heads; mirror ref tracks `opencode/main/desktop` until merge, then delete | 2026-08-04 |
| 4 | Track C build123d spike + mesh-repair gate protocol | desktop | laptop | **WAITING on desktop** — `opencode/build123d/laptop` (`8ddfc7a` spike, `e8d6254` protocol, `7bc624e` BOOT_STATE) posted #23 comment-17906678; merge decision is desktop's call. Branch now also carries K3 doc fixes B1/B2/C-phase (comment-17914586) | 2026-08-06 |
| 5 | `kalles-main-branch` deleted from origin | desktop | laptop | **WAITING on desktop** — flagged #23 comment-17906728; no commits lost (tip `b198c4c` ancestor of `opencode/main/laptop`); confirm rename/deletion intent | 2026-08-05 |
| 6 | Kimi K3 doc fixes + `baroque_clarinet.json` decision | desktop | laptop | **WAITING on desktop** — laptop applied + posted confirmed K3 fixes (comment-17914586); desktop to decide `baroque_clarinet.json` option-1/2 (laptop recommended option 2 in `discussioncomment-17914412`); Fusion 360 contract change also unapproved | 2026-08-06 |

## Nudge rule

- Stale = the awaited machine has not replied to a direct question in a while
  (typically hours for an active session; use judgment for long-running tasks).
- A nudge is one short #23 post: restate the open item, link the thread, note
  the expected action.
- After nudging, wait; do not re-nudge within the same session unless the item
  is time-critical.

## How to keep this file healthy

- Edit it in the **same commit** as the #23 post that moves a thread.
- Keep rows terse (one line per thread); delete resolved rows.
- Add a row the moment you leave something waiting on the other machine.
