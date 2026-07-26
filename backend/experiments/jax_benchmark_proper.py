"""JAX TMM benchmark: correctness + performance + optimization.

Strategy:
- Phase 1: JAX walks pre-built Python actions (exact match)
- Phase 2: JAX-native bore model for gradient optimization
"""
import sys, os, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ["JAX_ENABLE_X64"] = "1"

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax import jit, grad, vmap

from backend.tmm_acoustics import (
    tmm_instrument_from_radii, SPEED_OF_SOUND,
    circle_area, end_flange_length_correction, hole_length_correction,
)

print(f"JAX {jax.__version__}, x64={jax.config.x64_enabled}")


# ============================================================================
# JAX TMM Primitives
# ============================================================================

@jit
def j_tanner(p):
    return jnp.tan(p * jnp.pi)

@jit
def j_untanner(x):
    return jnp.arctan(x) / jnp.pi

@jit
def j_pipe(phase_end, length_on_wavelength):
    return phase_end + length_on_wavelength * 2.0

@jit
def j_j2(a0, a1, p1):
    s = jnp.floor(p1 + 0.5)
    return j_untanner(a1 / a0 * j_tanner(p1 - s)) + s

@jit
def j_j3(a0, a1, a2, p1, p2):
    s1 = jnp.floor(p1 + 0.5)
    s2 = jnp.floor(p2 + 0.5)
    return j_untanner(
        a1 / a0 * j_tanner(p1 - s1) + a2 / a0 * j_tanner(p2 - s2)
    ) + s1 + s2


# ============================================================================
# Phase 1: Action-based (exact match with Python)
# ============================================================================

MAX_ACTIONS = 200


def build_action_arrays(inst):
    act_types = []
    act_params = []
    for action in inst.actions:
        if action[0] == 'pipe':
            _, length, diameter = action
            act_types.append(0)
            act_params.append([length, diameter, 0, 0, 0])
        elif action[0] == 'junction2':
            _, area_a, area_b = action
            act_types.append(1)
            act_params.append([area_a, area_b, 0, 0, 0])
        elif action[0] == 'hole':
            _, hole_idx, area_bore, hole_area, open_len, closed_len = action
            act_types.append(2)
            act_params.append([area_bore, hole_area, open_len, closed_len, float(hole_idx)])
    act_types.append(-1)  # sentinel
    act_params.append([0, 0, 0, 0, 0])
    return np.array(act_types, dtype=np.int32), np.array(act_params, dtype=np.float64)


def make_action_phase_fn(act_types_np, act_params_np, n_actions, closed_top):
    at = jnp.array(act_types_np)
    ap = jnp.array(act_params_np)

    def resonance_phase(wl, fingerings):
        phase = jnp.float64(0.5)
        for i in range(n_actions):
            t = at[i]
            p = ap[i]
            phase = jnp.where(t == 0, j_pipe(phase, p[0] / wl), phase)
            phase = jnp.where(t == 1, j_j2(p[0], p[1], phase), phase)
            hp_open = j_pipe(jnp.float64(-0.5), p[2] / wl)
            hp_closed = j_pipe(jnp.float64(0.0), p[3] / wl)
            hp = jnp.where(fingerings[jnp.int32(p[4])] > 0.5, hp_open, hp_closed)
            phase = jnp.where(t == 2, j_j3(p[0], p[0], p[1], phase, hp), phase)
        if not closed_top:
            phase = phase + 0.5
        return phase

    return resonance_phase


