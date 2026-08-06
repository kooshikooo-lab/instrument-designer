"""STL watertightness regression tests.

Regenerates a curated batch of instrument presets from the parametric
`INSTRUMENTS` specs in `backend.cadquery_export` and asserts the exported
STL meshes are watertight with positive volume. Guards against the earlier
negative-wall / non-manifold regressions (presets fixed in `e3492ed`;
xaphoon_C was the previously-known problem case).

Note: this is intentionally parametric (no committed STL artifacts), so it
catches future preset or exporter regressions rather than stale files.
"""
import os
import sys

import pytest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from backend.cadquery_export import generate_by_name  # noqa: E402
from backend.stl_verifier import compute_mesh_metrics  # noqa: E402

# Every preset that had a negative-wall / non-manifold regression in the past.
BATCH = [
    "koncovka_C",
    "pvc_flute_D",
    "soprano_recorder_C",
    "bass_chalumeau_C",
    "fujara_G",
    "xaphoon_C",
]


@pytest.mark.parametrize("name", BATCH)
def test_preset_stl_is_watertight(name, tmp_path):
    out_dir = str(tmp_path / "stl")
    generate_by_name(name, output_dir=out_dir)
    stl_path = os.path.join(out_dir, name + ".stl")
    assert os.path.exists(stl_path), stl_path

    metrics = compute_mesh_metrics(stl_path)
    assert metrics.watertight, (
        f"{name}: mesh is not watertight "
        f"(verts={metrics.vertex_count}, faces={metrics.face_count})"
    )
    assert metrics.volume_mm3 > 10_000.0, (
        f"{name}: implausibly small volume {metrics.volume_mm3:.1f} mm3"
    )
