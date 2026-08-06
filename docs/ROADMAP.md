# Roadmap: Instrument Designer

## Completed
- [x] Bore optimization with pymoo + OpenWInD (basic)
- [x] Impedance solver resolution fix (800 → 5000 points)
- [x] Quadratic interpolation for peak finding
- [x] Impedance caching for repeated evaluations
- [x] Intonation accuracy research (documented in chat-logs/2026-07-18)
- [x] CORS middleware added to FastAPI backend
- [x] demakein installed and design pipeline working
- [x] Preset dropdown grouped by category (Flute / Woodwind)
- [x] SimulationWorker: renamed finished signal, added exception handling
- [x] ProjectWidget: public methods, cross-platform folder open
- [x] Cloned chalumier (Kotlin demakein rewrite) for evaluation
- [x] STL generation: CadQuery-based pipeline (replaced broken demakein Maker classes)
- [x] Quick mode support for demakein designs (faster draft iterations)
- [x] chalumier wrapper module (ready when JDK is available)
- [x] Error handling: _run_design try/except, unified job status responses
- [x] freecad_engine.py: robust JSON parsing from stdout
- [x] YAML bore_length unit consistency (mm throughout)
- [x] validate_optimizer.py: fixed paths, phased thresholds, portability

---

## Phase 0: Critical Bug Fixes (CURRENT — 2026-08-07)

> **Blocking issues identified 2026-08-07 audit. Must complete before any feature work.**

### 0.1 Speed-of-Sound Literal Cleanup (Law 7)
- [ ] Fix 46 non-canonical SoS literals across 10 files (by layer):
  - Layer 1 (Physics): `backend/physics/losses.py:96` → import canonical
  - Layer 2 (Optimizers): `bore_optimizer_lbfgs.py:188`, `optimizer.py:358`, `flute_calculator.py:44` → use temp formula
  - Layer 3 (Core): `modular_components.py:334`, `core/network.py:146` → import canonical
  - Layer 4 (Tone-hole): `tone_hole_corrections.py:190,262,263,270` → import canonical
  - Layer 5 (Tests): Update expectations to 346100 mm/s in `test_bore_design.py`, `test_architecture.py`, `test_bore_check.py`, `test_sympy_validation.py`, `validate_flutomat.py`, `compare_optimizers.py`
- [ ] Pre-commit `validate_pre_commit.py` passes (has `SPEED_OF_SOUND_LITERAL_RE`)

### 0.2 Two-Phase Optimizer Fixes (Default ACCURATE Strategy)
- [ ] Extract `detect_registers()` to shared `backend/physics/register_detection.py`
- [ ] Wire into `backend/optimization/selector.py` (`TwoPhaseOptimizer.optimize()`)
- [ ] Wire into `backend/two_phase_optimizer.py` (import shared)
- [ ] Add `bore_length_bounds` enforcement for bass instruments (>1m)
- [ ] Remove hardcoded `outer_diameter=22.0`, `closed_top=False` → read from config
- [ ] Bass chalumeau converges to correct register (not 108¢ error)

### 0.3 Bass Chalumeau Merge Conflict Resolution
- [ ] Desktop has tone-hole fix in `build_bass_chalumeau_Bb()`; laptop doesn't
- [ ] Before laptop→desktop merge: manually diff `backend/modular_components.py` to preserve tone holes
- [ ] Preferred: laptop merges `origin/opencode/main/desktop` → `opencode/main/laptop`, then PR to desktop

### 0.4 Merged PRs (2026-08-07)
- [x] PR #63: Remove phantom `openwind` gitlink (shadowed pip package)
- [x] PR #62: 45-file import repair (tmm_acoustics imports moved to archived_optimizers)

---

## Phase 1: Architecture Completion (Next Session)

### 1.1 WoodwindOpenWind FEM Integration
- [ ] Create `backend/woodwind_openwind.py` mirroring `TrumpetOpenWind`:
  - Bore + hole conversion (mm→m) from `OpenWindSolver._network_to_openwind()`
  - Register vent logic (open for reg≥2) from `compute_frequencies():178-190`
  - Woodwind fingering chart from `_build_fingering_chart()`
  - Resonance/antiresonance selection (BoundaryType.REED vs OPEN)
  - Impedance + frequency methods mirroring `TrumpetOpenWind`
- [ ] Register `REFINED` strategy for woodwinds in selector:
  - Route CLARINET, SAXOPHONE, FLUTE, CHALUMEAU → OpenWind FEM
- [ ] Add TMM vs FEM comparison to `run_optimizer_comparison`

### 1.2 Surrogate Audit
- [ ] Audit `backend/surrogate/mlp_surrogate.py` + `bi_objective_bo.py`
- [ ] Document scope and prevent duplicate `BoreSection` vs `Joint` pattern

