"""Test STL export pipeline."""
import sys, time
sys.path.insert(0, "C:\\instrument-designer")
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json

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

print("Running optimizer...")
opt = SequentialBoreOptimizer(
    target_frequencies=target_freqs,
    fingering_sets=fingerings,
    bore_radius=6.0,
    outer_diameter=20.0,
    closed_top=False,
    n_register=1,
    hole_diameter=6.5,
    hole_length=3.0,
)
result = opt.run(verbose=False)
print(f"  RMS: {result['final_rms_cents']:.4f}c | L: {result['bore_length_mm']:.0f}mm")
print(f"  Holes: {len(result['hole_positions'])}")

print("\nExporting STL...")
t0 = time.time()
stl_path = export_optimizer_result(result, "C:\\instrument-designer\\output\\soprano_sax.stl")
print(f"  STL: {stl_path} ({time.time()-t0:.2f}s)")

t0 = time.time()
bore_path = export_bore_only(result, "C:\\instrument-designer\\output\\soprano_sax_bore.stl")
print(f"  Bore: {bore_path} ({time.time()-t0:.2f}s)")

t0 = time.time()
json_path = export_bore_profile_json(result, "C:\\instrument-designer\\output\\soprano_sax_profile.json")
print(f"  JSON: {json_path} ({time.time()-t0:.2f}s)")

import os
for p in [stl_path, bore_path, json_path]:
    size = os.path.getsize(p)
    print(f"  {os.path.basename(p)}: {size:,} bytes")
