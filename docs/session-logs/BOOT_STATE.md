# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/main/desktop`** (naming convention
  `opencode/<app>/<machine>`, user directive 2026-08-04; renamed from
  `opencode-instrument-designer`). `opencode-instrument-designer` remains as the
  PR #62 head mirror until merge (GitHub CLI cannot retarget PR heads). Based on
  `origin/main` (now `c8b9fd2` after laptop's docs-only cherry-pick of the CAD
  research). PR **#62** open against `main` (import repair + numba restore +
  AI/ML-family port + Step-3 reconciliation + intonation pass standards + topk
  polish family; MERGEABLE).
- **CAD / design-tool track (current focus, 2026-08-05)**: retired the old
  `woodwind-design-automation` and `instrument-designer-backup` repos (deleted
  via web UI by the user; only `instrument-designer` + `chalumier` remain).
  Built one-click view workflows for the human's preference (no GUI hunting, no
  fullscreen):
  - **Blender**: 5.2 LTS installed (winget); `blender_addon/` (View3D Sidebar
    panel, std-lib only) + `scripts/view_instrument.py` + `scripts/blender_view.py`
    + `launchers/view_instrument.bat` (committed `84b393e`, pushed). One-click
    `View Instrument.bat` on Desktop. Blender always launched
    `--window-geometry 60 60 1280 800` (never fullscreen).
  - **three.js web preview (track B)**: `web/preview.html` (three 0.160 via CDN
    importmap, STLLoader, OrbitControls, preset dropdown) served by a new
    `/preview` route in `design_server`; `scripts/view_browser.py` starts the
    server if down and opens the browser; `launchers/view_browser.bat`; `View in
    Browser.bat` on Desktop.
- Standing items (not this session's work): `backend/spectral` design awaits user
  approval; laptop Phase 2G surrogate work + build123d spike live on laptop
  branches.
- Standing directive: tools must be **integrated into a pipeline**, never just
  installed and forgotten (tool registry guard is live).
- User's fallback instruction: if no task is assigned, do something **safe** (no
  architecture changes, no law-breaking, no deletion, no merging).

## Constraints & Preferences