---

## Phase 2: High-Value Features (This Week)

### 2.1 CT-Scan Benchmarking (Issue #47)
- [ ] Download bassoon FT40/FT44 STL from Zenodo (10.5281/zenodo.3246324)
- [ ] Extract bore profiles from CT scan data
- [ ] Run two-phase optimizer on bassoons
- [ ] Run sequential optimizer on contra clarinets (Contra-Alto, Contra-Bass)
- [ ] Run sequential optimizer on Baroque Clarinet
- [ ] Compare optimized vs CT-measured bore profiles
- [ ] Document RMS cents error vs CT ground truth
- [ ] Export STL for 3D printing validation

### 2.2 Demakein Replacement (Issue #48)
- [ ] Extract 11 preset bore profiles via TMM optimizer
- [ ] Replace `woodwind_designer/engine/demakein_wrapper.py` internals:
  - Lookup pre-optimized bore profile from registry
  - Apply transpose (frequency shift)
  - Run CadQuery export with profile
  - Return DesignResult with STL, YAML, log
- [ ] Remove demakein import, `_patch_optimize()`, `HAVE_DEMAKEIN` flag
- [ ] Keep public API: `design()`, `list_families()`, `list_subcategories()`, `list_presets()`, `get_description()`
- [ ] Test all 11 presets generate valid STLs

### 2.3 Monte Carlo Tolerance Budget (Tier 1 — Claude)
- [ ] Sample geometry perturbations from actual printer tolerance distribution
- [ ] Per-note cents-deviation histogram output for existing bass chalumeau design
- [ ] Acceptance artifact: histogram file saved

### 2.4 Surrogate Integration
- [ ] Wire `mlp_surrogate.py` into DE global search phase
- [ ] Fallback to real TMM for L-BFGS-B local refinement
- [ ] Benchmark speedup vs pure TMM

---

## Phase 3: Tier 2 — Human Checkpoint First

| Work | Dependency | Notes |
|------|------------|-------|
| Reaming Allowance / Post-print Adjustability | Schema decision | New field in `design_output.schema.json` |
| JND-Weighted Intonation Objective | Literature summary | Kergomard/Laloë psychoacoustics first |
| Printer Calibration Layer | Measurement data | Blocked on ream-and-remeasure |
| Audio-Embedding Sound Matching | Isolate in `backend/experiments/` | Heavy deps (torch, CLAP/VGGish) |

---

## Phase 4: Ongoing (from existing roadmap)

### 4.1 Intonation-Only Optimization (Phase 1)
- [x] TMM Optimizer — Phase-based engine, L-BFGS-B, sequential refinement
- [x] closedTop Convention — Verified for cones (always `closedTop=False`)
- [ ] Speed — Parallelize optimizer (StarmapParallelization, pymoo)
- [ ] Accuracy — Bore quality constraints (monotonicity, smoothness, global pitch offset)
- [ ] Validation — Benchmark against chalumier/demakein (recorder, dwhistle)
- [ ] Bore Representation — More control points (12 → 20-30) after constraints
- [ ] **Metric Standardization** — Remove median correction from ALL optimizers:
  - `optimizer_global.py:_evaluate()` — remove `np.median(c1)` offset
  - `tmm_acoustics.py:phase_cost_with_offset()` — remove median subtraction
  - `two_phase_optimizer.py` — remove median correction
  - Report Absolute RMS, MAD, SD, Max deviation, per-note table
- [ ] Timbre Optimization — Impedance peak amplitude ratios (a₂/a₁)
- [ ] Bi-objective Pareto (intonation + timbre) — NSGA-II (needs pymoo)

### 4.2 Optimization Methods Research
- [ ] Ernoult phase-based cost (unwrapped phase of reflection function)
- [ ] Noreland two-phase validation (Phase 1: first register only)
- [ ] Pareto front (intonation + timbre) — bore smoothness + hole radiation proxy
- [ ] WIDesigner validation (Java open-source)
- [ ] Manufacturing tolerance sensitivity (±0.1mm noise → re-evaluate)

### 4.3 JAX Autodiff Stage 2
- [x] JAX autodiff for bore-radii refinement (exact gradients)
- [ ] Extend to hole positions/diameters (currently blocked by static action chain)

### 4.4 Computational Accuracy Targets
| Phase | Target | Status |
|-------|--------|--------|
| C1 | <20 cents | **ACHIEVED** (23.9c cone) |
| C2 | <10 cents | **ACHIEVED** (Phase 2b DE) |
| C3 | <5 cents | **ACHIEVED** (0.01-0.32c RMS) |
| C4 | <3 cents | **ACHIEVED** (0.00c xaphoon) |

---

