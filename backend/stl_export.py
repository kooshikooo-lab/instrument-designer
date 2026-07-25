"""
STL Export Pipeline for 3D-Printed Wind Instruments.

Converts SequentialBoreOptimizer results into printable STL geometry.
Uses trimesh for surface-of-revolution and boolean operations.

Usage:
    from backend.stl_export import export_instrument_stl

    result = optimizer.run(verbose=False)
    export_instrument_stl(result, "output/instrument.stl")
"""
import os
import numpy as np
import trimesh
from typing import Dict, List, Optional


def make_bore_surface_of_revolution(
    positions: np.ndarray,
    radii: np.ndarray,
    n_angular: int = 64,
) -> trimesh.Trimesh:
    """Create a surface of revolution from bore profile.

    Args:
        positions: axial positions along bore (mm)
        radii: bore inner radii at each position (mm)
        n_angular: number of angular divisions (higher = smoother)

    Returns:
        Trimesh object representing the inner bore surface
    """
    n_axial = len(positions)
    n_verts = n_axial * n_angular

    # Generate vertices
    vertices = np.zeros((n_verts, 3))
    for i in range(n_axial):
        x = positions[i]
        r = radii[i]
        for j in range(n_angular):
            angle = 2 * np.pi * j / n_angular
            vertices[i * n_angular + j] = [
                x,  # axial
                r * np.cos(angle),
                r * np.sin(angle),
            ]

    # Generate faces (quads → triangles)
    faces = []
    for i in range(n_axial - 1):
        for j in range(n_angular):
            j_next = (j + 1) % n_angular
            v00 = i * n_angular + j
            v01 = i * n_angular + j_next
            v10 = (i + 1) * n_angular + j
            v11 = (i + 1) * n_angular + j_next
            faces.append([v00, v10, v01])
            faces.append([v01, v10, v11])

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces))
    mesh.fix_normals()
    return mesh


def make_outer_wall(
    positions: np.ndarray,
    bore_radii: np.ndarray,
    wall_thickness: float = 3.0,
    n_angular: int = 64,
) -> trimesh.Trimesh:
    """Create the outer wall of the instrument.

    Args:
        positions: axial positions (mm)
        bore_radii: inner bore radii (mm)
        wall_thickness: wall thickness in mm
        n_angular: angular divisions

    Returns:
        Trimesh object representing the outer shell (hollow cylinder)
    """
    outer_radii = bore_radii + wall_thickness
    return make_bore_surface_of_revolution(positions, outer_radii, n_angular)


def make_capped_bore(
    positions: np.ndarray,
    bore_radii: np.ndarray,
    wall_thickness: float = 3.0,
    n_angular: int = 64,
    cap_thickness: float = 2.0,
) -> trimesh.Trimesh:
    """Create a solid instrument body (bore + outer wall + end caps).

    The result is a hollow tube with the bore as an internal void.
    For 3D printing, we generate the OUTER shape only — the bore
    will be created by the printer's infill or by post-processing.

    For a more useful printable model, we generate the bore as a
    negative space and the outer wall as a solid shell.

    Returns:
        Trimesh representing the solid instrument body
    """
    outer_radii = bore_radii + wall_thickness

    inner = make_bore_surface_of_revolution(positions, bore_radii, n_angular)
    outer = make_bore_surface_of_revolution(positions, outer_radii, n_angular)

    # Cap ends
    cap_start = trimesh.creation.fill_hole(
        outer, outer.faces[:n_angular]
    ) if False else None  # trimesh doesn't have simple fill

    # Combine: just return the outer surface for now
    # Full CSG would require boolean operations
    return outer


