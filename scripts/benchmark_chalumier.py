"""
Benchmark: Chalumier vs Our TMM Optimizer

Runs chalumier on example instruments, parses output, evaluates with our TMM,
and compares with our optimizer on the same fingering charts.

Usage:
    python benchmark_chalumier.py           # Full benchmark
    python benchmark_chalumier.py --quick   # Quick test (2 instruments)
"""
import sys, os, time, json, re, subprocess, math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from tmm_acoustics import TMMInstrument, SPEED_OF_SOUND

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
    if rest and rest[0] == 'b':
        s -= 1; rest = rest[1:]
    if rest and rest[0] in ('#', 's'):
        s += 1; rest = rest[1:]
    s += 12 * int(rest) if rest else 0
    return 440.0 * 2.0**((s - 57) / 12.0) * mult

def cents_error(actual, target):
    if actual <= 0 or target <= 0:
        return 1e10
    return 1200.0 * math.log2(actual / target)

def parse_chal_fingerings(spec_path):
    with open(spec_path) as f:
        content = f.read()
    fingerings = []
    m = re.search(r'fingerings\s*=\s*\[', content)
    if not m:
        return fingerings
    start = m.end()
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i] == '[': depth += 1
        elif content[i] == ']': depth -= 1
        i += 1
    block = content[start:i-1]
    for entry in re.finditer(r'\{([^}]+)\}', block):
        inner = entry.group(1)
        # Try noteName = "X4" or note = "X4"
        note_m = re.search(r'noteName\s*=\s*"([^"]+)"', inner)
        if not note_m:
            note_m = re.search(r'note\s*=\s*"([^"]+)"', inner)
        # Try fingers = ["X","O",...] or fingers = "XXOOOO"
        fingers_m = re.search(r'fingers\s*=\s*\[([^\]]+)\]', inner)
        if fingers_m:
            # Array format: ["X", "O", ...]
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

def parse_json5_output(path):
    with open(path) as f:
        raw = f.read()
    cleaned = re.sub(r'//.*?$', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r'"\1":', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)

def find_jar():
    import glob as g
    matches = g.glob(os.path.join('chalumier', 'app', 'build', 'libs', 'chalumier*.jar'))
    if matches:
        return matches[0]
    raise FileNotFoundError("chalumier JAR not found")

def find_java():
    jdk = os.path.join('jdk-17.0.13+11', 'bin', 'java.exe')
    if os.path.isfile(jdk):
        return os.path.abspath(jdk)
    return 'java'

def run_chalumier(spec_path, output_dir, timeout=600):
    json5_files = list(Path(output_dir).glob('*-parameters.json5'))
    if json5_files:
        params = parse_json5_output(str(json5_files[0]))
        params['_elapsed'] = 0
        params['_cached'] = True
        return params
    if '--run-chal' not in sys.argv:
        return {'error': 'no cached output (use --run-chal to generate)', 'elapsed': 0}
    jar = find_jar()
    java = find_java()
    os.makedirs(output_dir, exist_ok=True)
    cmd = [java, '-jar', jar, 'design', '--output-dir', output_dir, spec_path]
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0
    except subprocess.TimeoutExpired:
        return {'error': 'timeout', 'elapsed': timeout}
    json5_files = list(Path(output_dir).glob('*-parameters.json5'))
    svg_files = list(Path(output_dir).glob('*-design.svg'))
    if not json5_files:
        return {'error': 'no output', 'stderr': (result.stderr or '')[-500:], 'elapsed': elapsed}
    params = parse_json5_output(str(json5_files[0]))
    params['_elapsed'] = elapsed
    params['_svg'] = str(svg_files[0]) if svg_files else None
    return params

