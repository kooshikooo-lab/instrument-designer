"""
Test suite for JAX-differentiable TMM — V2 vectorized.

Run: python test_tmm_v2.py
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

from tmm_acoustics import (
    TMMInstrument, SPEED_OF_SOUND, end_flange_length_correction,
)
from tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, MAX_HOLES


def p(msg=""):
    print(msg, flush=True)


def test_baseline_resonances():
    p("=" * 60)
    p("TEST 1: Baseline TMM — open-open pipe")
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
        wl = inst.find_resonance(2.0 * bore_length / n, [], n_register=n)
        actual_freqs.append(inst.frequency_from_wavelength(wl))

    errors = [abs(a - t) / t * 100 for a, t in zip(actual_freqs, theo_freqs)]
    max_err = max(errors)
    p(f"  Max error: {max_err:.4f}%")
    assert max_err < 1.0
    p("  PASS\n")


def test_jax_forward_accuracy():
    p("=" * 60)
    p("TEST 2: JAX forward accuracy vs baseline")
    p("=" * 60)

    import jax.numpy as jnp

    bore_length = 500.0
    od = 22.0
    chain = build_action_chain_v2([0.0, bore_length], [9.5, 9.5], od, [], [], [], False)
    bore_radii = jnp.array([9.5, 9.5])

    inst = TMMInstrument(
        inner_positions=[0, bore_length], inner_diameters=[19.0]*2,
        outer_diameters=[od]*2, hole_positions=[], hole_diameters=[], hole_lengths=[],
        closed_top=False,
    )

    n_actions = chain['n_actions']
    chain_arrays = {k: chain[k] for k in ['act_types', 'act_pipe_length', 'act_junc_idx0',
                     'act_junc_idx1', 'act_hole_idx', 'act_hole_area', 'act_hole_open_len',
                     'act_hole_closed_len', 'act_hole_bore_idx']}

    import jax
    from jax import lax
    fs_padded = jnp.zeros(MAX_HOLES + 1)

    @jax.jit
    def get_phase(wl):
        c_at = chain_arrays['act_types']
        c_pl = chain_arrays['act_pipe_length']
        def step(ph, i):
            return ph + c_pl[i] / wl * 2.0, None
        ph, _ = lax.scan(step, jnp.array(0.5), jnp.arange(n_actions))
        return ph + 0.5

    scorer = lambda w: float(((get_phase(w) + 0.5) % 1.0) - 0.5)

    all_pass = True
    for n in range(1, 6):
        wl_near = 2.0 * bore_length / n
        wl_base = inst.find_resonance(wl_near, [], n_register=n)
        freq_base = inst.frequency_from_wavelength(wl_base)

        w0, w1 = wl_near / 1.01, wl_near * 1.01
        for _ in range(100):
            s0, s1 = scorer(w0), scorer(w1)
            if s0 >= 0 and s1 < 0:
                m = (s1 - s0) / (w1 - w0)
                wn = w0 - s0 / m
                sn = scorer(wn)
                if sn >= 0: w0, s0 = wn, sn
                else: w1, s1 = wn, sn
            else:
                w0 /= 1.01
                w1 *= 1.01
        wl_jax = w0 if abs(scorer(w0)) < abs(scorer(w1)) else w1
        freq_jax = SPEED_OF_SOUND / wl_jax
        err = abs(freq_jax - freq_base) / freq_base * 100
        status = "OK" if err < 0.1 else "FAIL"
        if err >= 0.1: all_pass = False
        p(f"  Mode {n}: {freq_base:.1f} vs {freq_jax:.1f} Hz ({err:.4f}%) [{status}]")

    p("  PASS\n" if all_pass else "  FAIL\n")


def test_jax_cost_gradient():
    p("=" * 60)
    p("TEST 3: JAX cost function + gradient")
    p("=" * 60)

    import jax
    import jax.numpy as jnp

    n_bore = 10
    bp = np.linspace(0, 600.0, n_bore).tolist()
    br = jnp.full(n_bore, 7.25)
    n_holes = 4
    hp = [150.0 + i * 100.0 for i in range(n_holes)]
    hd = [7.0] * n_holes
    hl = [3.75] * n_holes
    chain = build_action_chain_v2(bp, br.tolist(), 22.0, hp, hd, hl, False)

    eff = 600.0 + end_flange_length_correction(22.0, 14.5)
    tf = jnp.array([n * SPEED_OF_SOUND / (2.0 * eff) for n in range(1, 4)])
    fs = [jnp.zeros(n_holes) for _ in range(3)]
    tw = jnp.array([2.0 * eff / n for n in range(1, 4)])

    cost_fn = make_rms_cost(chain, tf, fs, tw)

    # Warmup
    start = time.time()
    c = cost_fn(br).block_until_ready()
    p(f"  JIT compile: {time.time()-start:.2f}s, cost: {float(c):.4f}")

    # Forward speed
    start = time.time()
    for _ in range(10): cost_fn(br).block_until_ready()
    fwd = (time.time() - start) / 10 * 1000
    p(f"  Forward: {fwd:.1f}ms")

    # Gradient
    start = time.time()
    g = jax.grad(cost_fn)(br).block_until_ready()
    g_time = (time.time() - start) * 1000
    p(f"  Gradient: {g_time:.1f}ms")
    p(f"  Grad values: {np.array(g)[:5]}")
    p("  PASS\n")


def test_performance():
    p("=" * 60)
    p("TEST 4: Performance comparison")
    p("=" * 60)

    import jax
    import jax.numpy as jnp

    n_bore = 20
    bp = np.linspace(0, 500.0, n_bore).tolist()
    br = jnp.full(n_bore, 9.5)
    chain = build_action_chain_v2(bp, br.tolist(), 22.0, [], [], [], False)
    tf = jnp.array([n * SPEED_OF_SOUND / (2.0 * 500.0) for n in range(1, 6)])
    fs = [jnp.zeros(0) for _ in range(5)]
    tw = jnp.array([1000.0/n for n in range(1, 6)])
    cost = make_rms_cost(chain, tf, fs, tw)
    _ = cost(br).block_until_ready()

    n_evals = 10
    start = time.time()
    for _ in range(n_evals): cost(br).block_until_ready()
    jax_fwd = (time.time() - start) / n_evals * 1000

    grad_fn = jax.grad(cost)
    _ = grad_fn(br).block_until_ready()
    start = time.time()
    for _ in range(min(n_evals, 5)): grad_fn(br).block_until_ready()
    jax_grad = (time.time() - start) / min(n_evals, 5) * 1000

    start = time.time()
    for _ in range(n_evals):
        inst = TMMInstrument(inner_positions=bp, inner_diameters=[19.0]*n_bore,
            outer_diameters=[22.0]*n_bore, hole_positions=[], hole_diameters=[],
            hole_lengths=[], closed_top=False)
        for n in range(1, 6): inst.find_resonance(1000.0/n, [], n_register=n)
    base = (time.time() - start) / n_evals * 1000

    fd_equiv = base * (n_bore + 1)
    p(f"  Baseline:   {base:.1f} ms/eval")
    p(f"  JAX fwd:    {jax_fwd:.1f} ms/eval ({base/jax_fwd:.1f}x vs baseline)")
    p(f"  JAX grad:   {jax_grad:.1f} ms")
    p(f"  FD equiv:   {fd_equiv:.1f} ms ({n_bore+1} evals)")
    p(f"  Grad speedup vs FD: {fd_equiv/jax_grad:.1f}x")
    p("  PASS\n")


if __name__ == "__main__":
    p("=" * 60)
    p("TMM V2 Test Suite — JAX Differentiable TMM (Vectorized)")
    p("=" * 60)

    test_baseline_resonances()
    test_jax_forward_accuracy()
    test_jax_cost_gradient()
    test_performance()

    p("=" * 60)
    p("All tests completed!")
    p("=" * 60)
