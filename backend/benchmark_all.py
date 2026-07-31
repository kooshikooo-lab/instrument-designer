"""Full benchmark: Sequential + refinement on all instruments."""
import sys, os, time, math
import numpy as np
from scipy.optimize import minimize as sp_min, differential_evolution

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

INSTRUMENTS = {
    "chromatic_flute_C": {
        "desc": "Concert flute in C (Boehm, 17 holes, chromatic C4-C6)",
        "closed_top": False,
        "targets": [
            261.63, 277.18, 293.66, 311.13, 329.63, 349.23,
            369.99, 392.00, 415.30, 440.00, 466.16, 493.88,
            523.25, 554.37, 587.33, 622.25, 659.25, 698.46,
            739.99, 783.99, 830.61, 880.00, 932.33, 987.77,
            1046.50,
        ],
        "names": [
            "C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4","A4","A#4","B4",
            "C5","C#5","D5","D#5","E5","F5","F#5","G5","G#5","A5","A#5","B5","C6",
        ],
        "bore_radius": 9.5, "outer_diameter": 22.0,
        "hole_diameter": 12.5, "hole_length": 3.0,
        "fingerings": [
            ["closed"]*17,  # C4
            ["open"]+["closed"]*16,  # C#4
            ["open"]*2+["closed"]*15,  # D4
            ["open"]*3+["closed"]*14,  # D#4
            ["open"]*4+["closed"]*13,  # E4
            ["open"]*5+["closed"]*12,  # F4
            ["open"]*6+["closed"]*11,  # F#4
            ["open"]*7+["closed"]*10,  # G4
            ["open"]*8+["closed"]*9,   # G#4
            ["open"]*9+["closed"]*8,   # A4
            ["open"]*10+["closed"]*7,  # A#4
            ["open"]*11+["closed"]*6,  # B4
            ["closed"]*17,  # C5 (same as C4, upper register)
            ["open"]+["closed"]*16,  # C#5
            ["open"]*2+["closed"]*15,  # D5
            ["open"]*3+["closed"]*14,  # D#5
            ["open"]*4+["closed"]*13,  # E5
            ["open"]*5+["closed"]*12,  # F5
            ["open"]*6+["closed"]*11,  # F#5
            ["open"]*7+["closed"]*10,  # G5
            ["open"]*8+["closed"]*9,   # G#5
            ["open"]*9+["closed"]*8,   # A5
            ["open"]*10+["closed"]*7,  # A#5
            ["open"]*11+["closed"]*6,  # B5
            ["open"]*12+["closed"]*5,  # C6
        ],
        # Registers: 2 for C4-B4, 3 for C5-C6
        "_n_registers": [2]*12 + [3]*13,
        "_chromatic": True,
        "ranges": {
            "C4_B4": {
                "targets": [
                    261.63, 277.18, 293.66, 311.13, 329.63, 349.23,
                    369.99, 392.00, 415.30, 440.00, 466.16, 493.88,
                ],
                "names": ["C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4","A4","A#4","B4"],
                "fingerings": [
                    ["closed"]*17, ["open"]+["closed"]*16,
                    ["open"]*2+["closed"]*15, ["open"]*3+["closed"]*14,
                    ["open"]*4+["closed"]*13, ["open"]*5+["closed"]*12,
                    ["open"]*6+["closed"]*11, ["open"]*7+["closed"]*10,
                    ["open"]*8+["closed"]*9, ["open"]*9+["closed"]*8,
                    ["open"]*10+["closed"]*7, ["open"]*11+["closed"]*6,
                ],
                "n_registers": [2]*12,
            },
            "C5_C6": {
                "targets": [
                    523.25, 554.37, 587.33, 622.25, 659.25, 698.46,
                    739.99, 783.99, 830.61, 880.00, 932.33, 987.77, 1046.50,
                ],
                "names": ["C5","C#5","D5","D#5","E5","F5","F#5","G5","G#5","A5","A#5","B5","C6"],
                "fingerings": [
                    ["closed"]*17, ["open"]+["closed"]*16,
                    ["open"]*2+["closed"]*15, ["open"]*3+["closed"]*14,
                    ["open"]*4+["closed"]*13, ["open"]*5+["closed"]*12,
                    ["open"]*6+["closed"]*11, ["open"]*7+["closed"]*10,
                    ["open"]*8+["closed"]*9, ["open"]*9+["closed"]*8,
                    ["open"]*10+["closed"]*7, ["open"]*11+["closed"]*6,
                    ["open"]*12+["closed"]*5,
                ],
                "n_registers": [3]*13,
            },
        },
    },
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
    "diatonic_D_chalumeau": {
        "desc": "Diatonic D chalumeau (baroque, closed-open, La Belle Note style)",
        "closed_top": True,
        "targets": [277.2, 293.7, 329.6, 370.0, 392.0, 440.0, 493.9],
        "names": ["C#4", "D4", "E4", "F#4", "G4", "A4", "B4"],
        "bore_radius": 8.0, "outer_diameter": 14.0,
        "hole_diameter": 5.0, "hole_length": 3.0,
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
    if cfg.get("_chromatic", False) and "_n_registers" in cfg:
        n_reg = cfg["_n_registers"]
    else:
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
    """Sequential + global DE + 4-stage L-BFGS-B refinement.

    Delegates to jax_optimizer.refine_sequential for consistent results
    across all benchmark paths.
    """
    from backend.jax_optimizer import refine_sequential
    t0 = time.time()
    rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
        cfg, verbose=False, use_jax_bore=False,
    )
    dt = time.time() - t0
    return rms, L, hp, hd, dt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the TMM bore benchmark suite.")
    parser.add_argument(
        "--instruments", "-i", default=None,
        help="Comma-separated instrument keys to run (default: all). "
             "Keys: " + ", ".join(INSTRUMENTS.keys()),
    )
    parser.add_argument(
        "--no-dask", action="store_true",
        help="Accepted for compatibility; this benchmark runs in-process.",
    )
    parser.add_argument("--dask", action="store_true", help="Ignored (see --no-dask).")
    args = parser.parse_args()

    selected = [s.strip() for s in args.instruments.split(",")] if args.instruments else None
    if selected:
        unknown = [k for k in selected if k not in INSTRUMENTS]
        if unknown:
            parser.error(f"unknown instrument key(s): {', '.join(unknown)}")

    # Run
    all_results = {}
    for name, cfg in INSTRUMENTS.items():
        if selected and name not in selected:
            continue
        print(f"\n{'#'*60}")
        print(f"# {cfg['desc']}")
        print(f"{'#'*60}")

        # Chromatic instruments use per-note registers (not compatible with
        # sequential optimizer — the 17-hole geometry is for validation only).
        # Evaluate them directly via eval_all.
        if cfg.get("_chromatic", False):
            print(f"\n  --- Direct evaluation (chromatic instrument) ---")
            try:
                # Build instrument from the model
                model = cfg.get("_chromatic_model")
                if model is None:
                    from backend.chromatic_flute import ChromaticFluteModel
                    model = ChromaticFluteModel()
                inst = model.build_instrument()
                tw = [c / f for f in cfg["targets"]]
                n_reg = cfg.get("_n_registers", 2)
                freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], n_reg)
                cents = []
                for a, t in zip(freqs, cfg["targets"]):
                    cents.append(1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10)
                ca = np.array(cents)
                rms = float(np.sqrt(np.mean(ca ** 2))) if np.all(np.isfinite(ca)) else 1e10
                r = {
                    "Eval": {"rms": rms, "time": 0, "bore": 613, "holes": 17},
                }
                # Also report per-range
                ranges = cfg.get("ranges", {})
                for rname, rcfg in ranges.items():
                    if not rcfg.get("targets"):
                        continue
                    rtw = [c / f for f in rcfg["targets"]]
                    rfreqs = inst.compute_fingered_frequencies(
                        rtw, rcfg["fingerings"], rcfg["n_registers"])
                    rcents = []
                    for a, t in zip(rfreqs, rcfg["targets"]):
                        rcents.append(1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10)
                    rca = np.array(rcents)
                    rrms = float(np.sqrt(np.mean(rca ** 2))) if np.all(np.isfinite(rca)) else 1e10
                    r[f"Eval_{rname}"] = {"rms": rrms, "time": 0, "bore": 613, "holes": 17}
                    print(f"    {rname}: RMS={rrms:.2f}c")
                print(f"    Full range: RMS={rms:.2f}c")
            except Exception as e:
                import traceback
                print(f"    FAILED: {e}")
                traceback.print_exc()
                r = {"Eval": {"rms": 1e10, "time": 0, "bore": 0, "holes": 0}}
            all_results[name] = r
            continue

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
