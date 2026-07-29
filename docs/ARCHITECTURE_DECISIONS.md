# Architecture Decision Records

All significant architectural decisions are recorded here as ADRs. Each ADR has a unique number, status, rationale, and consequences.

---

## ADR-001: Explicit Geometry Layer

**Status:** Accepted (2026-07-29)

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

**Title:** Pipeline modules never re-implement optimization

**Context:**
`inverse_design.py` contained a full custom NSGA-II implementation (`TimbreProblem` class, pymoo setup) for Tier 3 timbre matching. This duplicated the pymoo setup already in `pareto_optimizer.py`.

**Decision:**
Pipeline modules (`design_from_wav.py`, `design_from_unconventional.py`) call shared optimizers only. A general-purpose `nsga2_minimize()` wrapper was added to `pareto_optimizer.py` so single-objective NSGA-II can be invoked without re-implementing the pymoo Problem/Algorithm.

**Consequences:**
- Positive: One place to maintain pymoo setup.
- Positive: Pipeline modules are readable ~200-line orchestrators.
- Negative: WAV-specific cost functions (timbre matching) still live in `design_from_wav.py` because they depend on the specific recording's target envelope ÔÇö they cannot be generalized.

---

## ADR-003: Backward-Compatible Re-Export Layer

**Status:** Accepted (2026-07-29)

**Title:** `inverse_design.py` becomes a pure re-export module

**Context:**
After extracting sound analysis ÔåÆ `sound_analysis.py` and WAV pipeline ÔåÆ `design_from_wav.py`, ~20 files imported `analyze_wav`, `match_timbre`, `design_from_sound`, etc. from `backend.inverse_design`. Changing all callers simultaneously was risky.

**Decision:**
`inverse_design.py` is gutted of all implementation and becomes a backward-compat re-export layer. All original names (`analyze_wav`, `match_timbre`, `design_from_sound`, `synthesize_harmonic`, etc.) are re-exported from their new homes.

**Consequences:**
- Positive: Zero breakage in `design_server.py`, tests, and scripts.
- Positive: Clean migration path ÔÇö old imports keep working indefinitely.
- Negative: `inverse_design.py` is now an empty shell. Future refactoring should remove it.

---

## ADR-004: Shared Optimizer

**Status:** Accepted (2026-07-29)

**Title:** `pareto_optimizer.py` as the single pymoo wrapper

**Context:**
Both `inverse_design.py` (Tier 3) and `pareto_optimizer.py` (bi-objective front) duplicated pymoo Problem/Algorithm setup. Adding a third NSGA-II consumer would triple the duplication.

**Decision:**
`pareto_optimizer.py` exports three entry points:
- `nsga2_minimize()` ÔÇö single-objective NSGA-II (generic cost function)
- `run_pareto()` ÔÇö bi-objective NSGA-II (intonation vs timbre)
- `pareto_sweep()` ÔÇö weighted-sum sweep with L-BFGS-B refinement

No other module instantiates pymoo classes.

**Consequences:**
- Positive: If pymoo API changes, one file to update.
- Positive: New optimization consumers call `nsga2_minimize(fn, bounds)` without learning pymoo.
- Negative: The optimizer cannot know instrument-specific physics ÔÇö those details are passed via closures.

---

## ADR-005: Three-Tier Inverse Design Pipeline

**Status:** Accepted (2026-07-28)

**Title:** Inverse design decomposes into Tier 1 (analysis), Tier 2 (scale), Tier 3 (timbre)

**Context:**
Inverse design from a WAV file involves fundamentally different operations: signal processing (Tier 1), geometric scale optimization (Tier 2), and bore-profile timbre matching (Tier 3). Mixing them into a single optimizer would be intractable.

**Decision:**
Three sequential tiers:
1. `sound_analysis.analyze_wav()` ÔÇö FFT, autocorrelation, harmonic extraction. No geometry.
2. `design_from_wav.design_scale()` ÔÇö calls generative agent to place holes for a 12-TET scale.
3. `design_from_wav.match_timbre()` ÔÇö calls `nsga2_minimize` to optimize bore radii against the WAV's harmonic envelope.

**Consequences:**
- Positive: Each tier can be tested, tuned, and replaced independently.
- Positive: Users can stop after Tier 1 (analysis only) or Tier 2 (playable instrument, any timbre).
- Negative: Tier 2's result constrains Tier 3 ÔÇö if the hole placement is poor, timbre optimization cannot fully compensate.

---

## ADR-006: TMM as Primary Solver

**Status:** Accepted (2026-07-27)

**Title:** Transfer Matrix Method is the primary acoustic solver

