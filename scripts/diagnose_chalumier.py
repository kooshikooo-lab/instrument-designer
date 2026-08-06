"""
Diagnostic: compare our TMM bore stepping with chalumier's.
Also tests whether using trueLength vs length changes results.
"""
import sys, os, json, re, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from backend.tmm_acoustics import (
    TMMInstrument, SPEED_OF_SOUND, Profile,
    end_flange_length_correction, circle_area,
    pipe_reply_phase, junction2_reply_phase, junction3_reply_phase,
    hole_length_correction
)

c = SPEED_OF_SOUND

def parse_json5(path):
    with open(path) as f:
        raw = f.read()
    cleaned = re.sub(r'//.*?$', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r'"\1":', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return json.loads(cleaned)

def test_whistle():
    print("=" * 70)
    print("  WHISTLE DIAGNOSTIC")
    print("=" * 70)
    
    params = parse_json5(os.path.join('output-dwhistle', 'd-whistle-parameters.json5'))
    
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
    
    # Interpolate outer
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
                    outer_at.append((1-t)*outer_diams[j] + t*outer_diams[j+1])
                    break
    while len(outer_at) < len(pos):
        outer_at.append(outer_diams[-1])
    outer_at = outer_at[:len(pos)]
    
    hole_pos = [float(p) for p in params.get('holePositions', [])]
    hole_diams = [float(d) for d in params.get('holeDiameters', [])]
    hole_lens = [float(l) for l in params.get('holeLengths', [3.5]*len(hole_pos))]
    cone_step = params.get('coneStep', 0.125)
    bore_length = pos[-1]
    true_length = params.get('trueLength', bore_length)
    
    print(f"\n  Bore length: {bore_length:.2f}mm")
    print(f"  True length: {true_length:.2f}mm")
    print(f"  Difference: {bore_length - true_length:.2f}mm")
    
    print(f"\n  Bore profile:")
    for i in range(len(pos)):
        print(f"    [{i}] pos={pos[i]:8.2f}  low={low[i]:6.2f}  high={high[i]:6.2f}  avg={diameters[i]:6.2f}  outer={outer_at[i]:6.2f}")
    
    # Build Profile and step it
    prof = Profile(pos, low, high)
    stepped = prof.as_stepped(cone_step)
    
    print(f"\n  Stepped profile: {len(stepped.pos)} points (from {len(pos)} original)")
    for i in range(min(len(stepped.pos), 30)):
        print(f"    [{i}] pos={stepped.pos[i]:8.2f}  low={stepped.low[i]:6.2f}  high={stepped.high[i]:6.2f}")
    if len(stepped.pos) > 30:
        print(f"    ... ({len(stepped.pos) - 30} more)")
    
    # Compute end flange correction
    outer_d0 = outer_at[0]
    inner_d0 = diameters[0]
    efc = end_flange_length_correction(outer_d0, inner_d0)
    print(f"\n  End flange correction: {efc:.4f}mm")
    print(f"    outer_d0={outer_d0:.2f} inner_d0={inner_d0:.2f}")
    
    # Build TMM with full bore
    inst_full = TMMInstrument(
        inner_positions=pos, inner_diameters=diameters, outer_diameters=outer_at,
        hole_positions=hole_pos, hole_diameters=hole_diams, hole_lengths=hole_lens,
        closed_top=False, cone_step=cone_step,
    )
    
    # Build TMM with bore clipped to trueLength
    # Filter pos/diams/outer to only include points <= trueLength
    clip_idx = 0
    for i, p in enumerate(pos):
        if p <= true_length:
            clip_idx = i
    clip_pos = pos[:clip_idx+1]
    clip_diams = diameters[:clip_idx+1]
    clip_outer = outer_at[:clip_idx+1]
    # Add endpoint at trueLength
    if clip_pos[-1] < true_length:
        # Interpolate diameter at trueLength
        for i in range(len(pos)-1):
            if pos[i] <= true_length <= pos[i+1]:
                t = (true_length - pos[i]) / (pos[i+1] - pos[i])
                d = (1-t)*diameters[i] + t*diameters[i+1]
                o = (1-t)*outer_at[i] + t*outer_at[i+1]
                clip_pos.append(true_length)
                clip_diams.append(d)
                clip_outer.append(o)
                break
    
    print(f"\n  Clipped bore ({len(clip_pos)} points, to trueLength={true_length:.2f}):")
    for i in range(len(clip_pos)):
        print(f"    [{i}] pos={clip_pos[i]:8.2f}  d={clip_diams[i]:6.2f}  outer={clip_outer[i]:6.2f}")
    
    inst_clipped = TMMInstrument(
        inner_positions=clip_pos, inner_diameters=clip_diams, outer_diameters=clip_outer,
        hole_positions=hole_pos, hole_diameters=hole_diams, hole_lengths=hole_lens,
        closed_top=False, cone_step=cone_step,
    )
    
    # Compare resonance for a few notes
    test_notes = [
        ("D4", 587.33, "XXXXXX"),
        ("A4", 880.00, "OOOOXX"),
        ("B5", 1975.53, "OOOOOX"),
    ]
    
    print(f"\n  Resonance comparison:")
    print(f"  {'Note':>6} {'Target':>8} {'Full bore':>10} {'Clipped':>10} {'Diff':>8}")
    for note, target, fingering in test_notes:
        fl = ['open' if c in 'Oo' else 'closed' for c in fingering]
        wl_full = inst_full.find_resonance(c / target, fl, n_register=2)
        f_full = inst_full.frequency_from_wavelength(wl_full)
        wl_clip = inst_clipped.find_resonance(c / target, fl, n_register=2)
        f_clip = inst_clipped.frequency_from_wavelength(wl_clip)
        cents_full = 1200 * math.log2(f_full / target)
        cents_clip = 1200 * math.log2(f_clip / target)
        print(f"  {note:>6} {target:8.1f} {cents_full:+8.2f}c {cents_clip:+8.2f}c {cents_clip-cents_full:+8.2f}c")
    
    # Now test: what if we use trueLength as the bore length?
    print(f"\n  Testing with bore length = trueLength ({true_length:.2f}mm):")
    # Build bore that ends at trueLength (no whistle head)
    # The bore should end at the last kink before the whistle head
    
    # Find the position of the last kink (before whistle head)
    inner_kinks = [float(k) for k in params.get('innerKinks', [])]
    print(f"  Inner kinks: {[f'{k:.2f}' for k in inner_kinks]}")
    
    # The bore profile before patching ends at the last kink + some extension
    # Let's try using the bore up to trueLength
    print(f"\n  NOTE: The bore profile in JSON extends to {bore_length:.2f}mm")
    print(f"  but trueLength is {true_length:.2f}mm")
    print(f"  The difference ({bore_length - true_length:.2f}mm) is the whistle head windway")
    print(f"  Chalumier's optimizer evaluates resonance using the PATCHED bore (full length)")
    print(f"  Our model also uses the full bore, so this should be correct")
    
    # Test with manual phase computation to verify
    print(f"\n  Manual phase computation for D4 (full bore, n=2):")
    target_freq = 587.33
    wl = c / target_freq
    fl = ['closed'] * 6
    
    phase = inst_full.resonance_phase(wl, fl)
    print(f"    wavelength={wl:.2f}mm  phase={phase:.6f}  (target=2.0)")
    print(f"    phase - 2 = {phase - 2:.6f}")
    
    # Find exact resonance
    wl_res = inst_full.find_resonance(wl, fl, n_register=2)
    f_res = inst_full.frequency_from_wavelength(wl_res)
    print(f"    resonant wavelength: {wl_res:.4f}mm")
    print(f"    resonant frequency: {f_res:.2f}Hz")
    print(f"    cents error: {1200*math.log2(f_res/target_freq):+.2f}c")

def test_clarinet():
    print("\n" + "=" * 70)
    print("  CLARINET DIAGNOSTIC")
    print("=" * 70)
    
    params = parse_json5(os.path.join('output-bbclarinet', 'BbClarinet-parameters.json5'))
    
    inner = params.get('inner', {})
    pos = [float(p) for p in inner.get('pos', [])]
    low = [float(d) for d in inner.get('low', [])]
    high = [float(d) for d in inner.get('high', low)]
    diameters = [(l + h) / 2.0 for l, h in zip(low, high)]
    
    bore_length = pos[-1]
    true_length = params.get('trueLength', bore_length)
    reed_virtual_length = 34.0
    bore_diameter = 14.5
    
    print(f"\n  Bore length: {bore_length:.2f}mm")
    print(f"  True length: {true_length:.2f}mm")
    print(f"  Reed virtual length: {reed_virtual_length}x bore = {bore_diameter * reed_virtual_length:.1f}mm")
    print(f"  Total with reed: {true_length + bore_diameter * reed_virtual_length:.1f}mm")
    
    print(f"\n  Bore profile:")
    for i in range(len(pos)):
        print(f"    [{i}] pos={pos[i]:8.2f}  low={low[i]:6.2f}  high={high[i]:6.2f}  avg={diameters[i]:6.2f}")
    
    print(f"\n  KEY FINDING: For clarinet (reed instrument), chalumier's patchInstrument()")
    print(f"  prepends a virtual reed tube of length bore*reedVirtualLength = {bore_diameter}*{reed_virtual_length} = {bore_diameter*reed_virtual_length:.1f}mm")
    print(f"  This extends the bore from {true_length:.1f}mm to {true_length + bore_diameter*reed_virtual_length:.1f}mm")
    print(f"  Our TMM model does NOT include this reed tube â€” this explains the huge error")

if __name__ == '__main__':
    test_whistle()
    test_clarinet()
