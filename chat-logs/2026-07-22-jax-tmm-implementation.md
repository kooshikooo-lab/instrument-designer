# Session: JAX TMM V2 Implementation

**Date:** 2026-07-22

## Goal
Port TMM resonance engine to JAX for autodiff-accelerated bore optimization.

## Work Done

### tmm_acoustics_jax.py — Complete rewrite (V2)
- Replaced Python for-loop action chain with `lax.scan` over fixed-size array encoding
- Action chain stored as dict of padded JAX arrays (MAX_ACTIONS=128)
- `make_rms_cost()` and `make_intonation_profile_cost()` return `@jax.jit` compiled cost functions
- `jax.vmap` batches fingering searches in parallel
- Expanding-window resonance search matches baseline `wavelength_near()` behavior
- Backward-compatible aliases: `build_action_chain`, `rms_cost_jax`, etc.

### tmm_optimizer_v2.py — NEW
- L-BFGS-B bore optimizer using `jax.grad` instead of finite differences
- `TMMBoreOptimizerJAX` class with full pipeline: chain build → cost fn → optimize → extract radii
- Known-good radii warmstart support
- Verified: 40 gradient evals in 0.3s end-to-end

### Key bug fix
- Expanding-window resonance search: original secant assumed zero crossing within ±0.1% of guess
- When initial guess off by >0.1%, search diverged to wrong resonance
- Fixed with alternating left/right extension matching baseline behavior

## Results
- Forward: 1.0ms (1.1x vs baseline)
- Gradient: 6.9ms (3.4x vs FD equivalent 23.7ms)
- Accuracy: 0% error vs baseline on all 5 modes of open-open pipe
- All 4 tests pass
- Commit: 3f21cb6

## Performance Comparison
| Metric | Baseline (Python TMM) | JAX V1 (abandoned) | JAX V2 (current) |
|--------|----------------------|---------------------|-------------------|
| Forward (20 bore, 5 fingers) | 1.1ms | 1500ms | 1.0ms |
| Gradient | N/A | 17000ms | 6.9ms |
| FD equivalent | N/A | N/A | 23.7ms |
| Gradient speedup | - | 0.07x (slower) | 3.4x (faster) |

## JAX V1 → V2: Why the rewrite
V1 used Python for-loop over action chain → JAX traced/unrolled every iteration.
Result: 1500ms forward, 17000ms gradient. Worse than baseline.
V2 uses `lax.scan` (fixed iteration count) + `@jax.jit` closure compilation + `jax.vmap`.
Result: 1.0ms forward, 6.9ms gradient. Better than baseline.

## Open Items
- Optimizer converges but gradient accuracy (~20% vs FD) limits final precision
- Expanding-window search creates non-smooth gradient landscape
- Consider: FD gradients for refinement after JAX warmup
- OpenWInD integration still pending (needs Linux/WSL2)

## Commits
- 799c579: Session log for JAX TMM
- 3f21cb6: Vectorized JAX TMM + JIT optimizer
- d647579: Remove temp test file
