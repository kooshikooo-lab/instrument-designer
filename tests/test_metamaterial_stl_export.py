"""CAD smoke tests for the metamaterial resonator-section generator.

Skipped when cadquery is not installed (the ``cad`` extra).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

from backend.cadquery_export import export_stl, generate_metamaterial_section

cadquery = pytest.importorskip("cadquery")


def _resonators():
    return [(30.0, 4.0, 8.0, 20.0, 40.0), (70.0, 4.0, 8.0, 20.0, 40.0)]


def test_section_is_single_solid():
    solid = generate_metamaterial_section(
        bore_length=120.0, bore_diameter=25.0, wall_thickness=6.0,
        resonators=_resonators(), closed_end=True,
    )
    assert solid.val().Volume() > 0.0


def test_section_volume_exceeds_plain_tube():
    plain = generate_metamaterial_section(
        bore_length=120.0, bore_diameter=25.0, wall_thickness=6.0,
        resonators=[], closed_end=True,
    )
    with_res = generate_metamaterial_section(
        bore_length=120.0, bore_diameter=25.0, wall_thickness=6.0,
        resonators=_resonators(), closed_end=True,
    )
    assert with_res.val().Volume() > plain.val().Volume()


def test_section_stl_export(tmp_path):
    solid = generate_metamaterial_section(
        bore_length=120.0, bore_diameter=25.0, wall_thickness=6.0,
        resonators=_resonators(), closed_end=True,
    )
    out = tmp_path / "section.stl"
    export_stl(solid, str(out))
    assert out.stat().st_size > 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
