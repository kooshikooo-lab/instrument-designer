# FAILURE REPORT — Dual-Machine Audit

Generated: 2026-08-06
Branch: `opencode/main/desktop`
Scope: **both machines** — desktop and laptop failed in different ways. Sources:
git history (all branches, 552 commits), Discussion #23 (team channel),
`docs/ARCHITECTURE_AUDIT.md`, `docs/AI_REVIEW_FACT_CHECK.md`,
`docs/AI_FAILURE_PATTERNS.md` (10 logged patterns), `docs/session-logs/BOOT_STATE.md`,
`docs/REMINDERS.md`.

Each entry: **Symptom** → **Root cause** → **Fix status** → **Regression test**.

---

## Executive summary

The two machines failed along different axes:

- **Desktop's failures were mostly single-process bugs** (environment-variable
  contract mismatch, missing geometry validation, state-file pollution, duplicate
  test functions) that were localized, diagnosed, and fixed in one or two commits.
- **Laptop's failures were mostly silent regressions and process failures**:
  a function silently lost when a file was recreated from an older tree, chat
  messages silently dropped, test files silently excluded, an API break from a
  dependency bump — each silent until much later.
- **Shared failures were coordination failures**: a chess channel built on an
  env-var contract both sides had to guess, a monitor one machine never ran, a
  cluster that drops workers, and PR/workflow workarounds forced by tooling.

The recurring meta-pattern: **silent state drift** (files overwritten from older
trees, cursor bugs, missing whitelist entries, env mismatches) rather than
loud crashes. Most fixed; the open ones are tracked in the status columns.

---

## Section A — Desktop failures

### A1. Machine-name resolution bug (broke the chess channel)
- **Symptom**: `tailscale_monitor.py test` and `chess_game.py challenge` died
  with `cannot determine machine name. Set MACHINE_NAME=desktop or laptop` even
  when `TEAM_MACHINE=desktop` was set. Hostname `TWITCHY` (COMPUTERNAME) matched
  no hint. This aborted chess match attempts.
- **Root cause**: both `_machine_name()` implementations honored only
  `MACHINE_NAME`, not `TEAM_MACHINE` — an env-var contract mismatch between the
  launcher scripts and the monitor/chess code.
- **Fix status**: **FIXED** (`962b3f9`). `_machine_name()` now checks
  `MACHINE_NAME`, then `TEAM_MACHINE`, then falls back to matching `tailscale ip -4`
  against the config `ip` keys. `check_team_chat.py` defaults `MACHINE_NAME=desktop`.
- **Regression test**: `tests/test_team_channel_health.py` R1 (6 cases).

### A2. Monitor state file pollution (duplicates + stale queue)
- **Symptom**: `.tailscale_monitor.json` accumulated duplicate message ids
  (`laptop-1785983408131` twice) and `queued_messages` over 15h old.
- **Root cause**: pre-fix code appended every received message without dedup, and
  an older monitor version left a `queued_messages` structure that the current
  code never clears.
- **Fix status**: **FIXED** (`962b3f9` + state-file cleanup to 185 msgs / 0 queued).
  Desktop monitor restarted on fixed code (PID 4184).
- **Regression test**: R6 (no duplicate ids, no stale queued msgs).

### A3. Match-series rule not enforced
- **Symptom**: `chess_game.py challenge --games 1` was accepted, contradicting
  "a match is a series of >1 games".
- **Root cause**: no validation in the `challenge` command.
- **Fix status**: **FIXED** (`962b3f9`) — `--games < 2` rejected with exit 1.
- **Regression test**: R9 `test_r9_match_requires_more_than_one_game`.

### A4. Test-design mistake during this session (R9 analysis test)
- **Symptom**: the first R9 test called `_analyze_match(...)`, which writes
  `scripts/chess_match_analysis.json` and can post to the team channel — a side
  effect inside a unit test.
- **Root cause**: tested a reporting function instead of the rule it enforces.
- **Fix status**: **FIXED** — replaced with the CLI-enforcement test (A3).
- **Regression test**: R9 `test_r9_match_requires_more_than_one_game`.

