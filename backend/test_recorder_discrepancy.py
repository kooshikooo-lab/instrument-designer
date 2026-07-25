import sys, os, math, numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from benchmark_all import eval_all, INSTRUMENTS as BENCHMARKS
from tmm_optimizer_sequential import SequentialBoreOptimizer

cfg = BENCHMARKS['recorder_C']
print("Recorder config:")
print("  bore_radius=%s" % cfg["bore_radius"])
print("  outer_diameter=%s" % cfg["outer_diameter"])
print("  hole_diameter=%s" % cfg["hole_diameter"])
print("  closed_top=%s" % cfg["closed_top"])

# Run the optimizer
opt = SequentialBoreOptimizer(
    target_frequencies=cfg["targets"],
    fingering_sets=cfg["fingerings"],
    bore_radius=cfg["bore_radius"],
    outer_diameter=cfg["outer_diameter"],
    closed_top=cfg["closed_top"],
    hole_diameter=cfg["hole_diameter"],
    hole_length=cfg["hole_length"],
)
result = opt.run(verbose=True)

print("\n=== Final Evaluation ===")
print("Optimizer reports: RMS=%.4f, Peak=%.4f" % (result["final_rms_cents"], result["peak_error_cents"]))

# Now eval_all from benchmark_all.py (absolute RMS)
hp = result["hole_positions"]
hd = result["hole_diameters"]
hl = result["hole_lengths"]
bl = result["bore_length_mm"]
radii = np.array(result["bore_radii"])
rms2 = eval_all(radii, bl, hp, hd, hl, cfg)
print("eval_all absolute RMS: %.4f" % rms2)
