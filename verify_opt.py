import sys
sys.path.insert(0, r'C:\instrument-designer')
from backend.instruments.bass_clarinet import BassClarinetBuilder
from backend.solvers.tmm_solver import TMMSolver
from backend.core.network import AcousticNetwork, Tonehole
import numpy as np

builder = BassClarinetBuilder.standard()
builder.add_toneholes(
    positions=[176, 293, 338, 445, 532, 610, 636],
    radii=[5.25, 5.5, 5.75, 6.0, 6.5, 7.0, 7.5],
    lengths=[5.0] * 7,
)
net = builder.build()
net.reed_virtual_length = 493.0

# Use optimized bore length
opt_bore = 1045.7
opt_positions = [209, 333, 375, 432, 586, 666, 686]

net_opt = AcousticNetwork(
    segments=[net.segments[0].__class__(length=opt_bore, radius_in=net.segments[0].radius_in, radius_out=net.segments[0].radius_out)],
    ports=[net.ports[0].__class__(position=p, radius=r, length=l) for p, r, l in zip(opt_positions, [5.25, 5.5, 5.75, 6.0, 6.5, 7.0, 7.5], [5.0]*7)],
    boundary_reed=net.boundary_reed,
    boundary_bell=net.boundary_bell,
    speed_of_sound=net.speed_of_sound,
    reed_virtual_length=net.reed_virtual_length,
)
net_opt.ports.append([p for p in net.ports if p.is_register_vent][0])
net_opt.ports.sort(key=lambda p: p.position)

solver = TMMSolver()
targets = [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8]
names = ['D2','E2','F#2','G2','A2','B2','C#3','D3']

fingering_sets = []
for i in range(8):
    f = ['closed'] * 7
    for j in range(i):
        f[6-j] = 'open'
    fingering_sets.append(f)

target_wl = [net_opt.speed_of_sound / f for f in targets]
freqs = solver.compute_frequencies(net_opt, target_wl, fingering_sets, n_register=1)

print('Optimized with reed_virtual_length=493mm:')
cents = []
for name, target, actual in zip(names, targets, freqs):
    c = 1200 * np.log2(actual/target) if actual > 0 else 1e10
    print(f'  {name}: target={target:.1f} actual={actual:.1f} cents={c:+.1f}')
    cents.append(c)

c = np.array(cents)
offset = np.median(c)
rms = np.sqrt(np.mean((c - offset)**2))
abs_rms = np.sqrt(np.mean(c**2))
print(f'RMS (offset removed): {rms:.1f}c  Offset: {offset:+.0f}c')
print(f'Abs RMS: {abs_rms:.1f}c')