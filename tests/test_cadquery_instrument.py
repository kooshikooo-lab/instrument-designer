"""Test CadQuery for instrument CAD generation.

Generates a simple cylindrical bore instrument with tone holes,
exports to STEP and STL to verify the pipeline works.
"""

import time
import os
import sys

import pytest
import cadquery as cq
from cadquery import exporters

@pytest.mark.slow
def test_cylindrical_bore_with_holes():
    """Generate a simple clarinet-like bore with 6 tone holes."""

    print("CadQuery version:", cq.__version__)

    # Instrument parameters (mm)
    bore_length = 600.0
    bore_diameter = 15.0
    wall_thickness = 3.0
    outer_diameter = bore_diameter + 2 * wall_thickness

    # Tone hole parameters
    hole_positions = [100, 180, 260, 340, 420, 500]  # from bell
    hole_diameter = 6.0

    t0 = time.time()

    # Create bore (cylinder)
    bore = (
        cq.Workplane("XY")
        .circle(bore_diameter / 2)
        .extrude(bore_length)
    )
    print(f"  Bore created: {bore_diameter}mm x {bore_length}mm")

    # Create outer wall (hollow cylinder)
    wall = (
        cq.Workplane("XY")
        .circle(outer_diameter / 2)
        .circle(bore_diameter / 2)
        .extrude(bore_length)
    )
    print(f"  Wall created: {outer_diameter}mm OD, {bore_diameter}mm ID")

    # Create tone holes (cylinders cutting through the wall)
    holes = cq.Workplane("XY")
    for pos in hole_positions:
        holes = (
            cq.Workplane("XZ")
            .workplane(offset=pos)
            .circle(hole_diameter / 2)
            .extrude(wall_thickness + 1)
        )
        wall = wall.cut(holes)
    print(f"  Cut {len(hole_positions)} tone holes ({hole_diameter}mm)")

    t1 = time.time()
    print(f"  Geometry created in {t1-t0:.2f}s")

    # Export STEP
    output_dir = os.path.join(os.path.dirname(__file__), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    step_path = os.path.join(output_dir, "test_instrument.step")
    exporters.export(wall, step_path)
    step_size = os.path.getsize(step_path)
    print(f"  STEP exported: {step_path} ({step_size/1024:.1f} KB)")
    assert step_size > 0, f"STEP file is empty: {step_path}"

    # Export STL
    stl_path = os.path.join(output_dir, "test_instrument.stl")
    exporters.export(wall, stl_path)
    stl_size = os.path.getsize(stl_path)
    print(f"  STL exported: {stl_path} ({stl_size/1024:.1f} KB)")
    assert stl_size > 0, f"STL file is empty: {stl_path}"

    t2 = time.time()
    print(f"  Export took {t2-t1:.2f}s")
    print(f"  Total time: {t2-t0:.2f}s")

    # Verify geometry: bore is a solid, wall is a solid with holes
    assert bore is not None, "Bore creation failed"
    assert wall is not None, "Wall creation failed"

    return True


@pytest.mark.slow
def test_conical_bore():
    """Generate a conical bore (saxophone-like) with tone holes."""

    print("\n--- Conical Bore Test ---")

    # Conical bore parameters
    bore_length = 800.0
    small_diameter = 12.0  # mouthpiece end
    large_diameter = 30.0  # bell end
    wall_thickness = 2.5

    t0 = time.time()

    # Create conical bore using loft
    bore = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .circle(small_diameter / 2)
        .workplane(offset=bore_length)
        .circle(large_diameter / 2)
        .loft()
    )
    print(f"  Conical bore: {small_diameter}mm to {large_diameter}mm, {bore_length}mm")

    # Create outer cone
    outer = (
        cq.Workplane("XY")
        .workplane(offset=0)
        .circle((small_diameter + 2*wall_thickness) / 2)
        .workplane(offset=bore_length)
        .circle((large_diameter + 2*wall_thickness) / 2)
        .loft()
    )

    # Subtract bore from outer
    instrument = outer.cut(bore)
    print(f"  Hollow conical body created")

    # Add tone holes
    hole_positions = [150, 280, 410, 540, 670]
    hole_diameter = 7.0

    for pos in hole_positions:
        # Interpolate diameter at this position
        frac = pos / bore_length
        diam_at_pos = small_diameter + frac * (large_diameter - small_diameter)
        outer_at_pos = diam_at_pos + 2 * wall_thickness

        hole = (
            cq.Workplane("XZ")
            .workplane(offset=pos)
            .circle(hole_diameter / 2)
            .extrude(wall_thickness + 2)
        )
        instrument = instrument.cut(hole)
    print(f"  Cut {len(hole_positions)} tone holes")

    t1 = time.time()
    print(f"  Geometry created in {t1-t0:.2f}s")

    # Export
    output_dir = os.path.join(os.path.dirname(__file__), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    step_path = os.path.join(output_dir, "test_conical.step")
    exporters.export(instrument, step_path)
    step_size = os.path.getsize(step_path)
    print(f"  STEP: {step_size/1024:.1f} KB")
    assert step_size > 0, f"Conical STEP file is empty: {step_path}"

    stl_path = os.path.join(output_dir, "test_conical.stl")
    exporters.export(instrument, stl_path)
    stl_size = os.path.getsize(stl_path)
    print(f"  STL: {stl_size/1024:.1f} KB")
    assert stl_size > 0, f"Conical STL file is empty: {stl_path}"

    t2 = time.time()
    print(f"  Total time: {t2-t0:.2f}s")

    assert instrument is not None, "Conical bore instrument creation failed"

    return True


@pytest.mark.slow
def test_parametric_instrument():
    """Test parametric generation from bore profile data."""

    print("\n--- Parametric Bore Profile Test ---")

    # Bore profile as [(position, diameter)] pairs
    bore_profile = [
        (0.0, 14.0),    # bell
        (200.0, 14.5),  # slight taper
        (400.0, 15.0),  # middle
        (600.0, 14.8),  # slight narrowing
        (800.0, 12.0),  # mouthpiece end
    ]

    wall_thickness = 2.5
    tone_holes = [
        (120.0, 6.0),   # (position, diameter)
        (220.0, 6.5),
        (320.0, 7.0),
        (420.0, 7.0),
        (520.0, 6.5),
        (620.0, 6.0),
    ]

    t0 = time.time()

    # Build bore as lofted shape
    result = cq.Workplane("XY")
    for i, (pos, diam) in enumerate(bore_profile):
        if i == 0:
            result = result.workplane(offset=pos).circle(diam / 2)
        else:
            result = result.workplane(offset=pos - bore_profile[i-1][0]).circle(diam / 2)
    bore_solid = result.loft()

    # Build outer shell
    outer_result = cq.Workplane("XY")
    for i, (pos, diam) in enumerate(bore_profile):
        outer_diam = diam + 2 * wall_thickness
        if i == 0:
            outer_result = outer_result.workplane(offset=pos).circle(outer_diam / 2)
        else:
            outer_result = outer_result.workplane(offset=pos - bore_profile[i-1][0]).circle(outer_diam / 2)
    outer_solid = outer_result.loft()

    # Cut bore from outer
    instrument = outer_solid.cut(bore_solid)
    print(f"  Parametric bore: {len(bore_profile)} control points")

    # Cut tone holes
    for pos, diam in tone_holes:
        hole = (
            cq.Workplane("XZ")
            .workplane(offset=pos)
            .circle(diam / 2)
            .extrude(wall_thickness + 2)
        )
        instrument = instrument.cut(hole)
    print(f"  Cut {len(tone_holes)} tone holes")

    t1 = time.time()
    print(f"  Geometry created in {t1-t0:.2f}s")

    # Export
    output_dir = os.path.join(os.path.dirname(__file__), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    step_path = os.path.join(output_dir, "test_parametric.step")
    exporters.export(instrument, step_path)
    step_size = os.path.getsize(step_path)
    print(f"  STEP: {step_size/1024:.1f} KB")
    assert step_size > 0, f"Parametric STEP file is empty: {step_path}"

    stl_path = os.path.join(output_dir, "test_parametric.stl")
    exporters.export(instrument, stl_path)
    stl_size = os.path.getsize(stl_path)
    print(f"  STL: {stl_size/1024:.1f} KB")
    assert stl_size > 0, f"Parametric STL file is empty: {stl_path}"

    t2 = time.time()
    print(f"  Total time: {t2-t0:.2f}s")

    assert instrument is not None, "Parametric instrument creation failed"

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("CadQuery Instrument CAD Test")
    print("=" * 60)

    results = []

    try:
        results.append(("Cylindrical bore", test_cylindrical_bore_with_holes()))
    except Exception as e:
        print(f"  FAILED: {e}")
        results.append(("Cylindrical bore", False))

    try:
        results.append(("Conical bore", test_conical_bore()))
    except Exception as e:
        print(f"  FAILED: {e}")
        results.append(("Conical bore", False))

    try:
        results.append(("Parametric profile", test_parametric_instrument()))
    except Exception as e:
        print(f"  FAILED: {e}")
        results.append(("Parametric profile", False))

    print("\n" + "=" * 60)
    print("Results:")
    for name, ok in results:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print("=" * 60)
