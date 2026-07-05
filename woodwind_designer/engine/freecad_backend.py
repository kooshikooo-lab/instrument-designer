"""
FreeCAD backend script - runs inside freecadcmd.exe (FreeCAD's Python).
Called as subprocess by freecad_engine.py via FC_PARAMS env var.

Usage:
    set FC_PARAMS=<json>
    freecadcmd.exe freecad_backend.py
"""

import sys, json, os


def create_instrument(params):
    import FreeCAD, Part, Mesh

    output_path = params.get("output_path", "")
    bore_segments = params.get("bore_segments", [])
    tone_holes = params.get("tone_holes", [])
    export_stl = params.get("export_stl", True)
    export_step = params.get("export_step", False)
    export_fcstd = params.get("export_fcstd", False)

    os.makedirs(output_path, exist_ok=True)
    doc = FreeCAD.newDocument("Instrument")

    if len(bore_segments) < 2:
        bore_segments = [[0.0, 0.008], [0.65, 0.018]]

    # -- Build bore by revolving a profile --
    pts = [FreeCAD.Vector(x, r, 0) for x, r in bore_segments]
    pts.append(FreeCAD.Vector(bore_segments[-1][0], 0, 0))
    pts.append(FreeCAD.Vector(bore_segments[0][0], 0, 0))
    pts.append(FreeCAD.Vector(bore_segments[0][0], bore_segments[0][1], 0))

    profile = Part.makePolygon(pts)
    bore_shape = profile.revolve(FreeCAD.Vector(0, 0, 0),
                                  FreeCAD.Vector(1, 0, 0), 360)
    bore_feat = doc.addObject("Part::Feature", "Bore")
    bore_feat.Shape = bore_shape

    # -- Create tone holes (subtracted from bore) --
    if tone_holes:
        hole_shapes = None
        for h in tone_holes:
            pos = h.get("position", 0.1)
            rad = h.get("radius", 0.003)
            height = h.get("chimney_height", 0.008)
            bore_r = _interpolate_radius(bore_segments, pos)
            hole_len = bore_r * 2 + height * 4

            hole = Part.makeCylinder(rad, hole_len,
                                     FreeCAD.Vector(pos, -bore_r - height * 2, 0),
                                     FreeCAD.Vector(0, 1, 0))
            hole_shapes = hole if hole_shapes is None else hole_shapes.fuse(hole)

        if hole_shapes:
            hole_feat = doc.addObject("Part::Feature", "HolesTemp")
            hole_feat.Shape = hole_shapes

            cut = doc.addObject("Part::Cut", "Body")
            cut.Base = bore_feat
            cut.Tool = hole_feat
            bore_feat = cut

    doc.recompute()
    results = {"files": []}

    if export_stl:
        stl_path = os.path.join(output_path, "instrument.stl")
        Mesh.export([bore_feat], stl_path)
        results["files"].append(stl_path)

    if export_step:
        step_path = os.path.join(output_path, "instrument.step")
        try:
            import Import
            Import.export([bore_feat], step_path)
            results["files"].append(step_path)
        except ImportError:
            pass  # STEP export not available in console mode

    if export_fcstd:
        fcstd_path = os.path.join(output_path, "instrument.FCStd")
        doc.saveAs(fcstd_path)
        results["files"].append(fcstd_path)

    results["bore_length"] = bore_segments[-1][0]
    results["n_holes"] = len(tone_holes)
    return results


def _interpolate_radius(segments, x):
    if not segments:
        return 0.01
    xs = [s[0] for s in segments]
    rs = [s[1] for s in segments]
    if x <= xs[0]:
        return rs[0]
    if x >= xs[-1]:
        return rs[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i]) if xs[i + 1] != xs[i] else 0
            return rs[i] + t * (rs[i + 1] - rs[i])
    return rs[-1]


# NOTE: freecadcmd runs this as a module (__name__ != "__main__"),
# so execution happens at module level (no if __name__ guard).
import traceback as _tb
params_raw = os.environ.get("FC_PARAMS")
if params_raw:
    try:
        params = json.loads(params_raw)
        result = create_instrument(params)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e), "traceback": _tb.format_exc()}))
else:
    print(json.dumps({"error": "FC_PARAMS env var not set"}))
import sys
sys.stdout.flush()
sys.exit(0)
