"""Tests for STL rendering + bbox overlay + compare-grid compositing.

The VTK renderer runs offscreen; these tests keep the STL tiny (a trimesh
cylinder) so the suite stays fast.
"""
import io
import os
import sys

import numpy as np
import pytest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from backend.stl_verifier import (  # noqa: E402
    compose_compare_grid,
    compute_mesh_metrics,
    overlay_dimension_band,
    render_mesh_views,
    render_with_dimensions,
)

from PIL import Image  # noqa: E402


@pytest.fixture(scope="module")
def tiny_stl(tmp_path_factory):
    """A known-geometry cylinder STL: radius 5, height 20 mm."""
    import trimesh

    out_dir = tmp_path_factory.mktemp("render")
    path = str(out_dir / "cyl.stl")
    mesh = trimesh.creation.cylinder(radius=5, height=20, sections=24)
    mesh.export(path)
    return path


def test_compute_mesh_metrics_on_cylinder(tiny_stl):
    m = compute_mesh_metrics(tiny_stl)
    assert m.watertight
    assert m.volume_mm3 > 1000.0  # cylinder: pi*25*20 ~= 1571
    assert m.bbox_mm[2] == pytest.approx(20.0, abs=1.0)


def test_render_mesh_views_pngs(tiny_stl):
    views = render_mesh_views(tiny_stl)
    assert set(views) == {"front", "side", "isometric", "top"}
    for name, png in views.items():
        assert png[:4] == b"\x89PNG", name
        assert len(png) > 100, name


def test_overlay_dimension_band_grows_image(tiny_stl):
    base = render_mesh_views(tiny_stl)["isometric"]
    annotated = overlay_dimension_band(base, "bbox (x,y,z) = 10.0 x 10.0 x 20.0 mm")

    with Image.open(io.BytesIO(annotated)) as img:
        assert img.width == 768
        assert img.height == 768 + 40  # band_height default


def test_render_with_dimensions_annotates_all_views(tiny_stl):
    annotated = render_with_dimensions(tiny_stl)
    assert set(annotated) == {"front", "side", "isometric", "top"}
    for name, png in annotated.items():
        assert png[:4] == b"\x89PNG", name
        with Image.open(io.BytesIO(png)) as img:
            assert img.height == 768 + 40


def test_compose_compare_grid_two_up(tiny_stl):
    base = render_mesh_views(tiny_stl)
    cells = [
        {"label": "front", "png": base["front"]},
        {"label": "side", "png": base["side"]},
    ]
    grid = compose_compare_grid(cells, cols=2)
    assert grid[:4] == b"\x89PNG"
    with Image.open(io.BytesIO(grid)) as img:
        assert img.width == 2 * 768
        assert img.height == 768 + 34  # one row: cell + label


def test_compose_compare_grid_requires_cells():
    with pytest.raises(ValueError):
        compose_compare_grid([])
