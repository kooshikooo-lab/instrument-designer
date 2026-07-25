import sys, os, time, math, numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from benchmark_all import eval_all, INSTRUMENTS
from tmm_optimizer_sequential import SequentialBoreOptimizer

# Test both instruments
for name in ['chalumeau_C', 'recorder_C']:
    cfg = INSTRUMENTS[name]
    print("\n" + "="*60)
    print("BENCHMARK: %s" % cfg["desc"])
    print("="*60)
    
    t0 = time.time()
    opt = SequentialBoreOptimizer(
        target_frequencies=cfg["targets"],
        fingering_sets=cfg["fingerings"],
        bore_radius=cfg["bore_radius"],
        outer_diameter=cfg["outer_diameter"],
        closed_top=cfg["closed_top"],
        hole_diameter=cfg["hole_diameter"],
        hole_length=cfg["hole_length"],
    )
    result = opt.run(verbose=False)
    dt = time.time() - t0
    
    # Report
    hp = result["hole_positions"]
    hd = result["hole_diameters"]
    hl = result["hole_lengths"]
    bl = result["bore_length_mm"]
    radii = np.array(result["bore_radii"])
    rms = eval_all(radii, bl, hp, hd, hl, cfg)
    
    print("  Bore: %.1fmm x %.1fmm radius" % (bl, cfg["bore_radius"]))
    print("  Holes: %d" % len(hp))
    for i, (p, d) in enumerate(zip(hp, hd)):
        print("    Hole %d: %.1fmm dia=%.1fmm" % (i, p, d))
    print("  RMS: %.4f cents (abs) | Peak: %.4f cents" % (result["final_rms_cents"], result["peak_error_cents"]))
    print("  Time: %.1fs" % dt)
