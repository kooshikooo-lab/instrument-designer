import time, os
os.makedirs("test_output", exist_ok=True)

t0 = time.time()
import cadquery as cq
print(f"Import: {time.time()-t0:.2f}s")

t1 = time.time()
cyl = cq.Workplane("XY").circle(7.5).extrude(600)
print(f"Cylinder 15mm x 600mm: {time.time()-t1:.2f}s")

t2 = time.time()
wall = cq.Workplane("XY").circle(10).circle(7.5).extrude(600)
print(f"Hollow cylinder: {time.time()-t2:.2f}s")

t3 = time.time()
hole = cq.Workplane("XZ").workplane(offset=100).circle(3).extrude(6)
wall = wall.cut(hole)
print(f"Cut 1 hole: {time.time()-t3:.2f}s")

t4 = time.time()
from cadquery import exporters
exporters.export(wall, "test_output/cadquery_test.step")
print(f"STEP export: {time.time()-t4:.2f}s")

t5 = time.time()
exporters.export(wall, "test_output/cadquery_test.stl")
print(f"STL export: {time.time()-t5:.2f}s")

print(f"STEP: {os.path.getsize('test_output/cadquery_test.step')/1024:.1f} KB")
print(f"STL: {os.path.getsize('test_output/cadquery_test.stl')/1024:.1f} KB")
print(f"Total: {time.time()-t0:.2f}s")
