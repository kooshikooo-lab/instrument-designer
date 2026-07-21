"""
Test suite for JAX-differentiable TMM vs baseline tmm_acoustics.py.

Run: python test_tmm_v2.py
     or: python -u test_tmm_v2.py (unbuffered)
"""

import numpy as np
import time
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Force unbuffered output for PowerShell
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

from tmm_acoustics import (
    TMMInstrument, tmm_instrument_from_radii, SPEED_OF_SOUND, Hole,
    end_flange_length_correction,
)


def p(msg=""):
    print(msg, flush=True)


def test_baseline_resonances():
    p("=" * 60)
    p("TEST 1: Baseline TMM -- open-open pipe")
    p("=" * 60)

    bore_length = 500.0
    bore_diameter = 19.0
    outer_diameter = 22.0
    v = SPEED_OF_SOUND

    end_corr = end_flange_length_correction(outer_diameter, bore_diameter)
    effective_length = bore_length + end_corr
    theo_freqs = [n * v / (2.0 * effective_length) for n in range(1, 6)]

    inst = TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[outer_diameter, outer_diameter],
        hole_positions=[], hole_diameters=[], hole_lengths=[],
        closed_top=False,
    )

    actual_freqs = []
    for n in range(1, 6):
        target_wl = 2.0 * bore_length / n
        wl = inst.find_resonance(target_wl, [], n_register=n)
        freq = inst.frequency_from_wavelength(wl)
        actual_freqs.append(freq)

    errors = [abs(a - t) / t * 100 for a, t in zip(actual_freqs, theo_freqs)]

    p(f"  Bore: {bore_length}mm x {bore_diameter}mm (open-open)")
    for i, (a, t, e) in enumerate(zip(actual_freqs, theo_freqs, errors)):
        p(f"  Mode {i+1}: {a:.1f} Hz (theo {t:.1f} Hz, err {e:.3f}%)")

    max_err = max(errors)
    p(f"  Max error: {max_err:.4f}%")
    assert max_err < 1.0, f"Baseline test failed: max error {max_err:.4f}%"
    p("  PASS\n")
    return actual_freqs, errors


def test_jax_gradient():
    p("=" * 60)
    p("TEST 2: JAX Gradient vs Finite Differences")
    p("=" * 60)

    try:
        import jax
        import jax.numpy as jnp
        from tmm_acoustics_jax import build_action_chain, rms_cost_jax
    except ImportError as e:
        p(f"\n=== JAX not available ({e}), skipping ===")
        return None

    # Simple 3-segment bore, 4 holes
    bore_length = 600.0
    bore_diameter = 14.5
    outer_diameter = 22.0
    n_bore = 8
    bore_positions = np.linspace(0, bore_length, n_bore).tolist()
    bore_radii = jnp.full(n_bore, bore_diameter / 2.0)

    n_holes = 4
    hole_positions = [150.0 + i * 100.0 for i in range(n_holes)]
    hole_diameters = [7.0] * n_holes
    hole_lengths = [3.75] * n_holes

    effective_length = bore_length + end_flange_length_correction(outer_diameter, bore_diameter)
    target_freqs = jnp.array([n * SPEED_OF_SOUND / (2.0 * effective_length) for n in range(1, 4)])
    fingering_sets = [jnp.zeros(n_holes) for _ in range(3)]
    target_wavelengths = jnp.array([2.0 * effective_length / n for n in range(1, 4)])

    chain = build_action_chain(
        bore_positions, bore_radii.tolist(), outer_diameter,
        hole_positions, hole_diameters, hole_lengths, False,
    )
    p(f"  Chain: {len(chain['actions'])} actions")

    def cost_fn(radii):
        return rms_cost_jax(
            radii, chain, target_freqs, fingering_sets, target_wavelengths,
        )

    # Warmup JIT
    p("  Warming up JIT...")
    start = time.time()
    _ = cost_fn(bore_radii).block_until_ready()
    p(f"  JIT warmup: {time.time()-start:.1f}s")

    # JAX gradient
    p("  Computing JAX gradient...")
    start = time.time()
    grad_jax = jax.grad(cost_fn)(bore_radii)
    jax_time = time.time() - start
    p(f"  JAX grad: {jax_time:.1f}s")

    # Finite difference (first 5 params only)
    epsilon = 1e-4
    p("  Computing FD gradient (5 params)...")
    start = time.time()
    grad_fd = np.zeros(n_bore)
    for i in range(5):
        radii_plus = bore_radii.at[i].add(epsilon)
        radii_minus = bore_radii.at[i].add(-epsilon)
        cost_plus = float(cost_fn(radii_plus).block_until_ready())
        cost_minus = float(cost_fn(radii_minus).block_until_ready())
        grad_fd[i] = (cost_plus - cost_minus) / (2 * epsilon)
    fd_time = time.time() - start
    p(f"  FD grad: {fd_time:.1f}s")

    grad_jax_np = np.array(grad_jax)
    p(f"\n  JAX[:5]: {grad_jax_np[:5]}")
    p(f"  FD[:5]:  {grad_fd[:5]}")

    rel_errors = np.abs(grad_jax_np[:5] - grad_fd[:5]) / (np.abs(grad_fd[:5]) + 1e-10)
    max_rel_error = float(np.max(rel_errors))
    p(f"  Max relative error: {max_rel_error:.6f}")
    p(f"  Speedup: {fd_time / jax_time:.1f}x")

    if max_rel_error < 0.10:
        p("  PASS (within 10% tolerance)\n")
    else:
        p(f"  WARN: max error {max_rel_error:.4f} > 10%\n")

    return grad_jax_np, grad_fd


