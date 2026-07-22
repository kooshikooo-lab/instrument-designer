"""
Meaningful bore profile experiments for alto sax Eb.

Key insight from research:
- eval_all() subtracts median → only measures SCALE EVENNESS (always 0.00c)
- Bore shape affects ABSOLUTE TUNING and MULTI-REGISTER behavior
- Lefebvre (2011): straight cone fails for octave matching

So we test:
1. Absolute tuning error (no median subtraction)
2. Multi-register harmonicity (reg 1 vs reg 2)
3. Bore shape effects on BOTH
4. Simultaneous bore+hole optimization
"""
import numpy as np
import math
import time
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from benchmark_all import INSTRUMENTS, sequential, sequential_refined
from scipy.optimize import minimize as sp_min

c = SPEED_OF_SOUND


def eval_absolute(radii, bore_length, hp, hd, hl, cfg, n_reg=1):
    """Evaluate with cumulative fingering, NO median subtraction.
    Returns per-note cents errors and RMS."""
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [c / f for f in cfg["targets"]]
    fingerings = cfg["fingerings"]
    freqs = []
    for target_wl, fing in zip(tw, fingerings):
        wl = inst.find_resonance(target_wl, fing, n_register=n_reg)
        freqs.append(inst.frequency_from_wavelength(wl))
    cents = []
    for a, t in zip(freqs, cfg["targets"]):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)
    return cents


def eval_evenness(radii, bore_length, hp, hd, hl, cfg, n_reg=1):
    """Scale evenness (like eval_all but explicit)."""
    cents = eval_absolute(radii, bore_length, hp, hd, hl, cfg, n_reg)
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    return float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))


def eval_abs_rms(radii, bore_length, hp, hd, hl, cfg, n_reg=1):
    """Absolute RMS error (no median removal)."""
    cents = eval_absolute(radii, bore_length, hp, hd, hl, cfg, n_reg)
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    return float(np.sqrt(np.mean(ca ** 2)))


# ============================================================================
# 1. Bore shape vs absolute tuning + harmonicity
# ============================================================================

def bore_shape_experiment():
    """Compare bore shapes on absolute tuning and evenness."""
    print("\n" + "="*70)
    print("1. BORE SHAPE — Absolute tuning + evenness (cumulative fingering)")
    print("="*70)

    cfg = INSTRUMENTS["alto_sax_Eb"]
    closed_top = cfg["closed_top"]
    n_reg = 2  # open-open: register 2

    # Get optimized hole positions
    rms_seq, L_seq, hp_seq, t_seq = sequential(cfg)
    print(f"\n  Sequential baseline: RMS_evenness={rms_seq:.2f}c, L={L_seq:.0f}mm")
    print(f"  Hole positions: {[f'{p:.0f}' for p in hp_seq]}")

    n_h = len(hp_seq)
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h
    n_cp = 6

    # Different bore shapes to test
    shapes = {}

    # Cylindrical
    r = cfg["bore_radius"]
    shapes["Cylindrical"] = np.full(n_cp, r)

    # Conical (+20% from mouthpiece to bell)
    shapes["Cone+20%"] = np.linspace(r * 0.8, r * 1.2, n_cp)

    # Inverse cone
    shapes["Inv.Cone"] = np.linspace(r * 1.2, r * 0.8, n_cp)

    # Bulge (wider middle)
    shapes["Bulge"] = r * (1.0 + 0.15 * np.sin(np.linspace(0, math.pi, n_cp)))

    # Narrow middle
    shapes["Pinch"] = r * (1.0 - 0.10 * np.sin(np.linspace(0, math.pi, n_cp)))

    # L-BFGS-B optimized
    radii_init = np.full(n_cp, r)
    def obj(x):
        return eval_abs_rms(np.maximum(x, 3.0), L_seq, hp_seq, hd, hl, cfg, n_reg)
    res = sp_min(obj, radii_init, method='L-BFGS-B',
                 bounds=[(3.0, 15.0)] * n_cp,
                 options={"maxiter": 300, "ftol": 1e-10})
    shapes["L-BFGS-B abs"] = np.maximum(res.x, 3.0)

    # Also optimize for evenness
    def obj_even(x):
        return eval_evenness(np.maximum(x, 3.0), L_seq, hp_seq, hd, hl, cfg, n_reg)
    res2 = sp_min(obj_even, radii_init, method='L-BFGS-B',
                  bounds=[(3.0, 15.0)] * n_cp,
                  options={"maxiter": 300, "ftol": 1e-10})
    shapes["L-BFGS-B even"] = np.maximum(res2.x, 3.0)

    print(f"\n  {'Shape':<18} {'Abs RMS':>8} {'Even RMS':>9} {'Med err':>8} {'Profile (radii mm)'}")
    print(f"  {'-'*18} {'-'*8} {'-'*9} {'-'*8} {'-'*35}")

    for name, radii in shapes.items():
        cents = eval_absolute(radii, L_seq, hp_seq, hd, hl, cfg, n_reg)
        ca = np.array(cents)
        if np.any(np.abs(ca) > 1e5):
            print(f"  {name:<18} {'FAIL':>8}")
            continue
        abs_rms = float(np.sqrt(np.mean(ca ** 2)))
        med = float(np.median(ca))
        even = float(np.sqrt(np.mean((ca - med) ** 2)))
        profile = " ".join(f"{x:.1f}" for x in radii)
        print(f"  {name:<18} {abs_rms:>8.1f} {even:>9.1f} {med:>+8.1f} {profile}")

    # Show per-note errors for best shape
    print(f"\n  Per-note errors (L-BFGS-B abs, reg {n_reg}):")
    best_radii = shapes["L-BFGS-B abs"]
    cents = eval_absolute(best_radii, L_seq, hp_seq, hd, hl, cfg, n_reg)
    for name, freq, ct in zip(cfg["names"], cfg["targets"], cents):
        print(f"    {name:>5} ({freq:.1f} Hz): {ct:>+8.1f} cents")

    return shapes


