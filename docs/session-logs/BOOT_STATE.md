# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- Consolidate the acoustic-metamaterials research (Claude + Kimi exports + web
  research) into `docs/RESEARCH_acoustic_metamaterials.md` (reference doc) and the
  internal wiki, restructured into **one page per major topic** with the
  metamaterials page organized **by instrument category** and per specific
  instrument (low clarinets the deepest dive). **DONE, on `main`.**
- Land the numba-accelerated TMM resonance-phase fast path (laptop's
  `np.floor/arctan/tan/pi` fix) on `main` behind a feature flag. **DONE, on `main`.**
- Port the Claude metamaterial artifacts into `backend/experiments/` (user
  authorized porting when present). **DONE, on `main`** — `string_metamaterial.py`,
  `brass_scaffold.py`, `metamaterial_elements.py`, `folded_bore_elements.py`, all
  reproducing documented outputs exactly.
- Standing items from prior sessions (not this session's work): `backend/spectral`
  design awaits user approval; laptop Phase 2G surrogate work lives on
  `kalles-main-branch`.
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
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for commits touching
  `docs/CONSTRAINTS_AND_PREFERENCES.md`; don't commit regenerable artifacts
  (STLs, JSON dumps, benchmark logs, `bench_*.txt`).
- Direct-to-main preference, but the numba landing used a landing branch + clean
  port (laptop approved that plan explicitly).
- Tool adoption rule: install + declare (`docs/TOOLS.md`) + import + whitelisted
  test; guard = `tests/test_tool_registry.py` + `scripts/toolcheck.py`.
- Laptop's `team_chat.py` protocol fixes (cursor, watch-stale-save, sync-launch)
  are on `kalles-main-branch`, **not yet on `main`** — landing them is the
  laptop's call, do not merge unilaterally.

## Progress

### Done
- **Laptop confirmation on #23** (2026-08-03T01:41:04Z): verified desktop's
  `593e149` already contains the numba fix; laptop's holding branch
  `fix/tmm-medium-numba` obsolete and dropped; **114 passed** on laptop too;
  approved the landing plan (keep main's numba-free fallback, land feature-flagged
  wiring non-AUDIT, don't merge either copilot branch's pure-Python refactor).
- **TMM numba landing on `main`** (commit `32d4c9f`): new `backend/tmm_numba.py`
  (pure `np.*` inside `@njit`, no `import math`, no circular `Hole` import);
  3 hunks into `backend/tmm_acoustics.py` (`TMM_USE_NUMBA` env flag, lossless-only
  `_action_arrays` precompute in `__init__`, int32-mask fast path in
  `resonance_phase`); `perf = ["numba>=0.60"]` extra in `pyproject.toml`;
  `docs/TOOLS.md` declaration (toolcheck PASS); parity test
  `test_numba_resonance_phase_matches_python()` in `tests/test_tmm.py`.
  Verified on `32d4c9f`: 540 wired cases max diff **0.0**; `find_resonance`
  ~6.4x, standalone `resonance_phase` ~9.8x; full whitelisted suite **114 passed**
  (126.9s); `TMM_USE_NUMBA=0` fallback identical (2.355755).
- **Wiki restructure** (commit `5c7529f`): `wiki/Internal-Research.md` rewritten
  as a hub index; new topic pages `Internal-Research-Acoustics.md`,
  `Internal-Research-Optimization.md`, `Internal-Research-Measurement.md`,
  `Internal-Research-Perception.md`, `Internal-Research-Resources.md`,
  `Internal-Research-Metamaterials.md` (organized by instrument category:
  percussion §4, low-clarinet deep dive §5 contrabass Bb/contra-alto Eb/straight
  bass/bass-in-A/folded, guitar §6, low sax §7, bowed/piano §8, standard
  woodwinds §9, brass §10, lamellophones §11, TMM integration §12, references
  §13). Renamed `wiki/Internal-Metamaterials.md` → `wiki/Internal-Research-Metamaterials.md`;
  updated `wiki/Internal-Home.md` and `docs/WIKI-INDEX.md`.
- **Metamaterials reference doc committed** (in `5c7529f`):
  `docs/RESEARCH_acoustic_metamaterials.md` — Claude + Kimi exports merged
  (Kimi §2.4: cross-category ranking, folded-geometry advantage, within-family
  low-woodwind ranking, bore verdict, bass-clarinet-in-A timbre-revival idea)
  + web-verified references.
- **Wiki cross-link fixes** (commit `b42b5bf`, this session's safe task): 7 broken
  `[[...]]` links fixed in `Home.md`/`FAQ.md`/`Getting-Started.md`/
  `3D-Printing-Guide.md` (targets `Internal-Home`, `Internal-Branches`,
  `Internal-Optimization`, `Internal-Research-Measurement`, incl. anchor fix
   `#Metric Standardization (2026-07-25)`). Validation script: **77 links, 0 broken**
   (code-span content excluded). Pushed `32d4c9f..b42b5bf` → `main`.
- **Claude artifact ports** (this session): `string_metamaterial.py` (commit
  `91b0df8`), then `brass_scaffold.py` + `metamaterial_elements.py` +
  `folded_bore_elements.py` + doc/wiki updates + toolcheck fix (commit `cf7e625`),
  all pushed. Verified exact reproductions: string band gaps (rigid
  `(1580.0,4183.3),(4768.6,8000.0)`; local `(921.1,2925.6),(4183.8,5918.5)`);
  brass open peaks 684.5/715.6/846.2, 1-3 combo 705.5/736.1/838.3/888.4
  (838.3 Hz = −16.2c), 4cm³/24.9mm resonator → 852.2 Hz (+12.2c); folded
  low-clarinet −12.8c bass / −22.9c contra-alto / −27.8c contrabass + rigid-HR
  feasibility table (contrabass fundamental unreachable below V=100). Design
  finding: rigid HRs suit upper partials/formants; `effective_density_locally_resonant`
  liner for fundamentals. Captured in `docs/RESEARCH_acoustic_metamaterials.md`
  §7 (new) + Appendix A/B + `wiki/Internal-Research-Metamaterials.md` §5.8/§10/§12.2/§12.3.
- **toolcheck guard fix** (commit `cf7e625`): `scripts/toolcheck.py` `_is_local`
  now resolves sibling modules nested under local roots (e.g.
  `backend/experiments/brass_scaffold.py` imported bare by another experiment) —
  no longer misreported as PHANTOM. Guard PASS (29 imported, 0 phantom);
  `tests/test_tool_registry.py` passes.
- **Laptop metamaterial integration merged to `main`** (this session): pulled
  `kalles-main-branch` (`cc5b447`–`fbbd1b8`, `3d318dc`) into working tree;
  merged numba fast path from `main` (`32d4c9f`) into laptop's `tmm_acoustics.py`
  (adds `_NUMBA_ENABLED`, `_action_arrays`, numba fast path for lossless
  instruments without metamaterials). **All 114 tests pass** (incl. 74 metamaterial
  tests: `test_metamaterial.py` 13, `test_metamaterial_low_clarinets.py` 36,
  `test_metamaterial_graded.py` 11, `test_metamaterial_intonation.py` 8;
  `test_numba_resonance_phase_matches_python` passes). Toolcheck PASS (29
  imported, 0 phantom).

### In Progress
- None — this session's work is complete and pushed.

### Blocked
- Standing (not this session): `backend/spectral` implementation awaits user
  approval of `docs/DESIGN_spectral.md` (3 open questions). Inverse-design Tier 2
  blocked on `generative_agent`/`instrument_knowledge`/`spline_bore` not on `main`.

## Key Decisions

- Land wired numba onto `main` as a clean **port** (landing branch from
  `origin/main`, two commits), **not** a merge of the copilot branches; the
  pure-Python path stays the authoritative fallback (Law 1); laptop confirmed the
  pure-Python refactors were ~+15–20% slower and agreed not to merge them.
- Wiki restructure: **one page per major topic** (hub + Acoustics/Optimization/
  Measurement/Perception/Resources/Metamaterials), user-selected over finer or
  coarser grouping; metamaterials page by instrument category with per-instrument
  subsections, low clarinets deepest dive (user-requested).
- Research scope: reference doc + TMM-integration evaluation, **not** code
  porting; all metamaterial implementation ideas marked future-work. Repo
  integration mapping: Helmholtz side branch via `backend/core/network.py`
  `Port`/`NodeType` (new `HELMHOLTZ` node) feeding `junction2_reply_phase`/
  `junction3_reply_phase`; band-gap metrics from `backend/tone_hole_corrections.py`
  geometry; Piva/Gower/Abrahams formulas for resonator-distribution design; numba
  fast path is lossless-only so lossy resonator elements stay pure-Python or
  extend the njit function.
- This session: user asked for a task suggestion or, if none given, a **safe**
  fallback action — chose docs-only wiki cross-link repair (no architecture
  change, no law risk, no deletion, no merge).

## Next Steps

1. Standing: present `backend/spectral` design (`docs/DESIGN_spectral.md`) for
   user approval when the user is available.
2. Monitor `kalles-main-branch` for laptop's `team_chat.py` fixes landing on
   `main` (laptop's call) and for Phase 2G updates; laptop may want the L2-vs-L1
   parity sweep now that `main` has the ported experiment scripts.
3. Optional user-verification: folded/low-clarinet notes wording in
   `docs/RESEARCH_acoustic_metamaterials.md` §7 / wiki §5.8.
4. **ML optimization integration** (future): add ML-based optimization methods
   (e.g., Bayesian optimization, neural surrogates, gradient-free methods) to
   complement the existing two-phase optimizer (`backend/two_phase_optimizer.py`).
   Timing TBD — consider whether to optimize the physics pipeline further first
   (loss models, viscothermal accuracy) or proceed in parallel.

## Critical Context

- **`main` HEAD = `0c794fd`** (BOOT_STATE update) over `5d5c5a0` (Appendix B)
  over `401e889` (BOOT_STATE) over `cf7e625` (Claude artifact ports + doc/wiki +
  toolcheck fix) over `91b0df8` (string port) over `80a4435`/`e8780d7` (BOOT_STATE)
  over `b42b5bf` (wiki cross-link fixes) over `32d4c9f` (numba wiring) over
  `5c7529f` (wiki restructure); `origin/main` = `0c794fd`.
- Env: Windows, Python 3.14.6, numpy 2.4.6, numba 0.66.0, pytest 9.1.1, dask
  2026.7.1, jax 0.11.0; **conda NOT on PATH** — use system Python +
  `PYTHONPATH=<repo root>`; `tmmbench` env unavailable on desktop.
- Untracked regenerable artifacts left uncommitted: `bench_main.txt`,
  `bench_perf_tmm_medium.txt`, `bench_perf_tmm_refactor.txt`.
- #23 stream: laptop confirmation (01:41:04Z) + laptop's three `team_chat.py`
  bugfixes pushed to `kalles-main-branch` (`45ddcb2`, `591c384`, `827c051`).
- **Laptop's low-clarinet metamaterial batch** — initially reported as "on main"
  but actually on `kalles-main-branch` (laptop corrected 02:48Z): commits
  `cc5b447` (family + STLs), `6a260d6` (graded arrays), `a4aed67` (12th-intonation
  curve), `fbbd1b8` (subcontrabass) = 83 tests passed, now at
  `origin/kalles-main-branch` = `fbbd1b8`. Physics: L2 homogenized under-estimates
  vs L1 explicit array (43–47% rel. err. at f0/base=4, 1.4–4% at f0/base=12–20;
  tests enforce f1_L1 < f1_L2); graded arrays give 2.0x stopband vs uniform at
  same target; depth-vs-12th curve 0.95x→+2..7c … 0.80x→+83..96c … 0.75x→+143..159c.
  Desktop can now run L2-vs-L1 parity sweep against ported `folded_bore_elements.py`
  / `metamaterial_elements.py` (laptop offers to port their code to `backend/experiments/`
  or adjust structure).
- **Laptop's register-suppression + soprano demos** (04:20Z/04:34Z): two new
  deliverables on `kalles-main-branch` (`478853c` → `b0a885d`):
  1. **Register-2 squeak suppression** (bass clarinet): HR stopband over the
     12th (~212 Hz) flattens phase margin at ~1.5 across 130–250 Hz; blind spot
     at f0=squeak (zero margin); compliance tail drops f1 −300..−1700c.
  2. **Soprano-clarinet demo** (600 mm × 15 mm): same physics at higher scale,
     429 Hz squeak suppressed (L1 margin 0.428, L2 0.149); trade-off curve
     f0/squeak 0.70–0.95 → margin ~0.43, f1 shift −1120..−1650c.
  Total metamaterial test suite: **89 passed** (7 test files). L1/L2 machinery
  generalizes across the full clarinet family (subcontrabass → soprano).
- **Laptop implemented metamaterials** (`3d318dc` on `kalles-main-branch`,
  186 passed, 02:06:45Z post): L1 `MetamaterialSideBranch` (Helmholtz side
  branch via `junction3_reply_phase`), L2 `MetamaterialSegment` (Dell/Krynkin/
  Horoshenkov effective-medium stopband), `TMMInstrument` `meta_slots`/
  `metamaterial_segments` args, `tests/test_metamaterial.py` (13 tests), doc
   `chat-logs/2026-08-03-metamaterial-implementation-research.md`. Desktop acked
   (discussioncomment-17875306) and offered to run the L2-vs-L1 parity sweep.
   **Not yet on `main`** — wiki §12 implementation items marked DONE on desktop's
   port side; laptop's own implementation is on `kalles-main-branch`.
- Research anchors (web-verified): Piva/Gower/Abrahams npj Acoustics 2:10 (2026)
  random Helmholtz-resonator band gaps w/ effective-properties formulas;
  Petersen/Kergomard et al. Acta Acustica 4:13 (2020) conical tonehole-lattice
  cutoff; Bader et al. JASA 145:3086 (2019) neodymium-magnet ring frame drum
  (~300–800 Hz); Bader Springer https://doi.org/10.1007/978-3-031-57892-2_16;
  Lercari et al. MDPI Appl. Sci. 12:8619 (2022) guitar top-plate cavities;
  Fischer et al. JASA 155(3_Suppl):A59 (2024) magnet-loaded guitar;
  Khodabakhsh 2025 spiral-neck HR; Lucklum DAS|DAGA 2025 interconnected HR
  lattice; Meier 2025 Materials & Design tunable phononic band gaps.
- Bass-clarinet family facts (used in doc/wiki): ~150 cm bore, written Eb3 ≈
  78 Hz, contrabass Bb ≈ 3 m tube doubled twice (hybrid cylindrical/conical,
  sub-wavelength features ~10–30 cm), contra-alto Eb >1.7 m straightened (least
  standardized), low-A bari-sax bell-length compromise, subcontrabass sax ≈
  2.74 m / 28.6 kg / lowest G#0 ≈ 25.95 Hz, bass clarinet in A from Wagner's
  *Lohengrin* (1848).
- Repo canonical constants unchanged: `SPEED_OF_SOUND = 346100.0` mm/s in
  `backend/tmm_acoustics.py` (Law 7 / chalumier parity).
- Git identity `Admin <kooshikooo@gmail.com>`; `gh` authed as `kooshikooo-lab`.
- Laptop identity `big-pickle`; desktop `TEAM_MACHINE=desktop`.

## Relevant Files

- `backend/tmm_acoustics.py` — numba wiring on `main` (env-flag block,
  lossless-only `_action_arrays`, int32-mask fast path in `resonance_phase`).
- `backend/tmm_numba.py` — **new on `main`** — `np.*` inside `@njit`, no
  `import math`, no circular `Hole` import.
- `pyproject.toml` / `docs/TOOLS.md` — `perf = ["numba>=0.60"]` extra + declaration.
- `tests/test_tmm.py` — `test_numba_resonance_phase_matches_python()` parity test.
- `docs/RESEARCH_acoustic_metamaterials.md` — Claude + Kimi + web research
  reference doc (committed); §7 = ported-artifact numerical findings, §8 =
  language/tooling.
- `wiki/Internal-Research.md` — hub index; `wiki/Internal-Research-{Acoustics,
  Optimization, Measurement, Perception, Resources, Metamaterials}.md` — topic
  pages; `wiki/Internal-Home.md`, `docs/WIKI-INDEX.md` — updated.
- `backend/experiments/` — ported Claude artifacts: `string_metamaterial.py`,
  `brass_scaffold.py`, `metamaterial_elements.py`, `folded_bore_elements.py`
  (all on `main`, exact reproductions verified; standalone `__main__` demos).
- `scripts/toolcheck.py` — `_is_local` resolves nested sibling modules (guard fix).
- `scripts/team_chat.py` + `scripts/.team_state.json` — Discussion #23 sync;
  laptop's 3 bugfixes on `kalles-main-branch`.
- `backend/core/network.py`, `backend/tone_hole_corrections.py`,
  `backend/mouthpiece_models.py`, `backend/trumpet_acoustics.py` — metamaterial
  integration points mapped in the research doc/wiki (future-work).
- Standing: `docs/DESIGN_spectral.md` (awaiting approval), `docs/TOOLS.md`
  (tool registry), `scripts/toolcheck.py`, `scripts/team_watch.ps1`.
