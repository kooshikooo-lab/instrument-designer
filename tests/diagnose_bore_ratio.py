"""Diagnose why alto sax and xaphoon fail while soprano sax works.

Key differences to check:
1. Bore diameter ratio (bore_radius / hole_diameter)
2. Number of notes vs bore length
3. Hole spacing relative to wavelength
4. Whether the TMM model handles larger bores correctly
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

INSTRUMENTS = {
    "soprano_sax": {
        "closed_top": False,
        "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
        "bore_radius": 6.0, "outer_diameter": 20.0,
        "hole_diameter": 6.5, "hole_length": 3.0,
    },
    "xaphoon": {
        "closed_top": False,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
        "bore_radius": 7.0, "outer_diameter": 20.0,
        "hole_diameter": 6.5, "hole_length": 3.0,
    },
    "alto_sax": {
        "closed_top": False,
        "targets": [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3],
        "bore_radius": 8.5, "outer_diameter": 26.0,
        "hole_diameter": 7.5, "hole_length": 3.5,
    },
}

for name, cfg in INSTRUMENTS.items():
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    
    bore_r = cfg["bore_radius"]
    hole_r = cfg["hole_diameter"] / 2
    fundamental = min(cfg["targets"])
    L_est = c / (2.0 * fundamental)
    wavelength_fund = c / fundamental
    
    print(f"  Bore radius:       {bore_r:.1f}mm")
    print(f"  Hole radius:       {hole_r:.1f}mm")
    print(f"  Ratio bore/hole:   {bore_r/hole_r:.2f}")
    print(f"  Fundamental:       {fundamental:.1f} Hz")
    print(f"  Wavelength:        {wavelength_fund:.0f}mm")
    print(f"  Est bore length:   {L_est:.0f}mm")
    print(f"  L/lambda ratio:    {L_est/wavelength_fund:.2f}")
    print(f"  Note span:         {cfg['targets'][-1]/cfg['targets'][0]:.2f}x ({1200*math.log2(cfg['targets'][-1]/cfg['targets'][0]):.0f}c)")
    
    # Test: place one hole at different positions, measure frequency shift
    bore_length = L_est
    print(f"\n  Single-hole sweep (bore L={bore_length:.0f}mm):")
    
    # All-closed resonance
    inst_closed = tmm_instrument_from_radii(
        np.full(8, bore_r), bore_length, [], [], [],
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    wl_closed = inst_closed.find_resonance(c / fundamental, [], 2)
    f_closed = inst_closed.frequency_from_wavelength(wl_closed)
    print(f"    All-closed freq:  {f_closed:.1f} Hz (target: {fundamental:.1f})")
    
    # Sweep hole position for the highest note
    target_high = cfg["targets"][-1]
    print(f"    Sweeping hole for {target_high:.1f} Hz:")
    
    positions = np.linspace(30, bore_length - 30, 20)
    for pos in positions:
        try:
            inst = tmm_instrument_from_radii(
                np.full(8, bore_r), bore_length,
                [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                cfg["outer_diameter"], cfg["closed_top"], 0.5,
            )
            wl = inst.find_resonance(c / target_high, ["open"], 2)
            f = inst.frequency_from_wavelength(wl)
            err = 1200 * math.log2(f / target_high)
            marker = " <-- TARGET" if abs(err) < 10 else ""
            print(f"      pos={pos:6.1f}mm  f={f:7.1f}Hz  err={err:+7.1f}c{marker}")
        except:
            print(f"      pos={pos:6.1f}mm  FAILED")
