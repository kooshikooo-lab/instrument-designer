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

- [x] Governance guard enabled on this clone (`scripts/install_hooks.ps1`).
- [x] Pre-commit hooks active: file placement, regenerable artifacts, UTF-16,
       bare excepts, hardcoded IPs, module size, **config schema**, **import consistency**.
- [x] Tailscale peer monitor running for real-time machine coordination
       (`scripts/tailscale_monitor.py`, `launchers/start_tailscale_monitor.bat`).
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
| 1 | Numba wiring restore on `main` | both | merge of PR #62 | laptop keeps guarded skip; restore lands via PR #62 merge, then laptop merges `main` | 2026-08-04 |
| 2 | PR #62 head mirror `opencode-instrument-designer` | desktop | PR #62 merge | GitHub CLI cannot retarget PR heads; mirror ref tracks `opencode/main/desktop` until merge, then delete | 2026-08-04 |
| 3 | Mesh-repair gate protocol (`docs/TOOLS.md`) | laptop | laptop draft | DECIDED: build123d-first + pymeshlab/pymeshfix repair fallback (desktop 17906945); laptop drafting protocol | 2026-08-05 |
| 4 | build123d spike merge `8ddfc7a`+`e8d6254`+`7bc624e` → `opencode/main/laptop` | laptop | laptop merge | Desktop approved step 1 (17921022): laptop merges `origin/opencode/main/desktop` → `opencode/build123d/laptop`, then opens PR to `opencode/main/desktop` | 2026-08-06 |
| 5 | `cadquery-ocp` pin in `cad` extra | desktop | desktop commit | Desktop added pin (avoid `cadquery-ocp-novtk` OCP namespace clobber) | 2026-08-05 |
| 6 | Config schema unification | desktop | laptop review of multi-register decision | Schema approved; 3 configs migrated to canonical; `baroque_clarinet.json` kept as legacy until multi-register decision | 2026-08-06 |
| 8 | Tailscale peer monitor | both | laptop start monitor | Symmetric monitor shipped (`3382839`); desktop monitor running; first chess match failed because laptop monitor at `100.100.66.117:9124` is unreachable | 2026-08-06 |
| 9 | Architecture audit P0 fixes | desktop | — | Done: hardcoded OD/closed_top threaded through, missing holes added, impossible ODs corrected; analysis doc remains for reference | 2026-08-06 |
| 10 | Fusion 360 personal-use free subscription | desktop | — | Resolved: laptop confirmed Phase 0/1 scriptable, CAM probe next, Simulation blocked by license | 2026-08-06 |
| 13 | Chess match rematch | laptop | laptop start monitor + `chess_game.py accept` | Match #1 aborted (no games played); both-fail rule applies until laptop is reachable | 2026-08-06 |

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
