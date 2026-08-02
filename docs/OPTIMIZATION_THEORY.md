# Optimization & Acoustics Theory — Research Note

**Date:** 2026-07-31
**Branch:** `refactor/clean-architecture`
**Scope:** Consolidates the acoustics theory and the optimizer algorithm inventory, cross-checks our implementation against the literature, and records gaps found during code review. This is an *index and analysis* note — the detailed research lives in the wiki and `chat-logs/` (see Sources below); this file does not duplicate it.

> Governance: informational document only; it was produced without changing code. Gap 5 was subsequently implemented (2026-07-31, see §6) and is recorded here with its empirical validation. Per Law 7, conventions referenced here (coordinates, register numbers, units) are canonicalized in `docs/PHYSICS_PRINCIPLES.md` / `wiki/Internal-Coordinates.md`; this note defers to them.

---

## 1. Sources (avoiding wiki duplication)

Overlapping research docs already exist; treat them as the authoritative detail:

| Detail lives in | Files |
|---|---|
| Reference index (papers by topic) | `wiki/Internal-Research.md`, `research/verified-references.md` |
| Goals & numeric targets | `wiki/Internal-Goals.md` |
| Algorithm literature deep-dive (Noreland/Ernoult/Petiot, np.inf bug, timings, init strategy) | `chat-logs/RESEARCH-REPORT.md`, `chat-logs/2026-07-20-noreland-research.md`, `chat-logs/2026-07-21-deep-research-findings.md`, `chat-logs/2026-07-18-intonation-accuracy-research.md` |
| Register/phase conventions (incl. sax n_register=3, c/f pitfall) | `research/saxophone/tmm-model.md`, `research/saxophone/benchmark-dimensions.md`, `research/saxophone-chromatic-fingering.md`, `research/flute-chromatic-fingering.md` |
| Saxophone geometry & hole theory | `research/SAXOPHONE_RESEARCH.md`, `research/saxophone/*` |
| Measured instrument dimensions | `research/instrument-measurements.md`, `research/bass_clarinet_specifications.md` |
| Physics first principles | `docs/PHYSICS_PRINCIPLES.md` |
| Solver-agnostic architecture & optimizer module map | `wiki/Internal-Architecture.md`, `docs/ARCHITECTURE.md` |

---

## 2. The acoustic model (TMM)

`backend/tmm_acoustics.py` is a port of chalumier (Mark C. Chu-Carroll / Paul Francis Harrison, Apache 2.0; demakein lineage).

- **Propagation:** cascaded plane-wave cylindrical segments; normalized admittance `Y = j·tan(kL)` (`tanner`/`untanner`); junctions add admittances with area weighting (pressure continuity + volume conservation).
- **Resonance = integer phase.** Open-open: `phase = 1 + 2L/λ`, resonance at integers → `f = c(n−1)/(2L)`. Closed-open: register maps to odd harmonics. This is why `n_register` is instrument-dependent (see §5 gap 3).
- **Toneholes:** open hole ≈ 180° phase flip with inertance-dominated series impedance; length corrections (Keefe/Nederveen); closed-hole behavior. Lattice cutoff `f_c ≈ 0.11(b/a)·c/√(s·l_eff)`.
- **Losses:** Keefe viscothermal model pluggable via `loss_model`.
- **Known model limits:** plane-wave validity ~1–2 kHz for clarinet-sized holes; radial cutoff ~8–11 kHz for 23–25 mm bores; Lefebvre — TMM tone-hole interaction error **~10 cents** is an inherent floor; flared bells and curvature are outside TMM's assumptions.

**Speed-of-sound discrepancy (finding B1, commit `38782b1`):** core TMM uses `346100.0` mm/s (≈24.4 °C) vs `343000.0` (20 °C) in some modules — ~15.6 cents. Documented in `docs/PHYSICS_PRINCIPLES.md`; unify before trusting cross-module comparisons.

---

## 3. Resonance detection — the core theoretical gap

| Method | Who | Cost smoothness | Our status |
|---|---|---|---|
| Peak matching (find_peaks + quadratic sub-bin interpolation, nearest-target by `|log2(f/f_target)|`) | Noreland 2013 (relative-frequency residuals) | Discontinuous — peaks merge/disappear under perturbation | Used in `benchmark_all.py eval_all`, `jax_optimizer.py`, `bore_optimizer_lbfgs.py`, `optimizer.py`; reporting/validation only in `two_phase_optimizer.py` |
| **Phase-based resonance** — unwrapped phase of reflection `R(f) = (Z−1)/(Z+1)`; phase accumulates monotonically → smooth gradient-friendly cost, sub-cent accuracy, adjoint gradients | Ernoult et al. 2020 (JASA 148(5) 2864–2877) | Smooth | Implemented in `two_phase_optimizer.py` Phase 2 via `peak_cost_nearest`: each register-n resonance is located from `resonance_phase` (`find_resonance`, i.e. where phase crosses the register integer) → **absolute RMS cents** (1.4 ms/call sin² forms) |

