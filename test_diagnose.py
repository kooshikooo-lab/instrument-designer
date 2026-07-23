"""Diagnose gradient noise in expanding-window resonance search."""
import sys, io
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

import numpy as np
import jax
import jax.numpy as jnp
from tmm_acoustics import TMMInstrument, SPEED_OF_SOUND, end_flange_length_correction
from tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, MAX_HOLES

print("=" * 70)
print("DIAGNOSTIC: Gradient Noise Analysis")
print("=" * 70)

# Simple test: 10 bore points, no holes, 5 harmonics
bore_length = 500.0
od = 22.0
n_bore = 10
bp = np.linspace(0, bore_length, n_bore).tolist()

# Known-good uniform bore
base_radii = np.full(n_bore, 9.5)
br_jax = jnp.array(base_radii)

# Build chain
chain = build_action_chain_v2(bp, base_radii.tolist(), od, [], [], [], False)

# Target: 5 harmonics of open-open pipe
eff = bore_length + end_flange_length_correction(od, 19.0)
tf = jnp.array([n * SPEED_OF_SOUND / (2.0 * eff) for n in range(1, 6)])
fs = [jnp.zeros(0) for _ in range(5)]
tw = jnp.array([2.0 * eff / n for n in range(1, 6)])

cost_fn = make_rms_cost(chain, tf, fs, tw)

# Warmup
c = cost_fn(br_jax).block_until_ready()
g = jax.grad(cost_fn)(br_jax).block_until_ready()
print(f"Cost at uniform: {float(c):.6f}")
print(f"Grad at uniform: {np.array(g)}")

# --- Test 1: Gradient accuracy vs finite differences ---
print("\n--- Test 1: JAX grad vs FD grad ---")
eps = 1e-4
fd_grad = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = base_radii.copy()
    br_minus = base_radii.copy()
    br_plus[i] += eps
    br_minus[i] -= eps
    c_plus = float(cost_fn(jnp.array(br_plus)).block_until_ready())
    c_minus = float(cost_fn(jnp.array(br_minus)).block_until_ready())
    fd_grad[i] = (c_plus - c_minus) / (2 * eps)

jax_grad = np.array(g)
rel_errors = np.abs(jax_grad - fd_grad) / (np.abs(fd_grad) + 1e-30)
print(f"  JAX grad:  {jax_grad}")
print(f"  FD  grad:  {fd_grad}")
print(f"  Rel error: {rel_errors}")
print(f"  Max rel error: {np.max(rel_errors):.4f}")
print(f"  Mean rel error: {np.mean(rel_errors):.4f}")

# --- Test 2: Cost landscape smoothness ---
print("\n--- Test 2: Cost landscape along one dimension ---")
# Perturb first radius and plot cost
test_idx = 0
perturbations = np.linspace(-2.0, 2.0, 41)
costs = []
for p in perturbations:
    br_test = base_radii.copy()
    br_test[test_idx] += p
    costs.append(float(cost_fn(jnp.array(br_test)).block_until_ready()))

costs = np.array(costs)
# Check smoothness: second derivative should be positive (convex)
d2cost = costs[2:] - 2 * costs[1:-1] + costs[:-2]
dp = perturbations[1] - perturbations[0]
d2cost_normalized = d2cost / dp**2
print(f"  Min cost: {np.min(costs):.6f} at perturbation={perturbations[np.argmin(costs)]:.3f}")
print(f"  Cost range: [{np.min(costs):.6f}, {np.max(costs):.6f}]")
print(f"  2nd derivative range: [{np.min(d2cost_normalized):.6f}, {np.max(d2cost_normalized):.6f}]")
print(f"  2nd derivative sign consistent (convex?): {np.all(d2cost_normalized > 0) or np.all(d2cost_normalized < 0)}")

