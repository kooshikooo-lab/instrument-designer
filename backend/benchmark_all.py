"""Full benchmark: Sequential + refinement on all instruments."""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

INSTRUMENTS = {
    "chalumeau_C": {
        "desc": "Chalumeau in C (closed-open)",
        "closed_top": True,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
        "names": ["C4", "D4", "E4", "F4", "G4", "A4"],
        "bore_radius": 7.25, "outer_diameter": 22.0,
        "hole_diameter": 7.0, "hole_length": 3.75,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
        ],
    },
    "bass_chalumeau_Bb": {
        "desc": "Bass chalumeau in Bb (closed-open)",
        "closed_top": True,
        "targets": [233.1, 261.6, 293.7, 311.1, 349.2, 392.0, 440.0, 466.2],
        "names": ["Bb2", "C3", "D3", "Eb3", "F3", "G3", "A3", "Bb3"],
        "bore_radius": 9.5, "outer_diameter": 28.0,
        "hole_diameter": 8.0, "hole_length": 4.0,
        "fingerings": [
            ["closed"] * 8,
            ["open", "closed", "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "open", "open", "closed"],
        ],
    },
    "soprano_sax_Bb": {
        "desc": "Soprano sax in Bb (open-open)",
        "closed_top": False,
        "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
        "names": ["Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5"],
        "bore_radius": 6.0, "outer_diameter": 20.0,
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
    },
    "xaphoon_C": {
        "desc": "Xaphoon in C (open-open, cylindrical)",
        "closed_top": False,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
        "names": ["C4", "D4", "E4", "F4", "G4", "A4", "B4"],
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
    },
    "alto_sax_Eb": {
        "desc": "Alto sax in Eb (open-open)",
        "closed_top": False,
        "targets": [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3],
        "names": ["Eb4", "F4", "G4", "Ab4", "Bb4", "C5", "D5"],
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
    },
}

c = SPEED_OF_SOUND


def eval_all(radii, bore_length, hp, hd, hl, cfg):
    """Evaluate and return RMS cents.
    
    Uses median-subtracted evenness. n_register depends on closed_top:
    - closed-open (clarinet): n_register=1
    - open-open (sax/flute): n_register=2
    """
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
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    return float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))


