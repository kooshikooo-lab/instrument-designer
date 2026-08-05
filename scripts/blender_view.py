"""Blender display script used by scripts/view_instrument.py.

Imports the given STL, removes the default cube, applies smooth shading, and
frames the model in the 3D viewport. Run by Blender at startup:
    blender.exe --python scripts/blender_view.py -- <path.stl>
"""

import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
stl_path = args[0] if args else ""
if not stl_path:
    raise SystemExit("No STL path given")

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

if hasattr(bpy.ops.wm, "stl_import"):
    bpy.ops.wm.stl_import(filepath=stl_path)
else:
    bpy.ops.import_mesh.stl(filepath=stl_path)

for obj in bpy.data.objects:
    if obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()

area = next(
    (a for s in bpy.data.screens for a in s.areas if a.type == "VIEW_3D"),
    None,
)
if area:
    with bpy.context.temp_override(area=area):
        for sp in area.spaces:
            sp.shading.type = "SOLID"
            sp.shading.color_type = "MATERIAL"
        bpy.ops.view3d.view_selected()
        bpy.ops.view3d.rotate(angle=0.5, orient_axis="Y")

print("VIEW READY")