### A5. CadQuery hole direction + Blender viewport regressions
- **Symptom**: tone holes cut with `-X` direction; Blender 4.x viewport broke;
  launchers popped windows.
- **Root cause**: CadQuery boolean cut direction bug + Blender API/viewport drift
  + launcher window handling.
- **Fix status**: **FIXED** (`2abce3c`).
- **Regression test**: existing cadquery instrument tests + manual launcher check.

### A6. Hardcoded geometry + impossible outer diameters
- **Symptom**: `jax_optimizer.py`/`two_phase_optimizer.py` hardcoded
  `outer_diameter_mm=22.0` and `closed_top=False`; benchmark presets had
  impossible diameters (`pvc_flute_D` bore_radius 10.2 with OD 14 → negative
  wall; `diatonic_D_chalumeau` same); `bass_chalumeau_Bb` had 0 tone holes vs an
  8-hole target.
- **Root cause**: params not threaded through optimizer signatures; presets with
  physically impossible OD; modular builder missing holes.
- **Fix status**: **PARTIALLY FIXED** (`e3492ed`, `47e1b9a`) — signatures accept
  `outer_diameter`/`closed_top`, benchmark ODs corrected, holes added. **OPEN**:
  no runtime guard enforcing `outer_diameter > 2*bore_radius` (planned this
  session, W2).
- **Regression test**: planned — negative-wall guard test (W2).

### A7. STL watertightness gaps (CadQuery path)
- **Symptom**: `xaphoon_C` exported by CadQuery was 2624/5264 non-watertight;
  build123d exported 1000/2012 watertight. STL batch validation checked only
  *importability* (verts/faces/bbox), not watertightness/volume.
- **Root cause**: CadQuery booleans not producing watertight shells for some
  geometry; no watertight gate in the export path.
