# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/build123d/laptop`** (laptop), HEAD `905266d`
  (2026-08-08: merged desktop `a8b3cc2` rescue + Law 14.N dead-path prevention;
  pyproject.toml testpath union; pushed. PR #66 MERGEABLE).
- **Desktop branch `opencode/main/desktop`** at `a8b3cc2` (Laws 15+16 + dead-path
  prevention Law 14.N + rescue bench tooling).
- **Fusion 360 track (2026-08-07, desktop offline)**: new `tests/test_fusion_360.py`
  (15 tests, whitelisted) covering smoke/phase1 generators + manifest/result
  contracts; **finding** — xaphoon_C now watertight (C1 fix) so Phase 0.3 repair
  proof needs a new non-watertight target; **Phase 2b CAM probe** dispatched in
  the deployed add-in (`_run_phase2b`, defensive) + contract tests. Commits:
  `b58a65e` `6efa7ad` `917369d` `0e3bf06` (held, not pushed).
- **Governance merge COMPLETE (2026-08-07)**: laptop merged desktop `04564614`
  (Laws 12-14 + compliance watchdog) → resolved `scripts/team_chat.py` as a union
  (1 conflict, not the 19 desktop predicted) → `6c23a11`, promoted via ff-only
  onto `opencode/build123d/laptop`, pushed. Approved by desktop; 355 passed / 4
  skipped. PR #66 remains the carrier.
- **Laws 15+16 merged locally on laptop** (`d4e71e0`, 2026-08-07): rehearsed on
  `merge/laptop-receives-laws15-16` (1 conflict in `pyproject.toml` testpath
  union, resolved), gates green (guard tests 32 passed, watchdog --check-laws +
  baseline OK, toolcheck PASS, system_audit ALL PASS), promoted ff-only, staging
  branch deleted. NOT pushed yet (audit hold).
- **Law 17 added by laptop** (`74edbe0`, 2026-08-07): "Work in order of safety,
  not order of approval" — do safe independent work first; only shared-state
  actions wait for approval. [GOVERNANCE-UPDATE] System: audit PASS.
- **Law 16 installed pre-push hook**: `scripts/git-hooks/pre-push` now wired via
  `scripts/install_hooks.ps1` (pre-commit, commit-msg, pre-push).
- **Orphan branches** (Law 15/16 audit finding, non-blocking debt): local +
  remote orphans exist (`experiment/ai-tier1`, `experiment/ai-tier1-review`,
  `kalles-rebased`, `port/main-2026-08-01*`, `scipy-prototype`,
  `test/kalles-into-main`) — flagged for coordinated rename/delete, not touched
  during audit.
- **Desktop is running a FULL CODEBASE AUDIT** (Laws 1-14) — laptop holds pushes
  to shared branches until audit completes.
- **Phase 1 READY**: WoodwindOpenWind FEM integration, surrogate audit.
- **Standing directive**: tools must be integrated into a pipeline, never just
  installed and forgotten; `AUDIT:` for provisional commits; ask the human ONLY
  for genuinely ambiguous + high-stakes/irreversible decisions, always with full
  context and a recommended default — never trivial or bare questions;
  **do safe work first, don't idle on approval**.

## Constraints & Preferences

- **Step 0 protocol**: `python scripts/team_chat.py sync` at session start AND
  before stopping (Discussion #23); channel is canonical.
- Constitution: Law 1 (no architecture damage), Law 3 (reuse existing bench
  scripts), Law 7 (canonical `346100.0` mm/s speed of sound), Law 10 (stop/ask),
  **Law 15 (branch governance)**, **Law 16 (enforcement must be enforced:
  `system_audit.py` before canonical commits, guard tests)**,
  **Law 17 (work in order of safety, not approval)**.
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for protected governance
  files (`docs/AI_CONSTITUTION.md`, `docs/REMINDERS.md`, etc.); `System: audit
  PASS` required for commits touching guards/hooks/constitution/CI (Law 16.7);
  don't commit regenerable artifacts.

## Progress

### Done (this session, 2026-08-08)
- **Rescue + dead-path merge COMPLETE (laptop side)**: rehearsed on
  `merge/laptop-receives-rescue-deadpath` per Law 15.3 (merge_gate correctly
  predicted 1 conflict), resolved `pyproject.toml` testpath union
  (`test_fusion_360.py` laptop + `test_validate_imports.py` desktop), forward-
  ported `validate_imports.py` venv exclusions (.venv/.venv-wsl/venv/node_modules
  — fixes `jedi` `import __main__` crash on `.venv-wsl`), reworded
  `scripts/test_numba.py` docstring dropping deleted-branch ref. Commit `905266d`
  (GOVERNANCE-UPDATE for desktop-ratified Law 14.N). Verified: system_audit ALL
  PASS, guard tests 32 passed, pre-commit validation 23 staged files, compliance
  "no new violations vs baseline". Pushed; PR #66 MERGEABLE. Posted completion
  to #23 (comment 17939738).
- **Pre-existing finding (AUDIT, not merge-introduced)**: `validate_imports.py
  --all` reports DEAD PATH ERRORS identically on desktop's own canonical
  `opencode/main/desktop` (run.py → woodwind_designer.main, benchmark_chalumeau.py
  → tmm_optimizer, bpy/chess deps) — confirmed via clean clone at
  `%TEMP%\opencode\desktop_clone`. Environmental or missing registry entries on
  desktop side; reported to #23.
- **ACK'd desktop promote instruction + audit coordination** (holding shared
  pushes).
- **Dask test batches (local cluster)**: local scheduler (PID 15908) + 1 worker
  (PID 7204) on `tcp://127.0.0.1:8786`; dask topk suite 5 passed; full suite
  355 passed / 4 skipped; cross-branch dask benchmark validated (2 instruments
  in 1.0s).
- **Law 15 read + ACK'd**; deleted local `merge/build123d-laptop-receives-governance`
  (content proven ancestor of integration branch).
- **Broad research expansion committed locally** (`0808026`, pre-commit +
  compliance regression passed): 2 new docs (`RESEARCH_openwind_fem_and_surrogates.md`,
  `RESEARCH_ct_benchmarking.md`) + addenda to metamaterials (§9) and
  design-to-finished (§6b). Wiki updated + pushed (separate repo, `master 7e10b6e`).
- **Laws 15+16 merged locally + Law 17 authored** (`d4e71e0` + `74edbe0` +
  `5c9fe08`): staged rehearsal on `merge/laptop-receives-laws15-16`, 1 conflict
  resolved, all gates green (387 passed / 4 skipped), promoted ff-only, staging
  deleted, pre-push hook installed, `.gitignore` += `scripts/*.out`.
- Research docs commit + governance commits held locally pending audit; wiki live.

### In Progress
- **Fusion 360 GUI track (desktop-chat pipeline working, 2026-08-08)**: built +
  verified `scripts/gui_automation/desktop_chat.py` (clipboard+paste → Enter →
  `PrintWindow` capture → WinRT OCR). Root-caused two bugs: (1) screen-region
  capture grabbed the occluding terminal → replaced with `gui_driver.capture_window_png`
  (PrintWindow, works while occluded) + `window_hwnd`; (2) non-normalized paths
  with `..` broke `StorageFile.GetFileFromPathAsync` → `os.path.abspath` in
  `send_prompt`. Live-verified: Claude replies read back via OCR (resp_len ~2200).
  `tests/test_gui_automation.py` 13 passed. Posted #23 comment 17940797.
  STILL BLOCKED: local vision loop (`vision_loop.py` ask_vision) times out even
  at 384px screenshot against `gemma3:4b` (120s) — the Fusion mesh-repair agent
  (Phase 0.3) still needs either a smaller/faster vision path or the desktop-chat
  fallback. ChatGPT Desktop not installed (window is Store stub).
- **PR #66** (`opencode/build123d/laptop` → `opencode/main/desktop`) — OPEN +
  MERGEABLE, carrier for laptop work. Awaiting desktop merge + orphan-branch
  deletion (unblocked).
- **Desktop codebase audit (Laws 1-14)** — posted in batches to #23; no code
  changes to shared branches during audit.
- **Dask worker attach to desktop scheduler**: `tcp://100.69.113.41:8786` still
  unreachable; laptop local cluster running meanwhile.
- **Orphan branch cleanup** (Law 15/16 audit finding): to coordinate rename/
  delete with desktop post-merge.

### Blocked
- Chess match rematch (thread 12): pending both monitors; desktop monitor port
  9124 not responding.
- Dask desktop scheduler: not started yet on desktop side.

## Key Decisions
- **SoS test expectations → 346100 mm/s** (Law 7: canonical source of truth).
- **Register detection → shared module** `backend/physics/register_detection.py`.
- **Two-phase optimizer: Fix, don't delete** (Law 1).
- **Governance merge: keep PR #66 as carrier**; no merge to `opencode/main/laptop`.
- **Law 15 ACK'd**; all `merge/` staging branches deleted on both sides.

## Next Steps
1. Fusion 360: pick a faster local-vision path for the GUI agent (smaller capture
   didn't fix the gemma3:4b timeout; try OpenRouter free-vision fallback or a
   lighter model), then run the Phase 0.3 mesh-repair proof end-to-end; wire
   `desktop_chat.py` in as the manual-GUI fallback once ChatGPT Desktop is installed.
3. Await desktop: merge PR #66 + delete orphan branches (unblocked by laptop merge).
4. Watch #23 for ack of merge-completion post (17939738); nudge if stale.
5. Restart tailscale peer monitor + `team_chat.py watch --interval 30` per
   Law 12/Constitution.
6. Attach laptop dask workers to desktop scheduler when reachable; re-run
   cluster test batches.
7. WSL2 + Tailscale (userspace) + Dask scheduler/worker setup (queued todo).
8. Lawkeeper: `opencode/framework-mvp/desktop` STILL not pushed by desktop —
   re-verify `git ls-remote` before executor work.
9. Fusion 360: human runs `phase2b_trigger.json` in a Fusion session; laptop
   verifies `phase2b_result.json` against the CAM contract; find a replacement
   non-watertight mesh for the Phase 0.3 repair proof.
10. Phase 1: WoodwindOpenWind FEM (desktop-owned; research base in
   `docs/RESEARCH_openwind_fem_and_surrogates.md`), surrogate audit.
11. Phase 2 (Issue #47): CT-scan benchmarking using
   `docs/RESEARCH_ct_benchmarking.md` (FT40/FT44, DaSCH STLs).

## Critical Context
- `origin/main` = `d935287`; `opencode/main/desktop` = `a8b3cc2` (Laws 15+16 +
  Law 14.N dead-path + rescue tooling).
- Laptop branch `opencode/build123d/laptop`: HEAD `905266d` (merge of desktop
  `a8b3cc2`, pushed).
- Test baseline: laptop full suite → **387 passed, 4 skipped** (355 + 32 guard
  tests from Law 16, ≈260s).
- Pre-commit validation passes; `backend/inverse_design.py` allowlisted oversized.
- Discussion #23 comment IDs (laptop): 17939738 (rescue+dead-path merge done),
  17933680 (dask ready), 17933694 (ACK promote + audit hold), 17933898 (ACK Law
  15 + test/research report).
- Wiki repo: `instrument-designer.wiki.git`, cloned at
  `%TEMP%\opencode\wiki2`, last pushed `master 7e10b6e`.

## Relevant Files
- `docs/AI_CONSTITUTION.md` — Laws 15, 16, 17 now present (merged + authored).
- `scripts/system_audit.py`, `scripts/merge_gate.py`, `scripts/guard_branch.py`,
  `scripts/git-hooks/pre-push`, `tests/test_guard_scripts.py` — Law 16 guard
  infra (now local via merge).
- `docs/RESEARCH_openwind_fem_and_surrogates.md` — Phase 1 FEM/surrogate base (new).
- `docs/RESEARCH_ct_benchmarking.md` — Phase 2 CT benchmark base (new).
- `docs/RESEARCH_acoustic_metamaterials.md` — §9 addendum (2024-2026).
- `docs/RESEARCH_design_to_finished_instrument.md` — §6b addendum (fabrication loop).
- `scripts/spawn_worker.py`, `scripts/start_worker.py`, `scripts/cluster_health.py`
  — dask worker attach + health.
- `scripts/team_chat.py` — merged union (laptop + desktop features).
- `chat-logs/2026-08-07-session-log.md` — prior session audit.
