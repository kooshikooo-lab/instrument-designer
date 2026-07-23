"""Full benchmark: Sequential + refinement on all instruments."""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min, differential_evolution

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
    "tin_whistle_D": {
        "desc": "Tin whistle in D (open-open, cylindrical)",
        "closed_top": False,
        "targets": [587.3, 659.3, 740.0, 784.0, 880.0, 987.8, 1108.7],
        "names": ["D5", "E5", "F#5", "G5", "A5", "B5", "C#6"],
        "bore_radius": 6.5, "outer_diameter": 16.0,
        "hole_diameter": 4.5, "hole_length": 2.5,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
            ["open", "open", "open", "open", "open", "open"],
        ],
    },
    "concert_flute_C": {
        "desc": "Concert flute in C (open-open, cylindrical)",
        "closed_top": False,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
        "names": ["C4", "D4", "E4", "F4", "G4", "A4", "B4"],
        "bore_radius": 9.5, "outer_diameter": 16.0,
        "hole_diameter": 8.0, "hole_length": 3.0,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
            ["open", "open", "open", "open", "open", "open"],
        ],
    },
    "alto_flute_G": {
        "desc": "Alto flute in G (open-open, cylindrical)",
        "closed_top": False,
        "targets": [196.0, 220.0, 246.9, 261.6, 293.7, 329.6, 369.9],
        "names": ["G3", "A3", "B3", "C4", "D4", "E4", "F#4"],
        "bore_radius": 11.0, "outer_diameter": 18.0,
        "hole_diameter": 9.0, "hole_length": 3.0,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
            ["open", "open", "open", "open", "open", "open"],
        ],
    },
    "pvc_flute_D": {
        "desc": "PVC flute in D (3/4\" schedule 40, open-open)",
        "closed_top": False,
        "targets": [293.7, 329.6, 369.9, 392.0, 440.0, 493.9, 554.4],
        "names": ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5"],
        "bore_radius": 10.2, "outer_diameter": 14.0,
        "hole_diameter": 8.0, "hole_length": 3.0,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
            ["open", "open", "open", "open", "open", "open"],
        ],
    },
    "recorder_C": {
        "desc": "Soprano recorder in C (open-open, conical)",
        "closed_top": False,
        "targets": [523.3, 587.3, 659.3, 698.5, 784.0, 880.0, 987.8, 1046.5],
        "names": ["C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6"],
        "bore_radius": 5.5, "outer_diameter": 14.0,
        "hole_diameter": 4.0, "hole_length": 2.0,
        "fingerings": [
            ["closed"] * 7,
            ["open", "closed", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "open", "closed"],
            ["open", "open", "open", "open", "open", "open", "open"],
        ],
    },
}

c = SPEED_OF_SOUND


