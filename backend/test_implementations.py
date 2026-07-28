"""
Test new implementations:
1. KeefeLoss integration into optimizer
2. Stress test: chromatic flute (25 notes, 17 holes)
3. Pareto front concept (timbre + intonation)
"""
import sys, os, time, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"C:\instrument-designer")
os.environ["JAX_ENABLE_X64"] = "1"

import numpy as np
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.physics.losses import KeefeLoss
from backend.benchmark_all import INSTRUMENTS
from scipy.optimize import minimize as sp_min, differential_evolution

c = SPEED_OF_SOUND


def opt_with_loss(name, cfg, loss_model=None):
    """Optimize one instrument, optionally with loss model."""
    t0 = time.time()

    targets = sorted(cfg["targets"])
    fundamental = min(targets)
    closed_top = cfg["closed_top"]
    n_reg = 1 if closed_top else 2
    n_cp = 6
    bore_radii = np.full(n_cp, cfg["bore_radius"])
    L_est = c / (4.0 * fundamental) if closed_top else c / (2.0 * fundamental)

    def bore_obj(L):
        try:
            inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
                cfg["outer_diameter"], closed_top, 0.5, loss_model=loss_model)
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
    hole_targets = targets[1:]

    for k, target in enumerate(hole_targets):
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
                    for j in range(k + 1):
                        fing[list(idx).index(j)] = "open"
                    inst = tmm_instrument_from_radii(bore_radii, bore_length,
                        pl_s, dl_s, ll_s, cfg["outer_diameter"], closed_top, 0.5,
                        loss_model=loss_model)
                else:
                    inst = tmm_instrument_from_radii(bore_radii, bore_length,
                        [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                        cfg["outer_diameter"], closed_top, 0.5,
                        loss_model=loss_model)
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
    L = bore_length
    radii = bore_radii.copy()

    def safe_eval(radii, L, hp, hd, hl):
        try:
            inst = tmm_instrument_from_radii(
                radii, L, hp, hd, hl,
                22.0, closed_top, 0.5, loss_model=loss_model)
            n_rg = 1 if closed_top else 2
            n_hl = len(hp)
            fngrs = [["open"]*(kk+1)+["closed"]*(n_hl-kk-1) for kk in range(n_hl)]
            if closed_top:
                fngrs.insert(0, ["closed"]*n_hl)
            tw = [c / f for f in cfg["targets"]]
            freqs = inst.compute_fingered_frequencies(tw, fngrs, n_rg)
            cents = [1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10 for a, t in zip(freqs, cfg["targets"])]
            ca = np.array(cents)
            if np.any(np.abs(ca) > 1e5): return 1e10
            return float(np.sqrt(np.mean(ca ** 2)))
        except: return 1e10

    if not closed_top and len(hp) > 0:
        n_h = len(hp)
        bore_r = cfg["bore_radius"]
        hd_min = bore_r * 0.4
        hd_max = bore_r * 0.9
        radii_de = np.full(n_cp, bore_r)
        def obj_de(x):
            hp_sorted = []
            hd_sorted = []
            idx_sorted = np.argsort(x[:n_h].tolist())
            for j in idx_sorted:
                hp_sorted.append(x[j])
                hd_sorted.append(x[n_h + j])
            return safe_eval(radii_de, L, hp_sorted, hd_sorted, hl)
        de_bounds = []
        for i in range(n_h):
            lo = int(i * L / (n_h * 1.5 + 1))
            hi = int((i + 2) * L / (n_h * 1.5 + 1))
            lo = max(lo, 20)
            hi = min(hi, int(L - 20))
            if hi <= lo: hi = lo + 10
            de_bounds.append((lo, hi))
        for i in range(n_h):
            de_bounds.append((hd_min, hd_max))
        x0_de = np.array(hp + hd)
        for i in range(n_h):
            x0_de[i] = np.clip(x0_de[i], de_bounds[i][0], de_bounds[i][1])
            x0_de[n_h + i] = np.clip(x0_de[n_h + i], hd_min, hd_max)
        result_de = differential_evolution(obj_de, de_bounds, x0=x0_de, seed=42,
                                          maxiter=100, popsize=max(10, n_h * 2),
                                          tol=1e-6, mutation=(0.5, 1.0),
                                          recombination=0.7, polish=True)
        de_idx = np.argsort(result_de.x[:n_h].tolist())
        hp = [result_de.x[j] for j in de_idx]
        hd = [result_de.x[n_h + j] for j in de_idx]

    GAP = 5.0
    bore_r = cfg["bore_radius"]
    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9
    rad_lo = max(3.0, bore_r * 0.5)
    rad_hi = min(15.0, bore_r * 2.0)
    n_h = len(hp)
    hole_lo = [0.0] * n_h
    hole_hi = [0.0] * n_h
    for i in range(n_h):
        hole_lo[i] = (hp[i-1] + GAP) if i > 0 else 30.0
        hole_hi[i] = (hp[i+1] - GAP) if i < n_h-1 else (L*1.3 - 30.0)
        hole_lo[i] = max(hole_lo[i], hp[i] - 20)
        hole_hi[i] = min(hole_hi[i], hp[i] + 20)
        if hole_lo[i] > hole_hi[i]:
            hole_lo[i] = hp[i] - 1
            hole_hi[i] = hp[i] + 1

    rad_bounds = [(rad_lo, rad_hi)] * n_cp
    def obj_bore(x): return safe_eval(radii, x[0], hp, hd, hl)
    r = sp_min(obj_bore, [L], method='L-BFGS-B', bounds=[(L*0.85, L*1.15)],
               options={"maxiter": 100, "ftol": 1e-8})
    L = r.x[0]

    def obj_rad(x): return safe_eval(np.maximum(x, rad_lo), L, hp, hd, hl)
    r = sp_min(obj_rad, radii, method='L-BFGS-B', bounds=rad_bounds,
               options={"maxiter": 200, "ftol": 1e-8})
    radii = np.maximum(r.x, rad_lo)

    hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)]
    diam_bounds = [(hd_min, hd_max)] * n_h
    if n_h > 0:
        def obj_holes(x): return safe_eval(radii, L, x[:n_h].tolist(), x[n_h:].tolist(), hl)
        x0_hd = np.array(hp + hd)
        r = sp_min(obj_holes, x0_hd, method='L-BFGS-B', bounds=hole_bounds + diam_bounds,
                    options={"maxiter": 200, "ftol": 1e-8})
        hp = r.x[:n_h].tolist()
        hd = r.x[n_h:].tolist()

    all_bounds = [(L*0.85, L*1.15)] + rad_bounds + hole_bounds + diam_bounds
    def obj_all(x):
        L_i = x[0]
        rad_i = np.maximum(x[1:1+n_cp], rad_lo)
        hp_i = x[1+n_cp:1+n_cp+n_h]
        hd_i = x[1+n_cp+n_h:1+n_cp+2*n_h]
        return safe_eval(rad_i, L_i, hp_i.tolist(), hd_i.tolist(), hl)
    x0 = np.concatenate([[L], radii, np.array(hp), np.array(hd)])
    r = sp_min(obj_all, x0, method='L-BFGS-B', bounds=all_bounds,
                options={"maxiter": 300, "ftol": 1e-10})
    L = r.x[0]
    radii = np.maximum(r.x[1:1+n_cp], rad_lo)
    hp = r.x[1+n_cp:1+n_cp+n_h].tolist()
    hd = r.x[1+n_cp+n_h:1+n_cp+2*n_h].tolist()

    final_rms = safe_eval(radii, L, hp, hd, hl)
    dt = time.time() - t0
    return final_rms, L, dt