def evaluate_chalumier_output(params, fingerings, transpose=0):
    inner = params.get('inner', {})
    pos = inner.get('pos', [])
    low = inner.get('low', [])
    high = inner.get('high', low)
    if not pos or not low:
        return []
    diameters = [(l + h) / 2.0 for l, h in zip(low, high)]
    outer_data = params.get('outer', {})
    outer_pos = outer_data.get('pos', [])
    outer_low = outer_data.get('low', [])
    outer_high = outer_data.get('high', outer_low)
    outer_diams = [(l + h) / 2.0 for l, h in zip(outer_low, outer_high)] if outer_pos else [d + 6.0 for d in diameters]
    if not outer_pos:
        outer_pos = pos
    outer_at = []
    for p in pos:
        if p <= outer_pos[0]:
            outer_at.append(outer_diams[0])
        elif p >= outer_pos[-1]:
            outer_at.append(outer_diams[-1])
        else:
            for j in range(len(outer_pos) - 1):
                if outer_pos[j] <= p <= outer_pos[j+1]:
                    t = (p - outer_pos[j]) / (outer_pos[j+1] - outer_pos[j])
                    outer_at.append((1-t) * outer_diams[j] + t * outer_diams[j+1])
                    break
    if len(outer_at) != len(pos):
        outer_at = [d + 6.0 for d in diameters]
    hp = params.get('holePositions', [])
    hd = params.get('holeDiameters', [])
    hl = params.get('holeLengths', [3.5] * len(hp))
    closed_top = params.get('closedTop', False)
    cone_step = params.get('coneStep', 0.125)
    inst = TMMInstrument(
        inner_positions=[float(p) for p in pos],
        inner_diameters=[float(d) for d in diameters],
        outer_diameters=[float(d) for d in outer_at],
        hole_positions=[float(p) for p in hp],
        hole_diameters=[float(d) for d in hd],
        hole_lengths=[float(l) for l in hl],
        closed_top=closed_top, cone_step=cone_step,
    )
    results = []
    for note_name, fingering_str, nth in fingerings:
        target_freq = note_to_freq(note_name)
        if transpose:
            target_freq *= 2.0 ** (transpose / 12.0)
        fl = ['open' if c in ('O', 'o') else 'closed' for c in fingering_str]
        while len(fl) < inst.n_holes:
            fl.append('open')
        fl = fl[:inst.n_holes]
        try:
            wl_guess = c / target_freq
            best_phase_reg = None
            best_dist = 1e10
            for pr in range(1, 6):
                try:
                    wl = inst.find_resonance(wl_guess, fl, n_register=pr)
                    f = inst.frequency_from_wavelength(wl)
                    dist = abs(cents_error(f, target_freq))
                    if dist < best_dist:
                        best_dist = dist
                        best_phase_reg = pr
                except:
                    continue
            wl = inst.find_resonance(wl_guess, fl, n_register=best_phase_reg)
            actual = inst.frequency_from_wavelength(wl)
            err = cents_error(actual, target_freq)
        except:
            actual = 0; err = 1e10
        results.append({'note': note_name, 'target': target_freq, 'actual': actual,
                        'cents': err, 'nth': nth, 'fingering': fingering_str})
    return results

