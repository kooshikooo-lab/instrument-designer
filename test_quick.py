"""Quick test to verify TMM optimizer works."""
import sys, os, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.tmm_optimizer import TMMBoreOptimizer

print("Starting baseline L-BFGS-B test for chalumeau...")
t0 = time.time()
opt = TMMBoreOptimizer(
    target_frequencies=[261.6, 277.2, 293.7, 311.1, 329.6, 349.2],
    fingering_sets=[
        ["closed", "closed", "closed", "closed", "closed", "closed"],
        ["open",   "closed", "closed", "closed", "closed", "closed"],
        ["open",   "open",   "closed", "closed", "closed", "closed"],
        ["open",   "open",   "open",   "closed", "closed", "closed"],
        ["open",   "open",   "open",   "open",   "closed", "closed"],
        ["open",   "open",   "open",   "open",   "open",   "closed"],
    ],
    n_control_points=12,
    bore_length=300.0,
    min_radius=3.625,
    max_radius=10.875,
    hole_positions=[50.0, 90.0, 130.0, 170.0, 210.0, 250.0],
    hole_diameters=[7.0]*6,
    hole_lengths=[3.75]*6,
    closed_top=True,
    outer_diameter=22.0,
    n_register=1,
)
result = opt.run(verbose=True, maxiter=50)
elapsed = time.time()-t0
print(f"\nDone in {elapsed:.1f}s, rms={result['final_rms_cents']:.2f} cents")
