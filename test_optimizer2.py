"""Full optimizer convergence test — starts from non-optimal bore."""
import sys, io
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True)

import numpy as np
import jax
import jax.numpy as jnp
import time
from tmm_acoustics import TMMInstrument, tmm_instrument_from_radii, SPEED_OF_SOUND, end_flange_length_correction
from tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, MAX_HOLES
from tmm_optimizer_v2 import TMMBoreOptimizerJAX

print("=" * 70)
print("FULL OPTIMIZER CONVERGENCE TEST — Non-optimal start")
print("=" * 70)

bore_length = 500.0
od = 22.0
n_holes = 6
hp = [120.0 + i * 55.0 for i in range(n_holes)]
hd = [7.0] * n_holes
hl = [3.75] * n_holes

fingerings = [
    ['closed'] * n_holes,
    ['closed'] * 5 + ['open'],
    ['closed'] * 4 + ['open'] * 2,
    ['closed'] * 3 + ['open'] * 3,
]

# Compute targets from a CONICAL bore (different from cylindrical start)
conical_radii = np.linspace(7.0, 12.0, 10)
inst_target = tmm_instrument_from_radii(
    conical_radii, bore_length, hp, hd, hl, od, False, 0.5,
)
target_freqs = []
for fs in fingerings:
    wl = inst_target.find_resonance(bore_length * 2, fs, n_register=1)
    freq = inst_target.frequency_from_wavelength(wl)
    target_freqs.append(freq)
    print(f"  Target: {freq:.1f} Hz")

# Start from cylindrical bore (NOT the target)
print(f"\n  Starting bore: cylindrical (9.5mm radius)")
print(f"  Target bore: conical (7.0 to 12.0mm)")

optimizer = TMMBoreOptimizerJAX(
    target_frequencies=target_freqs,
    fingering_sets=fingerings,
    n_control_points=10,
    bore_length=bore_length,
    closed_top=False,
    outer_diameter=od,
    hole_positions=hp,
    hole_diameters=hd,
    hole_lengths=hl,
)

result = optimizer.run(verbose=True, maxiter=300)

# Verify
inst_final = tmm_instrument_from_radii(
    np.maximum(np.array(result['best_radii']), 1.0), bore_length, hp, hd, hl, od, False, 0.5,
)
print(f"\n--- Verification with baseline TMM ---")
errors = []
for fs, tf in zip(fingerings, target_freqs):
    wl = inst_final.find_resonance(SPEED_OF_SOUND / tf, fs, n_register=1)
    af = inst_final.frequency_from_wavelength(wl)
    err = 1200 * np.log2(af / tf)
    errors.append(err)
    print(f"  target={tf:.1f}, actual={af:.1f}, err={err:+.2f} cents")

offset = np.median(errors)
corrected = np.abs(np.array(errors) - offset)
rms = np.sqrt(np.mean(corrected**2))
print(f"\n  Final RMS: {rms:.2f} cents (offset: {offset:+.2f} cents)")
print(f"  Wall time: {result['wall_time']:.1f}s")
print(f"  Iterations: {result['iterations']}")
