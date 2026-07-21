# Session Log: JAX TMM Implementation & Verification

**Date:** 2026-07-22
**Branch:** `experiment/tmm-improvements`
**Commit:** `7100dba`

## What Happened

### JAX TMM Module Rewrite (`tmm_acoustics_jax.py`)

**Problem:** Original approach tried to call `.tolist()` on traced JAX arrays during `jax.grad`, causing `ConcretizationTypeError`.

**Solution:** Restructured architecture:
1. `build_action_chain()` — precomputed ONCE from concrete geometry. Stores **bore radii indices** (not precomputed areas) so the chain is independent of the optimization variable.
2. `resonance_phase_jax()` — executes chain with JAX arrays. Looks up `bore_radii[idx]` at execution time. Fully differentiable.
3. Cost functions (`rms_cost_jax`, etc.) — take precomputed chain + JAX bore_radii.

**Key architectural decision:** The chain structure depends on bore_positions (fixed) not radii (variable). Only areas need to be computed from JAX radii. This allows smooth gradients.

### Bug Fixes

- Fixed dead code in `build_action_chain` where `current_bore_idx` was never updated after `continue` in the step event handler
- Added bore index to hole action tuples (`action[5]`) so `resonance_phase_jax` can look up the correct bore radius at each hole position
- Replaced `bore_radii[0]` placeholder with proper `bore_radii[bore_idx]` lookup

### Test Results

| Test | Result | Notes |
|------|--------|-------|
| 1. Baseline TMM | PASS | 0% error on open-open pipe |
| 2. JAX Gradient vs FD | PASS | 4.5% max relative error (within 10% tolerance) |
| 3. Intonation Profile | PASS | Cost = 498.045 |
| 4. Multi-Objective | PASS | All weight combinations work |
| 5. Performance | PASS | See below |

### Performance Findings (Honest Assessment)

On CPU with small bore models (20 bore points):

| Metric | Value |
|--------|-------|
| Baseline TMM | 2.8 ms/eval |
| JAX forward | 1565 ms/eval |
| JAX gradient | 16.7s |
| FD equivalent (21 evals) | 59.1 ms |
| Speedup vs FD | 0.0x (JAX slower!) |

**Why JAX is slower on CPU:**
1. Python for-loop in `resonance_phase_jax` gets unrolled by JAX tracing → massive computation graph
2. `lax.scan` (50 iterations) with `lax.cond` branching is expensive per-iteration on CPU
3. JIT compilation overhead dominates for small problems
4. `find_resonance_jax` calls `resonance_phase_jax` 50+ times during bisection

**Where JAX adds value:**
1. **GPU acceleration** (not available on this Windows machine)
2. **Correct gradients** (no finite-difference noise)
3. **Gradient cost scales independently of parameter count** (FD needs N+1 evals, JAX needs 1 forward + 1 backward)
4. **Larger problems** (100+ bore points) — the overhead per-iteration is fixed

### Next Steps (from ROADMAP)

1. **Vectorize action chain** — flatten into fixed-size JAX arrays, use `lax.scan` for action loop (eliminate Python for-loop)
2. **GPU testing** — run on CUDA-enabled machine
3. **OpenWInD integration** — `pip install openwind` for mature bore optimization
4. **Full optimizer** — `tmm_optimizer_v2.py` using JAX autodiff with all cost functions
5. **Benchmark comparison** — baseline vs JAX on realistic clarinet/saxophone models

## Files Changed

- `backend/tmm_acoustics_jax.py` — JAX-differentiable TMM (rewritten)
- `backend/mouthpiece_models.py` — Empirical mouthpiece models (new)
- `backend/tone_hole_corrections.py` — Tone hole interaction matrix (new)
- `test_tmm_v2.py` — Full test suite (rewritten)
- `ROADMAP.md` — Periodic Research Review section added
- `web/src/data/instruments.ts` — Clarinet(3) + Oboe(3) instruments
- `web/src/data/instrument-resources.ts` — Oboe + computational acoustics resources
- `backend/v2_scipy_optimizer.py` — Minor improvements
