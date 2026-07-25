"""
Diagnose refinement bounds: are they too tight for xaphoon?
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND


def eval_all(radii, bore_length, hp, hd, hl, cfg):
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [c / f for f in cfg["targets"]]
    n_reg = 1 if cfg["closed_top"] else 2
    freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], n_reg)
    cents = []
    for a, t in zip(freqs, cfg["targets"]):
        cents.append(1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10)
    return float(np.sqrt(np.mean(np.array(cents) ** 2)))


configs = {
    "soprano_sax": {
        "bore_length_mm": 379,
        "bore_radius": 6.0,
        "outer_diameter": 20.0,
        "closed_top": False,
        "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
        "fingerings": [
            ["closed"] * 7,
            ["open", "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "open", "closed"],
        ],
        "hp": [58, 93, 105, 138, 164, 189],
    },
    "xaphoon": {
        "bore_length_mm": 622,
        "bore_radius": 7.0,
        "outer_diameter": 20.0,
        "closed_top": False,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
        "fingerings": [
            ["closed"] * 7,
            ["open", "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "open", "closed"],
        ],
        "hp": [101, 169, 457, 472, 487, 502],
    },
}

for name, cfg in configs.items():
    L = cfg["bore_length_mm"]
    radii = np.full(6, cfg["bore_radius"])
    hp = cfg["hp"]
    n_h = len(hp)
    hd = [6.5] * n_h
    hl = [3.0] * n_h

    print(f"\n{'='*60}")
    print(f"{name} (L={L}mm, r={cfg['bore_radius']}mm)")
    print(f"{'='*60}")

    rms = eval_all(radii, L, hp, hd, hl, cfg)
    print(f"  Current RMS: {rms:.1f}c")
    print(f"  Hole positions: {hp}")

    GAP = 5.0
    hole_lo, hole_hi = [0.0]*n_h, [0.0]*n_h
    for i in range(n_h):
        hole_lo[i] = (hp[i-1] + GAP) if i > 0 else 30.0
        hole_hi[i] = (hp[i+1] - GAP) if i < n_h-1 else (L*1.3 - 30.0)
        hole_lo[i] = max(hole_lo[i], hp[i] - 20)
        hole_hi[i] = min(hole_hi[i], hp[i] + 20)
        if hole_lo[i] > hole_hi[i]:
            hole_lo[i] = hp[i] - 1
            hole_hi[i] = hp[i] + 1

    print(f"\n  Refinement bounds (±20mm clamp):")
    for i in range(n_h):
        span = hole_hi[i] - hole_lo[i]
        print(f"    Hole {i}: pos={hp[i]:6.0f}mm  bounds=[{hole_lo[i]:6.0f}, {hole_hi[i]:6.0f}]  span={span:.0f}mm")

    # Test: what happens if we double the bounds to ±40mm?
    hole_lo2, hole_hi2 = [0.0]*n_h, [0.0]*n_h
    for i in range(n_h):
        hole_lo2[i] = (hp[i-1] + GAP) if i > 0 else 30.0
        hole_hi2[i] = (hp[i+1] - GAP) if i < n_h-1 else (L*1.3 - 30.0)
        hole_lo2[i] = max(hole_lo2[i], hp[i] - 40)
        hole_hi2[i] = min(hole_hi2[i], hp[i] + 40)
        if hole_lo2[i] > hole_hi2[i]:
            hole_lo2[i] = hp[i] - 1
            hole_hi2[i] = hp[i] + 1

    print(f"\n  Wider bounds (±40mm clamp):")
    for i in range(n_h):
        span = hole_hi2[i] - hole_lo2[i]
        print(f"    Hole {i}: pos={hp[i]:6.0f}mm  bounds=[{hole_lo2[i]:6.0f}, {hole_hi2[i]:6.0f}]  span={span:.0f}mm")

    # Test: what happens if we use WIDE bounds (±100mm or more)?
    hole_lo3, hole_hi3 = [0.0]*n_h, [0.0]*n_h
    for i in range(n_h):
        hole_lo3[i] = (hp[i-1] + GAP) if i > 0 else 20.0
        hole_hi3[i] = (hp[i+1] - GAP) if i < n_h-1 else (L - 20.0)
        # No ±20mm clamp!

    print(f"\n  Wide bounds (no clamp, just non-crossing):")
    for i in range(n_h):
        span = hole_hi3[i] - hole_lo3[i]
        print(f"    Hole {i}: pos={hp[i]:6.0f}mm  bounds=[{hole_lo3[i]:6.0f}, {hole_hi3[i]:6.0f}]  span={span:.0f}mm")

    # Key test: what's the RMS if we optimize holes with WIDE bounds?
    from scipy.optimize import minimize as sp_min
    def obj_holes(x):
        return eval_all(radii, L, x.tolist(), hd, hl, cfg)
    hole_bounds_wide = [(hole_lo3[i], hole_hi3[i]) for i in range(n_h)]
    r = sp_min(obj_holes, np.array(hp, dtype=float), method='L-BFGS-B',
                bounds=hole_bounds_wide,
                options={"maxiter": 300, "ftol": 1e-10})
    rms_wide = r.fun
    new_hp = r.x.tolist()
    print(f"\n  Wide-bounds hole optimization: RMS={rms_wide:.1f}c")
    print(f"  New positions: {[f'{p:.0f}' for p in new_hp]}")
    print(f"  Old positions: {hp}")

    # Also test: bore radii with wider bounds
    rad_bounds_wide = [(3.0, 20.0)] * 6
    def obj_all_wide(x):
        L_i = x[0]
        rad_i = np.maximum(x[1:7], 3.0)
        hp_i = x[7:7+n_h]
        return eval_all(rad_i, L_i, hp_i.tolist(), hd, hl, cfg)
    x0 = np.concatenate([[L], radii, np.array(new_hp)])
    all_bounds_wide = [(L*0.8, L*1.2)] + rad_bounds_wide + hole_bounds_wide
    try:
        r2 = sp_min(obj_all_wide, x0, method='L-BFGS-B',
                    bounds=all_bounds_wide,
                    options={"maxiter": 500, "ftol": 1e-10})
        final_L = r2.x[0]
        final_radii = np.maximum(r2.x[1:7], 3.0)
        final_hp = r2.x[7:7+n_h].tolist()
        rms_final = eval_all(final_radii, final_L, final_hp, hd, hl, cfg)
        print(f"\n  Full optimization (wide bounds): RMS={rms_final:.1f}c")
        print(f"  L={final_L:.0f}mm  radii={[f'{r:.1f}' for r in final_radii]}")
        print(f"  holes={[f'{p:.0f}' for p in final_hp]}")
    except Exception as e:
        print(f"\n  Full optimization FAILED: {e}")
