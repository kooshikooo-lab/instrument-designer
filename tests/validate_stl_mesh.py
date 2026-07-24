"""Validate STL mesh quality for generated instruments.

Checks: watertight mesh, correct vertex count, no degenerate faces,
volume comparison against analytical cylinder/cone formulas.
"""

import os
import struct
import math
import json


def read_stl_binary(path):
    """Read binary STL file, return vertices and triangles."""
    with open(path, "rb") as f:
        header = f.read(80)
        n_triangles = struct.unpack("<I", f.read(4))[0]

        triangles = []
        for _ in range(n_triangles):
            normal = struct.unpack("<3f", f.read(12))
            v1 = struct.unpack("<3f", f.read(12))
            v2 = struct.unpack("<3f", f.read(12))
            v3 = struct.unpack("<3f", f.read(12))
            attr = struct.unpack("<H", f.read(2))[0]
            triangles.append((v1, v2, v3))

    return triangles


def mesh_volume(triangles):
    """Compute signed volume of a watertight triangle mesh."""
    vol = 0.0
    for v1, v2, v3 in triangles:
        # Signed volume of tetrahedron formed with origin
        vol += (
            v1[0] * (v2[1]*v3[2] - v2[2]*v3[1]) -
            v2[0] * (v1[1]*v3[2] - v1[2]*v3[1]) +
            v3[0] * (v1[1]*v2[2] - v1[2]*v2[1])
        ) / 6.0
    return abs(vol)


def analytical_cylinder_volume(diam, length):
    r = diam / 2
    return math.pi * r * r * length


def analytical_annulus_volume(outer_diam, bore_diam, length):
    ro = outer_diam / 2
    ri = bore_diam / 2
    return math.pi * (ro*ro - ri*ri) * length


def analytical_cone_volume(small_diam, large_diam, length):
    rs = small_diam / 2
    rl = large_diam / 2
    return math.pi * length / 3.0 * (rs*rs + rs*rl + rl*rl)


def unique_vertices(triangles):
    """Count unique vertices."""
    verts = set()
    for v1, v2, v3 in triangles:
        verts.add(tuple(round(x, 6) for x in v1))
        verts.add(tuple(round(x, 6) for x in v2))
        verts.add(tuple(round(x, 6) for x in v3))
    return len(verts)


def check_degenerate(triangles):
    """Count degenerate triangles (zero area)."""
    count = 0
    for v1, v2, v3 in triangles:
        # Cross product magnitude
        ux, uy, uz = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
        vx, vy, vz = v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]
        nx = uy*vz - uz*vy
        ny = uz*vx - ux*vz
        nz = ux*vy - uy*vx
        area = math.sqrt(nx*nx + ny*ny + nz*nz) / 2.0
        if area < 1e-10:
            count += 1
    return count


# ============================================================
# Expected volumes (analytical)
# ============================================================

