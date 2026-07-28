import time, os
import cadquery as cq
from cadquery import exporters

os.makedirs("test_output", exist_ok=True)

print("=== CadQuery Instrument CAD Test ===\n")

# --- Test 1: Cylindrical bore with 6 holes ---
print("--- Test 1: Cylindrical Bore ---")
t0 = time.time()

bore_diam = 15.0
wall_thick = 3.0
length = 600.0
holes = [(100, 6.0), (180, 6.5), (260, 7.0), (340, 7.0), (420, 6.5), (500, 6.0)]

instrument = cq.Workplane("XY").circle((bore_diam + 2*wall_thick)/2).circle(bore_diam/2).extrude(length)
for pos, diam in holes:
    h = cq.Workplane("XZ").workplane(offset=pos).circle(diam/2).extrude(wall_thick + 2)
    instrument = instrument.cut(h)

print(f"  Geometry: {time.time()-t0:.2f}s")

t1 = time.time()
exporters.export(instrument, "test_output/cyl_bore.step")
exporters.export(instrument, "test_output/cyl_bore.stl")
print(f"  Export: {time.time()-t1:.2f}s")
print(f"  STEP: {os.path.getsize('test_output/cyl_bore.step')/1024:.1f} KB")
print(f"  STL: {os.path.getsize('test_output/cyl_bore.stl')/1024:.1f} KB")

# --- Test 2: Conical bore (sax-like) ---
print("\n--- Test 2: Conical Bore ---")
t0 = time.time()

small_d = 12.0
large_d = 30.0
length2 = 800.0
wall2 = 2.5
holes2 = [(150, 7.0), (280, 7.0), (410, 7.5), (540, 7.5), (670, 7.0)]

outer = (
    cq.Workplane("XY")
    .circle((small_d + 2*wall2)/2)
    .workplane(offset=length2)
    .circle((large_d + 2*wall2)/2)
    .loft()
)
bore = (
    cq.Workplane("XY")
    .circle(small_d/2)
    .workplane(offset=length2)
    .circle(large_d/2)
    .loft()
)
instrument2 = outer.cut(bore)

for pos, diam in holes2:
    h = cq.Workplane("XZ").workplane(offset=pos).circle(diam/2).extrude(wall2 + 2)
    instrument2 = instrument2.cut(h)

print(f"  Geometry: {time.time()-t0:.2f}s")

t1 = time.time()
exporters.export(instrument2, "test_output/conical_bore.step")
exporters.export(instrument2, "test_output/conical_bore.stl")
print(f"  Export: {time.time()-t1:.2f}s")
print(f"  STEP: {os.path.getsize('test_output/conical_bore.step')/1024:.1f} KB")
print(f"  STL: {os.path.getsize('test_output/conical_bore.stl')/1024:.1f} KB")

# --- Test 3: Parametric bore profile ---
print("\n--- Test 3: Parametric Bore Profile ---")
t0 = time.time()

bore_profile = [
    (0.0, 14.0), (200.0, 14.5), (400.0, 15.0),
    (600.0, 14.8), (800.0, 12.0),
]
tone_holes = [
    (120.0, 6.0), (220.0, 6.5), (320.0, 7.0),
    (420.0, 7.0), (520.0, 6.5), (620.0, 6.0),
]
wall3 = 2.5

outer3 = cq.Workplane("XY")
bore3 = cq.Workplane("XY")
for i, (pos, diam) in enumerate(bore_profile):
    dz = pos - bore_profile[i-1][0] if i > 0 else pos
    outer3 = outer3.workplane(offset=dz).circle((diam + 2*wall3)/2)
    bore3 = bore3.workplane(offset=dz).circle(diam/2)

instrument3 = outer3.loft().cut(bore3.loft())

for pos, diam in tone_holes:
    h = cq.Workplane("XZ").workplane(offset=pos).circle(diam/2).extrude(wall3 + 2)
    instrument3 = instrument3.cut(h)

print(f"  Geometry: {time.time()-t0:.2f}s")

t1 = time.time()
exporters.export(instrument3, "test_output/parametric_bore.step")
exporters.export(instrument3, "test_output/parametric_bore.stl")
print(f"  Export: {time.time()-t1:.2f}s")
print(f"  STEP: {os.path.getsize('test_output/parametric_bore.step')/1024:.1f} KB")
print(f"  STL: {os.path.getsize('test_output/parametric_bore.stl')/1024:.1f} KB")

print("\n=== ALL TESTS PASSED ===")