def run_our_optimizer(fingerings, transpose=0, bore_length=None, n_holes=None,
                      closed_top=False, maxiter=300):
    import numpy as np
    from scipy.optimize import minimize as sp_min
    if n_holes is None:
        n_holes = max(len(f) for _, f, _ in fingerings)
    targets = []
    nth_list = []
    fing_lists = []
    for note, fs, nth in fingerings:
        freq = note_to_freq(note)
        if transpose:
            freq *= 2.0 ** (transpose / 12.0)
        targets.append(freq)
        nth_list.append(nth)
        fl = ['open' if c in ('O', 'o') else 'closed' for c in fs]
        while len(fl) < n_holes:
            fl.append('open')
        fing_lists.append(fl[:n_holes])
    targets = np.array(targets)
    if bore_length is None:
        bore_length = c / (2.0 * min(targets))
    bore_d = 11.0
    bore_d1 = bore_d * 1.2
    bore_d0 = bore_d * 0.85
    hole_positions = [bore_length * (i + 1) / (n_holes + 1) for i in range(n_holes)] if n_holes > 0 else []
    hole_lengths = [3.5] * n_holes
    hole_d0 = [bore_d * 0.54] * n_holes
    OD = bore_d + 6.0

    def detect_registers():
        inst = TMMInstrument(
            inner_positions=[0.0, bore_length],
            inner_diameters=[bore_d, bore_d],
            outer_diameters=[OD, OD],
            hole_positions=hole_positions, hole_diameters=hole_d0,
            hole_lengths=hole_lengths, closed_top=closed_top, cone_step=bore_length,
        )
        regs = []
        for tgt, fl in zip(targets, fing_lists):
            wl_guess = c / tgt
            best_pr = 2 if not closed_top else 1
            best_dist = 1e10
            for pr in range(1, 5):
                try:
                    wl = inst.find_resonance(wl_guess, fl, n_register=pr, max_steps=20)
                    f = inst.frequency_from_wavelength(wl)
                    dist = abs(cents_error(f, tgt))
                    if dist < best_dist:
                        best_dist = dist
                        best_pr = pr
                except:
                    continue
            regs.append(best_pr)
        return regs

    detected_regs = detect_registers()
    print(f"    Detected registers: {detected_regs}")

    def cost_fn(x):
        radii = x[:12]
        hd = list(x[12:12+n_holes])
        inst = TMMInstrument(
            inner_positions=np.linspace(0, bore_length, 12).tolist(),
            inner_diameters=(radii * 2).tolist(),
            outer_diameters=[OD] * 12,
            hole_positions=hole_positions, hole_diameters=hd,
            hole_lengths=hole_lengths, closed_top=closed_top, cone_step=0.5,
        )
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
    x0 = np.concatenate([
        np.linspace(bore_d0 / 2, bore_d1 / 2, 12),
        np.array(hole_d0) / 2,
    ])
    t0 = time.time()
    result = sp_min(cost_fn, x0, method='L-BFGS-B',
                    bounds=[(2.0, 30.0)] * (12 + n_holes),
                    options={'maxiter': maxiter, 'ftol': 1e-6})
    elapsed = time.time() - t0
    radii = result.x[:12]
    hd = list(result.x[12:12+n_holes])
    inst = TMMInstrument(
        inner_positions=np.linspace(0, bore_length, 12).tolist(),
        inner_diameters=(radii * 2).tolist(),
        outer_diameters=[OD] * 12,
        hole_positions=hole_positions, hole_diameters=hd,
        hole_lengths=hole_lengths, closed_top=closed_top, cone_step=0.5,
    )
    per_note = []
    for tgt, fl, pr, (note, fs, _) in zip(targets, fing_lists, detected_regs, fingerings):
        try:
            wl = inst.find_resonance(c / tgt, fl, n_register=pr)
            f = inst.frequency_from_wavelength(wl)
            err = cents_error(f, tgt)
        except:
            f = 0; err = 1e10
        per_note.append({'note': note, 'target': tgt, 'actual': f, 'cents': err, 'nth': nth})
    ca = np.array([r['cents'] for r in per_note if abs(r['cents']) < 1e5])
    evenness = float(np.sqrt(np.mean((ca - np.median(ca))**2))) if len(ca) > 0 else 999
    offset = float(np.median(ca)) if len(ca) > 0 else 999
    return {'per_note': per_note, 'evenness': evenness, 'offset': offset, 'elapsed': elapsed,
            'converged': result.success, 'bore_length': bore_length}

def compute_stats(per_note):
    ca = [r['cents'] for r in per_note if abs(r['cents']) < 1e5]
    if not ca:
        return 999, 999, 999, 999
    arr = __import__('numpy').array(ca)
    median = float(__import__('numpy').median(arr))
    evenness = float(__import__('numpy').sqrt(__import__('numpy').mean((arr - median)**2)))
    mean_abs = float(__import__('numpy').mean(__import__('numpy').abs(arr)))
    max_abs = float(__import__('numpy').max(__import__('numpy').abs(arr)))
    return evenness, mean_abs, max_abs, median