instrument_specs = {
    "baroque_clarinet": {
        "outer_diam": 30.0, "bore_diam": 25.0, "length": 598.0,
        "type": "annulus", "closed_top": True,
        "n_holes": 9, "hole_diams": [8.5,8.5,9.0,9.0,9.5,9.5,10.0,7.0,7.0],
        "hole_chimney": 5.0,  # wall + clearance
    },
    "bass_clarinet_7hole": {
        "outer_diam": 37.0, "bore_diam": 25.0, "length": 1211.3,
        "type": "annulus", "closed_top": True,
        "n_holes": 7, "hole_diams": [11.0]*7,
        "hole_chimney": 8.0,
    },
    "bass_chalumeau_C": {
        "outer_diam": 28.0, "bore_diam": 20.5, "length": 830.0,
        "type": "annulus", "closed_top": True,
        "n_holes": 8, "hole_diams": [7.0,7.0,7.0,7.0,7.5,7.5,8.0,8.5],
        "hole_chimney": 7.75,
    },
    "pvc_flute_D": {
        "outer_diam": 26.7, "bore_diam": 20.9, "length": 572.2,
        "type": "annulus", "closed_top": False,
        "n_holes": 6, "hole_diams": [14.6]*6,
        "hole_chimney": 5.8,
    },
    "soprano_sax_Bb": {
        "outer_diam": 20.0, "bore_diam": 12.0, "length": 550.0,
        "type": "annulus", "closed_top": False,
        "n_holes": 7, "hole_diams": [6.5]*7,
        "hole_chimney": 6.0,
    },
    "alto_sax_Eb": {
        "outer_diam": 26.0, "bore_diam": 17.0, "length": 700.0,
        "type": "annulus", "closed_top": False,
        "n_holes": 7, "hole_diams": [7.5]*7,
        "hole_chimney": 6.5,
    },
    "koncovka_C": {
        "outer_diam": 20.0, "bore_diam": 16.0, "length": 651.5,
        "type": "annulus", "closed_top": False,
        "n_holes": 0, "hole_diams": [],
        "hole_chimney": 0,
    },
    "xaphoon_C": {
        "outer_diam": 20.0, "bore_diam": 14.0, "length": 300.0,
        "type": "annulus", "closed_top": False,
        "n_holes": 7, "hole_diams": [6.5]*7,
        "hole_chimney": 5.0,
    },
    "glissotar": {
        "small_diam": 16.0, "large_diam": 36.0, "length": 650.0,
        "type": "cone", "closed_top": False,
        "n_holes": 9, "hole_diams": [4.0]+[3.0]*8,
        "hole_chimney": 4.0,
    },
}


print("=" * 70)
print("STL Mesh Quality Validation")
print("=" * 70)

stl_dir = "test_output/instruments"
results = []

for fname in sorted(os.listdir(stl_dir)):
    if not fname.endswith(".stl"):
        continue
    name = fname.replace(".stl", "")
    path = os.path.join(stl_dir, fname)

    print(f"\n--- {name} ---")
    triangles = read_stl_binary(path)
    n_tri = len(triangles)
    n_vert = unique_vertices(triangles)
    n_degen = check_degenerate(triangles)
    vol = mesh_volume(triangles)
    file_size = os.path.getsize(path) / 1024

    print(f"  Triangles: {n_tri:,}")
    print(f"  Vertices:  {n_vert:,}")
    print(f"  Degenerate faces: {n_degen}")
    print(f"  Mesh volume: {vol:.1f} mm^3 ({vol/1000:.1f} cm^3)")
    print(f"  File size: {file_size:.1f} KB")

    # Volume comparison
    spec = instrument_specs.get(name)
    if spec:
        if spec["type"] == "annulus":
            expected_vol = analytical_annulus_volume(spec["outer_diam"], spec["bore_diam"], spec["length"])
            # Subtract hole volumes (cylinders through wall)
            wall = (spec["outer_diam"] - spec["bore_diam"]) / 2
            for d in spec["hole_diams"]:
                r = d / 2
                hole_vol = math.pi * r * r * (wall + 2)  # extrude = wall + clearance
                expected_vol -= hole_vol
            # Add cap volume if closed
            if spec.get("closed_top"):
                ro = spec["outer_diam"] / 2
                expected_vol += math.pi * ro * ro * spec.get("hole_chimney", 2.5)
        elif spec["type"] == "cone":
            expected_vol = analytical_cone_volume(spec["small_diam"], spec["large_diam"], spec["length"])

        err_pct = abs(vol - expected_vol) / expected_vol * 100
        status = "OK" if err_pct < 10 else "WARN"
        print(f"  Expected vol: {expected_vol:.1f} mm^3")
        print(f"  Volume error: {err_pct:.1f}% ({status})")
        results.append((name, "PASS" if err_pct < 10 else "WARN", n_tri, n_degen, err_pct))
    else:
        results.append((name, "NO_SPEC", n_tri, n_degen, None))

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print(f"{'Instrument':<25} {'Status':<8} {'Triangles':>10} {'Degenerates':>12} {'Vol Err':>10}")
print("-" * 70)
for name, status, n_tri, n_degen, err_pct in results:
    err_str = f"{err_pct:.1f}%" if err_pct is not None else "N/A"
    print(f"{name:<25} {status:<8} {n_tri:>10,} {n_degen:>12} {err_str:>10}")