# ============================================================================
# 2. Multi-register: both octaves
# ============================================================================

def multi_register_experiment():
    """Test absolute tuning in both registers."""
    print("\n" + "="*70)
    print("2. MULTI-REGISTER — Alto sax (reg 1 + reg 2)")
    print("="*70)

    cfg = INSTRUMENTS["alto_sax_Eb"]
    n_reg = 2

    rms_seq, L_seq, hp_seq, _ = sequential(cfg)
    n_h = len(hp_seq)
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h
    n_cp = 6
    radii = np.full(n_cp, cfg["bore_radius"])

    print(f"\n  Bore: L={L_seq:.0f}mm, r={cfg['bore_radius']:.1f}mm")
    print(f"  Holes: {n_h}")

    for reg in [1, 2]:
        print(f"\n  --- Register {reg} ---")
        cents = eval_absolute(radii, L_seq, hp_seq, hd, hl, cfg, reg)
        ca = np.array(cents)
        if np.any(np.abs(ca) > 1e5):
            print(f"    All notes FAIL in register {reg}")
            continue
        abs_rms = float(np.sqrt(np.mean(ca ** 2)))
        med = float(np.median(ca))
        even = float(np.sqrt(np.mean((ca - med) ** 2)))
        print(f"    Abs RMS: {abs_rms:.1f}c | Even RMS: {even:.1f}c | Offset: {med:+.1f}c")
        for name, freq, ct in zip(cfg["names"], cfg["targets"], cents):
            print(f"      {name:>5} ({freq:.1f} Hz): {ct:>+8.1f} cents")

    # Now optimize bore profile to minimize BOTH registers simultaneously
    print(f"\n  --- Multi-register optimization ---")
    def obj_multi(x):
        radii = np.maximum(x[:n_cp], 3.0)
        L = x[n_cp]
        r1 = eval_abs_rms(radii, L, hp_seq, hd, hl, cfg, 1)
        r2 = eval_abs_rms(radii, L, hp_seq, hd, hl, cfg, 2)
        return (r1 + r2) / 2.0  # Equal weight both registers

    x0 = np.concatenate([radii, [L_seq]])
    bounds = [(3.0, 15.0)] * n_cp + [(L_seq * 0.8, L_seq * 1.2)]
    res = sp_min(obj_multi, x0, method='L-BFGS-B', bounds=bounds,
                 options={"maxiter": 500, "ftol": 1e-10})
    radii_m = np.maximum(res.x[:n_cp], 3.0)
    L_m = res.x[n_cp]

    print(f"    Optimized bore: L={L_m:.0f}mm, radii={' '.join(f'{x:.1f}' for x in radii_m)}")

    for reg in [1, 2]:
        cents = eval_absolute(radii_m, L_m, hp_seq, hd, hl, cfg, reg)
        ca = np.array(cents)
        if np.any(np.abs(ca) > 1e5):
            print(f"    Reg {reg}: FAIL")
            continue
        abs_rms = float(np.sqrt(np.mean(ca ** 2)))
        med = float(np.median(ca))
        even = float(np.sqrt(np.mean((ca - med) ** 2)))
        print(f"    Reg {reg}: Abs RMS={abs_rms:.1f}c | Even={even:.1f}c | Offset={med:+.1f}c")
        for name, freq, ct in zip(cfg["names"], cfg["targets"], cents):
            print(f"      {name:>5}: {ct:>+8.1f} cents")


# ============================================================================
# 3. Robustness with cumulative fingering (the real test)
# ============================================================================