def main():
    quick = '--quick' in sys.argv
    ex_dir = os.path.join('chalumier', 'examples')
    instruments = [
        {'name': 'dwhistle', 'path': os.path.join(ex_dir, 'dwhistle.chal'),
         'type': 'folkWhistle', 'transpose': 12},
        {'name': 'dmajor-folk-flute', 'path': os.path.join(ex_dir, 'dmajor-folk-flute.chal'),
         'type': 'folkFlute', 'transpose': 0},
        {'name': 'eminor-7hole-flute', 'path': os.path.join(ex_dir, 'eminor-7hole-flute.chal'),
         'type': 'folkFlute', 'transpose': 0},
        {'name': 'recorder', 'path': os.path.join(ex_dir, 'recorder.chal'),
         'type': 'recorder', 'transpose': 12},
        {'name': 'folkshawm', 'path': os.path.join(ex_dir, 'folkshawm.chal'),
         'type': 'folkShawm', 'transpose': 0},
    ]
    if quick:
        instruments = instruments[:2]

    all_results = []
    for inst_info in instruments:
        name = inst_info['name']
        print(f"\n{'='*70}")
        print(f"  {name} ({inst_info['type']})")
        print(f"{'='*70}")

        fingerings = parse_chal_fingerings(inst_info['path'])
        if not fingerings:
            print(f"  SKIP: no fingerings found in {inst_info['path']}")
            continue
        transpose = inst_info['transpose']
        n_holes = max(len(f) for _, f, _ in fingerings)
        print(f"  {n_holes} holes, {len(fingerings)} fingerings, transpose={transpose}")

        # Run chalumier
        print(f"\n  Running chalumier...", end='', flush=True)
        out_dir = os.path.join('chalumier', 'test-output', f'bench-{name}')
        chal_result = run_chalumier(inst_info['path'], out_dir, timeout=600)
        if 'error' in chal_result:
            print(f" ERROR: {chal_result['error']}")
            chal_per_note = []
            chal_elapsed = chal_result.get('elapsed', 0)
        else:
            chal_elapsed = chal_result.get('_elapsed', 0)
            print(f" done in {chal_elapsed:.1f}s")
            chal_per_note = evaluate_chalumier_output(chal_result, fingerings, transpose)
            ev, ma, mx, off = compute_stats(chal_per_note)
            print(f"  Chalumier (our TMM eval): even={ev:.1f}c mean={ma:.1f}c max={mx:.1f}c off={off:+.1f}c")
            for r in chal_per_note:
                if abs(r['cents']) < 1e5:
                    print(f"    {r['note']:>6} {r['fingering']:>10} -> {r['cents']:+7.1f}c")

        # Run our optimizer
        print(f"\n  Running our optimizer (L-BFGS-B)...", end='', flush=True)
        our_result = run_our_optimizer(fingerings, transpose, n_holes=n_holes, maxiter=50)
        print(f" done in {our_result['elapsed']:.1f}s")
        ev, ma, mx, off = compute_stats(our_result['per_note'])
        print(f"  Our optimizer: even={ev:.1f}c mean={ma:.1f}c max={mx:.1f}c off={off:+.1f}c")
        for r in our_result['per_note']:
            if abs(r['cents']) < 1e5:
                print(f"    {r['note']:>6} -> {r['cents']:+7.1f}c")

        all_results.append({
            'name': name, 'type': inst_info['type'],
            'n_holes': n_holes, 'n_fingerings': len(fingerings),
            'chal_elapsed': chal_elapsed,
            'chal_per_note': chal_per_note,
            'chal_stats': compute_stats(chal_per_note) if chal_per_note else (0,0,0,0),
            'our_elapsed': our_result['elapsed'],
            'our_per_note': our_result['per_note'],
            'our_stats': compute_stats(our_result['per_note']),
        })

    # Summary table
    print(f"\n\n{'='*90}")
    print(f"  SUMMARY: Chalumier (evolutionary) vs Our TMM (L-BFGS-B)")
    print(f"{'='*90}")
    print(f"  {'Instrument':<25} {'Holes':>5} {'Notes':>5} | {'Chal/s':>6} {'Chal ev':>8} {'Chal mn':>8} {'Chal mx':>8} | {'Our/s':>6} {'Our ev':>8} {'Our mn':>8} {'Our mx':>8}")
    print(f"  {'-'*25} {'-'*5} {'-'*5} | {'-'*6} {'-'*8} {'-'*8} {'-'*8} | {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
    for r in all_results:
        ce, cma, cmx, co = r['chal_stats']
        oe, oma, omx, oo = r['our_stats']
        print(f"  {r['name']:<25} {r['n_holes']:>5} {r['n_fingerings']:>5} | "
              f"{r['chal_elapsed']:>5.1f}s {ce:>7.1f}c {cma:>7.1f}c {cmx:>7.1f}c | "
              f"{r['our_elapsed']:>5.1f}s {oe:>7.1f}c {oma:>7.1f}c {omx:>7.1f}c")

    # Save results
    out_path = os.path.join('chalumier', 'test-output', 'benchmark_results.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Results saved to: {out_path}")

if __name__ == '__main__':
    main()
