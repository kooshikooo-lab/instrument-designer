import sys
sys.path.insert(0, r'C:\instrument-designer')
from backend.instruments.bass_clarinet import BassClarinetBuilder
from backend.solvers.tmm_solver import TMMSolver
from backend.optimization.stage1_optimizer import optimize_stage1
from backend.core.network import AcousticNetwork, Tonehole
import numpy as np

builder = BassClarinetBuilder.standard()
builder.add_toneholes(
    positions=[176, 293, 338, 445, 532, 610, 636],
    radii=[5.25, 5.5, 5.75, 6.0, 6.5, 7.0, 7.5],
    lengths=[5.0] * 7,
)
net = builder.build()
net.reed_virtual_length = 493.0  # Enable reed virtual length

solver = TMMSolver()
targets = [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8]

fingering_sets = []
for i in range(8):
    f = ['closed'] * 7
    for j in range(i):
        f[7-1-j] = 'open'
    fingering_sets.append(f)

print('Running Stage 1 optimization with reed_virtual_length=493mm...')
result = optimize_stage1(
    network=net,
    target_frequencies=targets,
    fingering_sets=fingering_sets,
    n_register=1,
    solver=solver,
    bore_length_bounds=(1000, 1300),
    maxiter=20,
    popsize=15,
)

print()
print('Result: bore_length=%.1fmm' % result.bore_length)
print('Hole positions:', ['%.0f' % p for p in result.hole_positions])
print('Cost: %.2f' % result.cost)
print('Time: %.1fs' % result.wall_time)

# Verify
net_opt = AcousticNetwork(
    segments=[net.segments[0].__class__(length=result.bore_length, radius_in=net.segments[0].radius_in, radius_out=net.segments[0].radius_out)],
    ports=[Tonehole(position=p, radius=r, length=l) for p, r, l in zip(result.hole_positions, [5.25, 5.5, 5.75, 6.0, 6.5, 7.0, 7.5], [5.0]*7)],
    boundary_reed=net.boundary_reed,
    boundary_bell=net.boundary_bell,
    speed_of_sound=net.speed_of_sound,
    reed_virtual_length=net.reed_virtual_length,
)
net_opt.ports.append([p for p in net.ports if p.is_register_vent][0])
net_opt.ports.sort(key=lambda p: p.position)

verifier = TMMSolver()
target_wl = [net_opt.speed_of_sound / f for f in targets]
freqs = verifier.compute_frequencies(net_opt, target_wl, fingering_sets, n_register=1)

print()
print('Verification:')
cents = []
for name, target, actual in zip(['D2','E2','F#2','G2','A2','B2','C#3','D3'], targets, freqs):
    c = 1200 * np.log2(actual/target) if actual > 0 else 1e10
    cents.append(c)
    print('  %s: target=%.1f actual=%.1f cents=%+.1f' % (name, target, actual, c))

c = np.array(cents)
offset = np.median(c)
rms = np.sqrt(np.mean((c - offset)**2))
print('RMS: %.1fc  Offset: %+.0fc' % (rms, offset))