The TMM engine's `find_resonance` was already phase-based (`wavelength_near` scorer `resonance_phase − n`, secant interpolation — see §6 gap 5 for the 2026-07-31 validation). The sin² forms `phase_cost` / `phase_cost_with_offset` exist but are **register-blind** (their minima repeat at every integer phase deviation), so they are unsuitable for gradient refinement and are used only in Phase 1's global DE search. The literature's "phase-based cost not yet implemented" finding therefore applies to OpenWind's impedance-`find_peaks` path (`bore_optimizer_lbfgs.py`), not the TMM path.

---

## 4. Algorithm inventory vs literature

| Module | Algorithm | Role | Literature match | Notes |
|---|---|---|---|---|
| `benchmark_all.py` (`sequential`) | Greedy sequential hole placement; bore length first; single-open-hole (open-open) / cumulative (closed-open) fingerings | Initial design | Noreland sequential; Debut single-open-hole independence | Matches theory |
| `jax_optimizer.py` (`sequential_placement`, `refine_sequential`) | Sequential + DE global re-optim (Phase 2b) + 4-stage L-BFGS-B (L → radii → holes+diams → all) | Production intonation pipeline | Noreland: sequential needs global re-optim; Lefebvre: L-BFGS-B+FD | Correct structure; objective is absolute RMS (anti-cheat) |
| `two_phase_optimizer.py` | Phase 1 DE + phase_cost; Phase 2 L-BFGS-B + peak_cost (nearest); KeefeLoss | Noreland-style two-phase | Noreland 2013 ("little success omitting Phase 1") | Correct structure |
| `bore_optimizer_lbfgs.py` | L-BFGS-B two-phase; PAVA repair; OpenWind FEM impedance | Bore-profile optimization | Noreland/Ernoult gradient methods | **Gap 1** (unit-mixed weighted sum), **Gap 2** (weight_timbre=0) |
| `optimizer.py` | pymoo NSGA-II, 3 objectives (freq accuracy, evenness, projection) + smoothness constraint; PAVA repair; SBX/PM; StarmapParallelization; OpenWind FEM | Legacy evolutionary path | `chat-logs/RESEARCH-REPORT.md` concludes NSGA-II is the wrong algorithm for scalar bore design | Superseded for scalar design |
| `pareto_optimizer.py` | `pareto_sweep` (weighted-sum, 8 weights, seeded from `refine_sequential`) + `run_pareto` (NSGA-II, LHS/SBX/PM, pop 30) | **Intonation vs timbre Pareto front** | Petiot 2025 (NSGA-II + RF surrogate); Poirson (GA Pareto) | Right place for NSGA-II; **Gap 2** (geometry-proxy timbre) |
| `jax_optimizer.py` (`jax_stage2_refine`) | JAX autodiff bore-radius refinement | Speed-up for Phase 2 radii | — | Only reliable for closed_top / n_register=1 |

**Common pattern (correct per literature):** global init (sequential/DE) → gradient local refinement (L-BFGS-B) → optional multi-objective Pareto (NSGA-II). "Smart initialization > better global search" (documented: cylindrical → ~350 c, Buffet R13 → ~30 c).

---

## 5. Timbre metrics

- **Literature standard:** Ernoult 2020 — amplitude ratio a₂/a₁; intonation and timbre are **fundamentally at odds** (parallel valleys in radius/chimney directions). Petiot 2025 — Pareto intonation vs ease of emission. Tournemenne — players accept worse intonation for better timbre.
- **Our impedance-based metric:** `backend/timbre_objectives.py` — `compute_inharmonicity` (B from `f_n = n·f0·√(1+Bn²)`) + peak-spacing sharpness (Wolfe); closest to a₂/a₁ we have. Wired into `bore_optimizer_lbfgs.py` but **off by default (`weight_timbre=0.0`)**.
- **Our Pareto metric:** `pareto_optimizer.compute_timbre_cost` — **geometry proxy** (std of second differences of bore radii + std of hole_area/bore_area). Fast but acoustically indirect; not the literature metric.

---

## 6. Gaps found in code review

