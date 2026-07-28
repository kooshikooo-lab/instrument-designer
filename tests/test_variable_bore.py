"""Test variable bore profiles on hard open-open instruments.

Key questions:
1. Does variable bore (n_bore_cp>0) improve xaphoon/alto sax?
2. What are the TMM model limitations for larger bores?
3. Does bore profile deviation from uniform help (per Lefebvre 2011)?
"""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

INSTRUMENTS = {
    "soprano_sax": {
        "desc": "Soprano sax Bb (open-open)",
        "closed_top": False,
        "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
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
    "xaphoon": {
        "desc": "Xaphoon C (open-open, cylindrical)",
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
    },
    "alto_sax": {
        "desc": "Alto sax Eb (open-open)",
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
    },
}


def eval_detail(radii, bore_length, hp, hd, hl, cfg):
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
    return np.array(cents)


def seq_place(cfg):
    """Sequential hole placement (bell to mouthpiece for open-open)."""
    targets = sorted(cfg["targets"])
    fundamental = min(targets)
    closed_top = cfg["closed_top"]
    n_reg = 1 if closed_top else 2
    bore_radii = np.full(8, cfg["bore_radius"])
    L_est = c / (4.0 * fundamental) if closed_top else c / (2.0 * fundamental)

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

    hp, hd, hl = [], [], []
    for target in targets[1:]:
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p: break
        best_pos, best_err = 0, 1e10
        for pos in np.linspace(min_p, max_p, 60):
            try:
                if closed_top:
                    pl = hp + [pos]
                    dl = hd + [cfg["hole_diameter"]]
                    ll = hl + [cfg["hole_length"]]
                    idx = np.argsort(pl)
                    pl_s = [pl[j] for j in idx]
                    dl_s = [dl[j] for j in idx]
                    ll_s = [ll[j] for j in idx]
                    fing = ["closed"] * len(pl)
                    for j in range(len(hp) + 1):
                        fing[list(idx).index(j)] = "open"
                    inst = tmm_instrument_from_radii(bore_radii, bore_length,
                        pl_s, dl_s, ll_s, cfg["outer_diameter"], closed_top, 0.5)
                else:
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

    ca = eval_detail(bore_radii, bore_length, hp, hd, hl, cfg)
    rms = float(np.sqrt(np.mean(ca ** 2)))
    return rms, bore_length, hp


def refine_bore_cp(cfg, bore_length, hp, hd, hl, n_cp_list):
    """Test different n_bore_cp values with refinement."""
    results = {}
    for n_cp in n_cp_list:
        t0 = time.time()
        n_h = len(hp)
        radii = np.full(n_cp, cfg["bore_radius"]) if n_cp > 0 else np.full(8, cfg["bore_radius"])

        GAP = 5.0
        hole_lo, hole_hi = [0.0]*n_h, [0.0]*n_h
        for i in range(n_h):
            hole_lo[i] = (hp[i-1] + GAP) if i > 0 else 30.0
            hole_hi[i] = (hp[i+1] - GAP) if i < n_h-1 else (bore_length*1.3 - 30.0)
            hole_lo[i] = max(hole_lo[i], hp[i] - 30)
            hole_hi[i] = min(hole_hi[i], hp[i] + 30)
            if hole_lo[i] > hole_hi[i]:
                hole_lo[i] = hp[i] - 1
                hole_hi[i] = hp[i] + 1

        L = bore_length

        # Stage 1: Bore length
        def obj_bore(x):
            r = np.full(n_cp, cfg["bore_radius"])
            ca = eval_detail(r, x[0], hp, hd, hl, cfg)
            return float(np.sqrt(np.mean(ca ** 2)))
        r = sp_min(obj_bore, [L], method='L-BFGS-B',
                   bounds=[(L*0.85, L*1.15)], options={"maxiter": 100, "ftol": 1e-8})
        L = r.x[0]

        # Stage 2: Bore radii (if n_cp > 0)
        if n_cp > 0:
            rad_bounds = [(3.0, 15.0)] * n_cp
            def obj_radii(x):
                ca = eval_detail(np.maximum(x, 3.0), L, hp, hd, hl, cfg)
                return float(np.sqrt(np.mean(ca ** 2)))
            r = sp_min(obj_radii, radii, method='L-BFGS-B',
                       bounds=rad_bounds, options={"maxiter": 200, "ftol": 1e-8})
            radii = np.maximum(r.x, 3.0)

        # Stage 3: Hole positions
        def obj_holes(x):
            ca = eval_detail(radii, L, x.tolist(), hd, hl, cfg)
            return float(np.sqrt(np.mean(ca ** 2)))
        r = sp_min(obj_holes, np.array(hp), method='L-BFGS-B',
                   bounds=[(hole_lo[i], hole_hi[i]) for i in range(n_h)],
                   options={"maxiter": 200, "ftol": 1e-8})
        hp_r = r.x.tolist()

        # Stage 4: Simultaneous
        all_bounds = [(L*0.85, L*1.15)]
        if n_cp > 0:
            all_bounds += [(3.0, 15.0)] * n_cp
        all_bounds += [(hole_lo[i], hole_hi[i]) for i in range(n_h)]

        def obj_all(x):
            L_i = x[0]
            if n_cp > 0:
                rad_i = np.maximum(x[1:1+n_cp], 3.0)
                hp_i = x[1+n_cp:1+n_cp+n_h]
            else:
                rad_i = radii
                hp_i = x[1:1+n_h]
            ca = eval_detail(rad_i, L_i, hp_i.tolist(), hd, hl, cfg)
            return float(np.sqrt(np.mean(ca ** 2)))

        x0_parts = [[L]]
        if n_cp > 0:
            x0_parts.append(radii)
        x0_parts.append(np.array(hp_r))
        x0 = np.concatenate(x0_parts)
        r = sp_min(obj_all, x0, method='L-BFGS-B',
                   bounds=all_bounds, options={"maxiter": 300, "ftol": 1e-10})

        if n_cp > 0:
            L_f = r.x[0]
            radii_f = np.maximum(r.x[1:1+n_cp], 3.0)
            hp_f = r.x[1+n_cp:].tolist()
        else:
            L_f = r.x[0]
            radii_f = radii
            hp_f = r.x[1:].tolist()

        ca = eval_detail(radii_f, L_f, hp_f, hd, hl, cfg)
        rms = float(np.sqrt(np.mean(ca ** 2)))
        dt = time.time() - t0

        results[n_cp] = {
            "rms": rms, "time": dt, "L": L_f,
            "radii": radii_f.tolist() if n_cp > 0 else None,
            "per_note": ca.tolist(),
        }
    return results


for name, cfg in INSTRUMENTS.items():
    print(f"\n{'='*60}")
    print(f"{cfg['desc']}")
    print(f"{'='*60}")

    # Phase 1+2: Sequential
    rms_seq, L_seq, hp_seq = seq_place(cfg)
    ca_seq = eval_detail(np.full(8, cfg["bore_radius"]), L_seq, hp_seq,
                         [cfg["hole_diameter"]]*len(hp_seq),
                         [cfg["hole_length"]]*len(hp_seq), cfg)
    print(f"  Sequential: {rms_seq:.1f}c | L={L_seq:.0f}mm | {len(hp_seq)} holes")
    print(f"  Per-note:   {[f'{x:+.0f}' for x in ca_seq]}")

    # Phase 3: Refine with different n_bore_cp values
    bore_cp_results = refine_bore_cp(cfg, L_seq, hp_seq,
                                     [cfg["hole_diameter"]]*len(hp_seq),
                                     [cfg["hole_length"]]*len(hp_seq),
                                     [0, 2, 4, 6])

    print(f"\n  {'n_cp':>4} {'RMS':>8} {'Time':>7} {'Bore L':>8}  Per-note")
    for n_cp, data in sorted(bore_cp_results.items()):
        bore_str = f"{data['radii']}" if data['radii'] else "uniform"
        print(f"  {n_cp:>4} {data['rms']:>7.2f}c {data['time']:>6.1f}s L={data['L']:.0f}")
        print(f"       Per-note: {[f'{x:+.0f}' for x in data['per_note']]}")
        if data['radii']:
            print(f"       Radii: {[f'{r:.1f}' for r in data['radii']]}")
