"""Mesh-repair gate tests (workstream A + audit S2).

Verifies the check-only gate added to ``backend.stl_verifier``
(``check_mesh_repair_gate`` / ``compute_mesh_metrics``) and that
``backend.cadquery_export.export_stl`` runs it after exporting. The gate
requires watertight AND manifold AND a single connected component (a compound
of separate shells fails, even when every shell is individually watertight).

Gate protocol reference: ``docs/TOOLS.md`` (build123d-first + repair fallback).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.cadquery_export import export_stl, generate_instrument
from backend.stl_verifier import check_mesh_repair_gate, compute_mesh_metrics

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")

KONCOVKA = {
    "bore_length": 651.5, "bore_diameter": 16.0, "wall_thickness": 2.0,
    "closed_top": False, "holes": [],
}

XAPHOON = {
    "bore_length": 300.0, "bore_diameter": 14.0, "wall_thickness": 3.0,
    "closed_top": False,
    "holes": [(40, 6.5), (80, 6.5), (120, 6.5), (160, 6.5),
              (200, 6.5), (240, 6.5), (280, 6.5)],
}


def _write_stl(mesh, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    mesh.export(path)
    return path


def test_koncovka_export_passes_gate():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "mesh_gate_koncovka.stl")
    export_stl(generate_instrument(**KONCOVKA), path)
    result = check_mesh_repair_gate(path)
    assert result["passed"], result
    assert result["watertight"] is True
    assert result["manifold"] is True
    assert result["component_count"] == 1
    assert result["volume_mm3"] > 0


def test_metrics_report_manifold():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "mesh_gate_koncovka.stl")
    export_stl(generate_instrument(**KONCOVKA), path)
    metrics = compute_mesh_metrics(path)
    assert metrics.watertight is True
    assert metrics.manifold is True
    assert metrics.component_count == 1


def test_open_triangle_fails_gate():
    import trimesh

    mesh = trimesh.Trimesh(
        vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float),
        faces=np.array([[0, 1, 2]]),
        process=False,
    )
    result = check_mesh_repair_gate(_write_stl(mesh, "mesh_gate_triangle.stl"))
    assert result["passed"] is False
    assert result["watertight"] is False


def test_non_manifold_fin_fails_gate():
    import trimesh

    # Tetrahedron plus an extra 'fin' face sharing edge (0,1): that edge is now
    # bordered by 3 triangles -> non-manifold even though the shell is closed.
    mesh = trimesh.Trimesh(
        vertices=np.array(
            [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [0.5, -0.5, 0.0]], float
        ),
        faces=np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3], [0, 4, 1]]),
        process=False,
    )
    result = check_mesh_repair_gate(_write_stl(mesh, "mesh_gate_fin.stl"))
    assert result["passed"] is False
    assert result["manifold"] is False


def test_compound_fails_gate():
    """Two watertight shells that do not touch are NOT one solid (audit S2):
    watertight+manifold both pass, but component_count=2 fails the gate."""
    import trimesh

    sphere = trimesh.creation.icosphere(subdivisions=1)
    compound = trimesh.util.concatenate(
        sphere, sphere.copy().apply_translation(np.array([5.0, 0.0, 0.0]))
    )
    result = check_mesh_repair_gate(_write_stl(compound, "mesh_gate_compound.stl"))
    assert result["passed"] is False
    assert result["watertight"] is True
    assert result["manifold"] is True
    assert result["component_count"] == 2


def test_xaphoon_export_passes_gate():
    """The 7-hole xaphoon was the known non-watertight CadQuery mesh before
    audit C1 centered the hole cutter; it must now export watertight and pass
    the gate (regression guard for the C1 fix)."""
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "mesh_gate_xaphoon.stl")
    export_stl(generate_instrument(**XAPHOON), path)
    result = check_mesh_repair_gate(path)
    assert result["passed"], result
    assert result["watertight"] is True
    assert result["manifold"] is True
    assert result["component_count"] == 1


def test_gate_never_raises_on_bad_path():
    result = check_mesh_repair_gate(os.path.join(OUT, "does_not_exist.stl"))
    assert result["passed"] is False
    assert result.get("error")
