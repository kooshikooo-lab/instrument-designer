"""Profile TMM evaluation speed."""
import sys, time
import numpy as np
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]

chart = []
for i in range(13):
    row = ["closed"] * (12 - i) + ["open"] * i + ["closed"]
    chart.append(row)

hole_pos = [150, 250, 350, 450, 550, 650, 750, 850, 950, 1050, 1100, 1150]
all_pos = sorted(hole_pos + [80.0])

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [11.0/2]*12 + [2.5/2], [5.0]*12 + [3.0], 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]

# Time single note evaluation
t0 = time.time()
for _ in range(100):
    inst.find_resonance(wl[0], chart[0], n_register=1)
t_single = (time.time() - t0) / 100
print("Single note: %.3fms" % (t_single * 1000))

# Time full chart (13 notes)
t0 = time.time()
for _ in range(10):
    inst.compute_fingered_frequencies(wl, chart, n_register=1)
t_chart = (time.time() - t0) / 10
print("Full chart (13 notes): %.1fms" % (t_chart * 1000))

# Estimate: L-BFGS-B with 12 vars, ~200 iters, ~24 evals/iter gradient
# Actually L-BFGS-B uses forward differences: 13 evals per iter
est = t_chart * 200 * 13
print("Estimated L-BFGS-B time: %.0fs" % est)
