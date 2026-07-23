"""Test saxophone with independent hole placement (each hole placed solo, then combined)."""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min

sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

INSTRUMENTS = {
    "chalumeau_C": {
        "desc": "Chalumeau in C (closed-open)",
        "closed_top": True,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
        "bore_radius": 7.25, "outer_diameter": 22.0,
        "hole_diameter": 7.0, "hole_length": 3.75,
        "fingerings": [
            ["closed"] * 6,
            ["open","closed","closed","closed","closed","closed"],
            ["open","open","closed","closed","closed","closed"],
            ["open","open","open","closed","closed","closed"],
            ["open","open","open","open","closed","closed"],
            ["open","open","open","open","open","closed"],
        ],
    },
    "soprano_sax_Bb": {
        "desc": "Soprano sax in Bb (open-open)",
        "closed_top": False,
        "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
        "bore_radius": 6.0, "outer_diameter": 20.0,
        "hole_diameter": 6.5, "hole_length": 3.0,
        "fingerings": [
            ["closed"] * 7,
            ["open","closed","closed","closed","closed","closed","closed"],
            ["open","open","closed","closed","closed","closed","closed"],
            ["open","open","open","closed","closed","closed","closed"],
            ["open","open","open","open","closed","closed","closed"],
            ["open","open","open","open","open","closed","closed"],
            ["open","open","open","open","open","open","closed"],
        ],
    },
}


def eval_all(radii, bore_length, hp, hd, hl, cfg):
    inst = tmm_instrument_from_radii(radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5)
    tw = [c / f for f in cfg["targets"]]
    freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 1)
    cents = []
    for a, t in zip(freqs, cfg["targets"]):
        cents.append(1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10)
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10, 0, freqs
    offset = np.median(ca)
    corrected = ca - offset
    return float(np.sqrt(np.mean(corrected ** 2))), float(np.max(np.abs(corrected))), freqs


def sequential_independent(cfg):
    """Place each hole independently (single open hole), then evaluate with combined fingerings."""
    t0 = time.time()
    targets = sorted(cfg["targets"])
    fundamental = min(targets)
    bore_radii = np.full(8, cfg["bore_radius"])
    L_est = c / (4.0 * fundamental) if cfg["closed_top"] else c / (2.0 * fundamental)

    bore_length = L_est

    # For each target (skip fundamental), find best position with SINGLE open hole
    hp = []
    hole_targets = targets[1:]
    for k, target in enumerate(hole_targets):
        # Fingering: only this hole open (rest closed)
        fing = ["open"] + ["closed"] * k  # Wrong — need to think about this
        # Actually: for single-hole test, just open the new hole
        best_pos, best_err = 0, 1e10
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p:
            break
        for pos in np.linspace(min_p, max_p, 60):
            try:
                inst = tmm_instrument_from_radii(bore_radii, bore_length,
                    [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                    cfg["outer_diameter"], cfg["closed_top"], 0.5)
                wl = inst.find_resonance(c / target, ["open"], 1)
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
    
    rms, peak, freqs = eval_all(bore_radii, bore_length, hp, hd, hl, cfg)
    dt = time.time() - t0
    return rms, peak, bore_length, hp, freqs, dt


def sequential_combined(cfg):
    """Sequential with combined fingerings (standard Bordeaux method)."""
    t0 = time.time()
    targets = sorted(cfg["targets"])
    fundamental = min(targets)
    bore_radii = np.full(8, cfg["bore_radius"])
    L_est = c / (4.0 * fundamental) if cfg["closed_top"] else c / (2.0 * fundamental)
    bore_length = L_est

    hp, hd, hl = [], [], []
    hole_targets = targets[1:]

    for k, target in enumerate(hole_targets):
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p:
            break

        best_pos, best_err = 0, 1e10
        for pos in np.linspace(min_p, max_p, 60):
            pl = hp + [pos]
            dl = hd + [cfg["hole_diameter"]]
            ll = hl + [cfg["hole_length"]]
            idx = np.argsort(pl)
            pl_s = [pl[j] for j in idx]
            dl_s = [dl[j] for j in idx]
            ll_s = [ll[j] for j in idx]
            fing = ["closed"] * len(pl)
            for j in range(k + 1):
                fing[list(idx).index(j)] = "open"
            try:
                inst = tmm_instrument_from_radii(bore_radii, bore_length,
                    pl_s, dl_s, ll_s, cfg["outer_diameter"], cfg["closed_top"], 0.5)
                wl = inst.find_resonance(c / target, fing, 1)
                f = inst.frequency_from_wavelength(wl)
                err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
                if err < best_err:
                    best_err, best_pos = err, pos
            except: pass
        hp.append(best_pos)
        hd.append(cfg["hole_diameter"])
        hl.append(cfg["hole_length"])

    idx = np.argsort(hp)
    hp = [hp[j] for j in idx]
    hd = [hd[j] for j in idx]
    hl = [hl[j] for j in idx]

    rms, peak, freqs = eval_all(bore_radii, bore_length, hp, hd, hl, cfg)
    dt = time.time() - t0
    return rms, peak, bore_length, hp, freqs, dt


for name, cfg in INSTRUMENTS.items():
    print(f"\n{'='*60}")
    print(f" {cfg['desc']}")
    print(f"{'='*60}")
    
    rms1, peak1, L1, hp1, f1, dt1 = sequential_independent(cfg)
    print(f"  Independent: RMS={rms1:.1f}c Peak={peak1:.1f}c L={L1:.0f}mm holes={[f'{p:.0f}' for p in hp1]} {dt1:.1f}s")
    for t, f in zip(cfg["targets"], f1):
        err = 1200*math.log2(f/t) if f > 0 else 0
        print(f"    {t:.1f} -> {f:.1f} ({err:+.1f}c)")
    
    rms2, peak2, L2, hp2, f2, dt2 = sequential_combined(cfg)
    print(f"  Combined:    RMS={rms2:.1f}c Peak={peak2:.1f}c L={L2:.0f}mm holes={[f'{p:.0f}' for p in hp2]} {dt2:.1f}s")
    for t, f in zip(cfg["targets"], f2):
        err = 1200*math.log2(f/t) if f > 0 else 0
        print(f"    {t:.1f} -> {f:.1f} ({err:+.1f}c)")
