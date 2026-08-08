# Session Log: Optimizer Convergence Fix — Root-Finding Approach

**Date:** 2026-07-22
**Branch:** `experiment/tmm-improvements`
**Commits:** `3a7a6b2`

## Problem

The JAX phase cost function (`make_phase_cost`) converges to 2.11 cents RMS from a near-optimal start, but finds the **wrong global minimum** (623 cents from a non-optimal start) because phase = integer at wrong harmonics too. The root-finding cost (`make_rms_cost_with_search`) has the correct global structure but its gradients are discontinuous (127% error vs finite differences) due to `jnp.where` operations in bisection.

Key findings from diagnostics:
- Phase function gradient is accurate: 6.5% max error vs FD (isolated from root-finding)
- `lax.scan` and Python loop give identical results for phase evaluation
- The `floor` operation in phase computation does NOT affect gradient w.r.t. bore radii
- Root-finding gradient error stems from `jnp.where(s_mid >= 0, ...)` creating discontinuous gradients at root boundary

## Solution

Rewrote `tmm_optimizer_v2.py` to use a **two-phase approach** where both phases optimize the **same root-finding objective**:

1. **Phase 1: Powell** (gradient-free, no FD overhead) — finds the correct basin of attraction. ~2/3 of iteration budget.
2. **Phase 2: L-BFGS-B** (scipy finite-difference gradients on root-finding cost) — local polish. ~1/3 of iteration budget.

This avoids the JAX gradient discontinuity problem entirely. Powell doesn't need gradients, and L-BFGS-B uses scipy's built-in finite differences (which work fine with the root-finding cost despite being noisy).

## Results

| Scenario | RMS cents | Time |
|----------|-----------|------|
| From known-good bore (convergence test) | 0.0000 | 9.8s |
| From cylindrical start (tapered target) | 4.98 | 2.6s |
| From cylindrical start (random target) | 26.8 | 72.2s |

The 0.0000 result from known-good bore confirms the optimizer converges perfectly when initialized near the optimum. The 4.98 cent result from cylindrical start on a round-trip test shows the optimizer can find a reasonable solution for a non-trivial problem.

## Key Insight

JAX autodiff is not suitable for root-finding based objectives due to `jnp.where` discontinuities. The clean solution is to use gradient-free methods (Powell/Nelder-Mead) for global search, then scipy L-BFGS-B with FD gradients for local polish. Both operate on the same correct objective.

The JAX TMM forward pass remains useful for fast evaluation and benchmarking (0.1ms vs 2.2ms baseline), but the optimizer no longer depends on JAX gradients.

## Files Changed

- `backend/tmm_optimizer_v2.py` — Complete rewrite to two-phase root-finding approach
- `backend/tmm_acoustics_jax.py` — Refactored to expose `_build_phase_function`, `_find_resonance_bisect`, `make_phase_cost` for reuse
- `test_diagnose.py` — Updated diagnostic tests
- `test_optimizer.py` — Updated optimizer convergence tests
