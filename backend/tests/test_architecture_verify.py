"""Verify full pipeline through new architecture.

Build -> Solve -> Optimize — all through AcousticNetwork.
Uses new Vent/Tonehole/RegisterVent hierarchy and separated Fingering model.
"""
import sys, os
sys.path.insert(0, r"C:\instrument-designer")

import numpy as np
from backend.core.network import (
    AcousticNetwork, Segment, Port, Tonehole, RegisterVent,
    Boundary, Fingering, NodeType, BoundaryType, ExcitationType,
)
from backend.instruments.clarinet import ClarinetBuilder
from backend.solvers.tmm_solver import TMMSolver
from backend.optimization.fingering_optimizer import FingeringOptimizer

# ── Step 1: Build instrument through architecture ──
builder = ClarinetBuilder()
builder.set_bore(length=1200.0, radius=12.5)
# Register vent: 3.5mm diameter (1.75mm radius), 80mm from reed
builder.set_register_vent(position=80.0, radius=1.75, length=3.0)
# Toneholes: graduated diameters, bell-first positions
builder.add_toneholes(
    positions=[176, 293, 338, 445, 532, 610, 636],
    radii=[5.25, 5.5, 5.75, 6.0, 6.5, 7.0, 7.5],
    lengths=[5.0] * 7,
)
net = builder.build()

print("Step 1: Build")
print("  Segments: %d  Toneholes: %d  Register vents: %d" % (
    net.n_segments, net.n_toneholes, net.n_register_vents))
print("  Length: %.0fmm  Radius: %.1fmm" % (net.total_length, net.segments[0].radius_in))
print("  Ports: %s" % ["%.0fmm" % p.position for p in net.ports])

# ── Step 2: Solve through architecture ──
solver = TMMSolver()

targets = [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8]
names = ["D2", "E2", "F#2", "G2", "A2", "B2", "C#3", "D3"]

# Bell-first ascending: open from LAST index first
fingering_sets = []
for i in range(8):
    f = ["closed"] * 7
    for j in range(i):
        f[7 - 1 - j] = "open"
    fingering_sets.append(f)

print("\nStep 2: Solve (default hole positions)")
target_wl = [net.speed_of_sound / f for f in targets]
freqs = solver.compute_frequencies(net, target_wl, fingering_sets, n_register=1)

fmt = "%-6s %8s %8s %8s"
print(fmt % ("Note", "Target", "Actual", "Cents"))
print("-" * 34)
cents_arr = []
for name, target, actual in zip(names, targets, freqs):
    c = 1200 * np.log2(actual / target) if actual > 0 else 1e10
    cents_arr.append(c)
    print(fmt % (name, "%.1f" % target, "%.1f" % actual, "%+.1f" % c))

c = np.array(cents_arr)
offset = np.median(c)
rms = np.sqrt(np.mean((c - offset) ** 2))
peak = np.max(np.abs(c - offset))
print("  RMS: %.1fc  Peak: %.1fc  Offset: %+.0fc" % (rms, peak, offset))

# ── Step 3: Verify Fingering model ──
print("\nStep 3: Verify Fingering model")
# Create a fingering with separated toneholes and register
fing = Fingering(
    name="D2",
    toneholes=[False, False, False, False, False, False, False],
    register=False,  # chalumeau register
)
print("  Fingering '%s': toneholes=%s, register=%s" % (
    fing.name, fing.toneholes, fing.register))

# Convert to TMM format
tmm_fing = net.fingering_to_tmm(fing)
print("  TMM format: %s" % tmm_fing)

# Verify port state lookup
for i, port in enumerate(net.ports):
    state = fing.get_port_state(port)
    print("  Port %d (%.0fmm, %s): %s" % (
        i, port.position,
        "TONEHOLE" if port.is_tonehole else "REGISTER",
        "open" if state else "closed"))

# ── Step 4: Optimize through architecture ──
print("\nStep 4: Optimize hole positions")
opt = FingeringOptimizer(
    network=net,
    target_frequencies=targets,
    fingering_sets=fingering_sets,
    n_register=1,
    solver=solver,
)
result = opt.optimize(verbose=True)

print("\n  Optimized positions: %s" % ["%.0f" % p for p in result.parameters["hole_positions"]])
print("  RMS: %.2fc  Cost: %.4f" % (result.rms_cents, result.cost))
print("  Time: %.1fs  Evals: %d" % (result.wall_time, result.n_evaluations))
