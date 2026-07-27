"""
Two-phase optimizer: phase cost (fast) coarse search → peak cost (correct) refinement.

Phase 1: DE + phase_cost_with_offset — fast (1.4ms/call), explores global space
Phase 2: L-BFGS-B + peak_cost_nearest — correct (140ms/call), refines to optimum

Test on recorder (chalumier achieved 24.8c evenness).
"""
import sys, os, time, math, re, json
import numpy as np
from scipy.optimize import differential_evolution, minimize as sp_min

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from tmm_acoustics import TMMInstrument, SPEED_OF_SOUND, tmm_instrument_from_radii

c = SPEED_OF_SOUND
SEMITONE_MAP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

def note_to_freq(name):
    if name.endswith('hz'):
        return float(name[:-2])
    mult = 1.0
    if '*' in name:
        idx = name.index('*')
        mult = float(name[idx+1:])
        name = name[:idx]
    s = SEMITONE_MAP[name[0].upper()]
    rest = name[1:]
    if rest and rest[0] == 'b': s -= 1; rest = rest[1:]
    if rest and rest[0] in ('#', 's'): s += 1; rest = rest[1:]
    s += 12 * int(rest) if rest else 0
    return 440.0 * 2.0**((s - 57) / 12.0) * mult

def cents_error(actual, target):
    if actual <= 0 or target <= 0: return 1e10
    return 1200.0 * math.log2(actual / target)

def parse_chal_fingerings(spec_path):
    with open(spec_path) as f:
        content = f.read()
    fingerings = []
    m = re.search(r'fingerings\s*=\s*\[', content)
    if not m: return fingerings
    start = m.end()
    depth = 1; i = start
    while i < len(content) and depth > 0:
        if content[i] == '[': depth += 1
        elif content[i] == ']': depth -= 1
        i += 1
    block = content[start:i-1]
    for entry in re.finditer(r'\{([^}]+)\}', block):
        inner = entry.group(1)
        note_m = re.search(r'noteName\s*=\s*"([^"]+)"', inner)
        if not note_m:
            note_m = re.search(r'note\s*=\s*"([^"]+)"', inner)
        fingers_m = re.search(r'fingers\s*=\s*\[([^\]]+)\]', inner)
        if fingers_m:
            parts = re.findall(r'"([^"]*)"', fingers_m.group(1))
            fingers_str = ''.join(parts)
        else:
            fingers_m = re.search(r'fingers\s*=\s*"([^"]+)"', inner)
            fingers_str = fingers_m.group(1) if fingers_m else ''
        nth_m = re.search(r'nth\s*=\s*(\d+)', inner)
        if note_m and fingers_str:
            nth = int(nth_m.group(1)) if nth_m else 1
            fingerings.append((note_m.group(1), fingers_str, nth))
    return fingerings

def parse_json5(path):
    with open(path) as f:
        raw = f.read()
    cleaned = re.sub(r'//.*?$', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r'"\1":', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)

def interpolate_outer(outer_pos, outer_diams, inner_pos):
    result = []
    for p in inner_pos:
        if p <= outer_pos[0]:
            result.append(outer_diams[0])
        elif p >= outer_pos[-1]:
            result.append(outer_diams[-1])
        else:
            for j in range(len(outer_pos) - 1):
                if outer_pos[j] <= p <= outer_pos[j+1]:
                    t = (p - outer_pos[j]) / (outer_pos[j+1] - outer_pos[j])
                    result.append((1-t)*outer_diams[j] + t*outer_diams[j+1])
                    break
    if len(result) != len(inner_pos):
        result = [d + 6.0 for d in [10.0]*len(inner_pos)]
    return result


def detect_registers(inst, targets, fing_lists, max_reg=5):
    """Detect the best register for each fingering using peak search."""
    regs = []
    for tgt, fl in zip(targets, fing_lists):
        wl_guess = c / tgt
        best_pr = 1
        best_dist = 1e10
        for pr in range(1, max_reg + 1):
            try:
                wl = inst.find_resonance(wl_guess, fl, n_register=pr)
                f = inst.frequency_from_wavelength(wl)
                dist = abs(cents_error(f, tgt))
                if dist < best_dist:
                    best_dist = dist
                    best_pr = pr
            except:
                continue
        regs.append(best_pr)
    return regs