def robustness_cumulative():
    """Test manufacturing tolerance with the REAL fingering model."""
    print("\n" + "="*70)
    print("3. ROBUSTNESS — Cumulative fingering (real playing)")
    print("="*70)

    cfg = INSTRUMENTS["alto_sax_Eb"]
    n_reg = 2

    rms_seq, L_seq, hp_seq, _ = sequential(cfg)
    n_h = len(hp_seq)
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h
    n_cp = 6
    radii = np.full(n_cp, cfg["bore_radius"])

    # Baseline with cumulative fingering
    cents_base = eval_absolute(radii, L_seq, hp_seq, hd, hl, cfg, n_reg)
    ca = np.array(cents_base)
    base_rms = float(np.sqrt(np.mean(ca ** 2)))
    base_even = float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))
    print(f"\n  Baseline: Abs RMS={base_rms:.1f}c, Even RMS={base_even:.1f}c")

    noise_levels = [0.0, 0.5, 1.0, 2.0, 5.0]
    n_trials = 30
    np.random.seed(42)

    print(f"\n  {'Noise':>6} {'MeanAbs':>8} {'MaxAbs':>8} {'MeanEven':>9} {'MaxEven':>9}")
    print(f"  {'-'*6} {'-'*8} {'-'*8} {'-'*9} {'-'*9}")

    for noise in noise_levels:
        abs_vals, even_vals = [], []
        for _ in range(n_trials):
            hp_noisy = [p + np.random.normal(0, noise) for p in hp_seq]
            L_noisy = L_seq + np.random.normal(0, noise * 0.5)
            try:
                cents = eval_absolute(radii, L_noisy, hp_noisy, hd, hl, cfg, n_reg)
                ca = np.array(cents)
                if not np.any(np.abs(ca) > 1e5):
                    abs_vals.append(float(np.sqrt(np.mean(ca ** 2))))
                    even_vals.append(float(np.sqrt(np.mean((ca - np.median(ca)) ** 2))))
            except:
                pass

        if abs_vals:
            print(f"  {noise:>4.1f}mm {np.mean(abs_vals):>8.1f} {max(abs_vals):>8.1f} "
                  f"{np.mean(even_vals):>9.1f} {max(even_vals):>9.1f}")
        else:
            print(f"  {noise:>4.1f}mm    FAIL")


# ============================================================================
# 4. Simultaneous bore + hole optimization
# ============================================================================

def simultaneous_optimization():
    """Optimize bore shape + hole positions together."""
    print("\n" + "="*70)
    print("4. SIMULTANEOUS — Bore + holes together (cumulative fingering)")
    print("="*70)

    cfg = INSTRUMENTS["alto_sax_Eb"]
    n_reg = 2
    n_cp = 6

    # Start from sequential result
    rms_seq, L_seq, hp_seq, _ = sequential(cfg)
    n_h = len(hp_seq)
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h

    print(f"\n  Starting from sequential: L={L_seq:.0f}mm, {n_h} holes")
    print(f"  Initial holes: {[f'{p:.0f}' for p in hp_seq]}")

    # Combined cost: absolute RMS in register 2
    GAP = 5.0
    def obj_all(x):
        radii = np.maximum(x[:n_cp], 3.0)
        L = x[n_cp]
        hp = list(x[n_cp + 1:])

        # Enforce ordering
        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + GAP:
                return 1e6
        if hp[0] < 20 or hp[-1] > L - 20:
            return 1e6

        return eval_abs_rms(radii, L, hp, hd, hl, cfg, n_reg)

    x0 = np.concatenate([
        np.full(n_cp, cfg["bore_radius"]),
        [L_seq],
        hp_seq,
    ])
    bounds = ([(3.0, 15.0)] * n_cp +
              [(L_seq * 0.8, L_seq * 1.3)] +
              [(20, L_seq * 1.3 - 20)] * n_h)

    print(f"\n  Optimizing {n_cp + 1 + n_h} variables...")
    t0 = time.time()
    res = sp_min(obj_all, x0, method='L-BFGS-B', bounds=bounds,
                 options={"maxiter": 1000, "ftol": 1e-12})
    dt = time.time() - t0

    radii_opt = np.maximum(res.x[:n_cp], 3.0)
    L_opt = res.x[n_cp]
    hp_opt = list(res.x[n_cp + 1:])

    print(f"  Done in {dt:.1f}s, cost={res.fun:.4f}")
    print(f"  Bore: L={L_opt:.0f}mm")
    print(f"  Radii: {' '.join(f'{x:.1f}' for x in radii_opt)}")
    print(f"  Holes: {[f'{p:.0f}' for p in hp_opt]}")

    # Evaluate
    for reg in [1, 2]:
        cents = eval_absolute(radii_opt, L_opt, hp_opt, hd, hl, cfg, reg)
        ca = np.array(cents)
        if np.any(np.abs(ca) > 1e5):
            print(f"  Reg {reg}: FAIL")
            continue
        abs_rms = float(np.sqrt(np.mean(ca ** 2)))
        med = float(np.median(ca))
        even = float(np.sqrt(np.mean((ca - med) ** 2)))
        print(f"  Reg {reg}: Abs RMS={abs_rms:.1f}c, Even={even:.1f}c, Offset={med:+.1f}c")
        for name, freq, ct in zip(cfg["names"], cfg["targets"], cents):
            print(f"    {name:>5}: {ct:>+8.1f} cents")


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    t0 = time.time()
    bore_shape_experiment()
    multi_register_experiment()
    robustness_cumulative()
    simultaneous_optimization()
    print(f"\n{'='*70}")
    print(f"Total time: {time.time() - t0:.1f}s")
    print(f"{'='*70}")