def eval_all(radii, bore_length, hp, hd, hl, cfg):
    """Evaluate and return RMS cents (absolute, not median-corrected).

    Uses absolute RMS to prevent the optimizer from achieving 0c by
    making all notes uniformly wrong (masked by median correction).

    n_register depends on closed_top:
    - closed-open (clarinet): n_register=1 (fundamental is 1st resonance)
    - open-open (sax/flute): n_register=2 (fundamental is 2nd resonance
      in TMM due to stepped-cylinder phantom 1st resonance)
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
    return float(np.sqrt(np.mean(ca ** 2)))


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
    """Sequential + global DE + 3-stage L-BFGS-B refinement with non-crossing bounds.

    Includes hole diameter optimization: diameters are design variables
    co-optimized with positions in DE and refined in L-BFGS-B.
    """
    rms_seq, L_seq, hp_seq, t_seq = sequential(cfg)
    t0 = time.time()

    n_cp = 6
    n_h = len(hp_seq)
    L = L_seq
    radii = np.full(n_cp, cfg["bore_radius"])
    hp = list(hp_seq)
    hd = [cfg["hole_diameter"]] * n_h
    hl = [cfg["hole_length"]] * n_h

    # Hole diameter bounds: [min, max] per hole
    # Min: ~40% of bore radius (small but audible)
    # Max: ~90% of bore radius (large, nearly full-bore)
    bore_r = cfg["bore_radius"]
    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9

    def safe_eval_all(radii, L, hp, hd, hl, cfg):
        try:
            return eval_all(radii, L, hp, hd, hl, cfg)
        except (TypeError, ValueError, OverflowError):
            return 1e10

    # Phase 2b: Global hole re-optimization for open-open instruments.
    # Sequential single-hole placement creates large gaps that L-BFGS-B can't fix.
    # Now co-optimizes hole positions AND diameters.
    if not cfg["closed_top"]:
        print(f"    Phase 2b: Global hole re-optimization (differential evolution)")
        radii_de = np.full(n_cp, cfg["bore_radius"])

        def obj_de(x):
            hp_sorted = []
            hd_sorted = []
            idx_sorted = np.argsort(x[:n_h].tolist())
            for j in idx_sorted:
                hp_sorted.append(x[j])
                hd_sorted.append(x[n_h + j])
            return safe_eval_all(radii_de, L, hp_sorted, hd_sorted, hl, cfg)

        # Overlapping bounds for positions + diameter bounds
        de_bounds = []
        for i in range(n_h):
            lo = int(i * L / (n_h * 1.5 + 1))
            hi = int((i + 2) * L / (n_h * 1.5 + 1))
            lo = max(lo, 20)
            hi = min(hi, int(L - 20))
            if hi <= lo:
                hi = lo + 10
            de_bounds.append((lo, hi))
        # Add diameter bounds
        for i in range(n_h):
            de_bounds.append((hd_min, hd_max))

        # Clip initial positions to within bounds
        x0_de = np.array(hp + hd)
        for i in range(n_h):
            x0_de[i] = np.clip(x0_de[i], de_bounds[i][0], de_bounds[i][1])
            x0_de[n_h + i] = np.clip(x0_de[n_h + i], hd_min, hd_max)
        result_de = differential_evolution(obj_de, de_bounds, x0=x0_de, seed=42,
                                          maxiter=100, popsize=max(10, n_h * 2),
                                          tol=1e-6, mutation=(0.5, 1.0),
                                          recombination=0.7, polish=True)
        # Extract optimized positions and diameters
        de_idx = np.argsort(result_de.x[:n_h].tolist())
        hp = [result_de.x[j] for j in de_idx]
        hd = [result_de.x[n_h + j] for j in de_idx]
        print(f"      RMS={result_de.fun:.2f}c  Holes: {[f'{p:.0f}mm/{d:.1f}mm' for p, d in zip(hp, hd)]}")

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
        return safe_eval_all(radii, x[0], hp, hd, hl, cfg)
    r = sp_min(obj_bore_length, [L], method='L-BFGS-B',
               bounds=[(L*0.85, L*1.15)], options={"maxiter": 100, "ftol": 1e-8})
    L = r.x[0]

    # Stage 2: Bore-radii only (n_cp variables, L-BFGS-B)
    if n_cp > 0:
        rad_lo = max(3.0, bore_r * 0.5)
        rad_hi = min(15.0, bore_r * 2.0)
        rad_bounds = [(rad_lo, rad_hi)] * n_cp
        def obj_radii(x):
            return safe_eval_all(np.maximum(x, rad_lo), L, hp, hd, hl, cfg)
        r = sp_min(obj_radii, radii, method='L-BFGS-B',
                    bounds=rad_bounds,
                    options={"maxiter": 200, "ftol": 1e-8})
        radii = np.maximum(r.x, rad_lo)

    # Stage 3: Hole positions + diameters (n_h*2 variables, L-BFGS-B with ordering)
    if n_h > 0:
        hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)]
        hole_diam_bounds = [(hd_min, hd_max)] * n_h
        def obj_holes_and_diams(x):
            return safe_eval_all(radii, L, x[:n_h].tolist(), x[n_h:].tolist(), hl, cfg)
        x0_hd = np.array(hp + hd)
        all_hole_bounds = hole_bounds + hole_diam_bounds
        r = sp_min(obj_holes_and_diams, x0_hd, method='L-BFGS-B',
                    bounds=all_hole_bounds,
                    options={"maxiter": 200, "ftol": 1e-8})
        hp = r.x[:n_h].tolist()
        hd = r.x[n_h:].tolist()

    # Stage 4: Simultaneous fine-tune (L-BFGS-B, all variables)
    all_bounds = [(L*0.85, L*1.15)]
    all_bounds += rad_bounds if n_cp > 0 else []
    all_bounds += hole_bounds if n_h > 0 else []
    all_bounds += hole_diam_bounds if n_h > 0 else []

    def obj_all(x):
        L_i = x[0]
        rad_i = np.maximum(x[1:1+n_cp], rad_lo) if n_cp > 0 else radii
        hp_i = x[1+n_cp:1+n_cp+n_h]
        hd_i = x[1+n_cp+n_h:1+n_cp+2*n_h]
        return safe_eval_all(rad_i, L_i, hp_i.tolist(), hd_i.tolist(), hl, cfg)

    x0 = np.concatenate([[L], radii, np.array(hp), np.array(hd)])
    r = sp_min(obj_all, x0, method='L-BFGS-B',
                bounds=all_bounds,
                options={"maxiter": 300, "ftol": 1e-10})
    L = r.x[0]
    radii = np.maximum(r.x[1:1+n_cp], rad_lo) if n_cp > 0 else radii
    hp = r.x[1+n_cp:1+n_cp+n_h].tolist()
    hd = r.x[1+n_cp+n_h:1+n_cp+2*n_h].tolist()

    rms = safe_eval_all(radii, L, hp, hd, hl, cfg)
    return rms, L, hp, hd, time.time() - t0 + t_seq


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
            result = fn(cfg)
            rms, L, hp, dt = result[0], result[1], result[2], result[-1]
            hd = result[3] if label == "Seq+Refine" else None
            r[label] = {"rms": rms, "time": dt, "bore": L, "holes": len(hp)}
            if hd is not None:
                r[label]["hole_diameters"] = hd
            print(f"  RMS={rms:.2f}c | L={L:.0f}mm | {len(hp)} holes | {dt:.1f}s")
        except Exception as e:
            import traceback
            print(f"  FAILED: {e}")
            traceback.print_exc()
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