def peak_cost_nearest(inst, targets, fing_lists, detected_regs):
    """Peak-matching cost: find nearest resonance peak to each target, compute evenness."""
    cents = []
    for tgt, fl, pr in zip(targets, fing_lists, detected_regs):
        try:
            wl = inst.find_resonance(c / tgt, fl, n_register=pr)
            f = inst.frequency_from_wavelength(wl)
            cents.append(cents_error(f, tgt))
        except:
            cents.append(1e10)
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    med = np.median(ca)
    return float(np.sqrt(np.mean((ca - med) ** 2)))


def evaluate_and_print(inst, fingerings, transpose, label=""):
    """Evaluate instrument against fingering chart and print results."""
    results = []
    for note_name, fingering_str, nth_default in fingerings:
        target_freq = note_to_freq(note_name)
        if transpose:
            target_freq *= 2.0 ** (transpose / 12.0)
        fl = ['open' if ch in ('O', 'o') else 'closed' for ch in fingering_str]
        while len(fl) < inst.n_holes:
            fl.append('open')
        fl = fl[:inst.n_holes]
        wl_guess = c / target_freq
        best_dist = 1e10
        best_freq = 0
        best_pr = 1
        for pr in range(1, 6):
            try:
                wl = inst.find_resonance(wl_guess, fl, n_register=pr)
                f = inst.frequency_from_wavelength(wl)
                dist = abs(cents_error(f, target_freq))
                if dist < best_dist:
                    best_dist = dist
                    best_freq = f
                    best_pr = pr
            except:
                continue
        err = cents_error(best_freq, target_freq) if best_freq > 0 else 1e10
        results.append({'note': note_name, 'target': target_freq, 'actual': best_freq,
                        'cents': err, 'fingering': fingering_str, 'pr': best_pr})
    ca = np.array([r['cents'] for r in results if abs(r['cents']) < 1e5])
    med = np.median(ca)
    even = float(np.sqrt(np.mean((ca - med) ** 2)))
    off = float(med)
    mean_abs = float(np.mean(np.abs(ca)))
    max_abs = float(np.max(np.abs(ca)))
    print(f"  {label}: even={even:.1f}c off={off:+.1f}c mean_abs={mean_abs:.1f}c max_abs={max_abs:.1f}c")
    for r in results:
        if abs(r['cents']) < 1e5:
            print(f"    {r['note']:>6} {r.get('fingering',''):>10} pr={r.get('pr','?')} -> {r['cents']:+7.1f}c")
    return even


# ============================================================================
# Phase 1: DE + phase cost (fast global search)
# ============================================================================

def phase1_de_search(bore_length, n_holes, hole_lens, targets, fing_lists,
                     n_register, bore_bounds_range, hole_pos_bounds_range,
                     popsize=15, maxiter=30, seed=42, verbose=True):
    """
    Phase 1: Differential Evolution with phase cost (fast).

    Variables: bore_radii (n_bore_ctrl), hole_diameters (n_holes), hole_positions (n_holes)
    Cost: phase_cost_with_offset — fast, smooth, but register-agnostic
    """
    n_bore_ctrl = 6  # bore shape control points
    n_vars = n_bore_ctrl + n_holes + n_holes
    bore_min, bore_max = bore_bounds_range
    hp_min, hp_max = hole_pos_bounds_range
    hd_min, hd_max = 3.0, 15.0

    def cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])
        # Enforce minimum hole spacing
        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + 3:
                return 1e6
        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lens,
                outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
            )
            return inst.phase_cost_with_offset(targets, fing_lists, n_register=n_register)
        except:
            return 1e6

    bounds = (
        [(bore_min, bore_max)] * n_bore_ctrl
        + [(hd_min, hd_max)] * n_holes
        + [(hp_min, hp_max)] * n_holes
    )

    t0 = time.time()
    result = differential_evolution(
        cost, bounds, seed=seed, maxiter=maxiter, popsize=popsize,
        tol=1e-6, mutation=(0.5, 1.0), recombination=0.7,
        disp=verbose,
    )
    elapsed = time.time() - t0
    if verbose:
        print(f"  Phase 1 DE: cost={result.fun:.6f} ({elapsed:.1f}s, {result.nfev} evals)")
    return result.x, result.fun, elapsed