def timbre_metric(radii, bore_length, hp, hd, hl, closed_top, targets, loss_model=None):
    """Compute timbre quality metric (radiation impedance matching).

    Better timbre = smoother bore profile + larger holes = brighter sound.
    Simple proxy: harmonic richness = ratio of radiated power at harmonics vs fundamental.
    We use the bell radiation efficiency as a proxy.
    """
    try:
        inst = tmm_instrument_from_radii(
            radii, bore_length, hp, hd, hl,
            22.0, closed_top, 0.5, loss_model=loss_model)

        # Compute radiation impedance at fundamental
        fundamental = min(targets)
        wl = c / fundamental

        # Bell radiation efficiency increases with (bore_radius / wavelength)^2
        # Higher = brighter timbre
        bell_radius = radii[-1] if len(radii) > 0 else 7.0
        radiation_eff = (bell_radius / wl) ** 2

        # Smoothness of bore profile (lower = smoother = less distorted timbre)
        if len(radii) > 1:
            profile_diffs = np.diff(radii)
            smoothness = np.std(profile_diffs)
        else:
            smoothness = 0.0

        # Combined timbre score (lower is better for minimization)
        # We want: good radiation + smooth profile
        timbre = smoothness / (radiation_eff + 1e-10)
        return float(timbre)
    except:
        return 1e10


