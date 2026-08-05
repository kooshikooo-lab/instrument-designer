"""build123d spike (track C): port koncovka_C and compare with CadQuery.

Spike goal: prove build123d can reproduce the ``cadquery_export`` geometry for a
no-hole cylindrical instrument, and quantify the difference at the STL level.

Findings (2026-08-05):
- koncovka_C (no holes, open): identical volume (0.000%), identical STL mesh
  topology (504 verts / 1008 faces), identical bbox [0, 651.5]. build123d export
  ~40x faster for this part (0.02s vs 0.87s).
- fujara_G (closed top): 0.000% volume error, both watertight.
- xaphoon_C (7 holes): 0.057% volume error (STL mesh tolerance only), but the
  CadQuery mesh is **NOT watertight** (2624 verts/5264 faces) while build123d's
  **IS** (1000 verts/2012 faces). This corroborates the mesh-repair-gate finding
  in ``docs/RESEARCH_design_to_finished_instrument.md`` — build123d booleans emit
  cleaner meshes that are already watertight.

Port strategy (track C assignment, see #23): build123d Cylinder solids + boolean
subtraction mirror ``generate_instrument``'s cylindrical path. Holes are cut with
horizontal build123d cylinders in the same way ``_cut_single_hole`` does, so the
spike generalizes to holed instruments too.

Run:
    python backend/experiments/build123d_koncovka.py

This is a reference experiment: it writes only to ``test_output/`` (gitignored)
and is not collected by pytest.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import numpy as np

from backend.cadquery_export import generate_instrument, export_stl as cq_export_stl

try:
    from build123d import Cylinder, Pos, export_stl as b123_export_stl, Compound
except ImportError as exc:  # pragma: no cover - spike only
    raise SystemExit(f"build123d not installed (pip install build123d): {exc}")


KONCOVKA = {
    "bore_length": 651.5,
    "bore_diameter": 16.0,
    "wall_thickness": 2.0,
    "closed_top": False,
    "holes": [],
}


def build123d_instrument(
    bore_length, bore_diameter, wall_thickness, holes=None, closed_top=False,
    hole_depth=None,
):
    """build123d port of ``cadquery_export.generate_instrument`` (cylindrical path).

    Build123d Cylinder is centered on the origin by default; the CadQuery model
    spans ``z in [0, bore_length]``. We translate by ``+bore_length/2`` so both
    models occupy the same axis-aligned box, making bounding-box/volume and STL
    comparisons meaningful.
    """
    import build123d as b

    if holes is None:
        holes = []
    if hole_depth is None:
        hole_depth = wall_thickness + 2

    outer_r = (bore_diameter + 2 * wall_thickness) / 2
    inner_r = bore_diameter / 2

    outer = b.Cylinder(outer_r, bore_length)
    bore = b.Cylinder(inner_r, bore_length)
    solid = outer - bore

    if closed_top:
        cap = Pos(0, 0, bore_length + wall_thickness / 2) * b.Cylinder(outer_r, wall_thickness)
        solid = solid + cap

    for i, (pos, diam) in enumerate(holes):
        side = 1 if i % 2 == 0 else -1
        cyl = Pos(inner_r * side, 0, pos) * b.Cylinder(diam / 2, wall_thickness + hole_depth)
        solid = solid - cyl

    return solid.translate((0, 0, +bore_length / 2))


def mesh_stats(path):
    import trimesh
    m = trimesh.load(path, force="mesh")
    vol = float(m.volume)
    if m.is_winding_consistent and m.is_watertight:
        return len(m.vertices), len(m.faces), vol, "watertight"
    return len(m.vertices), len(m.faces), vol, "NOT watertight"


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'test_output')
    os.makedirs(out, exist_ok=True)
    cq_stl = os.path.join(out, "build123d_spike_koncovka_cadquery.stl")
    b123_stl = os.path.join(out, "build123d_spike_koncovka_build123d.stl")

    print("=== CadQuery reference ===")
    t0 = time.time()
    cq_solid = generate_instrument(**KONCOVKA)
    cq_export_stl(cq_solid, cq_stl)
    print(f"  export: {time.time() - t0:.2f}s -> {cq_stl}")
    nv, nf, vol, status = mesh_stats(cq_stl)
    print(f"  verts={nv} faces={nf} volume={vol:.3f} mm3 [{status}]")

    print("\n=== build123d port ===")
    t0 = time.time()
    b123_solid = build123d_instrument(**KONCOVKA)
    b123_export_stl(b123_solid, b123_stl)
    print(f"  export: {time.time() - t0:.2f}s -> {b123_stl}")
    nv2, nf2, vol2, status2 = mesh_stats(b123_stl)
    print(f"  verts={nv2} faces={nf2} volume={vol2:.3f} mm3 [{status2}]")

    print("\n=== Comparison ===")
    bb_cq = cq_solid.val().BoundingBox()
    bb_b = b123_solid.bounding_box()
    print(f"  CadQuery  bbox: x[{bb_cq.xmin:.2f},{bb_cq.xmax:.2f}] "
          f"y[{bb_cq.ymin:.2f},{bb_cq.ymax:.2f}] z[{bb_cq.zmin:.2f},{bb_cq.zmax:.2f}]")
    print(f"  build123d bbox: x[{bb_b.min.X:.2f},{bb_b.max.X:.2f}] "
          f"y[{bb_b.min.Y:.2f},{bb_b.max.Y:.2f}] z[{bb_b.min.Z:.2f},{bb_b.max.Z:.2f}]")
    vol_err = abs(vol - vol2) / vol * 100
    print(f"  volume: cadquery={vol:.3f} build123d={vol2:.3f} rel err={vol_err:.3f}%")
    verdict = "MATCH (within mesh tolerance)" if vol_err < 1.0 else "DIFFERS"
    print(f"  VERDICT: {verdict}")


if __name__ == "__main__":
    main()