# ============================================================================
# Phase 2: L-BFGS-B + peak cost (correct local refinement)
# ============================================================================

def phase2_lbfgsb_refine(x0, bore_length, n_holes, hole_lens, targets, fing_lists,
                         detected_regs, bore_bounds_range, hole_pos_bounds_range,
                         n_iters=500, verbose=True):
    """
    Phase 2: L-BFGS-B with peak cost (correct).

    Uses peak_cost_nearest which correctly identifies register.
    """
    n_bore_ctrl = 6
    bore_min, bore_max = bore_bounds_range
    hp_min, hp_max = hole_pos_bounds_range
    hd_min, hd_max = 3.0, 15.0

    def cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])
        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + 3:
                return 1e6
        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lens,
                outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
            )
            return peak_cost_nearest(inst, targets, fing_lists, detected_regs)
        except:
            return 1e6

    bounds = (
        [(bore_min, bore_max)] * n_bore_ctrl
        + [(hd_min, hd_max)] * n_holes
        + [(hp_min, hp_max)] * n_holes
    )

    t0 = time.time()
    result = sp_min(cost, x0, method='L-BFGS-B', bounds=bounds,
                    options={'maxiter': n_iters, 'ftol': 1e-12})
    elapsed = time.time() - t0
    if verbose:
        print(f"  Phase 2 L-BFGS-B: cost={result.fun:.4f} ({elapsed:.1f}s, {result.nfev} evals)")
    return result.x, result.fun, elapsed


# ============================================================================
# Main: test on recorder
# ============================================================================

