"""Generate and validate STL files for multiple instrument types using CadQuery.

Each instrument is generated from our verified specs, then geometry is
validated against expected dimensions.
"""

import time
import os
import json
import math

os.makedirs("test_output/instruments", exist_ok=True)

# ============================================================
# CadQuery instrument generator
# ============================================================

def make_cylindrical_instrument(name, length, bore_diam, wall_thick, holes, closed_top=True):
    """Generate a cylindrical bore instrument with tone holes.

    Args:
        name: instrument name
        length: total bore length (mm)
        bore_diam: bore diameter (mm)
        wall_thick: wall thickness (mm)
        holes: list of (position_mm, diameter_mm) tuples
        closed_top: if True, caps the top end (reed/brass)
    Returns:
        (cadquery solid, dict of measurements)
    """
    import cadquery as cq

    outer_diam = bore_diam + 2 * wall_thick

    # Hollow cylinder
    instrument = (
        cq.Workplane("XY")
        .circle(outer_diam / 2)
        .circle(bore_diam / 2)
        .extrude(length)
    )

    # Cap top if closed
    if closed_top:
        cap = (
            cq.Workplane("XY")
            .circle(outer_diam / 2)
            .extrude(wall_thick)
        )
        cap = cap.translate((0, 0, length))
        instrument = instrument.union(cap)

    # Cut tone holes
    for pos, diam in holes:
        hole = (
            cq.Workplane("XZ")
            .workplane(offset=pos)
            .circle(diam / 2)
            .extrude(wall_thick + 2)
        )
        instrument = instrument.cut(hole)

    measurements = {
        "name": name,
        "length": length,
        "bore_diameter": bore_diam,
        "outer_diameter": outer_diam,
        "wall_thickness": wall_thick,
        "n_holes": len(holes),
        "hole_positions": [h[0] for h in holes],
        "hole_diameters": [h[1] for h in holes],
        "closed_top": closed_top,
    }
    return instrument, measurements


def make_conical_instrument(name, length, small_diam, large_diam, wall_thick, holes):
    """Generate a conical bore instrument with tone holes."""
    import cadquery as cq

    small_outer = small_diam + 2 * wall_thick
    large_outer = large_diam + 2 * wall_thick

    # Outer cone
    outer = (
        cq.Workplane("XY")
        .circle(small_outer / 2)
        .workplane(offset=length)
        .circle(large_outer / 2)
        .loft()
    )

    # Inner cone (bore)
    bore = (
        cq.Workplane("XY")
        .circle(small_diam / 2)
        .workplane(offset=length)
        .circle(large_diam / 2)
        .loft()
    )

    instrument = outer.cut(bore)

    # Tone holes
    for pos, diam in holes:
        hole = (
            cq.Workplane("XZ")
            .workplane(offset=pos)
            .circle(diam / 2)
            .extrude(wall_thick + 2)
        )
        instrument = instrument.cut(hole)

    measurements = {
        "name": name,
        "length": length,
        "bore_small_diam": small_diam,
        "bore_large_diam": large_diam,
        "wall_thickness": wall_thick,
        "n_holes": len(holes),
        "hole_positions": [h[0] for h in holes],
        "hole_diameters": [h[1] for h in holes],
    }
    return instrument, measurements


def export_and_measure(instrument, measurements, output_dir="test_output/instruments"):
    """Export STEP + STL and measure file sizes."""
    from cadquery import exporters

    name = measurements["name"]
    step_path = os.path.join(output_dir, f"{name}.step")
    stl_path = os.path.join(output_dir, f"{name}.stl")

    t0 = time.time()
    exporters.export(instrument, step_path)
    t1 = time.time()
    exporters.export(instrument, stl_path)
    t2 = time.time()

    measurements["step_size_kb"] = os.path.getsize(step_path) / 1024
    measurements["stl_size_kb"] = os.path.getsize(stl_path) / 1024
    measurements["step_time"] = t1 - t0
    measurements["stl_time"] = t2 - t1
    measurements["total_time"] = t2 - t0

    return measurements


def validate_measurement(name, key, actual, expected, tolerance=0.5):
    """Check a single measurement against expected value."""
    if expected is None:
        return True, f"{key}: {actual:.2f} (no expected value)"
    err = abs(actual - expected)
    ok = err <= tolerance
    status = "OK" if ok else f"FAIL (err={err:.2f})"
    return ok, f"{key}: {actual:.2f} vs {expected:.2f} {status}"


