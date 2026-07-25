import sys
sys.path.insert(0, r'C:\instrument-designer')
from backend.instruments.bass_clarinet import BassClarinetBuilder
from backend.solvers.tmm_solver import TMMSolver
from backend.optimization.stage1_optimizer import optimize_stage1
import numpy as np

builder = BassClarinetBuilder.standard()
builder.add_toneholes(
    positions=[176, 293, 338, 445, 532, 610, 636],
    radii=[5.25, 5.5, 5.75, 6.0, 6.5, 7.0, 7.5],
    lengths=[5.0] * 7,
)
net = builder.build()
net.reed_virtual_length = 493.0

solver = TMMSolver()
targets = [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8]

fingering_sets = []
for i in range(8):
    f = ['closed'] * 7
    for j in range(i):
        f[6-j] = 'open'
    fingering_sets.append(f)

print('Running Stage 1 optimization with reed_virtual_length=493mm...')
result = optimize_stage1(
    network=net,
    target_frequencies=targets,
    fingering_sets=fingering_sets,
    n_register=1,
    solver=solver,
    bore_length_bounds=(1000, 1300),
    maxiter=30,
    popsize=20,
)

print(f'Result: bore_length={result.bore_length:.1f}mm')
print(f'Hole positions: {[f"{p:.0f}" for p in result.hole_positions]}')
print(f'Cost: {result.cost:.2f}')
print(f'Time: {result.wall_time:.1f}s')