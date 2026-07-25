"""Test: what if we remove the sequential ordering constraint for open-open?

Ernoult (2021) says each hole is independent. But our optimizer forces
holes to be placed in order (min_pos = prev + 10mm). What if we allow
holes to be placed anywhere, optimizing all positions simultaneously?
"""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

XAPHOON = {
    "closed_top": False,
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
    "bore_radius": 7.0, "outer_diameter": 20.0,
    "hole_diameter": 6.5, "hole_length": 3.0,
    "fingerings": [
        ["closed"] * 7,
        ["open", "closed", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "open", "closed", "closed"],
        ["open", "open", "open", "open", "open", "open", "closed"],
    ],
}

ALTO_SAX = {
    "closed_top": False,
    "targets": [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3],
    "bore_radius": 8.5, "outer_diameter": 26.0,
    "hole_diameter": 7.5, "hole_length": 3.5,
    "fingerings": [
        ["closed"] * 7,
        ["open", "closed", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "closed", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "closed", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "closed", "closed", "closed"],
        ["open", "open", "open", "open", "open", "closed", "closed"],
        ["open", "open", "open", "open", "open", "open", "closed"],
    ],
}


def eval_all(radii, bore_length, hp, hd, hl, cfg):
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [c / f for f in cfg["targets"]]
    n_reg = 2
    freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], n_reg)
    cents = []
    for a, t in zip(freqs, cfg["targets"]):
        cents.append(1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10)
    return np.array(cents)


def eval_detail(radii, bore_length, hp, hd, hl, cfg):
    ca = eval_all(radii, bore_length, hp, hd, hl, cfg)
    return float(np.sqrt(np.mean(ca ** 2)))


def phase1_bore(cfg):
    """Optimize bore length for fundamental."""
    fundamental = min(cfg["targets"])
    bore_radii = np.full(8, cfg["bore_radius"])
    L_est = c / (2.0 * fundamental)
    
    def bore_obj(L):
        try:
            inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
                cfg["outer_diameter"], cfg["closed_top"], 0.5)
            wl = inst.find_resonance(c / fundamental, [], 2)
            f = inst.frequency_from_wavelength(wl)
            return abs(1200.0 * math.log2(f / fundamental))
        except: return 1e10
    
    r = sp_min(bore_obj, [L_est], method='L-BFGS-B',
               bounds=[(L_est * 0.7, L_est * 1.3)],
               options={"maxiter": 50, "ftol": 1e-8})
    return r.x[0]


def method_sequential(cfg):
    """Current method: sequential placement with ordering constraint."""
    bore_length = phase1_bore(cfg)
    bore_radii = np.full(8, cfg["bore_radius"])
    targets = sorted(cfg["targets"])
    
    hp = []
    for target in targets[1:]:
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p: break
        best_pos, best_err = 0, 1e10
        for pos in np.linspace(min_p, max_p, 60):
            try:
                inst = tmm_instrument_from_radii(bore_radii, bore_length,
                    [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                    cfg["outer_diameter"], cfg["closed_top"], 0.5)
                wl = inst.find_resonance(c / target, ["open"], 2)
                f = inst.frequency_from_wavelength(wl)
                err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
                if err < best_err:
                    best_err, best_pos = err, pos
            except: pass
        hp.append(best_pos)
    
    idx = np.argsort(hp)
    hp = [hp[j] for j in idx]
    
    hd = [cfg["hole_diameter"]] * len(hp)
    hl = [cfg["hole_length"]] * len(hp)
    rms = eval_detail(bore_radii, bore_length, hp, hd, hl, cfg)
    ca = eval_all(bore_radii, bore_length, hp, hd, hl, cfg)
    return rms, bore_length, hp, ca


def method_independent(cfg):
    """Ernoult method: place each hole independently, no ordering constraint."""
    bore_length = phase1_bore(cfg)
    bore_radii = np.full(8, cfg["bore_radius"])
    targets = sorted(cfg["targets"])
    
    hp = []
    for target in targets[1:]:
        # No ordering constraint - search entire bore
        best_pos, best_err = 0, 1e10
        for pos in np.linspace(30, bore_length - 30, 100):
            try:
                inst = tmm_instrument_from_radii(bore_radii, bore_length,
                    [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                    cfg["outer_diameter"], cfg["closed_top"], 0.5)
                wl = inst.find_resonance(c / target, ["open"], 2)
                f = inst.frequency_from_wavelength(wl)
                err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
                if err < best_err:
                    best_err, best_pos = err, pos
            except: pass
        hp.append(best_pos)
    
    idx = np.argsort(hp)
    hp = [hp[j] for j in idx]
    
    hd = [cfg["hole_diameter"]] * len(hp)
    hl = [cfg["hole_length"]] * len(hp)
    rms = eval_detail(bore_radii, bore_length, hp, hd, hl, cfg)
    ca = eval_all(bore_radii, bore_length, hp, hd, hl, cfg)
    return rms, bore_length, hp, ca


def method_simultaneous(cfg):
    """Simultaneous optimization: all holes at once."""
    bore_length = phase1_bore(cfg)
    bore_radii = np.full(8, cfg["bore_radius"])
    n_h = len(cfg["targets"]) - 1
    
    # Start from independent placement positions
    _, _, hp_init, _ = method_independent(cfg)
    
    hole_lo = [30.0] * n_h
    hole_hi = [bore_length - 30.0] * n_h
    GAP = 5.0
    
    def obj(x):
        hp = sorted(x.tolist())
        # Add ordering constraint as penalty
        penalty = 0
        for i in range(1, len(hp)):
            if hp[i] - hp[i-1] < GAP:
                penalty += (GAP - (hp[i] - hp[i-1])) * 100
        ca = eval_all(bore_radii, bore_length, hp,
                      [cfg["hole_diameter"]]*n_h,
                      [cfg["hole_length"]]*n_h, cfg)
        rms = float(np.sqrt(np.mean(ca ** 2)))
        return rms + penalty
    
    x0 = np.array(hp_init[:n_h])
    result = sp_min(obj, x0, method='L-BFGS-B',
                      bounds=[(30, bore_length-30)]*n_h,
                      options={"maxiter": 500, "ftol": 1e-10})
    
    hp = sorted(result.x.tolist())
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h
    rms = eval_detail(bore_radii, bore_length, hp, hd, hl, cfg)
    ca = eval_all(bore_radii, bore_length, hp, hd, hl, cfg)
    return rms, bore_length, hp, ca


for name, cfg in [("Xaphoon C", XAPHOON), ("Alto Sax Eb", ALTO_SAX)]:
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    
    for label, fn in [("Sequential (ordered)", method_sequential),
                       ("Independent (no order)", method_independent),
                       ("Simultaneous", method_simultaneous)]:
        t0 = time.time()
        rms, L, hp, ca = fn(cfg)
        dt = time.time() - t0
        print(f"\n  {label}:")
        print(f"    RMS={rms:.1f}c | L={L:.0f}mm | {len(hp)} holes | {dt:.1f}s")
        print(f"    Positions: {[f'{p:.0f}' for p in hp]}")
        print(f"    Per-note:  {[f'{x:+.0f}' for x in ca]}")
        print(f"    Spread:    {ca.max()-ca.min():.0f}c")
