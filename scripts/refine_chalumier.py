"""
Test: load chalumier's optimized output, refine with L-BFGS-B.

This answers the key question: is our TMM model accurate enough to match
chalumier, and can our optimizer improve on chalumier's design?
"""
import sys, os, time, json, re, math
import numpy as np
from scipy.optimize import minimize as sp_min
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from tmm_acoustics import TMMInstrument, SPEED_OF_SOUND

c = SPEED_OF_SOUND
SEMITONE_MAP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

def note_to_freq(name):
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

def evaluate_inst(inst, fingerings, transpose=0, label=""):
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
                        'cents': err, 'nth': nth_default, 'fingering': fingering_str, 'pr': best_pr})
    return results

def print_results(results, label=""):
    ca = np.array([r['cents'] for r in results if abs(r['cents']) < 1e5])
    med = np.median(ca)
    even = float(np.sqrt(np.mean((ca - med)**2)))
    off = float(med)
    mean_abs = float(np.mean(np.abs(ca)))
    max_abs = float(np.max(np.abs(ca)))
    print(f"  {label}: even={even:.1f}c off={off:+.1f}c mean_abs={mean_abs:.1f}c max_abs={max_abs:.1f}c")
    for r in results:
        if abs(r['cents']) < 1e5:
            print(f"    {r['note']:>6} {r.get('fingering',''):>10} pr={r.get('pr','?')} -> {r['cents']:+7.1f}c")
    return even

def refine_with_lbfgsb(inst, inner_pos, inner_diams, outer_at, hole_pos, hole_diams, hole_lens,
                        fingerings, targets, detected_regs, transpose=0,
                        bore_length=None, n_iters=300):
    """Refine chalumier's bore with L-BFGS-B, optimizing bore shape + hole diameters."""
    n_bore = len(inner_pos)
    n_holes = len(hole_pos)
    if bore_length is None:
        bore_length = inner_pos[-1]
    OD = float(np.mean(outer_at))

    def cost_fn(x):
        radii = x[:n_bore]
        hd = x[n_bore:n_bore+n_holes]
        try:
            inst2 = TMMInstrument(
                inner_positions=inner_pos.tolist(),
                inner_diameters=(radii * 2).tolist(),
                outer_diameters=[OD] * n_bore,
                hole_positions=hole_pos,
                hole_diameters=[float(d) for d in hd],
                hole_lengths=hole_lens,
                closed_top=False, cone_step=0.125,
            )
        except:
            return 1e10
        cents = []
        for tgt, fl, pr in zip(targets, fingerings, detected_regs):
            try:
                wl = inst2.find_resonance(c / tgt, fl, n_register=pr)
                f = inst2.frequency_from_wavelength(wl)
                cents.append(cents_error(f, tgt))
            except:
                cents.append(1e10)
        ca = np.array(cents)
        if np.any(np.abs(ca) > 1e5): return 1e10
        med = np.median(ca)
        return float(np.sqrt(np.mean((ca - med)**2)))

    x0 = np.concatenate([
        np.array(inner_diams) / 2.0,
        np.array(hole_diams),
    ])
    bore_bounds = [(3.0, 20.0)] * n_bore
    hole_bounds = [(2.0, 20.0)] * n_holes
    bounds = bore_bounds + hole_bounds

    t0 = time.time()
    result = sp_min(cost_fn, x0, method='L-BFGS-B', bounds=bounds,
                    options={'maxiter': n_iters, 'ftol': 1e-10})
    elapsed = time.time() - t0

    refined_radii = result.x[:n_bore]
    refined_hd = result.x[n_bore:n_bore+n_holes]
    inst_refined = TMMInstrument(
        inner_positions=inner_pos.tolist(),
        inner_diameters=(refined_radii * 2).tolist(),
        outer_diameters=[OD] * n_bore,
        hole_positions=hole_pos,
        hole_diameters=[float(d) for d in refined_hd],
        hole_lengths=hole_lens,
        closed_top=False, cone_step=0.125,
    )
    return inst_refined, result, elapsed

