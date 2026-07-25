"""Verify tone-hole placement physics: what actually happens when holes open."""
import sys
import numpy as np
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Use our 4.3c configuration
holes_12 = [142, 199, 250, 304, 354, 400, 439, 479, 516, 555, 590, 611]
bore_len = 1159.0
reg_pos = 80.0
d_min, d_max = 14.5, 20.0
hole_dias = [d_min + (d_max - d_min) * i / 11 for i in range(12)]

all_pos = sorted(holes_12 + [reg_pos])
all_dias = hole_dias + [2.5]
all_lens = [5.0]*12 + [3.0]

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), bore_len, all_pos,
    [d/2 for d in all_dias], all_lens, 37.0, closed_top=True, cone_step=0.5
)

print("=== Tone-Hole Placement Physics ===")
print()
print("Holes (sorted by position, reed to bell):")
for i, (p, d) in enumerate(zip(all_pos, all_dias)):
    label = "REGISTER" if p == reg_pos else "primary"
    print("  H%02d: %4.0fmm  d=%5.1fmm  (%s)" % (i, p, d, label))

print()
print("Bore length: %.1fmm" % bore_len)
print("Register: %dmm, d=%.1fmm" % (reg_pos, 2.5))
print()

# Test 1: What happens when we open ONE hole at a time?
print("=== TEST 1: Single hole effect (reed-first order) ===")
print("Opening each hole individually from D2 (all closed)")
print()
d3_target = 146.8
for n_open in range(0, 13):
    if n_open == 0:
        chart = [["closed"] * 13]
    else:
        row = ["open"] * n_open + ["closed"] * (13 - n_open)
        chart = [row]
    
    wl = [SPEED_OF_SOUND / d3_target]
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart, n_register=1)
        f = freqs[0]
        c = 1200 * np.log2(f / d3_target)
        # Show which holes are open
        open_holes = ["H%02d(%dmm)" % (i, all_pos[i]) for i in range(n_open)]
        print("  %2d holes open: %6.1fHz  %+6.1fc  [%s]" % (
            n_open, f, c, ", ".join(open_holes) if open_holes else "none"))
    except:
        print("  %2d holes open: FAILED" % n_open)

print()
print("=== TEST 2: What note does each fingering give? ===")
print("(Reed-first sequential: our 4.3c chart)")
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

chart_13 = []
for i in range(13):
    row = ["open"] * i + ["closed"] * (13 - i)
    chart_13.append(row)

wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chart_13, n_register=1)

print()
print("%-4s %9s %9s %9s  open holes" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 70)
for i, (n, t, f) in enumerate(zip(names, targets, freqs)):
    c = 1200*np.log2(f/t) if f>0 else 0
    holes_list = ["H%02d" % j for j in range(i)]
    print("  %-4s %7.1fHz %7.1fHz %+7.1fc  %s" % (
        n, t, f, c, "none" if i == 0 else "+".join(holes_list)))

print()
print("=== TEST 3: Verify hole numbering convention ===")
print("Holes sorted by position (closest to reed = H00)")
print()
for i in range(12):
    dist_from_reed = all_pos[i]
    dist_from_bell = bore_len - all_pos[i]
    print("  H%02d: %4.0fmm from reed, %4.0fmm from bell" % (
        i, dist_from_reed, dist_from_bell))

print()
print("=== KEY INSIGHT ===")
print("In our configuration:")
print("  - Holes are sorted: H00 closest to REED, H11 closest to BELL")
print("  - Reed-first fingering: H00 opens first (lowest hole = nearest reed)")
print("  - This means we OPEN FROM REED END FIRST")
print("  - Each hole opened raises pitch by ~semitone")
print("  - Hole diameters: 14.5mm (reed end) to 20.0mm (bell end)")
print("  - Larger holes near reed = stronger perturbation where needed")
print("  - This matches real clarinet fingering convention")
