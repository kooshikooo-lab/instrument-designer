"""build123d export backend (workstream B).

A build123d port of the cylindrical ``cadquery_export.generate_instrument``
path: a hollow tube (outer cylinder minus bore) with an optional closed top
and tone holes cut through the wall. Tone holes are **horizontal** cylinders
(axis along X, entering from alternating sides) exactly like CadQuery's
``_cut_single_hole``, so the two backends produce comparable geometry.

Motivation (track C spike, ``backend/experiments/build123d_koncovka.py``):
build123d booleans emit watertight meshes where CadQuery sometimes does not
(e.g. xaphoon_C: 2624v/5264f NOT watertight in CadQuery vs 1000v/2012f
watertight in build123d). Per the mesh-repair-gate protocol in
``docs/TOOLS.md`` (build123d-first + repair fallback), this module is the
preferred generator when a mesh must be printable as-is.

Scope: cylindrical bores only. Conical bores (CadQuery ``bore_diameter``
tuple) are left to ``cadquery_export`` for now. STEP/server wiring stays on the
desktop side (``backend/design_server.py``); this module only produces solids
and STL/STEP files locally.

Run:
    python -m backend.build123d_export            # parity self-check (STLs to test_output/)
"""
import os
import time


def generate_instrument_build123d(
    bore_length: float,
    bore_diameter: float | tuple[float, float],
    wall_thickness: float,
    holes: list[tuple[float, float]] = None,
    closed_top: bool = False,
    hole_depth: float = None,
):
    """Generate an instrument solid with build123d (cylindrical bore path).

    Mirrors ``cadquery_export.generate_instrument``: the model spans
    ``z in [0, bore_length]`` (build123d Cylinder is centered by default, so we
    translate by ``+bore_length/2``), tone holes alternate sides starting on +X,
    and each hole is a horizontal cylinder of diameter ``diam`` centered at
    ``(inner_r * side, 0, pos)`` with length ``wall_thickness + hole_depth``.
    """
    import build123d as b

    if holes is None:
        holes = []
    if hole_depth is None:
        hole_depth = wall_thickness + 2

    if isinstance(bore_diameter, (list, tuple)):
        raise NotImplementedError(
            "build123d backend supports cylindrical bores only; conical "
            "instruments go through cadquery_export.generate_instrument"
        )

    outer_r = (bore_diameter + 2 * wall_thickness) / 2
    inner_r = bore_diameter / 2

    solid = b.Cylinder(outer_r, bore_length) - b.Cylinder(inner_r, bore_length)

    if closed_top:
        # Cap sits on the z=+bore_length end (absolute), i.e. centered-z =
        # bore_length/2 + wall_thickness/2; the whole solid gets translated by
        # +bore_length/2 below.
        cap = b.Pos(0, 0, bore_length / 2 + wall_thickness / 2) * b.Cylinder(
            outer_r, wall_thickness
        )
        solid = solid + cap

    for i, (pos, diam) in enumerate(holes):
        side = 1 if i % 2 == 0 else -1
        # Hole cylinder is horizontal (axis along X), centered at the bore
        # surface and extending OUTWARD by `length` so it fully pierces the wall
        # on BOTH sides. (CadQuery's _cut_single_hole only extends toward +X,
        # so its odd-indexed −X holes are placed inside the bore and never cut
        # the wall — a known cadquery_export bug; see module docstring.)
        length = wall_thickness + hole_depth
        center_x = side * (inner_r + length / 2)
        # Hole z is absolute (0=bell, bore_length=top); the build123d frame is
        # centered, so subtract bore_length/2 here (whole solid translated below).
        hole = b.Pos(center_x, 0, pos - bore_length / 2) * b.Cylinder(
            diam / 2, length, rotation=(0, 90, 0)
        )
        solid = solid - hole

    return solid.translate((0, 0, bore_length / 2))


def export_stl_build123d(
    solid, path: str, tolerance: float = 0.01, angular_tolerance: float = 0.1
) -> float:
    """Export a build123d solid as STL (mirrors ``cadquery_export.export_stl``).

    Runs the check-only mesh-repair gate after exporting: build123d meshes are
    expected to pass (watertight + manifold), so a warning here is a signal the
    geometry or export settings regressed. The export itself never fails.
    """
    import logging

    import build123d as b

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    t0 = time.time()
    b.export_stl(solid, path, tolerance=tolerance, angular_tolerance=angular_tolerance)
    try:
        from backend.stl_verifier import check_mesh_repair_gate

        result = check_mesh_repair_gate(path)
        if not result.get("passed"):
            logging.getLogger(__name__).warning(
                "mesh-repair gate FAILED for %s: watertight=%s manifold=%s",
                result.get("stl"), result.get("watertight"), result.get("manifold"),
            )
    except Exception as e:  # noqa: BLE001 — gate is advisory
        logging.getLogger(__name__).warning("mesh-repair gate check skipped: %s", e)
    return time.time() - t0


def export_step_build123d(solid, path: str) -> float:
    """Export a build123d solid as STEP."""
    import build123d as b

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    t0 = time.time()
    b.export_step(solid, path)
    return time.time() - t0


def instrument_info_build123d(solid) -> dict:
    """Mirror ``cadquery_export.instrument_info`` (bbox lengths in mm)."""
    bb = solid.bounding_box()
    return {
        "length_x": round(bb.max.X - bb.min.X, 2),
        "length_y": round(bb.max.Y - bb.min.Y, 2),
        "length_z": round(bb.max.Z - bb.min.Z, 2),
    }


# ── Parity self-check (writes STLs to test_output/, gitignored) ─────────────

CASES = {
    "koncovka_C": dict(
        bore_length=651.5, bore_diameter=16.0, wall_thickness=2.0,
        closed_top=False, holes=[],
    ),
    "fujara_G": dict(
        bore_length=1746.2, bore_diameter=20.0, wall_thickness=3.0,
        closed_top=True, holes=[],
    ),
    "xaphoon_C": dict(
        bore_length=300.0, bore_diameter=14.0, wall_thickness=3.0,
        closed_top=False,
        holes=[(40, 6.5), (80, 6.5), (120, 6.5), (160, 6.5),
               (200, 6.5), (240, 6.5), (280, 6.5)],
    ),
}


def _stl_stats(path):
    import trimesh

    m = trimesh.load(path, force="mesh")
    status = "watertight" if (m.is_watertight and m.is_winding_consistent) else "NOT watertight"
    return len(m.vertices), len(m.faces), float(m.volume), status


def _cli():
    """Parity self-check: CadQuery vs build123d STL volume/watertightness."""
    from backend.cadquery_export import generate_instrument as cq_gen
    from backend.cadquery_export import export_stl as cq_export_stl

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")
    os.makedirs(out, exist_ok=True)
    print(f"{'case':<12} {'vol_err%':<9} {'cq_status':<13} {'b123_status'}")
    for name, kw in CASES.items():
        cq_path = os.path.join(out, f"parity_{name}_cadquery.stl")
        b123_path = os.path.join(out, f"parity_{name}_build123d.stl")
        cq_export_stl(cq_gen(**kw), cq_path)
        export_stl_build123d(generate_instrument_build123d(**kw), b123_path)
        nv1, nf1, v1, s1 = _stl_stats(cq_path)
        nv2, nf2, v2, s2 = _stl_stats(b123_path)
        vol_err = abs(v1 - v2) / v1 * 100 if v1 else float("nan")
        print(f"{name:<12} {vol_err:<9.3f} {s1:<13} {s2}")


if __name__ == "__main__":
    _cli()