- **Step 0 protocol**: `python scripts/team_chat.py sync` at session start AND
  before stopping (Discussion #23); never relay through the human; channel is
  canonical — decisions in #23 win. `TEAM_MACHINE` identifies the machine.
- Constitution: Law 1 (no architecture damage), Law 3 (reuse existing bench
  scripts), Law 7 (canonical `346100.0` mm/s speed of sound), Law 10 (stop/ask if
  intent unclear — **don't speculate about what the user wants, just ask**).
- **ORDER OF OPERATIONS (user directive 2026-08-05)**: "add to to-do list" = do
  NOT start the task; explain + ask before reordering work; **ASK, do not
  speculate** — when uncertain, ask rather than guess.
- User is very uncomfortable with visual/GUI interfaces and gets lost in
  maximized/fullscreen windows. Solutions must be one-click / keyboard-driven and
  never open fullscreen. (opencode window-state fixed to `isFullScreen:false`,
  2026-08-05.)
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for commits touching
  `docs/CONSTRAINTS_AND_PREFERENCES.md`; don't commit regenerable artifacts
  (STLs, JSON dumps, logs, `bench_*.txt`).
- Tool adoption rule: install + declare (`docs/TOOLS.md`) + import + whitelisted
  test; guard = `tests/test_tool_registry.py` + `scripts/toolcheck.py`.

## Progress

### Done (this session / CAD track)
- **Governance**: ORDER OF OPERATIONS + "ASK, do not speculate" written into
  `docs/CONSTRAINTS_AND_PREFERENCES.md` (committed with `GOVERNANCE-UPDATE` in
  `a1807bd`).
- **Governance hooks expanded** (`8acdb61`, pushed to `opencode/main/desktop`):
  - `.gitattributes` to keep shell scripts LF-encoded and executable.
  - `scripts/git-hooks/pre-commit` runs `scripts/validate_pre_commit.py`:
    blocks regenerable artifacts, UTF-16, file-placement violations, bare
    excepts, hardcoded IPs, and warns on oversized modules.
  - `scripts/git-hooks/commit-msg` runs `scripts/validate_commit_msg.py`:
    requires `GOVERNANCE-UPDATE` for governance files and `AUDIT:` for
    provisional keywords.
  - CI workflow updated to use `validate_commit_msg.py`.
- **Schema enforcement layer started** (`fd010fc` + `6ad42db`, pushed):
  - `schemas/instrument_config.schema.json` documents existing config variants
    (baroque clarinet, bass clarinet, bass chalumeau) and a canonical target.
  - `scripts/validate_instrument_configs.py` validates all `config/*.json`
    files and cross-checks fingering chart bit lengths against tonehole counts.
  - Pre-commit hook now runs the config validator on any staged `config/*.json`.
  - `tests/test_instrument_config_schema.py` added (5 tests passing).
  - `jsonschema` added to `dev` extras.
  - Draft schema posted to Discussion #23 for laptop review.
- **Design-output schema** (`f8fad63`, pushed):
  - `schemas/design_output.schema.json` for optimizer-generated JSON artifacts.
  - `scripts/validate_json_schema.py` generic validator (schema + file/dir).
  - `tests/test_design_output_schema.py` added (4 tests passing).
- **Team chat cursor bug fixed** (`051ae95`, pushed):
  - `scripts/team_chat.py` no longer updates the "last read" cursor after posting.
  - This caused desktop to miss the laptop's 00:54:58 reply to the schema thread.
- **Import-consistency validator** (`051ae95`, pushed):
  - `scripts/validate_imports.py` detects imports from deleted modules
    (`backend/archived_optimizers`, etc.) and unresolved imports.
  - Wired into `scripts/validate_pre_commit.py` for all staged Python files.
  - `tests/test_validate_imports.py` added (4 tests passing).
- **Instrument config schema updated** (`051ae95`, pushed):
  - Added explicit `performance` definition (register RMS/offset, twelfths RMS, note).
  - `performance` now allowed in canonical variant.
  - Fixed `fingering_chart` cross-check in `validate_instrument_configs.py` to
    handle both legacy nested and canonical flat structures.
- **Path-rewrite cleanup** (in `a1807bd`): all 15 active scripts/tests use
  repo-relative resolution (`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
  / `Split-Path $PSScriptRoot -Parent`), no hardcoded paths.
- **Cluster tooling** (in `a1807bd`): `scripts/start-cluster.ps1`,
  `spawn_worker.py`, `cluster_health.py`, `start_scheduler.py`, `start_worker.py`,
  upgraded `sync.ps1`. Scheduler running on desktop (PID 6468, since 12:51);
  `cluster_health` reports reachable, currently **1 worker** (laptop
  `tcp://100.100.66.117:52274`). Known cross-machine mismatch: laptop
  Python 3.14.6 / numpy 2.4.6 vs desktop 3.12.10 / numpy 2.5.1 (functions ship
  from client, so OK unless a worker imports local-only modules); pickled
  objectives need self-contained imports.
- **Repos retired**: old `woodwind-design-automation` + `instrument-designer-backup`
  deleted (user, web UI). Verified `gh repo list` = only `instrument-designer` +
  `chalumier`. Pruned stale `origin/kalles-main-branch` remote-tracking ref
  (branch is gone from origin; laptop confirmed tip `b198c4c` is an ancestor of
  `opencode/main/laptop`; **not** deleted intentionally by desktop).
- **Blender track delivered** (`84b393e`, pushed): `blender_addon/` (panel: Check
  Server / Refresh Presets / Import Instrument; urllib only), `scripts/view_instrument.py`
  (Blender auto-discovered via `BLENDER_EXE` env → PATH → glob of
  `C:\Program Files\Blender Foundation\Blender*\blender.exe`; STL via design_server
  with local cadquery fallback), `scripts/blender_view.py` (imports STL, smooth
  shade, frames model, prints `VIEW READY`), `launchers/view_instrument.bat`.
  E2E verified: server → 50,484-byte STL → 504-vertex mesh in Blender.
- **design_server**: running on desktop port 8000 (`python -m uvicorn
  woodwind_designer.engine.design_server:app --host 0.0.0.0 --port 8000`).
  Restarted this session (now PID 21480) to add `/preview`. Endpoints:
  `/health`, `/presets`, `/design...`, `/optimize...`, `/export/cadquery` (POST
  STL), `/export/cadquery/instruments` (90 presets), `/export/svg`, `/preview`.
- **three.js web preview (track B)** shipped: `web/preview.html` (three 0.160
  importmap from unpkg — verified reachable; STLLoader, OrbitControls, preset
  dropdown populated from `/export/cadquery/instruments`, auto-fit camera),
  `/preview` route in `design_server.py`, `scripts/view_browser.py` (starts server
  if down, opens browser at `/preview?preset=...`), `launchers/view_browser.bat`.
  Desktop shortcuts: `View Instrument.bat` + `View in Browser.bat`.
- **Mesh-repair gate DECISION** (posted to #23, 17906945): **build123d-first +
  pymeshlab/pymeshfix repair fallback** for legacy CadQuery paths; `cadquery-ocp`
  pinned in the `cad` extra (`2903873`) to stop pip pulling `cadquery-ocp-novtk`
  (which clobbers the OCP namespace and breaks cadquery).
- **Track C approved**: laptop's build123d spike `8ddfc7a` + mesh-gate protocol
  `e8d6254` + BOOT_STATE `7bc624e` approved for merge to `opencode/main/laptop`
  (posted 17906945). Laptop's key finding: build123d produces watertight meshes
  where CadQuery does not (xaphoon_C: CadQuery 2624/5264 non-watertight vs
  build123d 1000/2012 watertight).
- **Research doc on `main`**: laptop docs-only cherry-pick `8603240` → `c8b9fd2`
  (`docs/RESEARCH_design_to_finished_instrument.md`, WIKI §11, WIKI-INDEX; 123
  tests passed). Full laptop-branch merge deferred until after PR #62 merges
  (laptop is 55 commits ahead, carries the metamaterial stack).

### In Progress
- Governance/schema coordination with laptop via Discussion #23 (cursor bug fixed,
  reply posted at 2026-08-06, awaiting laptop confirmation).
- `scripts/dask_scheduler.log` left unstaged (live log, tracked pre-existing).

### Blocked
- Standing (not this session): `backend/spectral` implementation awaits user
  approval of `docs/DESIGN_spectral.md` (3 open questions). FreeCAD workbench
  (track A) deferred — user chose three.js first.

## Key Decisions

- **Mesh-repair gate**: build123d-first for new geometry + pymeshlab/pymeshfix
  repair step as fallback in the STL pipeline (2026-08-05).
- **Track C spike approved** for laptop merge (`8ddfc7a`/`e8d6254`/`7bc624e`).
- **`kalles-main-branch`**: not intentionally deleted; `opencode/main/laptop` is
  the carrier toward `main`; full branch merge waits for PR #62.
- `cadquery-ocp` explicitly pinned in the `cad` extra.
- opencode window fix: edit `window-state-*.json` `isFullScreen:false` + mark
  read-only so the app can't overwrite on close (then unlock once relaunched OK).
- Order of operations + ASK-don't-speculate are now binding governance.

## Next Steps

1. Stay on `opencode/main/desktop`; PR #62 (MERGEABLE) still needs no external
   approval per user; laptop is deferring its branch merge until PR #62 merges.
2. Await laptop feedback on `schemas/instrument_config.schema.json` (posted to #23).
   If approved, continue with unified canonical config format + migration of the 4
   existing configs. If laptop has additional config keys, revise schema first.
3. Continue governance / agent-coordination improvements: pre-commit
   import-consistency checks (per the other model's analysis) and/or design-output
   JSON schema.
4. Have the user verify the three.js preview (`View in Browser.bat`) and the
   Blender viewer; then continue or pivot.
5. Monitor #23 for: laptop's mesh-repair gate protocol draft for `docs/TOOLS.md`,
   laptop's merge of track C, cluster worker re-attach, PR #62 status.
6. Optional later: track A (FreeCAD workbench); `tests/test_stl_export.py` has a
   duplicate `test_stl_export` (l.8–47 dead code shadowed by l.50–83) to clean up.
7. Standing: present `backend/spectral` for approval when the user is available.
8. Acoustic improvements held pending user priority: Ernoult phase-based cost
   (already partially implemented in `tmm_acoustics.py` and `tmm_acoustics_jax.py`)
   and cross-fingerings for 12-hole chromatic clarinet.

## Critical Context

- **`origin/main` = `c8b9fd2`** (laptop's docs-only research cherry-pick).
  `opencode/main/desktop` = latest desktop work (HEAD incl. `2903873`). Laptop
  `opencode/main/laptop` is ahead (55 commits, metamaterial stack). Track C on
  `opencode/build123d/laptop`. PR #62 head mirrors to
  `opencode-instrument-designer` (delete after merge).
- **design_server** running on desktop (PID 21480, port 8000, restarted this
  session to add `/preview`). Blender 5.2 at
  `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` (auto-discovered).
- **Cluster**: scheduler PID 6468 (up since 12:51); 1 worker currently (laptop
  `tcp://100.100.66.117:52274`). Laptop worker has been dropped 3x on desktop
  scheduler restarts; laptop re-attaches via `scripts/start_worker.py` and will
  keep detached if the scheduler keeps bouncing. Cross-machine import issue:
  pickled objectives with module-level `from backend...` imports fail on workers
  — keep imports inside the function.
- Env (desktop): Windows, Python 3.12.10, numpy 2.5.1, cadquery 2.8.0, fastapi +
  uvicorn running. (Laptop: Python 3.14.6, numpy 2.4.6.) conda NOT on PATH — use
  system Python + `PYTHONPATH=<repo root>`.
- Repo canonical constants unchanged: `SPEED_OF_SOUND = 346100.0` mm/s (Law 7).
- Git identity `Admin <kooshikooo@gmail.com>`; `gh` authed as `kooshikooo-lab`.
  Desktop `TEAM_MACHINE=desktop`; laptop `TEAM_MACHINE=laptop` (Copilot Pro
  agents on the desktop paused until 2026-09-01).

## Relevant Files

- `web/preview.html` — three.js preview page (track B).
- `woodwind_designer/engine/design_server.py` — FastAPI server incl. `/preview`,
  `/export/cadquery` (90 presets), `/export/cadquery/instruments`.
- `scripts/view_browser.py` — one-click browser launcher (starts server if down).
- `scripts/view_instrument.py` + `scripts/blender_view.py` + `blender_addon/` —
  Blender one-click viewer + addon.
- `launchers/view_instrument.bat`, `launchers/view_browser.bat` — repo launchers.
- `scripts/team_chat.py` — Discussion #23 sync/post (use `post --file`). **Note:**
  posts no longer move the read cursor; always run `sync` after posting.
- `scripts/validate_imports.py` — import-consistency checker (staged files or `--path`).
- `schemas/instrument_config.schema.json` — migration + canonical schema for `config/*.json`.
- `scripts/start-cluster.ps1`, `spawn_worker.py`, `cluster_health.py`,
  `start_scheduler.py`, `start_worker.py`, `sync.ps1` — cluster tooling.
- `backend/cadquery_export.py` — 90 presets; `docs/RESEARCH_design_to_finished_instrument.md`
  (on `main` via `c8b9fd2`).
- `docs/CONSTRAINTS_AND_PREFERENCES.md` — governance (protected;
  `GOVERNANCE-UPDATE` required). `docs/REMINDERS.md` — pending threads table
  (currently rows 1–5).
- `tests/test_stl_export.py` — duplicate `test_stl_export` (dead code, fix later).
- `C:\Users\Admin\AppData\Roaming\ai.opencode.desktop\window-state-00d27f9b-60df-4cdf-b8de-500ef732713f.json` — opencode window state (fixed, unlocked).