## Phase 5: 3D Print Accuracy (Phase 2)

### 5.1 Print Tolerance Research
- [ ] SLA dimensional accuracy for bore geometries (10-25mm cylinders)
- [ ] Material shrinkage (engineering vs standard resin)
- [ ] Bore surface roughness impact (layer heights 25/50/100µm)
- [ ] Warp/distortion over length (500mm bores, multi-part joins)

### 5.2 Shrinkage Compensation
- [ ] Per-resin shrinkage factor in STL export
- [ ] Non-uniform shrinkage (axial vs radial)

### 5.3 Measurement Loop
- [ ] Import measured impedance from real instruments
- [ ] Compare designed vs measured bore profiles
- [ ] Iterative correction: measure → optimize → print → measure

### Physical Accuracy Targets
| Phase | Target | Status |
|-------|--------|--------|
| P1 | <20 cents | After C1 |
| P2 | <10 cents | After P1 |
| P3 | <5 cents | After P2 |
| P4 | <3 cents | Stretch goal |

---

## Phase 6: Integration & Polish

### 6.1 Chalumier Integration
- [x] `chalumier_wrapper.py` created (branch: `experiment-chalumier-integration`)
- [x] Web UI integration: BoreProfileView SVG, build trigger
- [x] Backend endpoints: `/chalumier/design`, `/chalumier/build`
- [ ] Install JDK 17+ (build chalumier JAR)
- [ ] Compare chalumier vs our TMM optimizer output quality/speed
- [ ] Add chalumier instrument types to preset list

### 6.2 GUI Enhancements
- [ ] Real-time bore profile visualization during optimization
- [ ] Impedance peak display with target overlay
- [ ] Export optimization history (convergence plots)
- [ ] Bore profile editor (drag control points)

---

## Phase 7: Linux Deployment & Server Hosting

### 7.1 Local Linux Testing (WSL2)
- [ ] Enable virtualization in BIOS (Intel VT-x / AMD-V)
- [ ] Install Ubuntu: `wsl --install -d Ubuntu`
- [ ] Benchmark optimizer: serial vs parallel (fork context)
  - Expected: 3-5x speedup over Windows 1.67x
  - Target: 6-8x matching core count

### 7.2 Server Deployment
- [ ] Choose VPS (4-8 cores, $5-10/mo)
- [ ] Docker container with Python + deps
- [ ] Deploy FastAPI (port 8000) + frontend
- [ ] nginx reverse proxy + HTTPS
- [ ] systemd/supervisor auto-restart

---

## Phase 8: Desktop App (Tauri)

- [ ] Tauri capabilities: `core:event:allow-listen`, `core:event:allow-emit`, `process:allow-spawn`
- [ ] HTTP backend (Tauri spawns Python FastAPI as managed process)
- [ ] Native features: file dialogs, tray, auto-update
- [ ] Future: Pure Rust + PyO3 (embed demakein optimizer, 10-50x speedup)

---

## Ongoing: Periodic Research Review (Every 2-4 Weeks)

- New papers: JASA, Acta Acustica, POMA, Music & Science, arXiv cs.SD/eess.AS, HAL
- Labs: CAML (McGill), CCRMA (Stanford), IRCAM/INRIA, NESS (Edinburgh), Chalmers, Aalto, Stuttgart, Politecnico Milano
- Conferences: ISMA 2026 Helsinki, ISMRA 2025, ASA, Forum Acusticum, DAFx, NIME
- GitHub: Neuralacoustics, NESS, Resonarium, VIBRA, OpenWind, WIDesigner

---

## AI Governance System — COMPLETE

- [x] `docs/CONSTRAINTS_AND_PREFERENCES.md` — AI Boot Sequence (6-step init)
- [x] `docs/AI_CONSTITUTION.md` — 10 non-negotiable project laws
- [x] `docs/ARCHITECTURE_DECISIONS.md` — 6 seeded ADR records
- [x] `docs/ARCHITECTURE_CHECKLIST.md` — 20-item pre-flight checklist
- [x] `docs/COMPLIANCE_CHECK.md` — Trigger-based compliance (15min, before code, after tests)
- [x] `docs/AI_FAILURE_PATTERNS.md` — Failure pattern log (5 seeded)
- [x] Governance pages pushed to GitHub wiki

---

## P0 Questions Blocking Phase 0 (Posted to Discussion #23)

1. **Impossible outer diameters** in `benchmark_all.py` — correct wall thickness?
2. **Missing tone holes** in `build_bass_chalumeau_Bb()` — add 7-8 holes or remove benchmark target?
3. **Two-phase optimizer scope** — P0 bugs only, or include P1 import fixes?
4. **Bass chalumeau merge conflict** — laptop merges desktop first?

---

*Last updated: 2026-08-07*