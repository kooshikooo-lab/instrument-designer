"""Internal Blender script run by scripts/test_blender_import.py.

Imports the STL given on the command line and prints a JSON report line.
"""
import json
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
stl_path = args[0] if args else ""

report = {"ok": False, "error": ""}

if not stl_path:
    report["error"] = "No STL path"
else:
    try:
        # Clear default scene
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

        if hasattr(bpy.ops.wm, "stl_import"):
            bpy.ops.wm.stl_import(filepath=stl_path)
        else:
            bpy.ops.import_mesh.stl(filepath=stl_path)

        meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
        if not meshes:
            raise RuntimeError("No mesh imported")

        total_verts = sum(len(m.data.vertices) for m in meshes)
        total_faces = sum(len(m.data.polygons) for m in meshes)
        bbox = [list(meshes[0].bound_box[i]) for i in range(8)]

        report = {
            "ok": True,
            "verts": total_verts,
            "faces": total_faces,
            "bbox": bbox,
            "objects": len(meshes),
        }
    except Exception as e:
        report["error"] = str(e)

print(f"BLENDER_IMPORT_REPORT:{json.dumps(report)}")
