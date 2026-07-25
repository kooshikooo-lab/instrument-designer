"""Use GlobalFingeringOptimizer directly (L-BFGS-B only) for 12-hole cross-fingering.

This uses the optimizer's internal _evaluate which handles chart mapping correctly.
Skip DE (too slow), use L-BFGS-B only with good initial guess.
"""
import sys, time
import numpy as np
sys.path.insert(0, '.')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Cross-fingering chart
chart = [
    [0,0,0,0,0,0,0,0,0,0,0,0, 0],
    [1,0,0,0,0,0,0,0,0,0,0,0, 0],
    [1,1,0,0,0,0,0,0,0,0,0,0, 0],
    [1,1,1,0,0,0,0,0,0,0,0,0, 0],
    [1,1,1,1,0,0,0,0,0,0,0,0, 0],
    [1,1,1,0,1,0,0,0,0,0,0,0, 0],
    [1,1,1,1,1,0,0,0,0,0,0,0, 0],
    [1,1,0,0,1,0,0,0,0,0,0,0, 0],
    [1,0,0,0,1,0,0,1,0,0,0,0, 0],
    [1,0,0,0,1,1,0,0,0,0,0,0, 0],
    [1,0,0,0,1,1,1,0,0,0,0,0, 0],
    [1,0,0,0,1,1,1,1,0,0,0,0, 0],
    [1,1,1,1,1,1,1,1,0,0,0,0, 0],
]
chart_str = [["open" if x else "closed" for x in row] for row in chart]

initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]

print("=== GlobalFingeringOptimizer (L-BFGS-B only, reg2 primary) ===")

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart_str,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=[(80.0, 2.5, 3.0)],
    register_weights=(0.15, 1.0),
    optimize_grad=True,
    grad_bounds=(6.0, 12.0, 16.0, 22.0),
)

result = opt.optimize(initial_positions=initial, bounds_per_hole=200,
                      use_de=False, verbose=True)
dt = time.time() - t0

print("\nTime: %.0fs" % dt)
print("Reg1 RMS: %.2fc" % result['final_rms_1st_cents'])
print("Reg2 RMS: %.2fc" % result['final_rms_2nd_cents'])
print("Holes: %s" % [round(p) for p in result['free_hole_positions']])
if 'graduated_diameters' in result:
    print("Diameters: %s" % [round(d, 1) for d in result['graduated_diameters']])

# Detailed reg1 eval
free_pos = sorted(result['free_hole_positions'])
all_pos = sorted(free_pos + [80.0])
grad_diam = result.get('graduated_diameters', [11.0]*12)

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [d/2.0 for d in grad_diam] + [2.5/2.0],
    [5.0]*12 + [3.0], 37.0, closed_top=True, cone_step=0.5
)
chal_chart = [row[:12] + ["closed"] for row in chart_str]
wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chal_chart, n_register=1)

print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
errs = []
for n, t, f in zip(names, targets, freqs):
    c = 1200*np.log2(f/t) if f>0 else 0
    errs.append(c)
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, f, c))
e = np.array(errs)
off = np.median(e)
rms = np.sqrt(np.mean((e - off)**2))
print("\nChalumeau RMS=%.2fc offset=%+.1fc" % (rms, off))