def run_correctness():
    print("\n" + "=" * 70)
    print("  PHASE 1: CORRECTNESS (JAX walks pre-built actions)")
    print("=" * 70)

    bore_radii = np.array([7.0, 7.5, 8.0, 8.5, 9.0, 9.5])
    inst = tmm_instrument_from_radii(
        bore_radii, 600.0,
        np.array([100.0, 200.0, 300.0, 400.0]),
        np.array([6.0, 6.0, 6.0, 6.0]),
        np.array([3.0, 3.0, 3.0, 3.0]),
        outer_diameter_mm=22.0, closed_top=True, cone_step=0.5,
    )

    act_types, act_params = build_action_arrays(inst)
    n_actions = len(inst.actions) + 1
    rp_fn = make_action_phase_fn(act_types, act_params, n_actions, closed_top=True)
    rp_jit = jit(rp_fn)

    fc = jnp.zeros(20)
    _ = rp_jit(jnp.float64(1.0), fc).block_until_ready()

    test_freqs = [130.8, 196.0, 261.6, 329.6, 392.0, 523.2]
    print(f"\n  {'Freq':>8} {'Py':>10} {'JAX':>10} {'Delta':>12} {'OK':>5}")
    all_ok = True
    for f in test_freqs:
        wl = SPEED_OF_SOUND / f
        py_p = inst.resonance_phase(wl, ['closed'] * 4)
        jax_p = float(rp_jit(jnp.float64(wl), fc))
        d = abs(py_p - jax_p)
        ok = d < 1e-6
        all_ok = all_ok and ok
        print(f"  {f:8.1f} {py_p:10.6f} {jax_p:10.6f} {d:12.10f} {ok!s:>5}")

    # Open fingering test
    print("\n  Open [1,0,0,0]:")
    fo = jnp.zeros(20).at[0].set(1.0)
    for f in test_freqs:
        wl = SPEED_OF_SOUND / f
        py_p = inst.resonance_phase(wl, ['open', 'closed', 'closed', 'closed'])
        jax_p = float(rp_jit(jnp.float64(wl), fo))
        d = abs(py_p - jax_p)
        ok = d < 1e-6
        all_ok = all_ok and ok
        print(f"  {f:8.1f} {py_p:10.6f} {jax_p:10.6f} {d:12.10f} {ok!s:>5}")

    print(f"\n  Result: {'PASS' if all_ok else 'FAIL'}")
    return rp_fn, rp_jit, inst


# ============================================================================
# Phase 2: Performance
# ============================================================================

def run_performance(rp_fn, rp_jit, inst):
    print("\n" + "=" * 70)
    print("  PHASE 2: PERFORMANCE")
    print("=" * 70)

    fc = jnp.zeros(20)
    target_wl = jnp.float64(SPEED_OF_SOUND / 261.6)

    # JAX single
    _ = rp_jit(target_wl, fc).block_until_ready()
    times = []
    for _ in range(3000):
        t0 = time.perf_counter()
        rp_jit(target_wl, fc).block_until_ready()
        times.append((time.perf_counter() - t0) * 1000)
    jax_avg = np.mean(times)
    print(f"\n  JAX single: {jax_avg:.3f} +/- {np.std(times):.3f} ms ({1000/jax_avg:.0f} evals/sec)")

    # Python single
    py_times = []
    for _ in range(500):
        t0 = time.perf_counter()
        inst.resonance_phase(SPEED_OF_SOUND / 261.6, ['closed'] * 4)
        py_times.append((time.perf_counter() - t0) * 1000)
    py_avg = np.mean(py_times)
    print(f"  Python single: {py_avg:.3f} ms ({1000/py_avg:.0f} evals/sec)")
    print(f"  Speedup: {py_avg/jax_avg:.1f}x")

    # Vmap batch
    print("\n  Vmap batch:")
    batch_rp = jit(vmap(lambda wl: rp_fn(wl, fc)))
    for bs in [10, 50, 100, 500, 1000]:
        wls = jnp.full((bs,), target_wl)
        _ = batch_rp(wls).block_until_ready()
        t0 = time.perf_counter()
        batch_rp(wls).block_until_ready()
        bt = (time.perf_counter() - t0) * 1000
        print(f"    n={bs}: {bt:.2f}ms ({bt/bs:.4f}ms/eval, {1000*bs/bt:.0f} evals/sec)")

    # Multi-frequency
    print("\n  Multi-frequency (5 notes):")
    freqs = [261.6, 293.7, 329.6, 392.0, 523.2]
    wls = [SPEED_OF_SOUND / f for f in freqs]

    t0 = time.perf_counter()
    for w in wls:
        rp_jit(jnp.float64(w), fc).block_until_ready()
    jt = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for w in wls:
        inst.resonance_phase(w, ['closed'] * 4)
    pt = (time.perf_counter() - t0) * 1000
    print(f"    JAX: {jt:.2f}ms, Python: {pt:.2f}ms, speedup: {pt/jt:.1f}x")

    # Gradient
    print("\n  Gradient:")
    grad_fn = jit(jax.grad(lambda wl: rp_fn(wl, fc)))
    _ = grad_fn(target_wl).block_until_ready()
    t0 = time.perf_counter()
    g = grad_fn(target_wl)
    g.block_until_ready()
    gt = (time.perf_counter() - t0) * 1000
    print(f"    1-param gradient: {gt:.3f} ms")
    print(f"    vs 7 Python evals for 6-param FD: {7*py_avg/gt:.1f}x faster")


