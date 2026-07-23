"""
Minimal deep diagnosis — avoids find_resonance which may hang.
Only uses resonance_phase directly.
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import (
    TMMInstrument, tmm_instrument_from_radii, SPEED_OF_SOUND,
    Profile, Hole, end_flange_length_correction, circle_area,
    pipe_reply_phase, junction2_reply_phase, junction3_reply_phase,
    tanner, untanner, hole_length_correction,
)

c = SPEED_OF_SOUND
SEP = "=" * 72

XAPHOON = {
    "bore_radius": 7.0, "bore_length": 662.0, "outer_diameter": 20.0,
    "hole_diameter": 6.5, "hole_length": 3.0, "closed_top": False,
    "hole_positions": [101, 169, 457, 472, 487, 502],
    "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9],
    "names": ["C4", "D4", "E4", "F4", "G4", "A4", "B4"],
}
SAX = {
    "bore_radius": 6.0, "bore_length": 371.0, "outer_diameter": 20.0,
    "hole_diameter": 6.5, "hole_length": 3.0, "closed_top": False,
    "hole_positions": [60, 100, 160, 200, 240, 280, 320],
    "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0],
    "names": ["Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5"],
}


def make_fingerings(n_holes, n_notes):
    fing = []
    for i in range(n_notes):
        row = [Hole.OPEN if h < i else Hole.CLOSED for h in range(n_holes)]
        fing.append(row)
    return fing


def build_inst(cfg):
    n = len(cfg["hole_positions"])
    radii = np.array([cfg["bore_radius"]])
    hp = cfg["hole_positions"]
    hd = [cfg["hole_diameter"]] * n
    hl = [cfg["hole_length"]] * n
    return tmm_instrument_from_radii(
        radii, cfg["bore_length"], hp, hd, hl,
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )


def cents(f, t):
    if f <= 0 or t <= 0 or not math.isfinite(f):
        return 1e10
    return 1200.0 * math.log2(f / t)


def find_resonance_manual(inst, wl_guess, fingerings, n_reg=2, max_steps=200, step_size=1.005):
    """Manual bisection-style resonance finder, avoids the potentially-hanging wavelength_near."""
    w = wl_guess
    p = inst.resonance_phase(w, fingerings)
    dev = p - n_reg
    # Walk right until phase > n_reg
    for _ in range(max_steps):
        w2 = w * step_size
        p2 = inst.resonance_phase(w2, fingerings)
        dev2 = p2 - n_reg
        if dev * dev2 <= 0:
            # sign change bracket
            break
        w, p, dev = w2, p2, dev2
    else:
        # Also try walking left
        w = wl_guess
        p = inst.resonance_phase(w, fingerings)
        dev = p - n_reg
        for _ in range(max_steps):
            w2 = w / step_size
            p2 = inst.resonance_phase(w2, fingerings)
            dev2 = p2 - n_reg
            if dev * dev2 <= 0:
                break
            w, p, dev = w2, p2, dev2

    # Bisect the bracket
    w_lo, w_hi = min(w, w2), max(w, w2)
    for _ in range(60):
        w_mid = 0.5 * (w_lo + w_hi)
        p_mid = inst.resonance_phase(w_mid, fingerings) - n_reg
        if p_mid > 0:
            w_hi = w_mid
        else:
            w_lo = w_mid
    return 0.5 * (w_lo + w_hi)


print(SEP)
print("  PART A: Full resonance trace")
print(SEP)

for label, cfg in [("XAPHOON", XAPHOON), ("SOPRANO SAX", SAX)]:
    print(f"\n--- {label} ---")
    inst = build_inst(cfg)
    n_holes = len(cfg["hole_positions"])
    n_reg = 2
    fingerings = make_fingerings(n_holes, len(cfg["targets"]))

    bore_d = cfg["bore_radius"] * 2
    efc = end_flange_length_correction(cfg["outer_diameter"], bore_d)
    open_corr = hole_length_correction(cfg["hole_diameter"], bore_d, False)
    print(f"  Bore: L={cfg['bore_length']}mm, D={bore_d}mm")
    print(f"  Hole positions: {cfg['hole_positions']}")
    print(f"  Number of instrument holes: {inst.n_holes}")
    print(f"  End flange correction: {efc:.3f}mm")
    print(f"  Open hole correction: {open_corr:.3f}mm")
    print(f"  Actions: {len(inst.actions)}")

    # Count action types
    from collections import Counter
    types = Counter(a[0] for a in inst.actions)
    print(f"  Action types: {dict(types)}")

    print(f"\n  {'Note':<6} {'Target':>8} {'TargWl':>10} {'Phase':>12} {'Dev':>12} {'Fing'}")
    print(f"  {'-'*6} {'-'*8} {'-'*10} {'-'*12} {'-'*12} {'-'*20}")

    for i, (name, target) in enumerate(zip(cfg["names"], cfg["targets"])):
        target_wl = c / target
        fing = fingerings[i]
        fing_str = "".join("O" if f == Hole.OPEN else "C" for f in fing)
        phase = inst.resonance_phase(target_wl, fing)
        dev = phase - n_reg
        print(f"  {name:<6} {target:>8.1f} {target_wl:>10.1f} {phase:>12.6f} {dev:>12.6f}  {fing_str}")

    # Now find actual resonances
    print(f"\n  Actual resonances (n_register={n_reg}):")
    print(f"  {'Note':<6} {'Target':>8} {'Freq':>10} {'CentsErr':>10}")
    print(f"  {'-'*6} {'-'*8} {'-'*10} {'-'*10}")
    for i, (name, target) in enumerate(zip(cfg["names"], cfg["targets"])):
        target_wl = c / target
        fing = fingerings[i]
        wl_res = find_resonance_manual(inst, target_wl, fing, n_reg)
        freq_res = c / wl_res
        err = cents(freq_res, target)
        print(f"  {name:<6} {target:>8.1f} {freq_res:>10.1f} {err:>+10.2f}")


print(f"\n{SEP}")
print("  PART B: Cumulative vs Independent fingering")
print(SEP)

for label, cfg in [("XAPHOON", XAPHOON), ("SOPRANO SAX", SAX)]:
    print(f"\n--- {label} ---")
    n_holes = len(cfg["hole_positions"])
    n_reg = 2

    # Cumulative
    cum_fing = make_fingerings(n_holes, len(cfg["targets"]))
    print(f"\n  CUMULATIVE fingering:")
    for i in range(len(cfg["names"])):
        print(f"    {cfg['names'][i]}: {''.join('O' if f == Hole.OPEN else 'C' for f in cum_fing[i])}")

    cum_errs = []
    for i, (name, target) in enumerate(zip(cfg["names"], cfg["targets"])):
        inst = build_inst(cfg)
        fing = cum_fing[i]
        wl_res = find_resonance_manual(inst, c / target, fing, n_reg)
        freq_res = c / wl_res
        err = cents(freq_res, target)
        cum_errs.append(err)
        print(f"    {name}: {err:>+.2f}c  (target={target:.1f}, got={freq_res:.1f})")
    rms_cum = math.sqrt(sum(e**2 for e in cum_errs) / len(cum_errs))
    print(f"  RMS(cumulative) = {rms_cum:.2f}c")

    # Independent
    print(f"\n  INDEPENDENT fingering:")
    ind_errs = []
    for i, (name, target) in enumerate(zip(cfg["names"], cfg["targets"])):
        inst = build_inst(cfg)
        if i == 0:
            fing = [Hole.CLOSED] * n_holes
        else:
            fing = [Hole.CLOSED] * n_holes
            fing[i - 1] = Hole.OPEN
        fing_str = ''.join('O' if f == Hole.OPEN else 'C' for f in fing)
        wl_res = find_resonance_manual(inst, c / target, fing, n_reg)
        freq_res = c / wl_res
        err = cents(freq_res, target)
        ind_errs.append(err)
        print(f"    {name} {fing_str}: {err:>+.2f}c  (target={target:.1f}, got={freq_res:.1f})")
    rms_ind = math.sqrt(sum(e**2 for e in ind_errs) / len(ind_errs))
    print(f"  RMS(independent) = {rms_ind:.2f}c")


print(f"\n{SEP}")
print("  PART C: Simple tube (no holes) — verify basic TMM model")
print(SEP)

for label, cfg in [("XAPHOON", XAPHOON), ("SOPRANO SAX", SAX)]:
    print(f"\n--- {label} ---")
    inst = build_inst(cfg)  # won't use holes below
    # Build holeless
    radii = np.array([cfg["bore_radius"]])
    inst0 = tmm_instrument_from_radii(
        radii, cfg["bore_length"], [], [], [],
        cfg["outer_diameter"], cfg["closed_top"], 0.5,
    )

    L = cfg["bore_length"]
    for n_reg in range(1, 6):
        wl_guess = 2.0 * L / n_reg
        wl = find_resonance_manual(inst0, wl_guess, [], n_reg=n_reg)
        freq = c / wl
        if cfg["closed_top"]:
            expected = n_reg * c / (4.0 * L)
        else:
            expected = n_reg * c / (2.0 * L)
        err = cents(freq, expected)
        print(f"  Reg {n_reg}: wl={wl:.1f}mm, freq={freq:.1f}Hz, expected={expected:.1f}Hz, err={err:+.2f}c")

    # Phase at fundamental target
    target_wl = c / cfg["targets"][0]
    phase = inst0.resonance_phase(target_wl, [])
    print(f"  Phase at fundamental target wl={target_wl:.1f}mm: {phase:.6f} (want n_reg=2)")
    print(f"  Deviation: {phase - 2:.6f}")


print(f"\n{SEP}")
print("  PART D: Bore profile and action chain")
print(SEP)

for label, cfg in [("XAPHOON", XAPHOON), ("SOPRANO SAX", SAX)]:
    print(f"\n--- {label} ---")
    inst = build_inst(cfg)

    sp = inst.stepped_inner
    print(f"\n  Stepped bore profile ({len(sp.pos)} points):")
    for i in range(len(sp.pos)):
        print(f"    pos={sp.pos[i]:>8.1f}mm  low={sp.low[i]:.3f}mm  high={sp.high[i]:.3f}mm")

    print(f"\n  Action chain:")
    pos = -end_flange_length_correction(
        inst.outer.at(0.0, use_high=True),
        inst.stepped_inner.at(0.0, use_high=True),
    )
    print(f"    start_pos = {pos:.3f}mm (after flange correction)")
    for j, a in enumerate(inst.actions):
        if a[0] == 'pipe':
            print(f"    [{j:>2}] PIPE  len={a[1]:>8.2f}mm  cumul={pos + a[1]:.1f}mm")
            pos += a[1]
        elif a[0] == 'junction2':
            db = 2 * math.sqrt(a[2] / math.pi)
            da = 2 * math.sqrt(a[1] / math.pi)
            print(f"    [{j:>2}] STEP  {db:.3f}mm -> {da:.3f}mm  @{pos:.1f}mm")
        elif a[0] == 'hole':
            db = 2 * math.sqrt(a[3] / math.pi)
            dh = 2 * math.sqrt(a[4] / math.pi)
            print(f"    [{j:>2}] HOLE  idx={a[1]}  bore={db:.2f}mm  hole={dh:.2f}mm  "
                  f"open_L={a[4]:.2f}mm  closed_L={a[5]:.2f}mm  @{pos:.1f}mm")

    hp = cfg["hole_positions"]
    if len(hp) > 1:
        gaps = [hp[i+1] - hp[i] for i in range(len(hp)-1)]
        print(f"\n  Hole gaps: {gaps}")
        print(f"  Last hole to end: {cfg['bore_length'] - hp[-1]:.0f}mm")


print(f"\n{SEP}")
print("  DIAGNOSIS COMPLETE")
print(SEP)
