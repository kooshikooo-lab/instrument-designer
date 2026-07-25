"""Debug: check what the TMM instrument is actually computing."""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
L = 330.0
r = 7.8
radii = np.full(8, r)

# Test 1: bare pipe, no holes, open-open
inst = tmm_instrument_from_radii(
    radii, L, [], [], [], 24.0, closed_top=False, cone_step=0.5,
)
print("=== Bare pipe, open-open, L=330mm ===")
for n_reg in [1, 2, 3]:
    try:
        wl = inst.find_resonance(c / 500.0, [], n_reg)
        f = inst.frequency_from_wavelength(wl)
        print(f"  n_register={n_reg}: {f:.1f} Hz (expected: {c/(2*L*(n_reg-1)):.1f} Hz for n={n_reg})")
    except Exception as e:
        print(f"  n_register={n_reg}: FAILED ({e})")

# Test 2: bare pipe, no holes, closed-open
inst2 = tmm_instrument_from_radii(
    radii, L, [], [], [], 24.0, closed_top=True, cone_step=0.5,
)
print("\n=== Bare pipe, closed-open, L=330mm ===")
for n_reg in [1, 2, 3]:
    try:
        wl = inst2.find_resonance(c / 500.0, [], n_reg)
        f = inst2.frequency_from_wavelength(wl)
        print(f"  n_register={n_reg}: {f:.1f} Hz")
    except Exception as e:
        print(f"  n_register={n_reg}: FAILED ({e})")

# Test 3: check resonance_phase directly
print("\n=== Phase scan for open-open pipe ===")
for wl in [600, 800, 1000, 1200, 1400, 1600]:
    phase = inst.resonance_phase(wl, [])
    print(f"  wl={wl}mm: phase={phase:.4f}")

print("\n=== Phase scan for closed-open pipe ===")
for wl in [1000, 1200, 1300, 1400, 1500, 1600]:
    phase = inst2.resonance_phase(wl, [])
    print(f"  wl={wl}mm: phase={phase:.4f}")

# Test 4: with one hole open
print("\n=== One hole open, open-open pipe ===")
hp = [165.0]  # middle of bore
hd = [8.0]
hl = [4.0]
inst3 = tmm_instrument_from_radii(
    radii, L, hp, hd, hl, 24.0, closed_top=False, cone_step=0.5,
)
for wl in [400, 600, 800, 1000]:
    phase = inst3.resonance_phase(wl, ["O"])
    print(f"  wl={wl}mm: phase={phase:.4f}")
try:
    wl = inst3.find_resonance(c / 500.0, ["O"], 1)
    f = inst3.frequency_from_wavelength(wl)
    print(f"  Resonance: {f:.1f} Hz")
except Exception as e:
    print(f"  FAILED: {e}")
