"""Tests for backend/scan_to_bore.py: mesh slicing -> bore profile."""

import json
import os
import sys

import numpy as np
import pytest

trimesh = pytest.importorskip("trimesh")

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)

from backend.scan_to_bore import (  # noqa: E402
    bore_from_outer,
    cross_section_diameter,
    equivalent_diameter,
    profile_from_mesh,
    profile_to_json,
)


def test_equivalent_diameter_round_trip():
    assert equivalent_diameter(0.0) == 0.0
    d = equivalent_diameter(np.pi * 8.5 ** 2)
    assert d == pytest.approx(17.0, rel=1e-9)


def test_cross_section_diameter_cylinder():
    m = trimesh.creation.cylinder(radius=8.5, height=100.0)
    d = cross_section_diameter(m, 0.0, axis="z")
    assert d == pytest.approx(17.0, abs=0.15)


def test_profile_from_mesh_cylinder():
    m = trimesh.creation.cylinder(radius=8.5, height=100.0)
    positions, diameters = profile_from_mesh(m, axis="z", step_mm=10.0)
    assert len(positions) > 5
    assert positions[0] == pytest.approx(-50.0)
    assert positions[-1] == pytest.approx(50.0)
    assert np.allclose(diameters, 17.0, atol=0.2)


def test_profile_from_mesh_taper():
    m = trimesh.creation.cone(radius=20.0, height=100.0)
    positions, diameters = profile_from_mesh(m, axis="z", step_mm=10.0)
    # cone apex at z=+50 (radius 0), base at z=-50 (radius 20)
    assert diameters[-1] < 2.0
    assert diameters[0] == pytest.approx(40.0, abs=1.0)


def test_bore_from_outer():
    pos, inner = bore_from_outer([0.0, 10.0], [22.0, 24.0], wall_thickness_mm=2.5)
    assert list(inner) == [17.0, 19.0]
    _, clamped = bore_from_outer([0.0], [1.0], wall_thickness_mm=2.0)
    assert clamped[0] == 0.1


def test_profile_to_json(tmp_path):
    out = tmp_path / "bore.json"
    profile_to_json(np.array([0.0, 5.0]), np.array([17.0, 18.0]), str(out), closed_top=True)
    data = json.loads(out.read_text())
    assert data["inner_positions"] == [0.0, 5.0]
    assert data["inner_diameters"] == [17.0, 18.0]
    assert data["closed_top"] is True


def test_cli_writes_json(tmp_path):
    from backend.scan_to_bore import main

    m = trimesh.creation.cylinder(radius=8.5, height=100.0)
    stl = tmp_path / "scan.stl"
    m.export(str(stl))
    out = tmp_path / "bore.json"
    rc = main(["--stl", str(stl), "--axis", "z", "--step", "10", "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert len(data["inner_positions"]) > 5
    assert np.allclose(data["inner_diameters"], 17.0, atol=0.2)