def pareto_cost(x, n_cp, n_h, L, closed_top, cfg, loss_model=None):
    """Combined cost for Pareto: weighted intonation + timbre."""
    radii = np.maximum(x[:n_cp], 0.1)
    hp = sorted(x[n_cp:n_cp + n_h].tolist())
    hd = x[n_cp + n_h:n_cp + 2 * n_h].tolist()
    hl = [cfg["hole_length"]] * n_h

    bore_r = cfg["bore_radius"]
    targets = cfg["targets"]

    try:
        inst = tmm_instrument_from_radii(
            radii, L, hp, hd, hl,
            22.0, closed_top, 0.5, loss_model=loss_model)
        n_rg = 1 if closed_top else 2
        fngrs = [["open"]*(kk+1)+["closed"]*(n_h-kk-1) for kk in range(n_h)]
        if closed_top:
            fngrs.insert(0, ["closed"]*n_h)
        tw = [c / f for f in targets]
        freqs = inst.compute_fingered_frequencies(tw, fngrs, n_rg)
        cents = [1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10 for a, t in zip(freqs, targets)]
        ca = np.array(cents)
        if np.any(np.abs(ca) > 1e5): return 1e10, 1e10
        intonation = float(np.sqrt(np.mean(ca ** 2)))
    except:
        return 1e10, 1e10

    # Timbre: bell radiation proxy + profile smoothness
    bell_r = radii[-1] if len(radii) > 0 else 7.0
    wl = c / min(targets)
    radiation_eff = (bell_r / wl) ** 2
    smoothness = float(np.std(np.diff(radii))) if len(radii) > 1 else 0.0
    timbre = smoothness / (radiation_eff + 1e-10)

    return intonation, timbre


