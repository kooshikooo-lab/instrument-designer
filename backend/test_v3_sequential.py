"""Test the fixed sequential from benchmark_all.py — sequential step only."""
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
    "bass_chalumeau_Bb": {
        "desc": "Bass chalumeau in Bb (closed-open)",
        "closed_top": True,
        "targets": [233.1, 261.6, 293.7, 311.1, 349.2, 392.0, 440.0, 466.2],
        "bore_radius": 9.5, "outer_diameter": 28.0,
        "hole_diameter": 8.0, "hole_length": 4.0,
        "fingerings": [
            ["closed"] * 8,
            ["open","closed","closed","closed","closed","closed","closed","closed"],
            ["open","open","closed","closed","closed","closed","closed","closed"],
            ["open","open","open","closed","closed","closed","closed","closed"],
            ["open","open","open","open","closed","closed","closed","closed"],
            ["open","open","open","open","open","closed","closed","closed"],
            ["open","open","open","open","open","open","closed","closed"],
            ["open","open","open","open","open","open","open","closed"],
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
    "alto_sax_Eb": {
        "desc": "Alto sax in Eb (open-open)",
        "closed_top": False,
        "targets": [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3],
        "bore_radius": 8.5, "outer_diameter": 26.0,
        "hole_diameter": 7.5, "hole_length": 3.5,
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
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
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
    rms = float(np.sqrt(np.mean(corrected ** 2)))
    peak = float(np.max(np.abs(corrected)))
    return rms, peak, freqs


def sequential(cfg):
    t0 = time.time()
    targets = sorted(cfg["targets"])
    fundamental = min(targets)

    bore_radii = np.full(8, cfg["bore_radius"])
    L_est = c / (4.0 * fundamental) if cfg["closed_top"] else c / (2.0 * fundamental)

    # Phase 1: Bore length
    def bore_obj(L):
        try:
            inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
                cfg["outer_diameter"], cfg["closed_top"], 0.5)
            wl = inst.find_resonance(c / fundamental, [], 1)
            f = inst.frequency_from_wavelength(wl)
            if f <= 0 or not math.isfinite(f): return 1e10
            return abs(1200.0 * math.log2(f / fundamental))
        except: return 1e10

    r = sp_min(bore_obj, [L_est], method='L-BFGS-B',
               bounds=[(L_est * 0.7, L_est * 1.3)],
               options={"maxiter": 50, "ftol": 1e-8})
    bore_length = r.x[0]

    # Phase 2: Place holes (low→high position, skip fundamental)
    hole_targets = targets[1:]
    # Ensure bore is long enough for all holes
    min_bore_for_holes = 30 + (len(hole_targets)) * 15 + 30
    if bore_length < min_bore_for_holes:
        bore_length = min_bore_for_holes

    hp, hd, hl = [], [], []

    for k, target in enumerate(hole_targets):
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p:
            break  # No room for more holes

        best_pos, best_err = 0, 1e10
        for pos in np.linspace(min_p, max_p, 60):
            pl = hp + [pos]
            dl = hd + [cfg["hole_diameter"]]
            ll = hl + [cfg["hole_length"]]
            idx = np.argsort(pl)
            pl_s = [pl[j] for j in idx]
            dl_s = [dl[j] for j in idx]
            ll_s = [ll[j] for j in idx]
            # Fingering: holes 0..k open (all placed holes + new one, in sorted order)
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
    rms, peak, L, hp, freqs, dt = sequential(cfg)
    print(f"  Bore: {L:.0f}mm | Holes: {len(hp)} | RMS: {rms:.1f}c | Peak: {peak:.1f}c | Time: {dt:.1f}s")
    print(f"  Hole positions: {[f'{p:.0f}' for p in hp]}")
    for i, (t, f) in enumerate(zip(cfg["targets"], freqs)):
        err = 1200*math.log2(f/t) if f > 0 else 0
        print(f"    {t:.1f} Hz -> {f:.1f} Hz ({err:+.1f}c)")
