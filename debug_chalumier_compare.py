"""Check if the closedTop=True issue is in the model or the search"""
import sys, math, numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import TMMInstrument, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Pure cone: 4mm to 16mm over 661mm
L = 661.44
positions = np.linspace(0, L, 50).tolist()
diameters = np.linspace(4.0, 16.0, 50).tolist()
outer = np.linspace(25.0, 70.0, 50).tolist()

print("=== Phase at various wavelengths, closedTop=True ===")
inst_ct = TMMInstrument(positions, diameters, outer, [], [], [],
                         closed_top=True, cone_step=0.125)

# Check phase at many wavelengths to map the resonance structure
print("  Testing closedTop=True, no holes:")
for wl in [500, 1000, 1500, 2000, 2500, 3000, 3188, 3500, 4000, 5000, 8000, 15000]:
    phase = inst_ct.resonance_phase(wl, [])
    print(f"    wl={wl:6.0f}mm  f={c/wl:7.1f}Hz  phase={phase:.4f}")

print("\n=== Phase at various wavelengths, closedTop=False ===")
inst_ot = TMMInstrument(positions, diameters, outer, [], [], [],
                         closed_top=False, cone_step=0.125)

for wl in [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 8000, 15000]:
    phase = inst_ot.resonance_phase(wl, [])
    print(f"    wl={wl:6.0f}mm  f={c/wl:7.1f}Hz  phase={phase:.4f}")

# Analytical expectations for a cone:
# closedTop=False (open-open): phase = 1 + 2L/wl, resonance at phase=n -> wl = 2L/(n-1)
# closedTop=True (closed-open via TMM): phase = 0.5 + 2L/wl, resonance at phase=n -> wl = 2L/(n-0.5)
#
# But a REAL cone with closed small end has resonances at f = nc/(2L) for ALL n
# This is the SAME as open-open! A closed cone resonates like an open-open pipe.

print("\n=== Analytical vs TMM for cone ===")
print(f"  Cone length: {L}mm")
print(f"  Analytical (true cone, closed small end): f = nc/(2L)")
for n in [1, 2, 3, 4]:
    f_ana = n * c / (2 * L)
    print(f"    n={n}: f={f_ana:.1f}Hz  wl={c/f_ana:.0f}mm")

print(f"\n  TMM closedTop=False (open-open): phase = 1 + 2L/wl -> wl = 2L/(n-1)")
for n in [2, 3, 4, 5]:
    wl = 2 * L / (n - 1)
    f = c / wl
    print(f"    n_reg={n}: f={f:.1f}Hz  (same as analytical n={n-1})")

print(f"\n  TMM closedTop=True (closed-open): phase = 0.5 + 2L/wl -> wl = 2L/(n-0.5)")
for n in [1, 2, 3, 4]:
    wl = 2 * L / (n - 0.5)
    f = c / wl
    print(f"    n_reg={n}: f={f:.1f}Hz  (odd harmonics only: {(2*n-1)*c/(4*L):.1f}Hz)")

# Now test: does find_resonance actually find the right values?
print("\n=== Direct find_resonance test ===")
# For closedTop=False, n_reg=2 should give f = c/L = 523Hz
wl = inst_ot.find_resonance(c/300, [], n_register=2)
f = c / wl
print(f"  closedTop=False, n_reg=2: wl={wl:.0f}mm f={f:.1f}Hz (expected {c/L:.1f}Hz)")

# For closedTop=True, n_reg=1 should give f = c/(4L) = 130Hz
# (first odd harmonic of closed-open pipe)
wl2 = inst_ct.find_resonance(c/100, [], n_register=1)
f2 = c / wl2
print(f"  closedTop=True, n_reg=1: wl={wl2:.0f}mm f={f2:.1f}Hz (expected {c/(4*L):.1f}Hz)")

# The REAL question: does closedTop=True give correct cone harmonics?
# A true closed cone should give f = nc/(2L), NOT (2n-1)c/(4L)
# If the TMM gives (2n-1)c/(4L) for closedTop=True, the TMM is modeling a
# CYLINDER, not a cone. The stepped-cylinder approximation may not capture
# the cone's acoustic behavior correctly.

print("\n=== KEY QUESTION: Does stepped-cylinder correctly model a closed cone? ===")
print(f"  For a true cone with closed small end:")
print(f"    f1 = c/(2L) = {c/(2*L):.1f}Hz")
print(f"    f2 = 2c/(2L) = {c/L:.1f}Hz")
print(f"    f3 = 3c/(2L) = {3*c/(2*L):.1f}Hz")
print(f"  For a cylindrical closed-open pipe of same length:")
print(f"    f1 = c/(4L) = {c/(4*L):.1f}Hz")
print(f"    f2 = 3c/(4L) = {3*c/(4*L):.1f}Hz")
print(f"    f3 = 5c/(4L) = {5*c/(4*L):.1f}Hz")
print()
print(f"  TMM closedTop=False n_reg=2 -> phase=2: f = {2*c/(2*L):.1f}Hz = c/L (matches cone f1)")
print(f"  TMM closedTop=False n_reg=3 -> phase=3: f = {c/L:.1f}Hz (matches cone f2)")
print(f"  TMM closedTop=True  n_reg=1 -> phase=1: f = ??? (see above)")
print(f"  TMM closedTop=True  n_reg=2 -> phase=2: f = ??? (see above)")