def main():
    print("=" * 70)
    print("  TWO-PHASE OPTIMIZER: Phase cost (fast) -> Peak cost (correct)")
    print("=" * 70)

    instruments = [
        {
            'name': 'dwhistle',
            'spec': os.path.join('chalumier', 'examples', 'dwhistle.chal'),
            'json5': os.path.join('chalumier', 'test-output', 'd-whistle-parameters.json5'),
            'transpose': 12,
            'de_popsize': 10,
            'de_maxiter': 15,
        },
        {
            'name': 'recorder',
            'spec': os.path.join('chalumier', 'examples', 'recorder.chal'),
            'json5': os.path.join('chalumier', 'test-output', 'bench-recorder', 'recorder-parameters.json5'),
            'transpose': 12,
            'de_popsize': 10,
            'de_maxiter': 10,
        },
    ]

    for inst_info in instruments:
        name = inst_info['name']
        if not os.path.exists(inst_info['json5']):
            print(f"\n  {name}: SKIPPED (no cached output)")
            continue

        print(f"\n{'='*70}")
        print(f"  {name}")
        print(f"{'='*70}")

        params = parse_json5(inst_info['json5'])
        fingerings = parse_chal_fingerings(inst_info['spec'])
        transpose = inst_info['transpose']

        # Extract chalumier's optimized bore profile
        inner = params.get('inner', {})
        pos = [float(p) for p in inner.get('pos', [])]
        low = [float(d) for d in inner.get('low', [])]
        high = [float(d) for d in inner.get('high', low)]
        diameters = [(l + h) / 2.0 for l, h in zip(low, high)]

        outer_data = params.get('outer', {})
        outer_pos = [float(p) for p in outer_data.get('pos', [])]
        outer_low = [float(d) for d in outer_data.get('low', [])]
        outer_high = [float(d) for d in outer_data.get('high', outer_low)]
        outer_diams = [(l + h) / 2.0 for l, h in zip(outer_low, outer_high)]

        hole_pos = [float(p) for p in params.get('holePositions', [])]
        hole_diams = [float(d) for d in params.get('holeDiameters', [])]
        hole_lens = [float(l) for l in params.get('holeLengths', [3.5]*len(hole_pos))]

        n_holes = len(hole_pos)
        bore_length = pos[-1]

        # Build target frequencies and fingering lists
        targets = []
        fing_lists = []
        for note, fs, nth in fingerings:
            freq = note_to_freq(note)
            if transpose:
                freq *= 2.0 ** (transpose / 12.0)
            targets.append(freq)
            fl = ['open' if ch in ('O', 'o') else 'closed' for ch in fs]
            while len(fl) < n_holes: fl.append('open')
            fing_lists.append(fl[:n_holes])
        targets = np.array(targets)

        print(f"  Bore length: {bore_length:.1f}mm, {n_holes} holes")
        print(f"  {len(fingerings)} fingerings, {len(targets)} target frequencies")

        # ---- Evaluate chalumier's output as-is ----
        inst0 = TMMInstrument(
            inner_positions=pos, inner_diameters=diameters,
            outer_diameters=interpolate_outer(outer_pos, outer_diams, pos),
            hole_positions=hole_pos, hole_diameters=hole_diams, hole_lengths=hole_lens,
            closed_top=False, cone_step=0.125,
        )
        print(f"\n  Chalumier output (as-is in our TMM):")
        chal_even = evaluate_and_print(inst0, fingerings, transpose, "Chalumier")

        # ---- Phase 1: DE with phase cost (fast global search) ----
        print(f"\n  --- Phase 1: DE + phase cost (fast) ---")
        bore_ctrl = 6
        bore_min = min(diameters) * 0.4
        bore_max = max(diameters) * 1.5
        hp_min = 10.0
        hp_max = bore_length - 10.0

        x1, cost1, t1 = phase1_de_search(
            bore_length, n_holes, hole_lens, targets, fing_lists,
            n_register=2,
            bore_bounds_range=(bore_min, bore_max),
            hole_pos_bounds_range=(hp_min, hp_max),
            popsize=inst_info.get('de_popsize', 10),
            maxiter=inst_info.get('de_maxiter', 15),
            seed=42,
        )

        # Build instrument from Phase 1 result and evaluate
        radii1 = x1[:bore_ctrl]
        hd1 = x1[bore_ctrl:bore_ctrl + n_holes]
        hp1 = sorted(x1[bore_ctrl + n_holes:])
        inst1 = tmm_instrument_from_radii(
            radii1, bore_length, hp1, hd1, hole_lens,
            outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
        )
        print(f"\n  After Phase 1 (DE + phase cost):")
        p1_even = evaluate_and_print(inst1, fingerings, transpose, "Phase 1")

        # Detect registers from Phase 1 result
        regs1 = detect_registers(inst1, targets, fing_lists)
        print(f"  Detected registers: {regs1}")

        # ---- Phase 2: L-BFGS-B with peak cost (correct refinement) ----
        print(f"\n  --- Phase 2: L-BFGS-B + peak cost (correct) ---")
        x2, cost2, t2 = phase2_lbfgsb_refine(
            x1, bore_length, n_holes, hole_lens, targets, fing_lists,
            regs1,
            bore_bounds_range=(bore_min, bore_max),
            hole_pos_bounds_range=(hp_min, hp_max),
            n_iters=500,
        )

        # Build instrument from Phase 2 result and evaluate
        radii2 = x2[:bore_ctrl]
        hd2 = x2[bore_ctrl:bore_ctrl + n_holes]
        hp2 = sorted(x2[bore_ctrl + n_holes:])
        inst2 = tmm_instrument_from_radii(
            radii2, bore_length, hp2, hd2, hole_lens,
            outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
        )
        print(f"\n  After Phase 2 (L-BFGS-B + peak cost):")
        p2_even = evaluate_and_print(inst2, fingerings, transpose, "Phase 2")

        # ---- Summary ----
        print(f"\n  SUMMARY:")
        print(f"    Chalumier:  {chal_even:.1f}c")
        print(f"    Phase 1:    {p1_even:.1f}c  (DE + phase cost, {t1:.1f}s)")
        print(f"    Phase 2:    {p2_even:.1f}c  (L-BFGS-B + peak cost, {t2:.1f}s)")
        print(f"    Total:      {t1 + t2:.1f}s")
        print(f"    Bore radii: {[f'{r:.1f}' for r in radii2.tolist()]}")
        print(f"    Hole pos:   {[f'{p:.1f}' for p in hp2]}")
        print(f"    Hole diams: {[f'{d:.2f}' for d in hd2.tolist()]}")

    print("\n" + "=" * 70)
    print("  DONE")
    print("=" * 70)


if __name__ == '__main__':
    main()
