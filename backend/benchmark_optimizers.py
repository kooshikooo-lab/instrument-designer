"""
Comprehensive optimizer benchmark: all methods, multiple instruments.

Tests:
1. Original Powell+L-BFGS-B (v2)
2. Corrected Powell (free bore length)
3. Sequential (Bordeaux method: bore first, then holes one-by-one)
4. Multi-start Powell

Instruments:
- Chalumeau in C (closed-open, 6 holes)
- Bass chalumeau in Bb (closed-open, 8 holes)
- Soprano sax in Bb (open-open, 7 holes)
- Alto sax in Eb (open-open, 7 holes)
"""

import sys, os, time, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND


# ============================================================================
# Instruments
# ============================================================================

INSTRUMENTS = {
    "chalumeau_C": {
        "desc": "Chalumeau in C (closed-open)",
        "closed_top": True,
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
        "names": ["C4", "D4", "E4", "F4", "G4", "A4"],
        "bore_radius": 7.25,
        "outer_diameter": 22.0,
        "hole_diameter": 7.0,
        "hole_length": 3.75,
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
        "bore_radius": 9.5,
        "outer_diameter": 28.0,
        "hole_diameter": 8.0,
        "hole_length": 4.0,
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
        "bore_radius": 6.0,
        "outer_diameter": 20.0,
        "hole_diameter": 6.5,
        "hole_length": 3.0,
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
        "bore_radius": 8.5,
        "outer_diameter": 26.0,
        "hole_diameter": 7.5,
        "hole_length": 3.5,
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


# ============================================================================
# Helpers
# ============================================================================

def evaluate(radii, bore_length, cfg, label=""):
    """Evaluate a bore profile and print results."""
    inst = tmm_instrument_from_radii(
        np.array(radii), bore_length,
        cfg.get("hole_positions", []),
        cfg.get("hole_diameters", []),
        cfg.get("hole_lengths", []),
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )
    tw = [SPEED_OF_SOUND / f for f in cfg["targets"]]
    freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 1)

    cents = []
    for a, t in zip(freqs, cfg["targets"]):
        if a > 0 and math.isfinite(a):
            cents.append(1200.0 * math.log2(a / t))
        else:
            cents.append(1e10)

    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10, 1e10

    offset = np.median(ca)
    corrected = ca - offset
    rms = float(np.sqrt(np.mean(corrected ** 2)))
    peak = float(np.max(np.abs(corrected)))

    if label:
        print(f"  {label}: RMS={rms:.2f}c Peak={peak:.1f}c Offset={offset:+.1f}c")
    return rms, peak


# ============================================================================
# Method 1: Sequential (Bordeaux)
# ============================================================================

def optimize_sequential(cfg, verbose=False):
    """Sequential: bore length first, then holes one-by-one."""
    t0 = time.time()
    targets = sorted(cfg["targets"])
    fundamental = min(targets)

    # Phase 1: Bore length from fundamental
    c = SPEED_OF_SOUND
    L_est = c / (4.0 * fundamental) if cfg["closed_top"] else c / (2.0 * fundamental)

    best_L = L_est
    best_err = 1e10
    for L in np.linspace(L_est * 0.8, L_est * 1.2, 20):
        try:
            inst = tmm_instrument_from_radii(
                np.array([cfg["bore_radius"]]), L,
                [], [], [],
                cfg["outer_diameter"], cfg["closed_top"], 0.5,
            )
            wl = inst.find_resonance(c / fundamental, [], 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / fundamental)) if f > 0 else 1e10
            if err < best_err:
                best_err = err
                best_L = L
        except:
            pass

    bore_length = best_L
    bore_radii = np.full(8, cfg["bore_radius"])

    # Phase 2: Place holes one-by-one
    holes_pos = []
    holes_dia = []
    holes_len = []

    for i, target in enumerate(targets):
        target_wl = c / target

        best_pos = 0
        best_err = 1e10

        min_p = holes_pos[-1] + 15 if holes_pos else 30
        max_p = bore_length - 30

        for pos in np.linspace(min_p, max_p, 30):
            pos_list = holes_pos + [pos]
            dia_list = holes_dia + [cfg["hole_diameter"]]
            len_list = holes_len + [cfg["hole_length"]]

            idx = np.argsort(pos_list)
            pos_list = [pos_list[j] for j in idx]
            dia_list = [dia_list[j] for j in idx]
            len_list = [len_list[j] for j in idx]

            fing = ["closed"] * len(pos_list)
            new_idx = list(idx).index(i)
            fing[new_idx] = "open"

            try:
                inst = tmm_instrument_from_radii(
                    bore_radii, bore_length,
                    pos_list, dia_list, len_list,
                    cfg["outer_diameter"], cfg["closed_top"], 0.5,
                )
                wl = inst.find_resonance(target_wl, fing, 1)
                f = inst.frequency_from_wavelength(wl)
                err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
                if err < best_err:
                    best_err = err
                    best_pos = pos
            except:
                pass

        holes_pos.append(best_pos)
        holes_dia.append(cfg["hole_diameter"])
        holes_len.append(cfg["hole_length"])

    # Sort by position
    idx = np.argsort(holes_pos)
    holes_pos = [holes_pos[j] for j in idx]
    holes_dia = [holes_dia[j] for j in idx]
    holes_len = [holes_len[j] for j in idx]

    cfg_out = dict(cfg)
    cfg_out["hole_positions"] = holes_pos
    cfg_out["hole_diameters"] = holes_dia
    cfg_out["hole_lengths"] = holes_len

    elapsed = time.time() - t0
    rms, peak = evaluate(bore_radii, bore_length, cfg_out)
    return rms, peak, elapsed, bore_length, holes_pos