# --- Test 3: Expanding-window search accuracy vs actual resonance ---
print("\n--- Test 3: Expanding-window search accuracy ---")
inst = TMMInstrument(
    inner_positions=bp, inner_diameters=(base_radii * 2).tolist(),
    outer_diameters=[od]*n_bore, hole_positions=[], hole_diameters=[],
    hole_lengths=[], closed_top=False,
)

for n in range(1, 6):
    wl_near = 2.0 * bore_length / n
    wl_base = inst.find_resonance(wl_near, [], n_register=n)
    freq_base = inst.frequency_from_wavelength(wl_base)
    
    # Now compute via JAX expanding window
    def scorer(w):
        from tmm_acoustics_jax import _resonance_phase_internal as _
        # Just compare phases
        return None
    
    # Manually run expanding window
    step_cents = 2.0
    step = 2.0 ** (step_cents / 1200.0)
    step_increase = 1.05
    hs = jnp.sqrt(step)
    w_left = wl_near / hs
    w_right = wl_near * hs
    
    from tmm_acoustics_jax import _ACT_PIPE, _ACT_JUNCTION2, _ACT_HOLE
    c_at = chain['act_types']
    c_pl = chain['act_pipe_length']
    c_ji0 = chain['act_junc_idx0']
    c_ji1 = chain['act_junc_idx1']
    c_hbi = chain['act_hole_bore_idx']
    n_actions = chain['n_actions']
    
    def resonance_phase(wl):
        phase = jnp.array(0.5)
        for i in range(n_actions):
            act = c_at[i]
            pp = phase + c_pl[i] / wl * 2.0
            a0 = jnp.pi * base_radii[c_ji0[i]] ** 2
            a1 = jnp.pi * base_radii[c_ji1[i]] ** 2
            sh = jnp.floor(phase + 0.5)
            pj = jnp.arctan(a1 / a0 * jnp.tan((phase - sh) * jnp.pi)) / jnp.pi + sh
            new_phase = jnp.where(act == 0, pp, pj)
            phase = new_phase
        return phase + 0.5
    
    def scorer_jax(w):
        p = resonance_phase(w)
        return ((p + 0.5) % 1.0) - 0.5
    
    # Expanding window search
    s_left = float(scorer_jax(w_left))
    s_right = float(scorer_jax(w_right))
    
    w_l, w_r, s_l, s_r = float(w_left), float(w_right), s_left, s_right
    cur_step = float(step)
    for iteration in range(20):
        found = (s_l >= 0.0) and (s_r < 0.0)
        if found:
            m = (s_r - s_l) / (w_r - w_l)
            wl_interp = w_l - s_l / m if abs(m) > 1e-30 else 0.5 * (w_l + w_r)
            break
        # Extend left
        new_wl = w_l / cur_step
        new_sl = float(scorer_jax(new_wl))
        found_left = (new_sl >= 0.0) and (s_l < 0.0)
        if found_left:
            m_l = (s_l - new_sl) / (w_l - new_wl)
            wl_interp = new_wl - new_sl / m_l if abs(m_l) > 1e-30 else 0.5 * (new_wl + w_l)
            break
        # Extend right
        new_wr = w_r * cur_step
        new_sr = float(scorer_jax(new_wr))
        found_right = (s_r >= 0.0) and (new_sr < 0.0)
        if found_right:
            m_r = (new_sr - s_r) / (new_wr - w_r)
            wl_interp = w_r - s_r / m_r if abs(m_r) > 1e-30 else 0.5 * (w_r + new_wr)
            break
        # Update
        if not found_left:
            w_l = new_wl
            s_l = new_sl
        if not found_right:
            w_r = new_wr
            s_r = new_sr
        cur_step *= step_increase
    else:
        wl_interp = w_l if abs(s_l) < abs(s_r) else w_r
    
    freq_jax = SPEED_OF_SOUND / wl_interp
    err = abs(freq_jax - freq_base) / freq_base * 100
    print(f"  Mode {n}: base={freq_base:.4f} Hz, JAX={freq_jax:.4f} Hz, err={err:.6f}%, iters={iteration+1}")

print("\nDone.")
