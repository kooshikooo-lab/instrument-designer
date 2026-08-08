"""
Compare chalumier's optimized output with our TMM model.
Evaluates intonation accuracy of chalumier designs using our TMM engine.
"""
import sys, os, json, re, math
import numpy as np
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from backend.tmm_acoustics import TMMInstrument, SPEED_OF_SOUND

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

def parse_json5(path):
    with open(path) as f:
        raw = f.read()
    cleaned = re.sub(r'//.*?$', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r'"\1":', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)

def parse_chal_fingerings(spec_path):
    with open(spec_path) as f:
        content = f.read()
    fingerings = []
    m = re.search(r'fingerings\s*=\s*\[', content)
    if not m: return fingerings, {}
    start = m.end()
    depth = 1; i = start
    while i < len(content) and depth > 0:
        if content[i] == '[': depth += 1
        elif content[i] == ']': depth -= 1
        i += 1
    block = content[start:i-1]
    
    closed_top = 'closedTop' in content and 'closedTop = true' in content
    transpose = 0
    tm = re.search(r'transpose\s*=\s*(\d+)', content)
    if tm: transpose = int(tm.group(1))
    
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
    return fingerings, {'closed_top': closed_top, 'transpose': transpose}

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
    while len(result) < len(inner_pos):
        result.append(outer_diams[-1] if outer_diams else 22.0)
    return result[:len(inner_pos)]

def evaluate_inst(inst, fingerings, transpose=0):
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
            except Exception:
                continue
        err = cents_error(best_freq, target_freq) if best_freq > 0 else 1e10
        results.append({'note': note_name, 'target': target_freq, 'actual': best_freq,
                        'cents': err, 'nth': nth_default, 'fingering': fingering_str, 'pr': best_pr})
    return results

def print_results(results, label=""):
    valid = [r for r in results if abs(r['cents']) < 1e5]
    if not valid:
        print(f"  {label}: ALL FAILED")
        return 1e10
    ca = np.array([r['cents'] for r in valid])
    med = np.median(ca)
    even = float(np.sqrt(np.mean((ca - med)**2)))
    off = float(med)
    mean_abs = float(np.mean(np.abs(ca)))
    max_abs = float(np.max(np.abs(ca)))
    print(f"  {label}: even={even:.2f}c off={off:+.2f}c mean_abs={mean_abs:.2f}c max_abs={max_abs:.2f}c (n={len(valid)}/{len(results)})")
    for r in results:
        if abs(r['cents']) < 1e5:
            print(f"    {r['note']:>6} {r.get('fingering',''):>20} pr={r.get('pr','?')} -> {r['cents']:+8.2f}c  ({r['actual']:.1f}Hz vs {r['target']:.1f}Hz)")
        else:
            print(f"    {r['note']:>6} {r.get('fingering',''):>20} FAILED")
    return even

def build_inst_from_chalumier(params):
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
    closed_top = params.get('closedTop', False)

    inst = TMMInstrument(
        inner_positions=pos, inner_diameters=diameters, outer_diameters=outer_at,
        hole_positions=hole_pos, hole_diameters=hole_diams, hole_lengths=hole_lens,
        closed_top=closed_top, cone_step=cone_step,
    )
    return inst, pos, diameters, outer_at, hole_pos, hole_diams, hole_lens, cone_step

def main():
    print("=" * 80)
    print("  CHALUMIER vs OUR TMM: ACOUSTIC MODEL COMPARISON")
    print("=" * 80)

    instruments = [
        {
            'name': 'D Pennywhistle (open-open, 6 holes)',
            'spec': os.path.join('chalumier', 'examples', 'dwhistle.chal'),
            'json5': os.path.join('output-dwhistle', 'd-whistle-parameters.json5'),
        },
        {
            'name': 'Bb Clarinet (closed-open, 17 holes)',
            'spec': os.path.join('chalumier', 'examples', 'bb-clarinet.chal'),
            'json5': os.path.join('output-bbclarinet', 'BbClarinet-parameters.json5'),
        },
        {
            'name': 'Bb Clarinet (previous run)',
            'spec': os.path.join('chalumier', 'examples', 'bb-clarinet.chal'),
            'json5': os.path.join('chalumier', 'output', 'BbClarinet-parameters.json5'),
        },
    ]

    for inst_info in instruments:
        name = inst_info['name']
        if not os.path.exists(inst_info['json5']):
            print(f"\n  {name}: SKIPPED (no output at {inst_info['json5']})")
            continue

        print(f"\n{'=' * 80}")
        print(f"  {name}")
        print(f"{'=' * 80}")

        params = parse_json5(inst_info['json5'])
        fingerings, meta = parse_chal_fingerings(inst_info['spec'])
        transpose = meta.get('transpose', 0)

        print(f"  Closed top: {params.get('closedTop', False)}")
        print(f"  Transpose: {transpose}")
        print(f"  Bore length: {params.get('inner', {}).get('pos', [0])[-1]:.1f}mm")
        print(f"  Holes: {len(params.get('holePositions', []))}")
        print(f"  Target notes: {len(fingerings)}")

        inst, pos, diams, outer_at, hole_pos, hole_diams, hole_lens, cone_step = build_inst_from_chalumier(params)

        print(f"\n  Bore profile ({len(pos)} points):")
        for i in range(min(len(pos), 10)):
            print(f"    pos={pos[i]:.1f}mm  inner_d={diams[i]:.2f}mm  outer_d={outer_at[i]:.2f}mm")
        if len(pos) > 10:
            print(f"    ... ({len(pos)-10} more points)")

        print(f"\n  Hole positions: {[f'{p:.1f}' for p in hole_pos]}")
        print(f"  Hole diameters: {[f'{d:.2f}' for d in hole_diams]}")

        results = evaluate_inst(inst, fingerings, transpose)
        print_results(results, "Our TMM evaluation")

        print(f"\n  Key parameters from chalumier output:")
        for k in ['length', 'trueLength', 'emissionDivide', 'coneStep', 'closedTop']:
            if k in params:
                print(f"    {k}: {params[k]}")

if __name__ == '__main__':
    main()