# ============================================================================
# Method 2: Powell+L-BFGS-B with free bore length
# ============================================================================

def optimize_powell_free(cfg, verbose=False, maxiter=600):
    """Powell+L-BFGS-B with bore length as free variable."""
    from scipy.optimize import minimize as sp_minimize

    t0 = time.time()
    n_cp = 6
    c = SPEED_OF_SOUND
    L_est = c / (4.0 * min(cfg["targets"])) if cfg["closed_top"] else c / (2.0 * min(cfg["targets"]))

    hp = cfg.get("hole_positions", [])
    hd = cfg.get("hole_diameters", [])
    hl = cfg.get("hole_lengths", [])

    def objective(x):
        L = x[0]
        radii = np.maximum(x[1:], 3.0)
        try:
            inst = tmm_instrument_from_radii(
                radii, L, hp, hd, hl,
                cfg["outer_diameter"], cfg["closed_top"], 0.5,
            )
            tw = [c / f for f in cfg["targets"]]
            freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 1)
            cents = []
            for a, t in zip(freqs, cfg["targets"]):
                if a > 0 and math.isfinite(a):
                    cents.append(1200.0 * math.log2(a / t))
                else:
                    cents.append(1e6)
            ca = np.array(cents)
            if np.any(np.abs(ca) > 1e5):
                return 1e10
            return float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))
        except:
            return 1e10

    x0 = np.concatenate([[L_est], np.full(n_cp, cfg["bore_radius"])])
    bounds = [(L_est * 0.5, L_est * 2.0)] + [(3.0, cfg["bore_radius"] * 2)] * n_cp

    r1 = sp_minimize(objective, x0, method='Powell', bounds=bounds,
                     options={"maxiter": maxiter * 2 // 3, "ftol": 1e-8})
    r2 = sp_minimize(objective, r1.x, method='L-BFGS-B', bounds=bounds,
                     options={"maxiter": maxiter // 3, "ftol": 1e-10})

    best = r1 if r1.fun < r2.fun else r2
    bore_length = best.x[0]
    radii = np.maximum(best.x[1:], 3.0)

    elapsed = time.time() - t0
    rms, peak = evaluate(radii, bore_length, cfg)
    return rms, peak, elapsed, bore_length


# ============================================================================
# Method 3: Sequential + simultaneous refinement
# ============================================================================

def optimize_seq_refine(cfg, verbose=False):
    """Sequential placement + Powell refinement of everything."""
    from scipy.optimize import minimize as sp_minimize

    # First get sequential result
    rms_seq, peak_seq, t_seq, L_seq, pos_seq = optimize_sequential(cfg)

    t0 = time.time()

    # Now refine: [bore_length, radius_1..n, hole_pos_1..n]
    n_cp = 6
    n_holes = len(pos_seq)
    c = SPEED_OF_SOUND

    hp_init = np.array(pos_seq)
    hd = cfg.get("hole_diameters", [cfg["hole_diameter"]] * n_holes)
    hl = cfg.get("hole_lengths", [cfg["hole_length"]] * n_holes)

    def objective(x):
        L = x[0]
        radii = np.maximum(x[1:1+n_cp], 3.0)
        h_pos = x[1+n_cp:1+n_cp+n_holes]
        try:
            inst = tmm_instrument_from_radii(
                radii, L, h_pos.tolist(), hd, hl,
                cfg["outer_diameter"], cfg["closed_top"], 0.5,
            )
            tw = [c / f for f in cfg["targets"]]
            freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 1)
            cents = []
            for a, t in zip(freqs, cfg["targets"]):
                if a > 0 and math.isfinite(a):
                    cents.append(1200.0 * math.log2(a / t))
                else:
                    cents.append(1e6)
            ca = np.array(cents)
            if np.any(np.abs(ca) > 1e5):
                return 1e10
            return float(np.sqrt(np.mean((ca - np.median(ca)) ** 2)))
        except:
            return 1e10

    x0 = np.concatenate([
        [L_seq],
        np.full(n_cp, cfg["bore_radius"]),
        hp_init,
    ])
    bounds = [
        (L_seq * 0.7, L_seq * 1.3),
    ] + [(3.0, cfg["bore_radius"] * 2)] * n_cp + \
        [(20, L_seq - 20)] * n_holes

    r1 = sp_minimize(objective, x0, method='Powell', bounds=bounds,
                     options={"maxiter": 400, "ftol": 1e-8})
    r2 = sp_minimize(objective, r1.x, method='L-BFGS-B', bounds=bounds,
                     options={"maxiter": 200, "ftol": 1e-10})

    best = r1 if r1.fun < r2.fun else r2
    bore_length = best.x[0]
    radii = np.maximum(best.x[1:1+n_cp], 3.0)
    h_pos = best.x[1+n_cp:1+n_cp+n_holes].tolist()

    elapsed = time.time() - t0 + t_seq
    rms, peak = evaluate(radii, bore_length, cfg,
                         dict(cfg, hole_positions=h_pos))
    return rms, peak, elapsed, bore_length


# ============================================================================
# Run all benchmarks
# ============================================================================

METHODS = {
    "Sequential": optimize_sequential,
    "Powell (free L)": optimize_powell_free,
    "Seq+Refine": optimize_seq_refine,
}

all_results = {}

for inst_name, cfg in INSTRUMENTS.items():
    print(f"\n{'#'*70}")
    print(f"# {cfg['desc']}")
    print(f"# Bore r={cfg['bore_radius']}mm | {len(cfg['targets'])} notes | "
          f"{'closed' if cfg['closed_top'] else 'open'}-top")
    print(f"{'#'*70}")

    results = {}
    for method_name, method_fn in METHODS.items():
        print(f"\n  --- {method_name} ---")
        try:
            rms, peak, elapsed, bore_len = method_fn(cfg)
            results[method_name] = {
                "rms": rms, "peak": peak, "time": elapsed, "bore": bore_len,
            }
            print(f"  => RMS={rms:.2f}c Peak={peak:.1f}c Time={elapsed:.1f}s L={bore_len:.0f}mm")
        except Exception as e:
            print(f"  => FAILED: {e}")
            results[method_name] = {"rms": 1e10, "peak": 1e10, "time": 0, "bore": 0}

    all_results[inst_name] = results

# Summary table
print(f"\n{'#'*70}")
print("# FINAL RESULTS")
print(f"{'#'*70}")
print(f"\n  {'Instrument':<20} {'Method':<18} {'RMS':>8} {'Peak':>8} {'Time':>8} {'Bore':>8}")
print(f"  {'-'*20} {'-'*18} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
for inst_name, results in all_results.items():
    for method_name, data in results.items():
        rms = data["rms"]
        rms_s = f"{rms:.2f}" if rms < 1e5 else "FAIL"
        peak_s = f"{data['peak']:.1f}" if data["peak"] < 1e5 else "—"
        bore_s = f"{data['bore']:.0f}" if data["bore"] > 0 else "—"
        print(f"  {inst_name:<20} {method_name:<18} {rms_s:>8} {peak_s:>8} {data['time']:>7.1f}s {bore_s:>7}")
    print()