1. **Unit-mismatched weighted sum** — `bore_optimizer_lbfgs.py:253`: `freq_rms` (cents) + `0.3·evenness` (unitless) + `0.1·projection` (magnitude/1e6) + `10.0·smoothness` (**mm**) + `weight_timbre·timbre`. Additive terms in different physical units; the 10.0 smoothness weight likely dominates. Noreland's defensible form: unweighted sum of squared *relative* frequency errors (single objective).
2. **Timbre effectively disabled** — `weight_timbre=0.0` default in production; Pareto path uses the geometry proxy instead of the actual-peak `compute_timbre_objective`. The Ernoult-style a₂/a₁ tradeoff is therefore not actually exercised by the shipped optimizer.
3. **Saxophone register off-by-one** — `benchmark_all.py eval_all` / `pareto_optimizer.evaluate_bi_objective` use `n_register=2` for open-open, but `research/saxophone/tmm-model.md` documents **`n_register=3` (octave = c/L)** for the sax 2nd register, with the `c/f` vs `c/(2f)` position pitfall already identified as a bug in the sax branch. Open-open instruments likely need re-checking against this convention.
4. **Coordinate-convention drift** — `docs/ARCHITECTURE.md:87` says "0 = mouthpiece (same as OpenWind)"; `docs/PHYSICS_PRINCIPLES.md` and `wiki/Internal-Coordinates.md` canonically say **position 0 = bell / position L = reed (matches chalumier)**. Must be reconciled before any real-instrument cross-solver comparison (including the unrun `ow_baroque_probe.py`).
5. **Phase-based cost (§3)** — **IMPLEMENTED 2026-07-31 in `two_phase_optimizer.py` Phase 2**: the L-BFGS-B objective is `peak_cost_nearest` with pre-detected registers, which is phase-based (resonance located from `resonance_phase` where it crosses the register integer) and absolute (RMS cents, so register-safe). Validation found the sin² forms are **unsuitable for refinement**: `phase_cost`/`phase_cost_with_offset` minima repeat at every integer phase deviation, so L-BFGS-B drifts all notes to the next register and reports ~0 cost while the instrument is 800–980 c off (reproduced in `tests/test_phase2_objective.py::test_sin2_phase_cost_is_register_blind`; 0.00669 cost ↔ 806.15 c peak). They remain in Phase 1 DE (global, register-agnostic evenness is desired there). OpenWind's `bore_optimizer_lbfgs.py` impedance-`find_peaks` objective is still the unresolved peak-matching case.
6. **Confirmed fixed / not regressions:** `np.inf→1e10` (pymoo crowding-distance NaN), `OMP_NUM_THREADS=1` (OpenWind spsolve deadlock), PAVA monotonicity repair, median-offset reporting, absolute-RMS anti-cheat in `eval_all`.

---

## 7. What "correct" implementation looks like (literature consensus)

1. **Two-phase is non-negotiable** — Noreland: "Little success was achieved omitting Phase 1." Already done.
2. **Phase-based resonance cost** for every gradient step (Ernoult R=(Z−1)/(Z+1) unwrapped phase); keep peak matching only for reporting/validation. DONE in `two_phase_optimizer.py` Phase 2 (2026-07-31, see §6 gap 5). Use the **absolute** phase-based form (RMS cents via `find_resonance`), not the register-blind sin² forms, for any gradient step; still pending in `bore_optimizer_lbfgs.py` (OpenWind).
3. **Good init > better search** — seed from known-good geometry (e.g., Buffet R13 bore) wherever a reference exists.
4. **Register hole:** dedicated, ≈1/3 from the reed, minimizing shunt mass (small radius + long chimney — the optimizer naturally pushes to min radius, 1 mm, per Noreland). Szwarcberg sensitivities: 0.1 mm radius → ~3.4 c; +1 mm chimney → ~4 c.
5. **Timbre as amplitude ratio a₂/a₁** (Ernoult) or actual-peak inharmonicity/sharpness (`compute_timbre_objective`), not geometry; surface the intonation↔timbre tradeoff as a Pareto front (Petiot) only where multi-objective is the actual question.
6. **Register conventions:** closed-open → odd harmonics (12th, n_register=4 mapping); sax octave → `n_register=3`, positions at `c/f`; keep open-open `n_register=2` only for the stepped-cylinder phantom-1st-resonance quirk with explicit documentation.

---

## 8. Numeric anchors (verify against tests/benchmarks)

- Noreland 2013: 0.49 c RMS fundamental / 2.4 c 2nd register (config d: register hole + bore enlargement); prototype 1.97 c mean deviation after offset correction.
- Ernoult 2020: <0.025 c both registers, amplitude ratio within 20%.
- Szwarcberg 2025: 3.4 c per 0.1 mm register-hole radius.
- Lefebvre 2010: ±5 c design target; ~10 c TMM tone-hole-interaction floor.
- Project targets (`wiki/Internal-Goals.md`): <3 c absolute RMS, <2 c median-corrected (evenness), best-to-date 0.00–1.04 c across 12 instruments; Pareto front and timbre consistency still "not yet built/measured."

---

## 9. Recommended next steps (in priority order)

1. ~~Finish the **phase-based resonance cost** (gap 5) and use it in the L-BFGS-B gradient steps.~~ **DONE 2026-07-31** in `two_phase_optimizer.py` Phase 2 (absolute RMS-cents form; sin² forms rejected as register-blind — see §6 gap 5). Remaining: apply the same phase-based objective to the OpenWind path in `bore_optimizer_lbfgs.py` (currently impedance `find_peaks`).
2. Fix the **saxophone register convention** (gap 3) and re-verify open-open benchmarks.
3. Enable a physically-grounded timbre objective in the weighted sum (gap 2) — remove the unit mismatch (gap 1) first so timbre weighting is meaningful.
4. Reconcile the **coordinate convention** (gap 4), then run the baroque-clarinet OpenWind↔TMM validation with a corrected probe.
5. Consider adopting Noreland's squared-relative-error single objective as the canonical cost, with evenness/projection/smoothness as post-hoc metrics or constraints rather than unit-mixed additive terms.
