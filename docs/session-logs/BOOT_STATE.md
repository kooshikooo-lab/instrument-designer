# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/build123d/laptop`** (laptop), HEAD `0e3bf06`.
- **Desktop branch `opencode/main/desktop`** at `8a264a4` (Laws 15+16 merged locally on laptop via staging).
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
  installed and forgotten; `AUDIT:` for provisional commits; ask rather than
  speculate when intent is unclear; **do safe work first, don't idle on approval**.

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

### Done (this session, 2026-08-07)
- **Governance merge completed + verified**: side branch
  `merge/build123d-laptop-receives-governance` → merged desktop `04564614`,
  1 conflict resolved (`team_chat.py` union), exec-bit fixes on git hooks,
  compliance baseline regenerated 23→30, gates green, 355 passed / 4 skipped,
  promoted + pushed `6c23a11`. Posted merge report + completion to #23.
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
- **PR #66** (`opencode/build123d/laptop` → `opencode/main/desktop`) — OPEN +
  MERGEABLE, carrier for laptop work.
- **Desktop codebase audit (Laws 1-14)** — posted in batches to #23; no code
  changes to shared branches during audit.
- **Dask worker attach to desktop scheduler**: `tcp://100.69.113.41:8786` still
  unreachable; laptop local cluster running meanwhile.
- **Orphan branch cleanup** (Law 15/16 audit finding): to coordinate rename/
  delete with desktop post-audit.

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
1. Wait for desktop audit to complete / desktop back online; post any
   laptop-side gate findings.
2. Push laptop branch (research `0808026` + Laws 15/16 `d4e71e0` + Law 17
   `74edbe0` + gitignore `5c9fe08` + boot `2cd07ae` + Fusion tests/docs
   `b58a65e` `6efa7ad` `917369d` `0e3bf06`) after audit completes.
3. Attach laptop dask workers to desktop scheduler when reachable; re-run
   cluster test batches.
4. Coordinate orphan branch cleanup (rename/delete) with desktop per Law 15.
5. Fusion 360: human runs `phase2b_trigger.json` in a Fusion session; laptop
   verifies `phase2b_result.json` against the CAM contract; find a replacement
   non-watertight mesh for the Phase 0.3 repair proof.
6. Phase 1: WoodwindOpenWind FEM (desktop-owned; research base in
   `docs/RESEARCH_openwind_fem_and_surrogates.md`), surrogate audit.
7. Phase 2 (Issue #47): CT-scan benchmarking using
   `docs/RESEARCH_ct_benchmarking.md` (FT40/FT44, DaSCH STLs).

## Critical Context
- `origin/main` = `d935287`; `opencode/main/desktop` = `8a264a4` (Laws 15+16);
  desktop also has unmerged `opencode/system-guardrails/desktop` (Law 16 source).
- Laptop branch `opencode/build123d/laptop`: HEAD `5c9fe08` (Laws 15+16 merged +
  Law 17 + gitignore; committed locally, NOT pushed yet — audit hold).
- Test baseline: laptop full suite → **387 passed, 4 skipped** (355 + 32 guard
  tests from Law 16, ≈260s).
- Pre-commit validation passes; `backend/inverse_design.py` allowlisted oversized.
- Discussion #23 comment IDs (laptop): 17933680 (dask ready), 17933694 (ACK
  promote + audit hold), 17933898 (ACK Law 15 + test/research report).
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