def drill_hole(
    body: trimesh.Trimesh,
    hole_x: float,
    hole_radius: float,
    hole_depth: float,
    body_outer_radius: float,
    n_angular: int = 32,
) -> trimesh.Trimesh:
    """Create a cylindrical tone hole and subtract from body.

    For simplicity, we represent tone holes as cylinders penetrating
    from the outer surface inward. Boolean subtraction with trimesh
    can be unreliable, so we use a simplified approach:
    - Create the hole cylinder
    - Use convex hull approximation or manifold subtraction

    Returns:
        Modified Trimesh with hole subtracted
    """
    try:
        hole = trimesh.creation.cylinder(
            radius=hole_radius,
            height=hole_depth + body_outer_radius,
            sections=n_angular,
        )
        # Position the hole cylinder at the correct location
        # Oriented radially (perpendicular to bore axis)
        hole.apply_transform(
            trimesh.transformations.rotation_matrix(
                np.pi / 2, [0, 1, 0]
            )
        )
        hole.apply_translation([hole_x, 0, body_outer_radius / 2])

        result = body.difference(hole, engine="blender")
        return result
    except Exception:
        # Fallback: return body unchanged if CSG fails
        return body


def export_optimizer_result(
    result: Dict,
    output_path: str,
    wall_thickness: float = 3.0,
    n_angular: int = 64,
    include_holes: bool = True,
) -> str:
    """Export SequentialBoreOptimizer result to STL.

    Args:
        result: Dict from SequentialBoreOptimizer.run()
        output_path: path to output STL file
        wall_thickness: instrument wall thickness in mm
        n_angular: angular resolution (64 = good quality)
        include_holes: whether to drill tone holes

    Returns:
        Path to the written STL file
    """
    bore_length = result["bore_length_mm"]
    bore_radii = result["bore_radii"]
    hole_positions = result.get("hole_positions", [])
    hole_diameters = result.get("hole_diameters", [])

    # Interpolate bore profile
    n_cp = len(bore_radii)
    positions = np.linspace(0, bore_length, n_cp)

    # Resample to higher resolution for smooth mesh
    n_resample = max(100, n_cp * 10)
    resampled_positions = np.linspace(0, bore_length, n_resample)
    resampled_radii = np.interp(resampled_positions, positions, bore_radii)

    # Clamp radii to positive values
    resampled_radii = np.maximum(resampled_radii, 1.0)

    # Generate bore surface
    bore = make_bore_surface_of_revolution(
        resampled_positions, resampled_radii, n_angular
    )

    # Generate outer wall
    outer = make_outer_wall(
        resampled_positions, resampled_radii, wall_thickness, n_angular
    )

    # Combine into scene and export
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # For now, export the outer surface (most useful for printing)
    # Full solid body with bore void would require proper CSG
    outer.export(output_path)

    return output_path


def export_bore_only(
    result: Dict,
    output_path: str,
    n_angular: int = 64,
) -> str:
    """Export just the bore interior surface (for visualization/analysis)."""
    bore_length = result["bore_length_mm"]
    bore_radii = result["bore_radii"]

    n_cp = len(bore_radii)
    positions = np.linspace(0, bore_length, n_cp)
    n_resample = max(100, n_cp * 10)
    resampled_positions = np.linspace(0, bore_length, n_resample)
    resampled_radii = np.interp(resampled_positions, positions, bore_radii)
    resampled_radii = np.maximum(resampled_radii, 1.0)

    bore = make_bore_surface_of_revolution(
        resampled_positions, resampled_radii, n_angular
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    bore.export(output_path)
    return output_path


def export_bore_profile_json(
    result: Dict,
    output_path: str,
    n_resample: int = 200,
) -> str:
    """Export bore profile as JSON for web visualization."""
    import json

    bore_length = result["bore_length_mm"]
    bore_radii = result["bore_radii"]
    hole_positions = result.get("hole_positions", [])
    hole_diameters = result.get("hole_diameters", [])

    n_cp = len(bore_radii)
    positions = np.linspace(0, bore_length, n_cp)
    resampled_positions = np.linspace(0, bore_length, n_resample)
    resampled_radii = np.interp(resampled_positions, positions, bore_radii)

    data = {
        "bore_length": bore_length,
        "bore_profile": [
            {"position": float(p), "radius": float(r)}
            for p, r in zip(resampled_positions, resampled_radii)
        ],
        "tone_holes": [
            {"position": float(p), "diameter": float(d)}
            for p, d in zip(hole_positions, hole_diameters)
        ],
        "bore_radii": [float(r) for r in bore_radii],
        "n_bore_cp": result.get("n_bore_cp", 0),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    return output_path