- **Fix status**: **OPEN** — mesh-repair gate decided but not implemented
  (this session's W2); `backend/stl_verifier.py` exists as the numeric gate.
- **Regression test**: planned — watertight batch test (W2).

### A8. Deleted-module references (real bugs)
- **Symptom**: imports from deleted modules found by `validate_imports.py`:
  `backend/main.py → woodwind_designer.engine.design_server`,
  `run.py → woodwind_designer.main`,
  `scripts/benchmark_chalumier_dask.py → woodwind_designer.engine.chalumier_wrapper`,
  `tests/test_measure.py → backend.bore_optimizer`,
  `backend/benchmark_unconventional_shapes.py → woodwind_designer.engine.instrument_library`.
- **Root cause**: reorganized modules without fixing all import sites.
- **Fix status**: **OPEN** — validator added (`051ae95`) but fixes not all applied.
- **Regression test**: `tests/test_validate_imports.py`.

### A9. Test-suite debt
- **Symptom**: `tests/test_cadquery_instrument.py` returns `bool` instead of
  `assert`; STL tests (`test_stl_export.py` with two `test_stl_export` functions,
  `test_folded_export.py`) excluded from the pytest whitelist; a stray duplicate
  `import os`; `TEST_MATRIX.md` says 13 files, actual 14.
- **Root cause**: ad-hoc test scripts never converted to pytest + stale docs.
- **Fix status**: **OPEN** (this session's W2/W5).
- **Regression test**: none yet.

### A10. WSL/Ubuntu blocked (environment)
- **Symptom**: WSL2 installed but won't run; CPU virtualization disabled in
  BIOS/UEFI.
- **Root cause**: hardware/BIOS, not code.
- **Fix status**: **BLOCKED** — requires human to enter BIOS.

### A11. Optional deps missing in baseline environment
- **Symptom**: baseline 146 pass / 2 fail (`pymoo` missing) / 3 errors
  (`openwind` missing) / 1 skip.
- **Root cause**: `pymoo` not installed; `openwind` was not installed at audit
  time but IS now (so the 3 errors are likely resolved).
- **Fix status**: **OPEN** — pymoo tests fail on desktop; skip-guards planned (W5).

### A13. Spontaneous PowerShell pop-ups (stale Scheduled Tasks)
- **Symptom**: a PowerShell window popped up on the desktop **many times per day**
  with no user action; user explicitly confirmed it was not from clicking
  launchers.
- **Root cause**: 5 **Scheduled Tasks** ran `powershell.exe` **visibly**
  (interactive logon, no `-WindowStyle Hidden`), pointing at a **stale E: drive
  checkout** (`E:\Admin\WoodwindDesigner\woodwind-designer`, branch
  `feature/dask-jvm-chalumier-compliance`, commit `e8c6113`) instead of the
  current Desktop repo:
  - `ComplianceCheck` — time trigger, **~every 15 min** (the "many times a day").
  - `TestMatrixLow` — daily 02:00. `TestMatrixMedium` — weekly 03:00.
  - `DaskChalumierSweep`, `RemoteDesignSweep` — one-shot (last ran 01/08).
- **Fix status**: **FIXED** — all 5 tasks disabled (`Disable-ScheduledTask`;
  reversible with `Enable-ScheduledTask -TaskName <name>`).
- **Regression test**: `Get-ScheduledTask` — none of the 5 in `Ready`/`Running`
  state; next-run times cleared.

### A12. AI-agent process failures (desktop-side, logged in `AI_FAILURE_PATTERNS.md`)
1. Test file written to `test_output/` instead of `tests/` (2026-07-29).
2. Imported `backend.spectrum.PowerSpectrum` that didn't exist (twice).
3. Unused imports left after module extraction.
4. PowerShell `-Include` with `-Recurse` silently excluded docs from a zip.
5. Created `stl_generator.py` duplicating `backend/cadquery_export.py`.
6. "Verified" an optimizer restore without importing it (UTF-16 + shadow
   package shadowing) — `import backend.optimizer` hung.
7. Audited from the wrong branch and claimed governance docs "did not exist".
8. TMM vs OpenWind solver disagreement on a simple cylinder (register/boundary
   convention mismatch) — caught only by cross-solver validation.
9. Posted external instructions to a collaborator without user approval (Law 10).
- **Fix status**: **FIXED/LOGGED** — prevention rules added; `AI_FAILURE_PATTERNS.md`
  is the institutional-memory log.

---

## Section B — Laptop failures

### B1. `phase_at()` silently lost (worst laptop failure)
- **Symptom**: `test_metamaterial_register_suppression.py` failed after
  `7cae468`; the function `phase_at()` (added in `4f14203`, 2026-08-03 06:18)
  was gone.
- **Root cause**: `7cae468` (06:48, 30 min later) **recreated the file from an
  older tree**, overwriting the newer `phase_at()` addition (455 lines written
  back). Classic silent overwrite.
- **Fix status**: **FIXED** by laptop — `phase_at()` restored; whitelisted
  metamaterial suite back to 250 passed / 2 skipped.
- **Regression test**: `test_metamaterial_register_suppression.py` +
  `test_metamaterial_low_clarinets.py`.

### B2. Metamaterial tests silently excluded from the suite
- **Symptom**: 8 `test_metamaterial*.py` files were present but silently excluded
  from the whitelisted suite (baseline 159/2 instead of 250/2).
- **Root cause**: whitelist drift — files added but never whitelisted.
- **Fix status**: **FIXED** by laptop — whitelisted.
- **Regression test**: the 8 files now run in the suite.

### B3. Chat reliability bugs (coordination impact on desktop)
- **Symptom**: laptop's replies silently dropped; `post --discussion` crashed on
  None URLs; the team-chat cursor bug caused **desktop to miss laptop's reply**
  to the schema thread (00:54:58).
- **Root cause**: in-flight reply handling + `comment_id_from_url` guard +
  cursor updated after posting (cursor bug fixed on desktop side `051ae95`).
- **Fix status**: **FIXED** (`45ddcb2` stop dropping replies, `591c384` None-url
  guard, `051ae95` cursor).
- **Regression test**: `tests/test_team_channel_health.py` R0-adjacent sync
  checks; manual sync verification.

### B4. Surrogate training regressions
- **Symptom**: training broke on 30-dim samples (hardcoded `input_dim=50`);
  BatchNorm/Dropout mishandled; `build_surrogate_pipeline` didn't pass
  `bore_param_ranges`; `BiObjectiveBO` broke on `botorch>=0.16` API
  (`train_X/Y`, 2×d bounds, `squeeze Y`).
- **Root cause**: hardcoded dims, API drift after dependency bump.
- **Fix status**: **FIXED** (`9eb7ae3`, `712c763`, `a955286`, `77dd2d6`).
- **Regression test**: surrogate training/BO smoke tests.

### B5. Broken imports across 45 files
- **Symptom**: `tmm_acoustics` import breakage across 45 files after a reorg.
- **Root cause**: module moves without import rewiring.
- **Fix status**: **FIXED** (`56d0ec9`).
- **Regression test**: `tests/test_validate_imports.py`.

### B6. `is_available` NameError
- **Symptom**: `chalumier_wrapper.is_available` raised NameError.
- **Root cause**: module-level `import re` removed during refactor.
- **Fix status**: **FIXED** (`b5a27c6`).
- **Regression test**: chalumier dask benchmark script.

### B7. Tooling failures
- **Symptom**: `sync.ps1` pointed at a broken junction target (`5886194`) and
  pinged itself instead of the other machine (`3177146`); duplicate
  `[tool.pytest.ini_options]` after kalles/main merge (`dccb604`); hook install
  not worktree-safe (`b94f879`); `gh` CLI unresolvable under Task Scheduler's
  limited PATH (`9b7d6ef`).
- **Root cause**: stale config + PS scripting mistakes + merge duplication.
- **Fix status**: **FIXED** (all four).
- **Regression test**: manual/launcher smoke tests.

### B8. Interruption failures (upstream gateway instability)
- **Symptom**: 9× Nvidia free-tier 502 stream errors today (15 total, limit
  32/32 requests) killed turns mid-work; 550× `ENOTFOUND opencode.ai` in the
  last 24h (836 total) — requiring "go on" nudges.
- **Root cause**: **upstream** opencode/Nvidia gateway instability, not repo code.
- **Fix status**: **MITIGATED by governance** — laptop pushed `56cad29`:
  `AGENTS.md` auto-recover rule, `CONSTRAINTS_AND_PREFERENCES.md` **Step 0.5
  Recover from an interrupted turn**, `BOOT_STATE.md` **Current Task Cursor**,
  `scripts/resume_check.py`. Upstream bug report recommended.
- **Regression test**: `scripts/resume_check.py` (read-only cursor/state check).

### B9. Cross-machine environment mismatch
- **Symptom**: laptop Python 3.14.6 / numpy 2.4.6 vs desktop 3.12.10 / numpy
  2.5.1; laptop worker dropped 3× on desktop scheduler restarts; pickled
  objectives with module-level `from backend...` imports fail on workers.
- **Root cause**: divergent environments + scheduler restarts + non-self-contained
  pickles.
- **Fix status**: **WORKAROUND** — functions ship from client; imports must be
  kept inside functions. Worker drops recur until scheduler stops bouncing.
- **Regression test**: cluster health script (manual).

### B10. Laptop monitor port 9124 repeatedly down
- **Symptom**: desktop's peer-channel probes of `100.100.66.117:9124` fail
  (tailscale ping OK, port dead). Chess rematch blocked.
- **Root cause**: laptop not running `tailscale_monitor.py monitor` (or not on
  the fixed code). Laptop busy on P0-2b CAM probe.
- **Fix status**: **OPEN** — notice posted (comment 17924449); awaiting laptop
  to pull `962b3f9`, start monitor, run R8 tests.
- **Regression test**: R7/R8 (live, skip when peer offline).

---

## Section C — Shared / coordination failures

### C1. Chess match attempts (3 failed + 1 draw)
- **Symptom**: 3 match attempts failed to complete; one test game (2026-08-06
  13:06Z) ended in a **draw (1/2-1/2)**; the full 10-game 60+0 rematch is still
  pending.
- **Root cause**: A1 (machine-name crash on challenge/accept) + B10 (laptop port
  down). Timer/forfeit semantics also iterated (`7a76581`, `50e943b`, `d973904`).
- **Fix status**: **PARTIALLY FIXED** — A1 fixed and health-test-enforced;
  blocked on B10 (laptop monitor).
- **Regression test**: R8/R9.

### C2. Cluster worker instability
- **Symptom**: laptop worker dropped 3× on desktop scheduler restarts; worker
  only re-attaches via `scripts/start_worker.py`.
- **Root cause**: scheduler bouncing + no auto-reconnect.
- **Fix status**: **OPEN** — workaround: keep scheduler up, keep imports inside
  pickled functions.
- **Regression test**: `cluster_health.py` (manual).

### C3. PR #62 head mirror
- **Symptom**: PR #62 head can't be retargeted (GitHub CLI limitation); a mirror
  ref `opencode-instrument-designer` must track `opencode/main/desktop` until
  merge, then be deleted.
- **Root cause**: GitHub CLI tooling limitation.
- **Fix status**: **WORKAROUND ACTIVE** — mirror ref maintained.

### C4. kalles-main-branch deletion confusion
- **Symptom**: a `kalles-main-branch` remote-tracking ref appeared pruned;
  laptop confirmed the branch is gone from origin but not intentionally deleted
  by desktop.
- **Root cause**: branch cleanup ambiguity across machines.
- **Fix status**: **RESOLVED** — `opencode/main/laptop` is the carrier;
  divergence is intentional.
- **Regression test**: n/a.

### C5. Lock-file decision ping-pong
- **Symptom**: pip-tools vs per-platform locks vs WSL timing took multiple
  rounds to settle.
- **Root cause**: cross-machine dependency-version divergence.
- **Fix status**: **RESOLVED** (`6517b19`) — pip-tools from desktop Python 3.12,
  lock `[dev,cad,test]`, CI `dependency-locks` job.
- **Regression test**: `scripts/compile_requirements.py --check` in CI.

### C6. Fusion 360 license constraint
- **Symptom**: Phase 2 CAM scriptable and verified, but **Simulation blocked by
  license** (personal-use free tier).
- **Root cause**: external licensing, not code.
- **Fix status**: **WORKAROUND** — CAM proceed; Simulation deferred.

### C7. Merge divergence / sequencing
- **Symptom**: laptop is ~55 commits ahead on `opencode/main/laptop` carrying the
  metamaterial stack; full merge deferred until PR #62 lands.
- **Root cause**: per-machine integration-branch strategy + PR gate.
- **Fix status**: **ACTIVE** — approved order: laptop merges
  `origin/opencode/main/desktop` → `opencode/build123d/laptop`, then PR to
  `opencode/main/desktop`.
- **Regression test**: dependency check + tests before merge (CI).

---

## Recurring themes

1. **Silent state drift is the #1 failure class** (B1 file overwrite, A2 state
   pollution, B2 whitelist drift, B3 cursor, B10 monitor-down).
2. **Env-var contracts between machines must be single-source** (A1) — now
   health-test-enforced.
3. **Verify by running, not by diffing** (A12 #6, A1).
4. **External/published actions need approval** (A12 #10, Law 10).
5. **Upstream tooling instability** (B8) needs governance-level resilience, not
   code fixes.
6. **Optional deps and whitelists drift silently** (A9, A11, B2) — guard with
   skip-guards and whitelist regression tests.

## Follow-up actions tracked

- W2: negative-wall runtime guard, watertight gate, whitelist STL tests.
- W5: pymoo skip-guards, bool→assert, whitelist `test_team_channel_health.py`.
- B10/C1: chess rematch depends on laptop starting its monitor.
- B8: upstream bug report recommended (anomalyco/opencode).