def main():
    print("=" * 72)
    print("  IMPLEMENTATION TESTING")
    print("=" * 72)

    # ── Test 1: KeefeLoss integration ────────────────────────────────────
    print("\n--- Test 1: KeefeLoss Integration ---")
    print("Testing chalumeau_C with and without viscothermal losses...")
    loss = KeefeLoss(temperature=20.0)
    test_instruments = ["chalumeau_C", "bass_chalumeau_Bb", "concert_flute_C", "recorder_C"]

    for name in test_instruments:
        cfg = INSTRUMENTS[name]
        rms_no_loss, L_no, t_no = opt_with_loss(name, cfg, loss_model=None)
        rms_loss, L_loss, t_loss = opt_with_loss(name, cfg, loss_model=loss)
        delta = rms_loss - rms_no_loss
        print(f"  {name:30s}  no-loss={rms_no_loss:.4f}c  KeefeLoss={rms_loss:.4f}c  delta={delta:+.4f}c  L_no={L_no:.1f}mm  L_loss={L_loss:.1f}mm")

    # ── Test 2: Chromatic flute stress test ──────────────────────────────
    print("\n--- Test 2: Chromatic Flute Stress Test (25 notes, 17 holes) ---")
    cfg = INSTRUMENTS["chromatic_flute_C"]
    n_h = len(cfg["targets"]) - 1  # 24 holes for 25 notes
    
    # The chromatic flute is very complex. Test just the first octave.
    range_cfg = {
        "desc": "Chromatic flute C4-B4 (12 notes, 11 holes)",
        "closed_top": False,
        "targets": [261.63, 277.18, 293.66, 311.13, 329.63, 349.23,
                    369.99, 392.00, 415.30, 440.00, 466.16, 493.88],
        "bore_radius": 9.5, "outer_diameter": 22.0,
        "hole_diameter": 12.5, "hole_length": 3.0,
        "fingerings": [["closed"]*17] + [["open"]*(k+1)+["closed"]*(16-k) for k in range(11)],
    }

    print(f"  Target: {range_cfg['desc']}")
    print(f"  Notes: {len(range_cfg['targets'])}, Holes: {len(range_cfg['targets'])-1}")
    t0 = time.time()
    rms, L, dt = opt_with_loss("chromatic_flute_C4_B4", range_cfg, loss_model=None)
    print(f"  Result: RMS={rms:.4f}c, L={L:.1f}mm, time={dt:.1f}s")

    # ── Test 3: Full chromatic flute (all 25 notes) ─────────────────────
    print("\n--- Test 3: Full Chromatic Flute (25 notes) ---")
    cfg_full = INSTRUMENTS["chromatic_flute_C"]
    print(f"  Notes: {len(cfg_full['targets'])}, Holes in fingering: {len(cfg_full['fingerings'][0])}")
    t0 = time.time()
    rms, L, dt = opt_with_loss("chromatic_flute_FULL", cfg_full, loss_model=None)
    print(f"  Result: RMS={rms:.4f}c, L={L:.1f}mm, time={dt:.1f}s")

    # ── Test 4: Pareto front concept ────────────────────────────────────
    print("\n--- Test 4: Pareto Front Concept (Intonation vs Timbre) ---")
    print("Computing Pareto-optimal designs for chalumeau_C...")
    cfg_pc = INSTRUMENTS["chalumeau_C"]
    closed_top = cfg_pc["closed_top"]
    n_cp = 6
    n_h = 5  # 6 notes, 5 holes
    bore_r = cfg_pc["bore_radius"]
    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9

    # Get the intonation-optimal design as reference
    rms_ref, L_ref, _ = opt_with_loss("chalumeau_C", cfg_pc, loss_model=None)

    # Sweep timbre weight: from pure intonation to balanced
    weights = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
    print(f"  {'Weight':>8s}  {'Intonation':>12s}  {'Timbre':>12s}  {'Bore L':>8s}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*12}  {'-'*8}")

    for w_int in weights:
        w_tim = 1.0 - w_int
        t0 = time.time()

        # Optimize bore length first
        def bore_obj_w(L):
            radii = np.full(n_cp, bore_r)
            hp = [L*(i+1)/(n_h+1) for i in range(n_h)]
            hd = [cfg_pc["hole_diameter"]] * n_h
            hl = [cfg_pc["hole_length"]] * n_h
            intonation, timbre = pareto_cost(
                np.concatenate([radii, np.array(hp), np.array(hd)]),
                n_cp, n_h, L, closed_top, cfg_pc)
            return w_int * intonation + w_tim * timbre

        r = sp_min(bore_obj_w, [330.0], method='L-BFGS-B',
                   bounds=[(200.0, 500.0)], options={"maxiter": 50})
        L = r.x[0]

        # Optimize all parameters
        def obj_w(x):
            radii = np.maximum(x[:n_cp], 0.1)
            hp = sorted(x[n_cp:n_cp+n_h].tolist())
            hd = x[n_cp+n_h:n_cp+2*n_h].tolist()
            intonation, timbre = pareto_cost(
                np.concatenate([radii, np.array(hp), np.array(hd)]),
                n_cp, n_h, L, closed_top, cfg_pc, loss_model=None)
            return w_int * intonation + w_tim * timbre

        bounds = [(3.0, 15.0)] * n_cp + [(30.0, L-30)] * n_h + [(hd_min, hd_max)] * n_h
        x0 = np.random.RandomState(42).uniform(
            [b[0] for b in bounds], [b[1] for b in bounds])
        r = sp_min(obj_w, x0, method='L-BFGS-B', bounds=bounds,
                    options={"maxiter": 200, "ftol": 1e-10})

        radii_opt = np.maximum(r.x[:n_cp], 0.1)
        hp_opt = sorted(r.x[n_cp:n_cp+n_h].tolist())
        hd_opt = r.x[n_cp+n_h:n_cp+2*n_h].tolist()
        intonation, timbre = pareto_cost(
            np.concatenate([radii_opt, np.array(hp_opt), np.array(hd_opt)]),
            n_cp, n_h, L, closed_top, cfg_pc, loss_model=None)
        dt = time.time() - t0

        print(f"  {w_int:8.1f}  {intonation:12.4f}  {timbre:12.6f}  {L:8.1f}mm  ({dt:.1f}s)")

    print("\nDone!")


if __name__ == "__main__":
    main()
