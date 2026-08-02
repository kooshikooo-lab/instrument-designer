# Architecture Decision Records

All significant architectural decisions are recorded here as ADRs. Each ADR has a unique number, status, rationale, and consequences.

---

## BOOT SEQUENCE (summary)

Every session/agent must run these 6 steps before writing code. Full version: `docs/CONSTRAINTS_AND_PREFERENCES.md`.

1. **Read the AI Constitution** (`docs/AI_CONSTITUTION.md`) — state which laws apply to your task.
2. **Read architecture docs** — `ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `CODING_STANDARDS.md`, `PHYSICS_PRINCIPLES.md`.
3. **Identify your subsystem** — from the table in `CONSTRAINTS_AND_PREFERENCES.md`.
4. **Search before building** — reuse existing functions/classes/tests; never duplicate.
5. **Produce an implementation plan** — files, interfaces, tests, docs, ADRs.
6. **Implement** — follow `CODING_STANDARDS.md`; run `ARCHITECTURE_CHECKLIST.md` and `COMPLIANCE_CHECK.md` on every trigger.

---

## ADR-001: Explicit Geometry Layer

**Status:** Accepted (2026-07-29)

**Implementation Status:** PLANNED — `backend/geometry.py` (`BoreProfile`, `HoleLayout`, `InstrumentGeometry`) does not exist on `main` (`38782b1`). Geometry remains embedded in `TMMInstrument.__init__()`, `cadquery_export.py`, and `pareto_optimizer.py`. No `InstrumentGeometry.to_tmm()` exists. Annotated 2026-07-31 per governance gap audit.

**Title:** Separate `InstrumentGeometry` from the TMM solver

**Context:**
Previously, geometry (bore profile, hole layout) was embedded inside `TMMInstrument.__init__()` and recreated ad-hoc in `cadquery_export.py`, `pareto_optimizer.py`, and pipeline modules. There was no single source of truth.

**Decision:**
Create `backend/geometry.py` with `BoreProfile`, `HoleLayout`, and `InstrumentGeometry` as pure-geometry dataclasses. Solver evaluation becomes a one-way conversion: `InstrumentGeometry.to_tmm()`.

**Consequences:**
- Positive: Geometry can be validated, serialized, and cached independently of acoustics.
- Positive: CAD export can consume `InstrumentGeometry` directly without duplicating interpolation logic.
- Positive: Future solvers (FEM, OpenWind) each implement their own `from_geometry()` converter.
- Negative: Existing array-based APIs (`evaluate_bi_objective`, `pareto_sweep`) still use raw arrays. Migration is incremental via `instrument_from_radii_arrays()`.

---

## ADR-002: Thin Pipeline Orchestrators

**Status:** Accepted (2026-07-29)

**Implementation Status:** PLANNED — `design_from_wav.py`, `design_from_unconventional.py`, and the general-purpose `nsga2_minimize()` wrapper in `pareto_optimizer.py` do not exist on `main` (`38782b1`). Annotated 2026-07-31 per governance gap audit.

**Title:** Pipeline modules never re-implement optimization

**Context:**
`inverse_design.py` contained a full custom NSGA-II implementation (`TimbreProblem` class, pymoo setup) for Tier 3 timbre matching. This duplicated the pymoo setup already in `pareto_optimizer.py`.

**Decision:**
Pipeline modules (`design_from_wav.py`, `design_from_unconventional.py`) call shared optimizers only. A general-purpose `nsga2_minimize()` wrapper was added to `pareto_optimizer.py` so single-objective NSGA-II can be invoked without re-implementing the pymoo Problem/Algorithm.

**Consequences:**
- Positive: One place to maintain pymoo setup.
- Positive: Pipeline modules are readable ~200-line orchestrators.
- Negative: WAV-specific cost functions (timbre matching) still live in `design_from_wav.py` because they depend on the specific recording's target envelope — they cannot be generalized.

---

## ADR-003: Backward-Compatible Re-Export Layer

**Status:** Accepted (2026-07-29)

**Implementation Status:** PLANNED — `inverse_design.py`, `sound_analysis.py`, and `design_from_wav.py` do not exist on `main` (`38782b1`). Annotated 2026-07-31 per governance gap audit.

**Title:** `inverse_design.py` becomes a pure re-export module

**Context:**
After extracting sound analysis → `sound_analysis.py` and WAV pipeline → `design_from_wav.py`, ~20 files imported `analyze_wav`, `match_timbre`, `design_from_sound`, etc. from `backend.inverse_design`. Changing all callers simultaneously was risky.

**Decision:**
`inverse_design.py` is gutted of all implementation and becomes a backward-compat re-export layer. All original names (`analyze_wav`, `match_timbre`, `design_from_sound`, `synthesize_harmonic`, etc.) are re-exported from their new homes.

**Consequences:**
- Positive: Zero breakage in `design_server.py`, tests, and scripts.
- Positive: Clean migration path — old imports keep working indefinitely.
- Negative: `inverse_design.py` is now an empty shell. Future refactoring should remove it.

---

## ADR-004: Shared Optimizer

**Status:** Accepted (2026-07-29)

**Implementation Status:** PARTIAL — `pareto_optimizer.py` exists on `main` (`38782b1`) with `run_pareto()` and `pareto_sweep()`, but the ADR-mandated single-objective entry point `nsga2_minimize()` is missing. Annotated 2026-07-31 per governance gap audit.

**Title:** `pareto_optimizer.py` as the single pymoo wrapper

**Context:**
Both `inverse_design.py` (Tier 3) and `pareto_optimizer.py` (bi-objective front) duplicated pymoo Problem/Algorithm setup. Adding a third NSGA-II consumer would triple the duplication.

**Decision:**
`pareto_optimizer.py` exports three entry points:
- `nsga2_minimize()` — single-objective NSGA-II (generic cost function)
- `run_pareto()` — bi-objective NSGA-II (intonation vs timbre)
- `pareto_sweep()` — weighted-sum sweep with L-BFGS-B refinement

No other module instantiates pymoo classes.

**Consequences:**
- Positive: If pymoo API changes, one file to update.
- Positive: New optimization consumers call `nsga2_minimize(fn, bounds)` without learning pymoo.
- Negative: The optimizer cannot know instrument-specific physics — those details are passed via closures.

---

## ADR-005: Three-Tier Inverse Design Pipeline

**Status:** Accepted (2026-07-28)

**Implementation Status:** PLANNED — `sound_analysis.py`, `design_from_wav.py`, `generative_agent.py`, and `scale_definitions.py` referenced by Tiers 1–2 do not exist on `main` (`38782b1`). Annotated 2026-07-31 per governance gap audit.

**Title:** Inverse design decomposes into Tier 1 (analysis), Tier 2 (scale), Tier 3 (timbre)

**Context:**
Inverse design from a WAV file involves fundamentally different operations: signal processing (Tier 1), geometric scale optimization (Tier 2), and bore-profile timbre matching (Tier 3). Mixing them into a single optimizer would be intractable.

**Decision:**
Three sequential tiers:
1. `sound_analysis.analyze_wav()` — FFT, autocorrelation, harmonic extraction. No geometry.
2. `design_from_wav.design_scale()` — calls generative agent to place holes for a 12-TET scale.
3. `design_from_wav.match_timbre()` — calls `nsga2_minimize` to optimize bore radii against the WAV's harmonic envelope.

**Consequences:**
- Positive: Each tier can be tested, tuned, and replaced independently.
- Positive: Users can stop after Tier 1 (analysis only) or Tier 2 (playable instrument, any timbre).
- Negative: Tier 2's result constrains Tier 3 — if the hole placement is poor, timbre optimization cannot fully compensate.

---

## ADR-006: TMM as Primary Solver

**Status:** Accepted (2026-07-27)

**Title:** Transfer Matrix Method is the primary acoustic solver

**Context:**
The project needs an acoustic solver that runs fast enough for optimization (hundreds of evaluations per minute). FEM (OpenWind) is more accurate but 100–1000× slower.

**Decision:**
TMM in `tmm_acoustics.py` is the default solver for optimization loops. OpenWind FEM is available for final validation. The `AcousticNetwork` abstraction (when implemented) will allow plugging in alternative solvers.

**Consequences:**
- Positive: Optimization completes in seconds, not hours.
- Negative: TMM accuracy is limited below ~200 Hz and above ~5 kHz (plane-wave assumption breaks down).
- Negative: Visothermal losses must be approximated (Keefe model) rather than computed from first principles.

**Revisions:**
- **2026-07-31 (Revision 1):** Defined the sounding-note convention that makes OpenWind usable as the validation reference. `OpenWindSolver.compute_frequencies` now selects the boundary-dependent feature set from the input impedance: OPEN input (flute-like) plays the **antiresonances**, REED/CLOSED input plays the **resonances**. Register correspondence is locked to TMM: OpenWind register *n* == TMM register *n* for closed inputs, and == TMM register *n+1* for open inputs (TMM register 1 on open geometry is a spurious near-zero mode). The register vent is OPEN for register >= 2. Wrapper details in `backend/solvers/openwind_solver.py`; regression lock in `tests/test_openwind_solver.py`.

---

## ADR-007: CadQuery-Based STL Generation (Replace Demakein Maker Pipeline)

**Status:** Accepted (2026-07-31)**Title:** Replace demakein Maker-based STL pipeline with `backend/cadquery_export`

**Context:**
The demakein library provides `Make_flute` and `Make_reed_instrument` Maker classes for generating STL from optimization results. These classes had several issues:
1. `_before_run()` crash in frozen/PyInstaller builds (Bug A)
2. `process_make()` re-ran optimization then crashed on shutdown (Bug B)
3. Monkey-patches were required in `demakein_wrapper.py` for basic functionality
4. YAML generation read pickles as JSON — silent failure (Bug C)
5. No STEP file export capability

CadQuery 2.8 was already installed and maintained in `backend/cadquery_export.py` with a 1089-line instrument library and proven `generate_variable_bore_instrument()` function.

**Decision:**
Remove `Make_flute`/`Make_reed_instrument` imports and the `_DESIGN_TO_MAKER` dispatch dict from `demakein_wrapper.py`. Instead, sample the demakein `Instrument` bore profile at 64 points and pass it to `backend.cadquery_export.generate_variable_bore_instrument()`. Wall thickness auto-computed from inner/outer profiles. Both STL and STEP files are exported.

**Consequences:**
- Positive: Eliminates 5 known demakein Maker bugs
- Positive: STEP file export now available alongside STL
- Positive: No monkey-patches or frozen-build workarounds needed
- Positive: Uses well-maintained CadQuery library already in the project
- Positive: Bore profile reuse ensures consistency with YAML config export
- Negative: CadQuery STL files (~24MB for folk flute) are larger than demakein Makers produced
- Negative: Shell thickness auto-computed from mid-point; may need tuning for instruments with non-uniform wall profiles

**Revisions:**
- **2026-07-31 (Revision 1):** Fixed hole positioning — holes now start at the inner bore surface (not bore centerline, which cut through empty cavity) and alternate around the circumference (even index +X, odd index −X) for more realistic tone hole placement. Added `hole_depth` as chimney height past outer wall. Extracted shared `_cut_holes()` helper to eliminate duplicate loop logic between `generate_instrument` and `generate_variable_bore_instrument`. Added `_interpolate_inner_radius()` helper for variable-bore radius lookup. STL `tolerance` default set to 0.01 (vs CadQuery default 0.001) for balance between file size (~2-7MB) and FDM print fidelity.

---

## ADR-008: Absolute-RMS Primary Metric Contract

**Status:** Accepted (2026-07-31)

**Implementation Status:** IMPLEMENTED — canonical module `backend/metrics.py` created and verified; production objectives converted in `backend/optimizer.py` (NSGA-II `freq_accuracy`), `scripts/benchmark_chalumier.py`, `scripts/refine_chalumier.py`, `scripts/debug_cone.py`.

**Title:** One source of truth for tuning-error metrics; `final_rms_cents` is absolute RMS

**Context:**
Tuning-error metrics were computed inconsistently across the codebase. `scripts/benchmark_all.py` used absolute RMS with an explicit anti-median-masking comment, while `backend/optimizer.py` (NSGA-II), `scripts/benchmark_chalumier.py`, `scripts/debug_cone.py`, `scripts/refine_chalumier.py`, `backend/bore_optimizer_lbfgs.py`, and `tmm_acoustics.phase_cost_with_offset` all used median-corrected RMS. Median correction lets an optimizer score ~0¢ by making every note uniformly flat/sharp, hiding absolute intonation errors. The canonical names `final_rms_cents` / `scale_rms_cents` / `median_offset_cents` existed only on the port branch (`tmm_optimizer_sequential.py`), and `backend/ai_advisor.py` already read `final_rms_cents`.

**Decision:**
1. Create `backend/metrics.py` as the single source of truth (Laws 7/8): `compute_metrics()` returns `{final_rms_cents, scale_rms_cents, median_offset_cents, peak_error_cents}` plus `rms_cents()`, `scale_rms_cents()`, `median_offset_cents()`, `cents_from_frequencies()`. Non-finite readings are excluded; all-invalid inputs yield the `1e10` penalty sentinel.
2. `final_rms_cents` (absolute RMS, no median correction) is the primary accuracy metric. `scale_rms_cents` (median-corrected) is a subordinate diagnostic for scale-fit/evenness.
3. All production objectives minimize absolute RMS via `backend.metrics.rms_cents`.
4. The optimizer result design dicts emit a `metrics` block (`final_rms_cents`, `scale_rms_cents`, `median_offset_cents`, `peak_error_cents`) alongside the legacy `objectives` keys, and the FastAPI job result (`design_server.py`) serializes it.

**Consequences:**
- Positive: Optimizers can no longer game the metric with a global offset.
- Positive: `ai_advisor.py`, the API, and the benchmark scripts all read the same numbers from one module.
- Negative: Previously-optimized median-corrected scores are not directly comparable with the new absolute scores.
- Negative: Some callers still emit legacy keys (`frequency_accuracy`, `evenness`, `projection`, `rms_cents_median`) — kept as-is to avoid breaking consumers; they are not authoritative.

---

## ADR-009: Branch Canon and Deleted-Import Policy

**Status:** Accepted (2026-07-31)

**Title:** The port branch is the new laptop `main`; deleted-optimizer imports are repaired or quarantined, never silently restored

**Context:**
The repo exists in two working copies. The desktop copy is on `main` (`13a7a65` = `origin/main`); the port branch (`ccc7236`, 5 commits ahead) is now the new laptop `main` and is the authoritative reference for comparing algorithmic solutions between branches. Unique working solutions discovered on either branch are kept. Separately, on both branches, 11+ files still imported optimizer modules deleted from `backend/archived_optimizers/` (per `docs/ARCHIVED_OPTIMIZERS.md`), so `python -c "import scripts.benchmark_chalumier"` and several test files crashed with `ModuleNotFoundError`. The port branch claimed these were fixed in `PIPELINE_TEST_BUGLOG.md` but never completed the repair.

**Decision:**
1. **Branch canon:** treat the port branch as laptop `main`; compare algorithmic solutions between branches and keep unique working solutions. Do not merge remediation changes from desktop `main` into port unless the user asks.
2. **Repair first, quarantine second:** where a live equivalent exists, re-point the import (e.g. `scripts/profile_openwind.py` → `backend.optimizer` helpers). Where no live equivalent exists (SequentialBoreOptimizer, TMMBoreOptimizerJAX, MultiStartOptimizer, ScipyBoreOptimizer, GlobalFingeringOptimizer, staged_optimize), guard the file with a deterministic `raise SystemExit("ARCHIVED: … deleted on 2026-07-31 (docs/ARCHIVED_OPTIMIZERS.md)…")` so it fails loudly with the reason instead of a bare `ModuleNotFoundError`.
3. **Never silently restore** deleted optimizer files (Law 3; port's failed UTF-16/shadow-package restore precedent in `AI_FAILURE_PATTERNS.md`).
4. `scripts/benchmark_chalumier.py` / `scripts/refine_chalumier.py` / `scripts/debug_cone.py` sys.path fix: point at `<repo_root>/backend` (was `<script_dir>/backend`, which does not exist).

**Consequences:**
- Positive: `python -c "import …"` and `pytest` collect no longer crash on the deleted optimizers.
- Positive: The failure mode is self-documenting (points at the ADR and successor module).
- Positive: Both branches can be diffed for algorithm comparison without import noise.
- Negative: Quarantined files will not run until rewritten against `backend/two_phase_optimizer.py` or `backend/optimizer.py`.
- Negative: Two branch copies still drift; the port's unfinished `PIPELINE_TEST_BUGLOG.md` claim remains a known discrepancy to reconcile in the port copy.

---

## ADR-010: Folded (paperclip U-bend) Geometry in CAD Export

**Status:** Accepted (2026-08-02)

**Title:** Folded (paperclip U-bend) geometry in CAD export

**Context:**
The contra-alto and contra-bass clarinets in the instrument library were exported as straight cylindrical pipes. Real instruments of this class (Leblanc "paperclip" models 340/350, octo-contra designs) are folded into a compact U-bend so the long low-register tube fits in a playable footprint. The CAD exporter only lofted straight bores, so the STL did not match the physical instrument.

**Decision:**
Add `generate_folded_bore_instrument()` to `backend/cadquery_export.py`. The bore follows a U-shaped centerline in the XZ plane - two straight legs joined by a 180-degree semicircular bend - whose total length equals the acoustic `bore_length`, so folding does not change the acoustic length. Geometry is built by sweeping a circular profile (outer, then inner) along the centerline and cutting, producing a single fused solid. Tone holes are cut only on the straight legs; holes whose unfolded position falls inside the bend are skipped (real folded instruments carry keys on the straight sections). The `"bend_radius_mm"` key is an OPTIONAL, purely geometric property of an INSTRUMENTS entry; when present, `design_server.py` dispatches to the folded generator. Cylindrical bores only in v1.

**Consequences:**
- Positive: Folded contra STLs now match the physical paperclip shape of the Leblanc 340/350 and octo-contra instruments.
- Positive: Acoustic length is preserved - the folded centerline total equals `bore_length`, so the sounding length is unchanged.
- Positive: Reuses the existing position-from-bell tone hole convention shared with `generate_instrument` and `generate_variable_bore_instrument`.
- Positive: Higher-key folding is limited to bass clarinet and below per product decision.
- Negative: Holes whose unfolded position falls inside the bend are not modeled (v1 limitation).
- Negative: No conical-bore folding yet - v1 supports cylindrical bores only.
- Negative: CAD models only the shape, not the bend's acoustic impedance; bend acoustics stay in the acoustics layer, per Law 4 - the CAD module contains no physics.

**Laws Satisfied:**
- Law 4 (geometry separate from acoustics - the CAD module contains no physics)
- Law 9 (document architectural decisions - this ADR records the interface change)