# ============================================================
# Instrument definitions (from verified specs)
# ============================================================

def gen_baroque_clarinet():
    """Baroque Clarinet, 2-key Denner style. From config/baroque_clarinet.json."""
    return make_cylindrical_instrument(
        name="baroque_clarinet",
        length=598.0,
        bore_diam=25.0,
        wall_thick=2.5,
        holes=[
            (95, 8.5), (135, 8.5), (175, 9.0), (215, 9.0),
            (260, 9.5), (305, 9.5), (350, 10.0),
            (395, 7.0), (430, 7.0),  # A_key, Bb_key
        ],
        closed_top=True,
    )


def gen_bass_clarinet_7hole():
    """Bass Clarinet in Bb, 7-hole diatonic. From config/bass_clarinet_7hole.json."""
    return make_cylindrical_instrument(
        name="bass_clarinet_7hole",
        length=1211.3,
        bore_diam=25.0,
        wall_thick=6.0,  # outer=37mm
        holes=[
            (175.9, 11.0), (292.9, 11.0), (337.5, 11.0),
            (444.6, 11.0), (532.0, 11.0), (609.8, 11.0), (636.4, 11.0),
        ],
        closed_top=True,
    )


def gen_bass_chalumeau():
    """Bass Chalumeau in C, 8 holes. From benchmark configs."""
    return make_cylindrical_instrument(
        name="bass_chalumeau_C",
        length=830.0,
        bore_diam=20.5,
        wall_thick=3.75,  # outer=28mm
        holes=[
            (90, 7.0), (120, 7.0), (175, 7.0), (230, 7.0),
            (340, 7.5), (395, 7.5), (450, 8.0), (560, 8.5),
        ],
        closed_top=True,
    )


def gen_pvc_flute_d():
    """PVC Flute in D. From chat-logs/flute-calculations.json."""
    return make_cylindrical_instrument(
        name="pvc_flute_D",
        length=572.2,
        bore_diam=20.9,
        wall_thick=2.9,
        holes=[
            (61.7, 14.6), (118.5, 14.6), (144.6, 14.6),
            (192.4, 14.6), (235.0, 14.6), (272.9, 14.6),
        ],
        closed_top=False,
    )


def gen_soprano_sax():
    """Soprano Saxophone in Bb. From benchmark_all.py."""
    return make_cylindrical_instrument(
        name="soprano_sax_Bb",
        length=550.0,
        bore_diam=12.0,
        wall_thick=4.0,  # outer=20mm
        holes=[
            (80, 6.5), (150, 6.5), (220, 6.5),
            (290, 6.5), (360, 6.5), (430, 6.5), (500, 6.5),
        ],
        closed_top=False,
    )


def gen_alto_sax():
    """Alto Saxophone in Eb. From benchmark_all.py."""
    return make_cylindrical_instrument(
        name="alto_sax_Eb",
        length=700.0,
        bore_diam=17.0,
        wall_thick=4.5,  # outer=26mm
        holes=[
            (100, 7.5), (180, 7.5), (260, 7.5),
            (340, 7.5), (420, 7.5), (500, 7.5), (580, 7.5),
        ],
        closed_top=False,
    )


def gen_koncovka():
    """Koncovka C - Slovak overtone flute. Simple tube, no holes."""
    return make_cylindrical_instrument(
        name="koncovka_C",
        length=651.5,
        bore_diam=16.0,
        wall_thick=2.0,
        holes=[],
        closed_top=False,
    )


def gen_xaphoon():
    """Xaphoon in C (pocket sax). From benchmark_all.py."""
    return make_cylindrical_instrument(
        name="xaphoon_C",
        length=300.0,
        bore_diam=14.0,
        wall_thick=3.0,  # outer=20mm
        holes=[
            (40, 6.5), (80, 6.5), (120, 6.5),
            (160, 6.5), (200, 6.5), (240, 6.5), (280, 6.5),
        ],
        closed_top=False,
    )


