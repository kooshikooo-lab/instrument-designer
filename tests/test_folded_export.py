"""Lock in behavior of the folded-bore (paperclip U-bend) CAD generator.

Covers :func:`backend.cadquery_export.generate_folded_bore_instrument` and
:func:`backend.cadquery_export.export_stl` for the five INSTRUMENTS entries
that carry a ``bend_radius_mm`` key.

Verified geometry:
    leg1 == leg2 == (bore_length - pi*bend_radius_mm) / 2
    xlen == 2 * (bend_radius_mm + ro); zlen == leg1 + wall_thickness + bend_radius_mm + ro
    volume == pi*(ro^2 - ri^2)*bore_length, + cap if closed_top,
              - per tone hole on a straight leg pi*(d/2)^2 * 2*wall_thickness
"""
import math

import pytest

from backend.cadquery_export import (
    INSTRUMENTS,
    export_stl,
    generate_folded_bore_instrument,
)

FOLDED_NAMES = [
    "contra_alto_clarinet_Eb",
    "contra_bass_clarinet_Bb",
    "octo_contra_alto_clarinet_EEb",
    "octo_contra_bass_clarinet_BBB",
    "bass_clarinet_7hole_folded",
]

VOLUME_REL_TOL = 0.03
FOOTPRINT_REL_TOL = 0.08


def _folded_spec(name):
    return {k: v for k, v in INSTRUMENTS[name].items() if k != "_meta"}


def _leg_length(spec):
    return (spec["bore_length"] - math.pi * spec["bend_radius_mm"]) / 2.0


@pytest.fixture(scope="module")
def folded_solids():
    """Generate each folded instrument once, shared across the module."""
    return {name: generate_folded_bore_instrument(**_folded_spec(name)) for name in FOLDED_NAMES}


def test_centerline_length_matches_bore_length():
    """leg1 + leg2 + pi*Rb must reproduce the acoustic (bore) length."""
    for name in FOLDED_NAMES:
        spec = _folded_spec(name)
        bend_arc = math.pi * spec["bend_radius_mm"]
        leg1 = leg2 = _leg_length(spec)
        assert pytest.approx(leg1, rel=1e-9) == leg2
        assert pytest.approx(leg1 + leg2 + bend_arc, rel=1e-9) == spec["bore_length"]


def test_folded_is_compact_not_a_pipe(folded_solids):
    """A folded instrument must be far shorter than its bore length."""
    name = "contra_alto_clarinet_Eb"
    spec = _folded_spec(name)
    bb = folded_solids[name].val().BoundingBox()
    assert bb.zlen < 0.6 * spec["bore_length"]
    assert bb.xlen > 100


@pytest.mark.parametrize("name", FOLDED_NAMES)
def test_folded_footprint(folded_solids, name):
    """Bounding box: xlen ~ 2*(Rb+ro), zlen ~ leg1 + wall + Rb + ro."""
    spec = _folded_spec(name)
    bb = folded_solids[name].val().BoundingBox()
    ro = spec["bore_diameter"] / 2.0 + spec["wall_thickness"]
    leg1 = _leg_length(spec)
    assert pytest.approx(2 * (spec["bend_radius_mm"] + ro), rel=FOOTPRINT_REL_TOL) == bb.xlen
    assert pytest.approx(
        leg1 + spec["wall_thickness"] + spec["bend_radius_mm"] + ro,
        rel=FOOTPRINT_REL_TOL,
    ) == bb.zlen


@pytest.mark.parametrize("name", FOLDED_NAMES)
def test_volume_matches_analytic(folded_solids, name):
    """Volume matches the hollow-tube formula (+ cap, - straight-leg holes)."""
    spec = _folded_spec(name)
    ri = spec["bore_diameter"] / 2.0
    ro = ri + spec["wall_thickness"]
    leg = _leg_length(spec)
    bend_end = leg + math.pi * spec["bend_radius_mm"]

    expected = math.pi * (ro**2 - ri**2) * spec["bore_length"]
    if spec["closed_top"]:
        expected += math.pi * ro**2 * spec["wall_thickness"]
    for pos, diam in spec["holes"]:
        if pos <= leg or pos >= bend_end:
            expected -= math.pi * (diam / 2.0) ** 2 * 2.0 * spec["wall_thickness"]

    actual = folded_solids[name].val().Volume()
    assert pytest.approx(expected, rel=VOLUME_REL_TOL) == actual


@pytest.mark.parametrize("name", FOLDED_NAMES)
def test_single_solid(folded_solids, name):
    """The sweep must fuse into exactly one valid solid."""
    solid = folded_solids[name]
    assert len(solid.solids().vals()) == 1
    assert solid.val().Volume() > 0


def test_stl_export(folded_solids, tmp_path):
    """export_stl writes a real mesh; trimesh bounds match the solid bbox."""
    solid = folded_solids["contra_alto_clarinet_Eb"]
    out = tmp_path / "contra_alto_folded.stl"
    export_stl(solid, str(out))
    assert out.exists()
    assert out.stat().st_size > 100 * 1024

    try:
        import trimesh
    except ImportError:
        pytest.skip("trimesh not importable; cannot verify mesh bounds")

    mesh = trimesh.load(str(out))
    bb = solid.val().BoundingBox()
    assert pytest.approx(mesh.bounds[1][0] - mesh.bounds[0][0], rel=0.02) == bb.xlen
    assert pytest.approx(mesh.bounds[1][1] - mesh.bounds[0][1], rel=0.02) == bb.ylen
    assert pytest.approx(mesh.bounds[1][2] - mesh.bounds[0][2], rel=0.02) == bb.zlen


def test_raises_when_bend_too_large():
    """pi*Rb >= bore_length cannot fit a full U-bend -> ValueError."""
    spec = _folded_spec("contra_alto_clarinet_Eb")
    spec["bend_radius_mm"] = 510.0  # pi*510 ~ 1602 >= 1600
    with pytest.raises(ValueError):
        generate_folded_bore_instrument(**spec)
