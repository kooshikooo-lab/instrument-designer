"""Isolate gradient issue: test phase function gradient vs FD."""
import sys, io
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

import numpy as np
import jax
import jax.numpy as jnp
from tmm_acoustics_jax import build_action_chain_v2, _ACT_PIPE, _ACT_JUNCTION2, _ACT_HOLE

print("=" * 70)
print("DIAGNOSTIC: Phase Function Gradient")
print("=" * 70)

bore_length = 500.0
od = 22.0
n_bore = 10
bp = np.linspace(0, bore_length, n_bore).tolist()
base_radii = np.full(n_bore, 9.5)
br_jax = jnp.array(base_radii)

chain = build_action_chain_v2(bp, base_radii.tolist(), od, [], [], [], False)
n_actions = chain['n_actions']
c_at = chain['act_types']
c_pl = chain['act_pipe_length']
c_ji0 = chain['act_junc_idx0']
c_ji1 = chain['act_junc_idx1']

def tanner(x):
    return jnp.tan(x * jnp.pi)
def untanner(x):
    return jnp.arctan(x) / jnp.pi

def resonance_phase_simple(wl, bore_radii):
    """Direct implementation without lax.scan — pure Python loop."""
    phase = jnp.array(0.5)
    for i in range(n_actions):
        act = c_at[i]
        pp = phase + c_pl[i] / wl * 2.0
        a0 = jnp.pi * bore_radii[c_ji0[i]] ** 2
        a1 = jnp.pi * bore_radii[c_ji1[i]] ** 2
        sh = jnp.floor(phase + 0.5)
        pj = untanner(a1 / a0 * tanner(phase - sh)) + sh
        new_phase = jnp.where(act == 0, pp, pj)
        phase = new_phase
    return phase + 0.5

def scorer(wl, bore_radii):
    p = resonance_phase_simple(wl, bore_radii)
    return ((p + 0.5) % 1.0) - 0.5

# Test: gradient of scorer at a specific wavelength
wl_test = 1000.0  # near first harmonic
sc = scorer(wl_test, br_jax)
print(f"scorer at wl={wl_test}: {float(sc):.6f}")

# JAX gradient of scorer wrt bore_radii
jax_grad = jax.grad(lambda br: scorer(wl_test, br))(br_jax)
print(f"JAX grad of scorer: {np.array(jax_grad)}")

# FD gradient
eps = 1e-4
fd_grad = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = base_radii.copy()
    br_minus = base_radii.copy()
    br_plus[i] += eps
    br_minus[i] -= eps
    s_plus = float(scorer(wl_test, jnp.array(br_plus)))
    s_minus = float(scorer(wl_test, jnp.array(br_minus)))
    fd_grad[i] = (s_plus - s_minus) / (2 * eps)
print(f"FD  grad of scorer: {fd_grad}")

rel_err = np.abs(np.array(jax_grad) - fd_grad) / (np.abs(fd_grad) + 1e-30)
print(f"Rel error: {rel_err}")
print(f"Max rel error: {np.max(rel_err):.4f}")

# Test: gradient of phase function itself
print("\n--- Phase function gradient ---")
phase_val = resonance_phase_simple(wl_test, br_jax)
print(f"Phase at wl={wl_test}: {float(phase_val):.6f}")

jax_phase_grad = jax.grad(lambda br: resonance_phase_simple(wl_test, br))(br_jax)
fd_phase_grad = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = base_radii.copy()
    br_minus = base_radii.copy()
    br_plus[i] += eps
    br_minus[i] -= eps
    p_plus = float(resonance_phase_simple(wl_test, jnp.array(br_plus)))
    p_minus = float(resonance_phase_simple(wl_test, jnp.array(br_minus)))
    fd_phase_grad[i] = (p_plus - p_minus) / (2 * eps)

print(f"JAX phase grad: {np.array(jax_phase_grad)}")
print(f"FD  phase grad: {fd_phase_grad}")
rel_err_phase = np.abs(np.array(jax_phase_grad) - fd_phase_grad) / (np.abs(fd_phase_grad) + 1e-30)
print(f"Rel error: {rel_err_phase}")
print(f"Max rel error: {np.max(rel_err_phase):.4f}")

# Test: lax.scan version vs Python loop version
print("\n--- lax.scan vs Python loop ---")
def resonance_phase_scan(wl, bore_radii):
    def scan_step(phase, i):
        act = c_at[i]
        pp = phase + c_pl[i] / wl * 2.0
        a0 = jnp.pi * bore_radii[c_ji0[i]] ** 2
        a1 = jnp.pi * bore_radii[c_ji1[i]] ** 2
        sh = jnp.floor(phase + 0.5)
        pj = untanner(a1 / a0 * tanner(phase - sh)) + sh
        return jnp.where(act == 0, pp, pj), None
    phase, _ = jax.lax.scan(scan_step, jnp.array(0.5), jnp.arange(n_actions))
    return phase + 0.5

phase_loop = resonance_phase_simple(wl_test, br_jax)
phase_scan = resonance_phase_scan(wl_test, br_jax)
print(f"Phase (loop): {float(phase_loop):.10f}")
print(f"Phase (scan): {float(phase_scan):.10f}")
print(f"Diff: {abs(float(phase_loop) - float(phase_scan)):.2e}")

grad_loop = jax.grad(lambda br: resonance_phase_simple(wl_test, br))(br_jax)
grad_scan = jax.grad(lambda br: resonance_phase_scan(wl_test, br))(br_jax)
print(f"Grad (loop): {np.array(grad_loop)}")
print(f"Grad (scan): {np.array(grad_scan)}")
print(f"Grad diff: {np.max(np.abs(np.array(grad_loop) - np.array(grad_scan))):.2e}")

# Now test: what does the ACTUAL cost function's _find_resonance gradient look like?
print("\n--- Full cost function gradient (JAX vs FD) ---")
from tmm_acoustics import SPEED_OF_SOUND, end_flange_length_correction
from tmm_acoustics_jax import make_rms_cost, MAX_HOLES

eff = bore_length + end_flange_length_correction(od, 19.0)
tf = jnp.array([n * SPEED_OF_SOUND / (2.0 * eff) for n in range(1, 6)])
fs = [jnp.zeros(0) for _ in range(5)]
tw = jnp.array([2.0 * eff / n for n in range(1, 6)])

cost_fn = make_rms_cost(chain, tf, fs, tw)
c = cost_fn(br_jax).block_until_ready()
print(f"Cost: {float(c):.8f}")

jax_cost_grad = jax.grad(cost_fn)(br_jax)
print(f"JAX cost grad: {np.array(jax_cost_grad)}")

fd_cost_grad = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = base_radii.copy()
    br_minus = base_radii.copy()
    br_plus[i] += eps
    br_minus[i] -= eps
    c_plus = float(cost_fn(jnp.array(br_plus)).block_until_ready())
    c_minus = float(cost_fn(jnp.array(br_minus)).block_until_ready())
    fd_cost_grad[i] = (c_plus - c_minus) / (2 * eps)
print(f"FD  cost grad: {fd_cost_grad}")
rel_err_cost = np.abs(np.array(jax_cost_grad) - fd_cost_grad) / (np.abs(fd_cost_grad) + 1e-30)
print(f"Rel error: {rel_err_cost}")
print(f"Max rel error: {np.max(rel_err_cost):.4f}")