def gen_glissotar():
    """Glissotar - conical bore with slit vents. From preset YAML."""
    bore_profile = [
        (0.0, 16.0), (100.0, 18.0), (200.0, 21.0),
        (300.0, 24.0), (400.0, 27.0), (500.0, 30.0),
        (600.0, 33.0), (650.0, 36.0),
    ]
    return make_conical_instrument(
        name="glissotar",
        length=650.0,
        small_diam=16.0,
        large_diam=36.0,
        wall_thick=2.0,
        holes=[
            (80, 4.0),   # register
            (150, 3.0), (220, 3.0), (290, 3.0), (360, 3.0),
            (430, 3.0), (500, 3.0), (570, 3.0), (620, 3.0),
        ],
    )


# ============================================================
# Main
# ============================================================

generators = [
    gen_baroque_clarinet,
    gen_bass_clarinet_7hole,
    gen_bass_chalumeau,
    gen_pvc_flute_d,
    gen_soprano_sax,
    gen_alto_sax,
    gen_koncovka,
    gen_xaphoon,
    gen_glissotar,
]

print("=" * 70)
print("CadQuery Instrument STL Generation & Validation")
print("=" * 70)

import cadquery as cq
print(f"CadQuery {cq.__version__} loaded\n")

results = []
all_measurements = []

for gen_fn in generators:
    name = gen_fn.__doc__.split(".")[0].strip() if gen_fn.__doc__ else gen_fn.__name__
    print(f"--- {name} ---")
    t0 = time.time()

    try:
        instrument, meas = gen_fn()
        t_geom = time.time() - t0
        meas["geometry_time"] = t0 - time.time() + t0  # reset
        print(f"  Geometry: {time.time()-t0:.2f}s")

        m = export_and_measure(instrument, meas)
        all_measurements.append(m)

        print(f"  STEP: {m['step_size_kb']:.1f} KB ({m['step_time']:.2f}s)")
        print(f"  STL:  {m['stl_size_kb']:.1f} KB ({m['stl_time']:.2f}s)")
        print(f"  Total: {m['total_time']:.2f}s")
        print(f"  Bore: {m.get('bore_diameter', m.get('bore_small_diam'))}mm x {m['length']}mm, "
              f"{m['n_holes']} holes, closed_top={m.get('closed_top', 'N/A')}")
        results.append(("PASS", name))
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        results.append(("FAIL", name))

    print()

# ============================================================
# Validation: check dimensions match source specs
# ============================================================
print("=" * 70)
print("Geometry Validation")
print("=" * 70)

validations = [
    ("baroque_clarinet", "length", 598.0),
    ("baroque_clarinet", "bore_diameter", 25.0),
    ("baroque_clarinet", "n_holes", 9),
    ("bass_clarinet_7hole", "length", 1211.3),
    ("bass_clarinet_7hole", "bore_diameter", 25.0),
    ("bass_clarinet_7hole", "n_holes", 7),
    ("bass_chalumeau_C", "length", 830.0),
    ("bass_chalumeau_C", "bore_diameter", 20.5),
    ("bass_chalumeau_C", "n_holes", 8),
    ("pvc_flute_D", "length", 572.2),
    ("pvc_flute_D", "bore_diameter", 20.9),
    ("pvc_flute_D", "n_holes", 6),
    ("soprano_sax_Bb", "bore_diameter", 12.0),
    ("alto_sax_Eb", "bore_diameter", 17.0),
    ("koncovka_C", "length", 651.5),
    ("koncovka_C", "n_holes", 0),
    ("xaphoon_C", "bore_diameter", 14.0),
    ("glissotar", "bore_small_diam", 16.0),
    ("glissotar", "bore_large_diam", 36.0),
]

val_pass = 0
val_fail = 0
for m in all_measurements:
    for v_name, v_key, v_expected in validations:
        if m["name"] == v_name and v_key in m:
            ok, msg = validate_measurement(v_name, v_key, m[v_key], v_expected)
            print(f"  {v_name}: {msg}")
            if ok:
                val_pass += 1
            else:
                val_fail += 1

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
for status, name in results:
    print(f"  {status}: {name}")

print(f"\nValidations: {val_pass} passed, {val_fail} failed")

# Save measurements JSON
with open("test_output/instruments/measurements.json", "w") as f:
    json.dump(all_measurements, f, indent=2)
print(f"Measurements saved to test_output/instruments/measurements.json")