def main():
    print("="*70)
    print("  REFINING CHALUMIER OUTPUT WITH L-BFGS-B")
    print("="*70)

    instruments = [
        {
            'name': 'dwhistle',
            'spec': os.path.join('chalumier', 'examples', 'dwhistle.chal'),
            'json5': os.path.join('chalumier', 'test-output', 'd-whistle-parameters.json5'),
            'transpose': 12,
        },
        {
            'name': 'recorder',
            'spec': os.path.join('chalumier', 'examples', 'recorder.chal'),
            'json5': os.path.join('chalumier', 'test-output', 'bench-recorder', 'recorder-parameters.json5'),
            'transpose': 12,
        },
        {
            'name': 'folkshawm',
            'spec': os.path.join('chalumier', 'examples', 'folkshawm.chal'),
            'json5': os.path.join('chalumier', 'test-output', 'bench-folkshawm', 'folkShawm-parameters.json5'),
            'transpose': 0,
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

        # Extract bore profile
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
        outer_at = interpolate_outer(outer_pos, outer_diams, pos)

        hole_pos = [float(p) for p in params.get('holePositions', [])]
        hole_diams = [float(d) for d in params.get('holeDiameters', [])]
        hole_lens = [float(l) for l in params.get('holeLengths', [3.5]*len(hole_pos))]
        cone_step = params.get('coneStep', 0.125)

        n_holes = len(hole_pos)
        bore_length = pos[-1]

        # Build fingering lists + targets
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

        # Build initial TMM and evaluate
        inst0 = TMMInstrument(
            inner_positions=pos, inner_diameters=diameters, outer_diameters=outer_at,
            hole_positions=hole_pos, hole_diameters=hole_diams, hole_lengths=hole_lens,
            closed_top=params.get('closedTop', False), cone_step=cone_step,
        )
        print(f"  Chalumier output (as-is in our TMM):")
        results0 = evaluate_inst(inst0, fingerings, transpose)
        print_results(results0, "Initial")

        # Detect registers using chalumier's bore
        detected_regs = []
        for tgt, fl in zip(targets, fing_lists):
            wl_guess = c / tgt
            best_pr = 1
            best_dist = 1e10
            for pr in range(1, 6):
                try:
                    wl = inst0.find_resonance(wl_guess, fl, n_register=pr)
                    f = inst0.frequency_from_wavelength(wl)
                    dist = abs(cents_error(f, tgt))
                    if dist < best_dist:
                        best_dist = dist
                        best_pr = pr
                except:
                    continue
            detected_regs.append(best_pr)
        print(f"  Detected registers: {detected_regs}")

        # Refine with L-BFGS-B
        print(f"\n  Refining with L-BFGS-B (bore shape + hole diameters)...")
        for n_iter in [100, 300, 500]:
            inst_r, res, elapsed = refine_with_lbfgsb(
                inst0, np.array(pos), np.array(diameters), outer_at,
                hole_pos, hole_diams, hole_lens,
                fing_lists, targets, detected_regs, n_iters=n_iter,
            )
            print(f"\n  After {n_iter} iters ({elapsed:.1f}s, cost={res.fun:.4f}):")
            results_r = evaluate_inst(inst_r, fingerings, transpose)
            print_results(results_r, f"L-BFGS-B {n_iter}it")

        # Also try with hole positions optimizable
        print(f"\n  Refining with L-BFGS-B (bore + holes + positions)...")
        def cost_with_positions(x):
            radii = x[:n_bore]
            hd = x[n_bore:n_bore+n_holes]
            hp_vals = sorted(x[n_bore+n_holes:])
            for i in range(1, len(hp_vals)):
                if hp_vals[i] <= hp_vals[i-1] + 2: return 1e6
            if hp_vals[0] < 5 or hp_vals[-1] > bore_length - 5: return 1e6
            try:
                inst2 = TMMInstrument(
                    inner_positions=pos, inner_diameters=(radii * 2).tolist(),
                    outer_diameters=[OD] * n_bore,
                    hole_positions=hp_vals,
                    hole_diameters=[float(d) for d in hd],
                    hole_lengths=hole_lens,
                    closed_top=False, cone_step=cone_step,
                )
            except:
                return 1e10
            cents = []
            for tgt, fl, pr in zip(targets, fing_lists, detected_regs):
                try:
                    wl = inst2.find_resonance(c / tgt, fl, n_register=pr)
                    f = inst2.frequency_from_wavelength(wl)
                    cents.append(cents_error(f, tgt))
                except:
                    cents.append(1e10)
            ca = np.array(cents)
            if np.any(np.abs(ca) > 1e5): return 1e10
            med = np.median(ca)
            return float(np.sqrt(np.mean((ca - med)**2)))

        n_bore = len(pos)
        OD = float(np.mean(outer_at))
        x0_full = np.concatenate([
            np.array(diameters) / 2.0,
            np.array(hole_diams),
            np.array(hole_pos),
        ])
        bore_bounds = [(3.0, 20.0)] * n_bore
        hole_d_bounds = [(2.0, 20.0)] * n_holes
        hole_p_bounds = [(5.0, bore_length - 5.0)] * n_holes
        all_bounds = bore_bounds + hole_d_bounds + hole_p_bounds

        t0 = time.time()
        res_full = sp_min(cost_with_positions, x0_full, method='L-BFGS-B',
                         bounds=all_bounds,
                         options={'maxiter': 500, 'ftol': 1e-10})
        elapsed = time.time() - t0

        final_radii = res_full.x[:n_bore]
        final_hd = res_full.x[n_bore:n_bore+n_holes]
        final_hp = sorted(res_full.x[n_bore+n_holes:])
        inst_full = TMMInstrument(
            inner_positions=pos, inner_diameters=(final_radii * 2).tolist(),
            outer_diameters=[OD] * n_bore,
            hole_positions=final_hp,
            hole_diameters=[float(d) for d in final_hd],
            hole_lengths=hole_lens,
            closed_top=False, cone_step=cone_step,
        )
        print(f"\n  After full refinement ({elapsed:.1f}s, cost={res_full.fun:.4f}):")
        results_full = evaluate_inst(inst_full, fingerings, transpose)
        print_results(results_full, "Full refine")

        print(f"\n  Hole positions: {[f'{p:.1f}' for p in final_hp]}")
        print(f"  Hole diameters: {[f'{d:.2f}' for d in final_hd]}")
        print(f"  Bore diams: {[f'{d:.1f}' for d in (final_radii*2).tolist()]}")

    print("\n" + "="*70)
    print("  DONE")
    print("="*70)

if __name__ == '__main__':
    main()