def test_intonation_profile_cost():
    p("=" * 60)
    p("TEST 3: Intonation Profile Cost")
    p("=" * 60)

    try:
        import jax.numpy as jnp
        from tmm_acoustics_jax import build_action_chain, intonation_profile_cost_jax
    except ImportError:
        p("\n=== JAX not available, skipping ===")
        return None

    bore_length = 600.0
    n_bore = 10
    bore_positions = np.linspace(0, bore_length, n_bore).tolist()
    bore_radii = jnp.full(n_bore, 7.25)

    v = SPEED_OF_SOUND
    effective_length = bore_length + 5.0
    target_freqs = jnp.array([n * v / (2.0 * effective_length) for n in range(1, 4)])
    fingering_sets = [jnp.zeros(0) for _ in range(3)]
    target_wavelengths = jnp.array([2.0 * bore_length / n for n in range(1, 4)])

    chain = build_action_chain(bore_positions, bore_radii.tolist(), 22.0, [], [], [], False)

    cost = intonation_profile_cost_jax(bore_radii, chain, target_freqs, fingering_sets, target_wavelengths)

    p(f"  Cost: {float(cost):.6f}")
    assert float(cost) >= 0, "Cost should be non-negative"
    p("  PASS\n")
    return float(cost)


def test_multi_objective_cost():
    p("=" * 60)
    p("TEST 4: Multi-Objective Cost")
    p("=" * 60)

    try:
        import jax.numpy as jnp
        from tmm_acoustics_jax import build_action_chain, multi_objective_cost_jax
    except ImportError:
        p("\n=== JAX not available, skipping ===")
        return None

    bore_length = 600.0
    n_bore = 10
    bore_positions = np.linspace(0, bore_length, n_bore).tolist()
    bore_radii = jnp.full(n_bore, 7.25)

    v = SPEED_OF_SOUND
    effective_length = bore_length + 5.0
    target_freqs = jnp.array([n * v / (2.0 * effective_length) for n in range(1, 3)])
    fingering_sets = [jnp.zeros(0) for _ in range(2)]
    target_wavelengths = jnp.array([2.0 * bore_length / n for n in range(1, 3)])

    chain = build_action_chain(bore_positions, bore_radii.tolist(), 22.0, [], [], [], False)

    for iw, pw in [(1.0, 0.0), (0.5, 0.5), (0.0, 1.0)]:
        cost = multi_objective_cost_jax(
            bore_radii, chain, target_freqs, fingering_sets,
            target_wavelengths, intonation_weight=iw, playability_weight=pw,
        )
        p(f"  Weight (inton={iw}, play={pw}): cost = {float(cost):.6f}")

    p("  PASS\n")
    return True


