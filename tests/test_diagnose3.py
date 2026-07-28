"""Test gradient accuracy away from minimum."""
import sys, io
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

import numpy as np
import jax
import jax.numpy as jnp
from tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, make_phase_cost, SPEED_OF_SOUND, end_flange_length_correction

print("=" * 70)
print("GRADIENT TEST: Phase cost vs FD (away from minimum)")
print("=" * 70)

bore_length = 500.0
od = 22.0
n_bore = 10
bp = np.linspace(0, bore_length, n_bore).tolist()

# Perturbed bore (NOT at minimum)
base_radii = np.array([9.5, 9.0, 10.0, 8.5, 10.5, 8.0, 11.0, 7.5, 11.5, 9.5])
br_jax = jnp.array(base_radii)

chain = build_action_chain_v2(bp, base_radii.tolist(), od, [], [], [], False)

eff = bore_length + end_flange_length_correction(od, 19.0)
tf = jnp.array([n * SPEED_OF_SOUND / (2.0 * eff) for n in range(1, 6)])
fs = [jnp.zeros(0) for _ in range(5)]
tw = jnp.array([2.0 * eff / n for n in range(1, 6)])

cost_fn = make_phase_cost(chain, tf, fs, tw)
c = cost_fn(br_jax).block_until_ready()
print(f"Cost at perturbed bore: {float(c):.8f}")

# JAX gradient
jax_grad = jax.grad(cost_fn)(br_jax)
print(f"JAX grad: {np.array(jax_grad)}")

# FD gradient
eps = 1e-5
fd_grad = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = base_radii.copy()
    br_minus = base_radii.copy()
    br_plus[i] += eps
    br_minus[i] -= eps
    c_plus = float(cost_fn(jnp.array(br_plus)).block_until_ready())
    c_minus = float(cost_fn(jnp.array(br_minus)).block_until_ready())
    fd_grad[i] = (c_plus - c_minus) / (2 * eps)
print(f"FD  grad: {fd_grad}")

rel_err = np.abs(np.array(jax_grad) - fd_grad) / (np.abs(fd_grad) + 1e-30)
print(f"Rel error: {rel_err}")
print(f"Max rel error: {np.max(rel_err):.4f}")
print(f"Mean rel error: {np.mean(rel_err):.4f}")

# Also test with holes
print("\n" + "=" * 70)
print("GRADIENT TEST: With holes (clarinet-like)")
print("=" * 70)

n_holes = 6
hp = [120.0 + i * 55.0 for i in range(n_holes)]
hd = [7.0] * n_holes
hl = [3.75] * n_holes
base_radii2 = np.full(n_bore, 9.5)
br_jax2 = jnp.array(base_radii2)

chain2 = build_action_chain_v2(bp, base_radii2.tolist(), od, hp, hd, hl, True)

# Clarinet fingerings
fingerings = [
    ['closed'] * n_holes,
    ['closed'] * 5 + ['open'],
    ['closed'] * 4 + ['open'] * 2,
    ['closed'] * 3 + ['open'] * 3,
]

# Compute targets from baseline
from tmm_acoustics import TMMInstrument
inst = TMMInstrument(
    inner_positions=bp, inner_diameters=(base_radii2 * 2).tolist(),
    outer_diameters=[od]*n_bore,
    hole_positions=hp, hole_diameters=hd, hole_lengths=hl, closed_top=True,
)
target_freqs = []
for fs_str in fingerings:
    wl = inst.find_resonance(bore_length * 4, fs_str, n_register=1)
    freq = inst.frequency_from_wavelength(wl)
    target_freqs.append(freq)
    print(f"  Target: {freq:.1f} Hz (fingering: {fs_str})")

target_wavelengths = [SPEED_OF_SOUND / f for f in target_freqs]

fs_padded = []
for fs_str in fingerings:
    arr = np.zeros(n_holes)
    for i, h in enumerate(fs_str):
        if h == 'open':
            arr[i] = 1.0
    fs_padded.append(arr)

cost_fn2 = make_phase_cost(chain2, target_freqs, fs_padded, target_wavelengths)
c2 = cost_fn2(br_jax2).block_until_ready()
print(f"\nCost: {float(c2):.8f}")

jax_grad2 = jax.grad(cost_fn2)(br_jax2)
print(f"JAX grad: {np.array(jax_grad2)}")

fd_grad2 = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = base_radii2.copy()
    br_minus = base_radii2.copy()
    br_plus[i] += eps
    br_minus[i] -= eps
    c_plus = float(cost_fn2(jnp.array(br_plus)).block_until_ready())
    c_minus = float(cost_fn2(jnp.array(br_minus)).block_until_ready())
    fd_grad2[i] = (c_plus - c_minus) / (2 * eps)
print(f"FD  grad: {fd_grad2}")

rel_err2 = np.abs(np.array(jax_grad2) - fd_grad2) / (np.abs(fd_grad2) + 1e-30)
print(f"Rel error: {rel_err2}")
print(f"Max rel error: {np.max(rel_err2):.4f}")
print(f"Mean rel error: {np.mean(rel_err2):.4f}")
