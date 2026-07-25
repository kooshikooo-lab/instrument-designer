"""Verify TMM solver matches chalumier reference on simple cases.

Tests:
  1. Cylindrical bore (1200mm, 12.5mm radius) -- all-closed fundamental vs c/(4L)
  2. 6-hole chalumeau (300mm, 7.25mm radius) -- bell-first ascending fingerings
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.core.network import (
    AcousticNetwork, Segment, Port, Boundary, NodeType, BoundaryType, ExcitationType,
)
from backend.solvers.tmm_solver import TMMSolver
from backend.tmm_acoustics import SPEED_OF_SOUND, TMMInstrument, end_flange_length_correction

PASS = True


def report(label, ok, detail=""):
    global PASS
    status = "PASS" if ok else "FAIL"
    if not ok:
        PASS = False
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {label}{suffix}")


# =========================================================================
# Test 1 -- Cylindrical bore, all-closed, fundamental vs analytical c/(4L)
# =========================================================================
print("=" * 60)
print("TEST 1: Cylindrical bore -- all-closed resonance vs c/(4L)")
print("=" * 60)

L1 = 1200.0      # mm
R1 = 12.5        # mm
c = SPEED_OF_SOUND  # 346100 mm/s (chalumier value)

net1 = AcousticNetwork(
    segments=[Segment(length=L1, radius_in=R1, radius_out=R1)],
    ports=[],
    boundary_reed=Boundary(type=BoundaryType.REED, excitation=ExcitationType.REED),
    boundary_bell=Boundary(type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=L1),
)

solver = TMMSolver()

# Ideal closed pipe: f = c / (4L), lambda = 4L
f_ideal = c / (4.0 * L1)
wl_ideal = 4.0 * L1

# End-corrected: effective length includes bell flange correction
outer_diam = R1 * 2 * 2.5  # same formula as in TMMSolver.from_network
delta = end_flange_length_correction(outer_diam, R1 * 2)
L_eff = L1 + delta
f_corrected = c / (4.0 * L_eff)

# TMM resonance
wl_tmm = solver.find_resonance(net1, wl_ideal, [], n_register=1)
f_tmm = c / wl_tmm

error_ideal_pct = abs(f_tmm - f_ideal) / f_ideal * 100.0
error_ideal_cents = 1200.0 * math.log2(f_tmm / f_ideal)
error_corrected_cents = 1200.0 * math.log2(f_tmm / f_corrected)

print(f"  Ideal closed pipe:         f = {f_ideal:.2f} Hz,  lambda = {wl_ideal:.1f} mm")
print(f"  End-corrected (delta={delta:.2f}mm): f = {f_corrected:.2f} Hz")
print(f"  TMM solver:                f = {f_tmm:.2f} Hz,  lambda = {wl_tmm:.1f} mm")
print(f"  Error vs ideal:            {error_ideal_pct:.3f}%  ({error_ideal_cents:+.1f} cents)")
print(f"  Error vs end-corrected:    {error_corrected_cents:+.1f} cents")

report("Wavelength within 5% of 4L", error_ideal_pct < 5.0, f"{error_ideal_pct:.3f}%")
report(
    "Frequency within 15 cents of ideal c/(4L)",
    abs(error_ideal_cents) < 15.0,
    f"{error_ideal_cents:+.1f} cents",
)
report(
    "Frequency within 5 cents of end-corrected theory",
    abs(error_corrected_cents) < 5.0,
    f"{error_corrected_cents:+.1f} cents",
)

# Overtones: closed pipe has odd harmonics only.
# Register n -> (2n-1) * f_fundamental
print()
for n_reg in [2, 3]:
    harmonic_number = 2 * n_reg - 1  # reg 2 -> 3rd harmonic, reg 3 -> 5th
    wl_ov = solver.find_resonance(net1, wl_ideal / harmonic_number, [], n_register=n_reg)
    f_ov = c / wl_ov
    f_ov_ideal = harmonic_number * f_ideal
    f_ov_corrected = harmonic_number * f_corrected
    ov_err_ideal = 1200.0 * math.log2(f_ov / f_ov_ideal)
    ov_err_corr = 1200.0 * math.log2(f_ov / f_ov_corrected)
    print(
        f"  Register {n_reg} (harmonic {harmonic_number}x): "
        f"TMM = {f_ov:.2f} Hz,  ideal = {f_ov_ideal:.2f} Hz,  "
        f"err_vs_ideal = {ov_err_ideal:+.1f} cents,  "
        f"err_vs_corrected = {ov_err_corr:+.1f} cents"
    )
    report(
        f"Register {n_reg} within 15 cents of ideal",
        abs(ov_err_ideal) < 15.0,
        f"{ov_err_ideal:+.1f} cents",
    )
    report(
        f"Register {n_reg} within 5 cents of end-corrected",
        abs(ov_err_corr) < 5.0,
        f"{ov_err_corr:+.1f} cents",
    )


# =========================================================================
# Test 2 -- 6-hole chalumeau, bell-first ascending fingerings
# =========================================================================
print()
print("=" * 60)
print("TEST 2: 6-hole chalumeau -- bell-first ascending fingerings")
print("=" * 60)

L2 = 300.0       # mm
R2 = 7.25        # mm

# Place 6 holes.  Positions measured from reed end (pos 0 = reed, pos L = bell).
# Hole nearest bell opened first -> smallest pitch rise.
hole_positions = [150.0, 165.0, 180.0, 195.0, 210.0, 225.0]
hole_radius = 2.5   # mm (small holes for a chalumeau)
hole_chimney = 3.0  # mm

n_holes = len(hole_positions)

net2 = AcousticNetwork(
    segments=[Segment(length=L2, radius_in=R2, radius_out=R2)],
    ports=[
        Port(position=p, radius=hole_radius, length=hole_chimney)
        for p in hole_positions
    ],
    boundary_reed=Boundary(type=BoundaryType.REED, excitation=ExcitationType.REED),
    boundary_bell=Boundary(type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=L2),
)

# Build bell-first ascending fingering sequence:
#   all closed, then open last hole (nearest bell), then last-1, etc.
fingering_names = []
fingering_sets = []
for k in range(n_holes + 1):
    states = ["closed"] * n_holes
    for i in range(k):
        states[n_holes - 1 - i] = "open"  # bell-first (last index = nearest bell)
    fingering_sets.append(states)
    n_open = sum(1 for s in states if s == "open")
    fingering_names.append(f"open-{n_open}" if n_open > 0 else "all-closed")

# Target wavelengths: start near 4L for fundamental, adjust downward as holes open
base_wl = 4.0 * L2
target_wavelengths = [base_wl / (1.0 + 0.02 * k) for k in range(n_holes + 1)]

# Use the TMMSolver wrapper
freqs = solver.compute_frequencies(net2, target_wavelengths, fingering_sets, n_register=1)

# Compute cents relative to all-closed
f0 = freqs[0]
print()
print(f"  {'Fingering':<14} {'Freq (Hz)':>10}  {'d cents':>8}  {'Holes open':>10}")
print(f"  {'-'*14} {'-'*10}  {'-'*8}  {'-'*10}")

prev_cents = 0.0
pitch_rises = True
for i, (name, f) in enumerate(zip(fingering_names, freqs)):
    cents = 1200.0 * math.log2(f / f0)
    n_open = sum(1 for s in fingering_sets[i] if s == "open")
    print(f"  {name:<14} {f:>10.2f}  {cents:>+8.1f}  {n_open:>10}")
    if i > 0 and cents <= prev_cents:
        pitch_rises = False
    prev_cents = cents

# Verify: each successive fingering should raise pitch
print()
report("Pitch rises with each bell-first hole opening", pitch_rises)

# Verify: fundamental is in reasonable range for a 300mm closed pipe
f_expected_low = c / (4.0 * (L2 + 10.0))  # closed pipe + generous end correction
f_expected_high = c / (2.0 * L2)           # open pipe
report(
    f"All-closed fundamental in range ({f_expected_low:.0f} - {f_expected_high:.0f} Hz)",
    f_expected_low <= f0 <= f_expected_high,
    f"f0 = {f0:.2f} Hz",
)

# Verify monotonic: cents should increase monotonically
cents_values = [1200.0 * math.log2(f / f0) for f in freqs]
monotonic = all(cents_values[i] > cents_values[i - 1] for i in range(1, len(cents_values)))
report("Frequencies are monotonically increasing", monotonic)

# Verify: total pitch rise from all-closed to all-open is reasonable (typically 200-700 cents for 6 holes)
total_rise = cents_values[-1]
report(
    f"Total pitch rise 0->6 open in plausible range (100-900 cents)",
    100.0 < total_rise < 900.0,
    f"{total_rise:.1f} cents",
)

# Cross-check: also compute directly via TMMInstrument to confirm wrapper matches
print()
print("  Cross-check: direct TMMInstrument (bypassing TMMSolver wrapper)")
inst = solver.from_network(net2)
direct_freqs = inst.compute_fingered_frequencies(target_wavelengths, fingering_sets, n_register=1)
max_wrapper_diff = max(abs(a - b) for a, b in zip(freqs, direct_freqs))
report(
    "TMMSolver wrapper matches direct TMMInstrument (max diff < 0.01 Hz)",
    max_wrapper_diff < 0.01,
    f"max diff = {max_wrapper_diff:.6f} Hz",
)


# =========================================================================
# Summary
# =========================================================================
print()
print("=" * 60)
if PASS:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
print("=" * 60)