**Context:**
The project needs an acoustic solver that runs fast enough for optimization (hundreds of evaluations per minute). FEM (OpenWind) is more accurate but 100ÔÇô1000├ù slower.

**Decision:**
TMM in `tmm_acoustics.py` is the default solver for optimization loops. OpenWind FEM is available for final validation. The `AcousticNetwork` abstraction (when implemented) will allow plugging in alternative solvers.

**Consequences:**
- Positive: Optimization completes in seconds, not hours.
- Negative: TMM accuracy is limited below ~200 Hz and above ~5 kHz (plane-wave assumption breaks down).
- Negative: Visothermal losses must be approximated (Keefe model) rather than computed from first principles.

---

## ADR-007: Split pareto_optimizer.py into Responsibility-Focused Modules

**Status:** Accepted (2026-07-29)

**Title:** Decompose `pareto_optimizer.py` into `timbre_proxy`, `objectives`, `nsga2`, `pareto`

**Context:**
`pareto_optimizer.py` had grown to 674 lines with four distinct responsibilities: (1) a pure-numpy timbre proxy, (2) TMM-dependent intonation objective functions, (3) pymoo-encapsulated NSGA-II wrappers, and (4) Pareto-front optimisation algorithms. The timbre proxy was imported by `design_pipeline.py` using private function names (`_bore_smoothness`, `_hole_radiation_consistency`), indicating the proxy should be its own public module.

**Decision:**
Split into four new modules and keep `pareto_optimizer.py` as a backward-compat re-export layer:

- `backend/physics/timbre_proxy.py` — `bore_smoothness()`, `hole_radiation_consistency()`, `compute_timbre_cost()` (pure numpy, 90 lines)
- `backend/optimization/objectives.py` — `compute_intonation_cost()`, `evaluate_bi_objective()` (TMM-aware, 110 lines)
- `backend/optimization/nsga2.py` — `nsga2_minimize()` (generic single-objective NSGA-II, 64 lines)
- `backend/optimization/pareto.py` — `pareto_sweep()`, `run_pareto()`, CLI (270 lines)
- `backend/pareto_optimizer.py` — re-exports all public names + backward-compat aliases `_bore_smoothness`, `_hole_radiation_consistency`

All callers (`design_from_wav.py`, `design_from_unconventional.py`, `design_pipeline.py`, `generative_agent.py`, `scripts/pareto_sweep_all.py`) updated to import from the new homes directly.

**Consequences:**
- Positive: Each file is < 300 lines (Law 8).
- Positive: The timbre proxy is now a proper leaf module in `physics/` — it can be reused without optimizer or TMM dependencies.
- Positive: Private-function imports (`_bore_smoothness`) replaced with public API (`bore_smoothness`).
- Positive: Zero breaking changes — re-export layer preserves all existing imports.
- Negative: One extra hop in the import graph for backward-compat callers (but still works).

---

## ADR-008: AcousticNetwork — Solver-Agnostic Instrument Representation

**Status:** Accepted (2026-07-29)

**Title:** Introduce `AcousticNetwork` as the formal boundary between geometry and solvers

**Context:**
`InstrumentGeometry.to_tmm()` returns raw arrays (radii, lengths, hole_specs). Adding OpenWind or FEM would require each caller to replicate the array unpacking and pass the right formats. There was no single place to add new solver converters.

**Decision:**
Create `backend/core/network.py` with an `AcousticNetwork` dataclass — a solver-agnostic discretised instrument model:

```
InstrumentGeometry → AcousticNetwork → TMMNetwork / OpenWindNetwork / FEMNetwork
```

Each solver provides its own `from_network()` converter function. For TMM: `tmm_instrument_from_network()` in `tmm_acoustics.py`. For future solvers: the same pattern.

The network stores:
- `bore_points`: `list[(z_mm, inner_radius_mm, outer_radius_mm)]`
- `holes`: `list[(z_mm, radius_mm, chimney_height_mm)]`
- `closed_top`: bool
- `total_length`: float

**Consequences:**
- Positive: Adding a new solver means writing one converter function — no changes to geometry or orchestrator code.
- Positive: `InstrumentGeometry` remains pure shape (Law 4). The outer diameter (needed for TMM but not for pure geometry) is supplied at conversion time via `to_network(outer_diameter_mm=...)`.
- Positive: The network can be serialised, cached, and validated independently of any solver.
- Negative: An extra abstraction layer adds ~120 lines of code. For projects that only use TMM, this is overhead.
- Negative: `tmm_instrument_from_radii()` still exists for backward compatibility; two conversion paths now coexist.