def sequential(cfg):
    """Sequential hole placement.

    For closed-open (clarinet): combined fingering method (Bordeaux).
    For open-open (sax/flute): independent placement (each hole solo).

    Both skip the fundamental and optimize bore length first.
    """
    t0 = time.time()
    targets = sorted(cfg["targets"])
    fundamental = min(targets)
    closed_top = cfg["closed_top"]
    n_reg = 1 if closed_top else 2

    bore_radii = np.full(8, cfg["bore_radius"])
    L_est = c / (4.0 * fundamental) if closed_top else c / (2.0 * fundamental)

    # Phase 1: Optimize bore length
    def bore_obj(L):
        try:
            inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
                cfg["outer_diameter"], closed_top, 0.5)
            wl = inst.find_resonance(c / fundamental, [], n_reg)
            f = inst.frequency_from_wavelength(wl)
            if f <= 0 or not math.isfinite(f): return 1e10
            return abs(1200.0 * math.log2(f / fundamental))
        except: return 1e10

    from scipy.optimize import minimize as sp_min
    r = sp_min(bore_obj, [L_est], method='L-BFGS-B',
               bounds=[(L_est * 0.7, L_est * 1.3)],
               options={"maxiter": 50, "ftol": 1e-8})
    bore_length = r.x[0]

    # Phase 2: Place holes
    hp, hd, hl = [], [], []
    hole_targets = targets[1:]

    for k, target in enumerate(hole_targets):
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p:
            break

        best_pos, best_err = 0, 1e10
        for pos in np.linspace(min_p, max_p, 60):
            try:
                if closed_top:
                    # Combined fingering: all placed holes + new one open
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
                    inst = tmm_instrument_from_radii(bore_radii, bore_length,
                        pl_s, dl_s, ll_s, cfg["outer_diameter"], closed_top, 0.5)
                else:
                    # Independent: only new hole open
                    inst = tmm_instrument_from_radii(bore_radii, bore_length,
                        [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                        cfg["outer_diameter"], closed_top, 0.5)
                    fing = ["open"]

                wl = inst.find_resonance(c / target, fing, n_reg)
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

    rms = eval_all(bore_radii, bore_length, hp, hd, hl, cfg)
    return rms, bore_length, hp, time.time() - t0


def sequential_refined(cfg):
    """Sequential + 3-stage L-BFGS-B refinement with non-crossing bounds."""
    rms_seq, L_seq, hp_seq, t_seq = sequential(cfg)
    t0 = time.time()

    n_cp = 6
    n_h = len(hp_seq)
    L = L_seq
    radii = np.full(n_cp, cfg["bore_radius"])
    hp = list(hp_seq)
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h

    # Build non-crossing bounds for holes
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

    # Stage 1: Bore length only (1 variable, L-BFGS-B)
    def obj_bore_length(x):
        return eval_all(radii, x[0], hp, hd, hl, cfg)
    r = sp_min(obj_bore_length, [L], method='L-BFGS-B',
               bounds=[(L*0.85, L*1.15)], options={"maxiter": 100, "ftol": 1e-8})
    L = r.x[0]

    # Stage 2: Bore-radii only (n_cp variables, Nelder-Mead)
    if n_cp > 0:
        def obj_radii(x):
            return eval_all(np.maximum(x, 3.0), L, hp, hd, hl, cfg)
        r = sp_min(obj_radii, radii, method='Nelder-Mead',
                    options={"maxiter": 200, "xatol": 0.01, "fatol": 1e-6})
        radii = np.maximum(r.x, 3.0)

    # Stage 3: Hole positions only (n_h variables, L-BFGS-B with ordering)
    if n_h > 0:
        hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)]
        def obj_holes(x):
            return eval_all(radii, L, x.tolist(), hd, hl, cfg)
        r = sp_min(obj_holes, np.array(hp), method='L-BFGS-B',
                    bounds=hole_bounds,
                    options={"maxiter": 200, "ftol": 1e-8})
        hp = r.x.tolist()

    # Stage 4: Simultaneous fine-tune (L-BFGS-B, all variables)
    all_bounds = [(L*0.85, L*1.15)]
    all_bounds += [(3.0, 15.0)] * n_cp
    all_bounds += hole_bounds if n_h > 0 else []

    def obj_all(x):
        L_i = x[0]
        rad_i = np.maximum(x[1:1+n_cp], 3.0)
        hp_i = x[1+n_cp:1+n_cp+n_h]
        return eval_all(rad_i, L_i, hp_i.tolist(), hd, hl, cfg)

    x0 = np.concatenate([[L], radii, np.array(hp)])
    r = sp_min(obj_all, x0, method='L-BFGS-B',
                bounds=all_bounds,
                options={"maxiter": 300, "ftol": 1e-10})
    L = r.x[0]
    radii = np.maximum(r.x[1:1+n_cp], 3.0)
    hp = r.x[1+n_cp:].tolist()

    rms = eval_all(radii, L, hp, hd, hl, cfg)
    return rms, L, hp, time.time() - t0 + t_seq


# Run
all_results = {}
for name, cfg in INSTRUMENTS.items():
    print(f"\n{'#'*60}")
    print(f"# {cfg['desc']}")
    print(f"{'#'*60}")

    r = {}
    for label, fn in [("Sequential", sequential), ("Seq+Refine", sequential_refined)]:
        print(f"\n  --- {label} ---")
        try:
            rms, L, hp, dt = fn(cfg)
            r[label] = {"rms": rms, "time": dt, "bore": L, "holes": len(hp)}
            print(f"  RMS={rms:.2f}c | L={L:.0f}mm | {len(hp)} holes | {dt:.1f}s")
        except Exception as e:
            print(f"  FAILED: {e}")
            r[label] = {"rms": 1e10, "time": 0, "bore": 0, "holes": 0}
    all_results[name] = r

# Summary
print(f"\n{'#'*60}")
print("# SUMMARY")
print(f"{'#'*60}")
print(f"\n  {'Instrument':<22} {'Method':<14} {'RMS':>8} {'Time':>8}")
print(f"  {'-'*22} {'-'*14} {'-'*8} {'-'*8}")
for name, results in all_results.items():
    for method, data in results.items():
        rms = data["rms"]
        s = f"{rms:.2f}" if rms < 1e5 else "FAIL"
        print(f"  {name:<22} {method:<14} {s:>8} {data['time']:>7.1f}s")
    print()
