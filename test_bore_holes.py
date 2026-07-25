import sys
sys.path.insert(0, r'C:\instrument-designer')
from backend.solvers.tmm_solver import TMMSolver
from backend.tmm_acoustics import tmm_instrument_from_radii
import numpy as np

# Test bore length for correct D2
for L in [1100, 1159, 1200, 1250, 1300]:
    inst = tmm_instrument_from_radii(
        [12.5], L, [], [], [], 22.0, True, 0.5, 0.0, 0.0
    )
    wl = inst.find_resonance(343200/73.4, [], n_register=1)
    print('L=%dmm: wl=%.0f f=%.1fHz' % (L, wl, 343200/wl))

# With holes - test if holes shift fundamental correctly
# Build instrument with holes
from backend.tmm_acoustics import TMMInstrument
from backend.core.network import AcousticNetwork, Segment, Tonehole, Boundary, BoundaryType, ExcitationType
from backend.solvers.tmm_solver import TMMSolver

net = AcousticNetwork(
    segments=[Segment(length=1159, radius_in=12.5, radius_out=12.5)],
    ports=[],
    boundary_reed=Boundary(type=BoundaryType.REED, excitation=ExcitationType.REED),
    boundary_bell=Boundary(type=BoundaryType.BELL, position=1159),
    speed_of_sound=346100.0,
)

solver = TMMSolver()
inst = solver.from_network(net)

# Test with no holes first
wl = inst.find_resonance(343200/73.4, [], n_register=1)
print('No holes: wl=%.0f f=%.1fHz' % (wl, 343200/wl))

# Add holes and test
from backend.core.network import AcousticNetwork, Tonehole

net_holes = AcousticNetwork(
    segments=[Segment(length=1159, radius_in=12.5, radius_out=12.5)],
    ports=[Tonehole(position=176, radius=5.25, length=5.0)],
    boundary_reed=Boundary(type=BoundaryType.REED, excitation=ExcitationType.REED),
    boundary_bell=Boundary(type=BoundaryType.BELL, position=1159),
    speed_of_sound=346100.0,
)

inst2 = solver.from_network(net_holes)
wl = inst2.find_resonance(343200/73.4, ['closed']*8, n_register=1)
print('With 1 hole (all closed): wl=%.0f f=%.1fHz' % (wl, 343200/wl))

wl2 = inst2.find_resonance(343200/82.4, ['closed']*7 + ['open'], n_register=1)
print('With 1 hole open: wl=%.0f f=%.1fHz' % (wl2, 343200/wl2))