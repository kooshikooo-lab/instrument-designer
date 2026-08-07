"""Test the legacy trimesh STL export pipeline with a mock optimizer result."""
import os
import sys

import pytest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from backend.stl_export import (  # noqa: E402
    export_bore_only,
    export_bore_profile_json,
    export_optimizer_result,
)

MOCK_RESULT = {
    "final_rms_cents": 0.5,
    "bore_length_mm": 372.5,
    "bore_radii": [7.25] * 12,
    "hole_positions": [30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0],
    "hole_diameters": [6.5] * 7,
    "hole_lengths": [3.0] * 7,
    "outer_diameter": 22.0,
    "bore_radius": 7.25,
    "hole_diameter": 6.5,
    "hole_length": 3.0,
    "bore_length": 372.5,
}


def test_stl_export(tmp_path):
    """Export full instrument, bore-only, and profile JSON; all non-empty."""
    os.makedirs(tmp_path, exist_ok=True)
    stl_path = export_optimizer_result(MOCK_RESULT, str(tmp_path / "soprano_sax.stl"))
    bore_path = export_bore_only(MOCK_RESULT, str(tmp_path / "soprano_sax_bore.stl"))
    json_path = export_bore_profile_json(MOCK_RESULT, str(tmp_path / "soprano_sax_profile.json"))

    for p in (stl_path, bore_path, json_path):
        assert os.path.exists(p), p
        assert os.path.getsize(p) > 0, f"{p} should not be empty"
