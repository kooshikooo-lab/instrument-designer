"""Test variable bore profile optimization."""
import sys, time
sys.path.insert(0, "C:\\instrument-designer")
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer

target_freqs = [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0]
fingerings = [
    ['closed'] * 7,
    ['open', 'closed', 'closed', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'closed', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'open', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'open', 'open', 'closed'],
]

for ncp in [0, 4, 6]:
    print(f"=== n_bore_cp={ncp} ===")
    t0 = time.time()
    opt = SequentialBoreOptimizer(
        target_frequencies=target_freqs,
        fingering_sets=fingerings,
        bore_radius=6.0,
        outer_diameter=20.0,
        closed_top=False,
        n_register=1,
        hole_diameter=6.5,
        hole_length=3.0,
        n_bore_cp=ncp,
    )
    r = opt.run(verbose=False)
    print(f"  RMS={r['final_rms_cents']:.4f}c | L={r['bore_length_mm']:.0f}mm | {time.time()-t0:.1f}s")
    print(f"  Bore radii: {[f'{x:.2f}' for x in r['bore_radii']]}")
    print()
