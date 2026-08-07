# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/build123d/laptop`** (laptop), HEAD `0808026`.
- **Desktop branch `opencode/main/desktop`** at `84309099` (includes Law 15).
- **Governance merge COMPLETE (2026-08-07)**: laptop merged desktop `04564614`
  (Laws 12-14 + compliance watchdog) → resolved `scripts/team_chat.py` as a union
  (1 conflict, not the 19 desktop predicted) → `6c23a11`, promoted via ff-only
  onto `opencode/build123d/laptop`, pushed. Approved by desktop; 355 passed / 4
  skipped. PR #66 remains the carrier.
- **Law 15 (Branch governance) added by desktop** (`84309099`); NOT yet merged
  into laptop branch — bring it in via `merge/` staging when desktop authorizes
  (holding cross-machine merges during the audit).
- **Desktop is running a FULL CODEBASE AUDIT** (Laws 1-14) — laptop holds pushes
  to shared branches until audit completes.
- **Phase 1 READY**: WoodwindOpenWind FEM integration, surrogate audit.
- **Standing directive**: tools must be integrated into a pipeline, never just
  installed and forgotten; `AUDIT:` for provisional commits; ask rather than
  speculate when intent is unclear.

## Constraints & Preferences

- **Step 0 protocol**: `python scripts/team_chat.py sync` at session start AND
  before stopping (Discussion #23); channel is canonical.
- Constitution: Law 1 (no architecture damage), Law 3 (reuse existing bench
  scripts), Law 7 (canonical `346100.0` mm/s speed of sound), Law 10 (stop/ask),
  **Law 15 (branch governance — 4 namespaces, `merge/` staging, prove-before-delete)**.
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for protected governance
  files (`docs/CONSTRAINTS_AND_PREFERENCES.md`, `docs/REMINDERS.md`, etc.);
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
- Research docs commit held locally pending audit; wiki live.

### In Progress
- **PR #66** (`opencode/build123d/laptop` → `opencode/main/desktop`) — OPEN +
  MERGEABLE, carrier for laptop work.
- **Desktop codebase audit (Laws 1-14)** — posted in batches to #23; no code
  changes to shared branches during audit.
- **Dask worker attach to desktop scheduler**: `tcp://100.69.113.41:8786` still
  unreachable; laptop local cluster running meanwhile.

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
1. Wait for desktop audit to complete; post any laptop-side gate findings.
2. When desktop authorizes: bring Law 15 (`84309099`) into laptop branch via
   `merge/` staging per Law 15.3.
3. Attach laptop dask workers to desktop scheduler when reachable; re-run
   cluster test batches.
4. Phase 1: WoodwindOpenWind FEM (desktop-owned; research base in
   `docs/RESEARCH_openwind_fem_and_surrogates.md`), surrogate audit.
5. Phase 2 (Issue #47): CT-scan benchmarking using
   `docs/RESEARCH_ct_benchmarking.md` (FT40/FT44, DaSCH STLs).
6. Push research docs commit (`0808026`) after audit completes.

## Critical Context
- `origin/main` = `d935287`; `opencode/main/desktop` = `84309099` (includes Law 15).
- Laptop branch `opencode/build123d/laptop`: HEAD `0808026` (research docs,
  committed locally, NOT pushed yet — audit hold).
- Test baseline: laptop full suite → **355 passed, 4 skipped** (≈264s).
- Pre-commit validation passes; `backend/inverse_design.py` allowlisted oversized.
- Discussion #23 comment IDs (laptop): 17933680 (dask ready), 17933694 (ACK
  promote + audit hold), 17933898 (ACK Law 15 + test/research report).
- Wiki repo: `instrument-designer.wiki.git`, cloned at
  `%TEMP%\opencode\wiki2`, last pushed `master 7e10b6e`.

## Relevant Files
- `docs/RESEARCH_openwind_fem_and_surrogates.md` — Phase 1 FEM/surrogate base (new).
- `docs/RESEARCH_ct_benchmarking.md` — Phase 2 CT benchmark base (new).
- `docs/RESEARCH_acoustic_metamaterials.md` — §9 addendum (2024-2026).
- `docs/RESEARCH_design_to_finished_instrument.md` — §6b addendum (fabrication loop).
- `scripts/spawn_worker.py`, `scripts/start_worker.py`, `scripts/cluster_health.py`
  — dask worker attach + health.
- `scripts/team_chat.py` — merged union (laptop + desktop features).
- `docs/AI_CONSTITUTION.md` — now includes Law 15 (on `opencode/main/desktop`).
- `chat-logs/2026-08-07-session-log.md` — prior session audit.
