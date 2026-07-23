"""Diagnose TMM model accuracy for different bore sizes.

Compare: all-closed resonance frequencies vs analytic prediction.
Check: does the stepped-cylinder approximation degrade with larger bores?
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

# Test: same cone angle, different scales
# Soprano sax: half-angle ~1.74°, r_in=4.6mm (Szwarcberg 2025)
# Alto sax: half-angle ~3°, r_in=6.25mm (Lefebvre reference)
# Xaphoon: cylindrical r=7mm

CONFS = [
    ("Soprano sax (small)", 4.6, 1.74, 371, 466.2, 20.0, False),
    ("Alto sax (medium)", 6.25, 3.0, 556, 311.1, 26.0, False),
    ("Xaphoon (large cyl)", 7.0, 0.0, 662, 261.6, 20.0, False),
    ("Bass clarinet (large)", 9.0, 0.0, 950, 116.5, 28.0, True),
]

for name, r_in, half_angle_deg, L_target, f_target, od, closed_top in CONFS:
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    half_angle = math.radians(half_angle_deg)
    
    # Create cone bore: r_out = r_in + L * tan(half_angle)
    r_out = r_in + L_target * math.tan(half_angle)
    n_steps = 20
    
    # Interpolate radii along bore
    if half_angle_deg == 0:
        radii = np.full(n_steps, r_in)
    else:
        radii = np.linspace(r_in, r_out, n_steps)
    
    print(f"  r_in={r_in:.1f}mm r_out={r_out:.1f}mm L={L_target}mm")
    print(f"  Bore radii: {[f'{r:.1f}' for r in radii]}")
    
    # Test: find resonance for all-closed (no holes)
    n_reg = 1 if closed_top else 2
    inst = tmm_instrument_from_radii(
        radii, L_target, [], [], [], od, closed_top, 0.5,
    )
    
    # Find resonance near target
    wl_target = c / f_target
    try:
        wl = inst.find_resonance(wl_target, [], n_reg)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / f_target)
        print(f"  Target: {f_target:.1f} Hz (wl={wl_target:.0f}mm)")
        print(f"  Found:  {f:.1f} Hz (wl={wl:.0f}mm) err={err:+.1f}c")
    except Exception as e:
        print(f"  FAILED: {e}")
    
    # Also find several resonances
    print(f"\n  Full resonance spectrum (n_register 1-5):")
    for n in range(1, 6):
        try:
            # Search near analytic estimate
            if closed_top:
                wl_est = 4 * L_target / (2*n - 1)
            else:
                wl_est = 2 * L_target / n
            wl = inst.find_resonance(wl_est, [], n)
            f = inst.frequency_from_wavelength(wl)
            print(f"    n={n}: f={f:.1f} Hz  wl={wl:.0f}mm  "
                  f"(analytic wl~{wl_est:.0f}mm)")
        except:
            print(f"    n={n}: FAILED")
    
    # Check: what does the TMM impedance look like?
    print(f"\n  Impedance sweep 50-2000 Hz:")
    for f_test in [100, 200, 300, 500, 800, 1000, 1500]:
        try:
            wl_test = c / f_test
            wl = inst.find_resonance(wl_test, [], n_reg)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200 * math.log2(f / f_test))
            if err < 100:
                print(f"    Near {f_test}Hz -> found {f:.1f}Hz ({err:.1f}c)")
        except:
            pass