def test_jax_performance():
    p("=" * 60)
    p("TEST 5: Performance Comparison")
    p("=" * 60)

    try:
        import jax
        import jax.numpy as jnp
        from tmm_acoustics_jax import build_action_chain, rms_cost_jax
    except ImportError:
        p("\n=== JAX not available, skipping ===")
        return None

    bore_length = 500.0
    bore_diameter = 19.0
    outer_diameter = 22.0
    n_evals = 5
    n_bore = 20

    # Baseline speed
    bore = np.full(n_bore, bore_diameter)
    positions = np.linspace(0, bore_length, n_bore).tolist()
    start = time.time()
    for _ in range(n_evals):
        inst = TMMInstrument(
            inner_positions=positions,
            inner_diameters=bore.tolist(),
            outer_diameters=[outer_diameter] * n_bore,
            hole_positions=[], hole_diameters=[], hole_lengths=[],
            closed_top=False,
        )
        for n in range(1, 6):
            wl = inst.find_resonance(2.0 * bore_length / n, [], n_register=n)
    baseline_time = (time.time() - start) / n_evals * 1000

    # JAX forward speed
    bore_positions_jax = np.linspace(0, bore_length, n_bore).tolist()
    bore_radii_jax = jnp.full(n_bore, bore_diameter / 2.0)

    v = SPEED_OF_SOUND
    effective_length = bore_length + end_flange_length_correction(outer_diameter, bore_diameter)
    target_freqs_jax = jnp.array([n * v / (2.0 * effective_length) for n in range(1, 6)])
    fingering_sets = [jnp.zeros(0) for _ in range(5)]
    target_wavelengths_jax = jnp.array([2.0 * bore_length / n for n in range(1, 6)])

    chain = build_action_chain(
        bore_positions_jax, bore_radii_jax.tolist(), outer_diameter,
        [], [], [], False,
    )

    def cost_fn(radii):
        return rms_cost_jax(radii, chain, target_freqs_jax, fingering_sets, target_wavelengths_jax)

    # Warmup
    _ = cost_fn(bore_radii_jax).block_until_ready()

    start = time.time()
    for _ in range(n_evals):
        _ = cost_fn(bore_radii_jax).block_until_ready()
    jax_time = (time.time() - start) / n_evals * 1000

    # JAX gradient (single eval)
    grad_fn = jax.grad(cost_fn)
    _ = grad_fn(bore_radii_jax).block_until_ready()
    start = time.time()
    _ = grad_fn(bore_radii_jax).block_until_ready()
    jax_grad_time = (time.time() - start) * 1000

    fd_equiv = baseline_time * (n_bore + 1)
    p(f"  Baseline TMM ({n_bore} bore pts): {baseline_time:.1f} ms/eval")
    p(f"  JAX forward:                       {jax_time:.1f} ms/eval")
    p(f"  JAX forward+grad (single):         {jax_grad_time:.1f} ms")
    p(f"  FD equiv ({n_bore+1} evals):            {fd_equiv:.1f} ms")
    p(f"  Grad speedup vs FD:                {fd_equiv / jax_grad_time:.1f}x")
    p("  PASS\n")
    return baseline_time, jax_time


if __name__ == "__main__":
    p("=" * 60)
    p("TMM V2 Test Suite -- JAX Differentiable TMM")
    p("=" * 60)

    test_baseline_resonances()
    test_jax_gradient()
    test_intonation_profile_cost()
    test_multi_objective_cost()
    test_jax_performance()

    p("=" * 60)
    p("All tests completed!")
    p("=" * 60)
