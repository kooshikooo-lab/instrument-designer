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

1. **Ask the user** (Law 10, don't-speculate directive) whether they want the
   Claude artifacts (`brass_scaffold.py`, `string_metamaterial.py`) ported into
   the repo — do not assume.
2. Standing: present `backend/spectral` design (`docs/DESIGN_spectral.md`) for
   user approval when the user is available.
3. Monitor `kalles-main-branch` for laptop's `team_chat.py` fixes landing on
   `main` (laptop's call) and for Phase 2G updates.

## Critical Context

- **`main` HEAD = `b42b5bf`** (wiki cross-link fixes) over `32d4c9f` (numba
  wiring) over `5c7529f` (wiki restructure); `origin/main` = `b42b5bf`.
- Env: Windows, Python 3.14.6, numpy 2.4.6, numba 0.66.0, pytest 9.1.1, dask
  2026.7.1, jax 0.11.0; **conda NOT on PATH** — use system Python +
  `PYTHONPATH=<repo root>`; `tmmbench` env unavailable on desktop.
- Untracked regenerable artifacts left uncommitted: `bench_main.txt`,
  `bench_perf_tmm_medium.txt`, `bench_perf_tmm_refactor.txt`.
- #23 stream: laptop confirmation (01:41:04Z) + laptop's three `team_chat.py`
  bugfixes pushed to `kalles-main-branch` (`45ddcb2`, `591c384`, `827c051`).
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
  reference doc (committed).
- `wiki/Internal-Research.md` — hub index; `wiki/Internal-Research-{Acoustics,
  Optimization, Measurement, Perception, Resources, Metamaterials}.md` — topic
  pages; `wiki/Internal-Home.md`, `docs/WIKI-INDEX.md` — updated.
- `scripts/team_chat.py` + `scripts/.team_state.json` — Discussion #23 sync;
  laptop's 3 bugfixes on `kalles-main-branch`.
- `backend/core/network.py`, `backend/tone_hole_corrections.py`,
  `backend/mouthpiece_models.py`, `backend/trumpet_acoustics.py` — metamaterial
  integration points mapped in the research doc/wiki (future-work).
- Standing: `docs/DESIGN_spectral.md` (awaiting approval), `docs/TOOLS.md`
  (tool registry), `scripts/toolcheck.py`, `scripts/team_watch.ps1`.
