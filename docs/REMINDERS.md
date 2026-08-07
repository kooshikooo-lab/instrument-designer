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
       bare excepts, hardcoded IPs, module size, **config schema**, **import consistency**,
       **PowerShell 5.1 compatibility**, **pip-tools lock-file up-to-date check**.
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
| 1 | Numba wiring restore on `main` | both | merge of PR #62 | **DONE** — PR #62 merged, numba wiring restored | 2026-08-07 |
| 2 | PR #62 head mirror `opencode-instrument-designer` | desktop | PR #62 merge | **DONE** — PR #62 merged, mirror ref can be deleted | 2026-08-07 |
| 3 | Mesh-repair gate protocol (`docs/TOOLS.md`) | laptop | laptop draft | DECIDED: build123d-first + pymeshlab/pymeshfix repair fallback (desktop 17906945); laptop drafting protocol | 2026-08-05 |
| 4 | build123d spike merge → `opencode/main/laptop` | laptop | laptop merge | Desktop approved step 1: laptop merges `origin/opencode/main/desktop` → `opencode/build123d/laptop`, then PR to `opencode/main/desktop` | 2026-08-06 |
| 5 | `cadquery-ocp` pin in `cad` extra | desktop | — | Resolved: desktop added pin (avoid `cadquery-ocp-novtk` OCP namespace clobber) | 2026-08-05 |
| 6 | Config schema unification | desktop | laptop review of multi-register decision | Schema approved; 3 configs migrated to canonical; `baroque_clarinet.json` kept as legacy | 2026-08-06 |
| 7 | pip-tools dependency locks | desktop | — | Resolved: lock files generated for `[dev,cad,test,chess]` and committed | 2026-08-06 |
| 8 | Tailscale peer monitor | both | — | Resolved: symmetric monitor works; test chess game drawn 2026-08-06T13:06Z. Desktop monitor running. | 2026-08-06 |
| 9 | Architecture audit P0 fixes | desktop | — | **SUPERSEDED** — new P0 fixes in Phase 0 (SoS cleanup, two-phase register freeze, bass chalumeau) | 2026-08-07 |
| 10 | Fusion 360 personal-use free subscription | desktop | — | Resolved: laptop confirmed Phase 0/1 scriptable, CAM probe next | 2026-08-06 |
| 11 | PowerShell 5.1 compatibility lint | desktop | — | Resolved: `scripts/check_powershell_51_compat.py` added; wired into pre-commit + CI | 2026-08-06 |
| 12 | Chess match rematch | both | laptop reachable again | One test game drawn; full 10-game bullet rematch pending when both monitors online | 2026-08-06 |
| 13 | Laptop Opencode account / usage budget | desktop→laptop | laptop reply | Laptop went offline mid-session (2026-08-06) with Opencode Go + Zen subscriptions NOT active. Laptop must be more restrictive if different account. | 2026-08-06 |
| 14 | Team of experts agent model | desktop | comments / go-ahead on PoC | Proposal posted to #23 (17925874): lightweight `scripts/review_panel.py` with Physics Auditor + Math+Code Formalist first. Awaiting feedback. | 2026-08-06 |
| 15 | **Phase 0 P0 fixes** | desktop | human decisions on 4 questions | **BLOCKED** — 4 questions posted to Discussion #23: impossible ODs, bass chalumeau holes, two-phase scope, merge conflict. Need human decision before Phase 0 execution. | 2026-08-07 |
| 16 | **Bass chalumeau merge conflict** | desktop→laptop | laptop merge | **ACTION NEEDED** — Desktop has tone-hole fix in `build_bass_chalumeau_Bb()`; laptop doesn't. Laptop must merge `origin/opencode/main/desktop` → `opencode/main/laptop` before any merge, or manual diff required. | 2026-08-07 |
| 17 | **WoodwindOpenWind FEM** | desktop | Phase 0 completion | **PLANNED** — Create `backend/woodwind_openwind.py` mirroring `TrumpetOpenWind`; register `REFINED` strategy for woodwinds (CLARINET, SAXOPHONE, FLUTE, CHALUMEAU). | 2026-08-07 |
| 18 | **CT-Scan Benchmarking** (Issue #47) | desktop | Phase 1 | **PLANNED** — Download FT40/FT44 from Zenodo, extract bore profiles, run two-phase optimizer, document RMS vs CT ground truth. | 2026-08-07 |
| 19 | **Demakein Replacement** (Issue #48) | desktop | Phase 1 | **PLANNED** — Extract 11 preset profiles via TMM, replace `demakein_wrapper.py` internals, remove demakein import, keep public API. | 2026-08-07 |

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

(End of file)