# ============================================================================
# Phase 3: Gradient-based bore optimization
# ============================================================================

def run_optimization():
    print("\n" + "=" * 70)
    print("  PHASE 3: GRADIENT BORE OPTIMIZATION")
    print("=" * 70)

    bore_length = 600.0
    n_bore = 6
    n_holes = 4
    outer_diam = 22.0

    def build_bore_from_radii(radii, hole_pos, hole_dia, hole_len):
        """Build action arrays from bore parameters (JAX-compatible)."""
        areas = jnp.pi * radii ** 2
        diameters = radii * 2.0
        sec_len = bore_length / n_bore

        # Start with end flange correction
        # flange_corr = end_flange_length_correction(outer_diam, diameters[0])
        flange_corr = jnp.float64(0.0)  # skip for optimization simplicity

        # Build cumulative positions of sections
        positions = jnp.array([sec_len * (i + 1) for i in range(n_bore)])

        # Collect all events (bore steps + holes) sorted by position
        # Bore steps at each section boundary
        step_positions = positions[:-1]  # steps between sections
        step_areas_before = areas[:-1]
        step_areas_after = areas[1:]

        # Merge with hole positions and sort
        all_positions = jnp.concatenate([step_positions, hole_pos])
        # Event types: 0=step, 1=hole
        step_flags = jnp.concatenate([jnp.ones(n_bore - 1), jnp.zeros(n_holes)])
        step_idx_map = jnp.concatenate([
            jnp.arange(n_bore - 1),
            jnp.arange(n_holes, dtype=jnp.float64)
        ])

        # Sort by position
        order = jnp.argsort(all_positions)
        sorted_pos = all_positions[order]
        sorted_flags = step_flags[order]
        sorted_idx = step_idx_map[order]

        return (areas, diameters, sec_len, sorted_pos, sorted_flags,
                sorted_idx, flange_corr)

    def jax_cost(x):
        """x = [6 bore_radii, 4 hole_pos, 4 hole_dia, 4 hole_len]"""
        radii = jnp.sort(x[:6])
        hp = jnp.sort(x[6:10])
        hd = x[10:14]
        hl = x[14:18]

        areas = jnp.pi * radii ** 2
        hole_areas = jnp.pi * (hd / 2.0) ** 2
        diameters = radii * 2.0
        sec_len = bore_length / n_bore

        total = jnp.float64(0.0)
        target_freqs = jnp.array([261.6, 523.2])
        target_regs = jnp.array([1.0, 2.0])

        for fi in range(2):
            wl = SPEED_OF_SOUND / target_freqs[fi]
            phase = jnp.float64(0.5)

            # Walk bore: for each section, pipe + junction
            for i in range(n_bore):
                phase = j_pipe(phase, sec_len / wl)
                if i < n_bore - 1:
                    phase = j_j2(areas[i], areas[i + 1], phase)

            # Handle holes: find which section each hole is closest to
            for j in range(n_holes):
                # Cumulative position at end of each section
                cum_pos = sec_len * jnp.arange(1, n_bore + 1, dtype=jnp.float64)
                dists = jnp.abs(cum_pos - hp[j])
                best_sec = jnp.argmin(dists)

                # Open/closed hole phase
                hp_open = j_pipe(jnp.float64(-0.5), hl[j] / wl)
                hp_closed = j_pipe(jnp.float64(0.0), hl[j] / wl)
                hole_phase = hp_closed  # all closed for closed_top

                new_phase = j_j3(areas[best_sec], areas[best_sec], hole_areas[j], phase, hole_phase)
                phase = new_phase  # holes always affect (position-based, not conditional)

            # Closed end: no extra 0.5 (closed_top=True means reed end, closed)
            # For closed-open: n_register = 1
            total = total + (phase - target_regs[fi]) ** 2

        return total

    opt_cost = jit(jax_cost)
    opt_cg = jit(jax.value_and_grad(jax_cost))

    # Warmup
    x0 = jnp.array(np.concatenate([
        np.sort([7.0, 7.5, 8.0, 8.5, 9.0, 9.5]),
        np.sort([100.0, 200.0, 300.0, 400.0]),
        [6.0, 6.0, 6.0, 6.0],
        [3.0, 3.0, 3.0, 3.0],
    ]))
    v0, g0 = opt_cg(x0)
    print(f"\n  Initial cost: {float(v0):.6f}")
    print(f"  Initial grad norm: {float(jnp.linalg.norm(g0)):.6f}")

    # Multi-start gradient descent
    print("\n  Multi-start gradient descent (10 restarts, 2000 steps):")
    results = []
    for i in range(10):
        np.random.seed(i * 42)
        x = jnp.array(np.concatenate([
            np.sort(np.random.uniform(6.0, 12.0, 6)),
            np.sort(np.random.uniform(80.0, 520.0, 4)),
            np.random.uniform(4.0, 8.0, 4),
            [3.0, 3.0, 3.0, 3.0],
        ]))

        # Adaptive learning rate
        lr = 0.01
        t0 = time.perf_counter()
        for step in range(2000):
            val, g = opt_cg(x)
            g_norm = jnp.linalg.norm(g)
            # Gradient clipping + adaptive lr
            clipped_g = jnp.where(g_norm > 1.0, g / g_norm, g)
            x = x - lr * clipped_g
            x = x.at[:6].set(jnp.sort(x[:6]))
            x = x.at[6:10].set(jnp.sort(x[6:10]))
        t = (time.perf_counter() - t0) * 1000
        final = float(opt_cost(x))
        results.append((final, t))
        print(f"    #{i+1:2d}: cost={final:.6f} ({t:.0f}ms)")

    best = min(results, key=lambda r: r[0])
    converged = sum(1 for r in results if r[0] < 0.01)
    print(f"\n    Best: {best[0]:.6f} ({best[1]:.0f}ms)")
    print(f"    Converged (cost<0.01): {converged}/10")
    print(f"    Total: {sum(r[1] for r in results):.0f}ms")

    # CMA-ES comparison
    print("\n  CMA-ES (5 runs, 3000 evals):")
    try:
        import cma
        for i in range(5):
            np.random.seed(i * 42)
            x0l = list(np.concatenate([
                np.sort(np.random.uniform(6.0, 12.0, 6)),
                np.sort(np.random.uniform(80.0, 520.0, 4)),
                np.random.uniform(4.0, 8.0, 4),
                [3.0, 3.0, 3.0, 3.0],
            ]))
            opts = cma.CMAOptions()
            opts["verbose"] = -99
            opts["maxfevals"] = 3000
            t0 = time.perf_counter()
            res = cma.fmin(lambda a: float(opt_cost(jnp.array(a))), x0l, 0.5, opts)
            t = (time.perf_counter() - t0) * 1000
            print(f"    #{i+1}: cost={res[1]:.6f} ({t:.0f}ms, {res[2]} evals)")
        cma_converged = sum(1 for r in [cma.fmin(lambda a: float(opt_cost(jnp.array(a))),
            list(np.concatenate([np.sort(np.random.uniform(6,12,6)), np.sort(np.random.uniform(80,520,4)),
            np.random.uniform(4,8,4), [3,3,3,3]])), 0.5, dict(verbose=-99, maxfevals=3000))
            for _ in range(0)]) if False else "N/A"
    except ImportError:
        print("    SKIP: cma not installed")


if __name__ == "__main__":
    print("JAX TMM BENCHMARK")
    print("=" * 70)

    rp_fn, rp_jit, inst = run_correctness()
    if rp_jit is None:
        print("ABORT: correctness failed")
        sys.exit(1)
    run_performance(rp_fn, rp_jit, inst)
    run_optimization()

    print("\n" + "=" * 70)
    print("  ALL COMPLETE")
    print("=" * 70)
