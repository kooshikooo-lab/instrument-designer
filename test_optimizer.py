"""Test optimizer convergence with phase cost."""
import sys, io
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

import numpy as np
import jax
import jax.numpy as jnp
import time
from tmm_acoustics import TMMInstrument, SPEED_OF_SOUND, end_flange_length_correction
from tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, MAX_HOLES

print("=" * 70)
print("OPTIMIZER CONVERGENCE TEST: Phase cost vs old root-finding cost")
print("=" * 70)

bore_length = 500.0
od = 22.0
n_bore = 10
n_holes = 6
hp = [120.0 + i * 55.0 for i in range(n_holes)]
hd = [7.0] * n_holes
hl = [3.75] * n_holes
bp = np.linspace(0, bore_length, n_bore).tolist()

# Compute targets from baseline uniform bore
base_radii = np.full(n_bore, 9.5)
inst = TMMInstrument(
    inner_positions=bp, inner_diameters=(base_radii * 2).tolist(),
    outer_diameters=[od]*n_bore,
    hole_positions=hp, hole_diameters=hd, hole_lengths=hl, closed_top=False,
)

fingerings = [
    ['closed'] * n_holes,
    ['closed'] * 5 + ['open'],
    ['closed'] * 4 + ['open'] * 2,
    ['closed'] * 3 + ['open'] * 3,
]

target_freqs = []
target_wavelengths = []
for fs in fingerings:
    wl = inst.find_resonance(bore_length * 2, fs, n_register=1)
    freq = inst.frequency_from_wavelength(wl)
    target_freqs.append(freq)
    target_wavelengths.append(SPEED_OF_SOUND / freq)
    print(f"  Target: {freq:.1f} Hz")

# Build chain and cost function
chain = build_action_chain_v2(bp, base_radii.tolist(), od, hp, hd, hl, False)
fs_float = []
for fs in fingerings:
    arr = np.zeros(MAX_HOLES)
    for i, h in enumerate(fs):
        if h == 'open':
            arr[i] = 1.0
    fs_float.append(arr)

cost_fn = make_rms_cost(chain, target_freqs, fs_float, target_wavelengths)
grad_fn = jax.grad(cost_fn)

# Warmup
x0 = np.full(n_bore, 9.5)
_ = cost_fn(jnp.array(x0)).block_until_ready()
_ = grad_fn(jnp.array(x0)).block_until_ready()

# Benchmark gradient
start = time.time()
for _ in range(10):
    grad_fn(jnp.array(x0)).block_until_ready()
grad_time = (time.time() - start) / 10 * 1000
print(f"\n  Gradient time: {grad_time:.1f}ms")

# FD gradient for comparison
eps = 1e-5
start = time.time()
fd_grad = np.zeros(n_bore)
for i in range(n_bore):
    br_plus = x0.copy(); br_plus[i] += eps
    br_minus = x0.copy(); br_minus[i] -= eps
    c_plus = float(cost_fn(jnp.array(br_plus)).block_until_ready())
    c_minus = float(cost_fn(jnp.array(br_minus)).block_until_ready())
    fd_grad[i] = (c_plus - c_minus) / (2 * eps)
fd_time = (time.time() - start) * 1000
print(f"  FD gradient time: {fd_time:.1f}ms ({n_bore + 1} evals)")
print(f"  Speedup: {fd_time / grad_time:.1f}x")

jax_grad = np.array(grad_fn(jnp.array(x0)).block_until_ready())
rel_err = np.abs(jax_grad - fd_grad) / (np.abs(fd_grad) + 1e-30)
print(f"  Max gradient error: {np.max(rel_err):.1%}")
print(f"  Mean gradient error: {np.mean(rel_err):.1%}")

# Now run L-BFGS-B optimizer
from scipy.optimize import minimize

def objective_and_grad(x):
    radii_jax = jnp.array(x, dtype=jnp.float32)
    cost = cost_fn(radii_jax)
    grad = grad_fn(radii_jax)
    return float(cost), np.array(grad, dtype=np.float64)

print(f"\n--- Running L-BFGS-B optimizer (200 iterations) ---")
t0 = time.time()
result = minimize(
    lambda x: objective_and_grad(x)[0],
    x0,
    method='L-BFGS-B',
    jac=lambda x: objective_and_grad(x)[1],
    bounds=[(1.0, 15.0)] * n_bore,
    options={"maxiter": 200, "ftol": 1e-8, "gtol": 1e-6},
)
wall_time = time.time() - t0
print(f"  Wall time: {wall_time:.1f}s")
print(f"  Iterations: {result.nit}")
print(f"  Grad evals: {result.nfev}")
print(f"  Objective: {result.fun:.6f}")

# Verify with baseline TMM
from tmm_acoustics import tmm_instrument_from_radii
inst_final = tmm_instrument_from_radii(
    np.maximum(result.x, 1.0), bore_length, hp, hd, hl, od, False, 0.5,
)
print(f"\n--- Verification with baseline TMM ---")
for fs, tf in zip(fingerings, target_freqs):
    wl = inst_final.find_resonance(SPEED_OF_SOUND / tf, fs, n_register=1)
    af = inst_final.frequency_from_wavelength(wl)
    err = 1200 * np.log2(af / tf)
    print(f"  target={tf:.1f}, actual={af:.1f}, err={err:+.2f} cents")

# RMS
errors = []
for fs, tf in zip(fingerings, target_freqs):
    wl = inst_final.find_resonance(SPEED_OF_SOUND / tf, fs, n_register=1)
    af = inst_final.frequency_from_wavelength(wl)
    errors.append(1200 * np.log2(af / tf))
offset = np.median(errors)
corrected = np.abs(np.array(errors) - offset)
rms = np.sqrt(np.mean(corrected**2))
print(f"\n  Final RMS: {rms:.2f} cents (offset: {offset:+.2f} cents)")
