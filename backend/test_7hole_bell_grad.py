"""Test: 7-hole with bell and graduated diameters."""
import sys, time
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 82.407, 97.999, 110.000, 130.813, 146.832, 164.814, 195.998]
names = ['D2','E2','G2','A2','C3','D3','E3','G3']

chart = [
    ['closed']*7 + ['closed'],
    ['open'] + ['closed']*6 + ['closed'],
    ['open','open'] + ['closed']*5 + ['closed'],
    ['open']*3 + ['closed']*4 + ['closed'],
    ['open']*4 + ['closed']*3 + ['closed'],
    ['open']*5 + ['closed']*2 + ['closed'],
    ['open']*6 + ['closed'] + ['closed'],
    ['open']*7 + ['closed'],
]

hole_positions = [176, 293, 338, 445, 532, 610, 636]

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.15, 1.0),
    optimize_grad=True,
    grad_bounds=(8.0, 12.0, 16.0, 22.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=False, verbose=True)
t1 = time.time()
print(f'\nTime: {t1-t0:.0f}s')
print(f'Reg1 RMS: {result["final_rms_1st_cents"]:.2f}c')
print(f'Reg2 RMS: {result["final_rms_2nd_cents"]:.2f}c')
print(f'Holes: {[f"{p:.0f}" for p in result["free_hole_positions"]]}')
if 'graduated_diameters' in result:
    print(f'Diameters: {[f"{d:.1f}" for d in result["graduated_diameters"]]}')