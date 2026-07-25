"""STL exporter for AcousticNetwork.

Generates 3D mesh files of instrument bore geometry for visualization
and manufacturing review.
"""
import numpy as np
from stl import mesh
from typing import Optional
import os

from ..core.network import AcousticNetwork, Segment, Port, NodeType


def export_bore_stl(
    network: AcousticNetwork,
    filepath: str,
    n_angular: int = 32,
    wall_thickness: float = 2.0,
    include_holes: bool = True,
    hole_depth: float = 5.0,
) -> str:
    """Export instrument bore as STL mesh.

    Creates a hollow tube representing the internal bore geometry.
    The mesh is centered on the bore axis (z-axis).

    Args:
        network: acoustic network definition
        filepath: output STL file path
        n_angular: number of angular segments (higher = smoother)
        wall_thickness: outer wall thickness in mm
        include_holes: whether to include tonehole cylinders
        hole_depth: depth of tonehole cylinders in mm

    Returns:
        Path to the written STL file
    """
    vertices = []
    faces = []

    # Generate bore profile points
    bore_points = []
    pos = 0.0
    for seg in network.segments:
        n_segments = max(2, int(seg.length / 5.0))  # ~5mm per segment
        for i in range(n_segments):
            t = i / n_segments
            r = seg.radius_in + t * (seg.radius_out - seg.radius_in)
            bore_points.append((pos + t * seg.length, r))
        pos += seg.length
    # Add final point
    bore_points.append((pos, network.segments[-1].radius_out))

    # Generate outer bore (for wall thickness)
    outer_points = [(p, r + wall_thickness) for p, r in bore_points]

    # Create bore mesh (inner surface)
    _add_cylinder_mesh(vertices, faces, bore_points, n_angular, flip_normals=False)

    # Create outer wall mesh
    _add_cylinder_mesh(vertices, faces, outer_points, n_angular, flip_normals=True)

    # Add end caps
    _add_end_cap(vertices, faces, bore_points[0], outer_points[0], n_angular)
    _add_end_cap(vertices, faces, bore_points[-1], outer_points[-1], n_angular)

    # Add tonehole cylinders
    if include_holes:
        for port in network.ports:
            if port.node_type in (NodeType.TONEHOLE, NodeType.REGISTER_VENT):
                _add_hole_mesh(vertices, faces, port, hole_depth, n_angular // 2)

    # Create STL mesh
    stl_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            stl_mesh.vectors[i][j] = vertices[f[j]]

    # Save
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    stl_mesh.save(filepath)
    return filepath


def _add_cylinder_mesh(vertices, faces, points, n_angular, flip_normals=False):
    """Add a cylinder mesh from a list of (z, radius) points."""
    n_points = len(points)
    base_idx = len(vertices)

    # Generate vertices
    for i, (z, r) in enumerate(points):
        for j in range(n_angular):
            angle = 2 * np.pi * j / n_angular
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            vertices.append([x, y, z])

    # Generate faces
    for i in range(n_points - 1):
        for j in range(n_angular):
            j_next = (j + 1) % n_angular

            idx00 = base_idx + i * n_angular + j
            idx01 = base_idx + i * n_angular + j_next
            idx10 = base_idx + (i + 1) * n_angular + j
            idx11 = base_idx + (i + 1) * n_angular + j_next

            if flip_normals:
                faces.append([idx00, idx10, idx01])
                faces.append([idx01, idx10, idx11])
            else:
                faces.append([idx00, idx01, idx10])
                faces.append([idx01, idx11, idx10])


def _add_end_cap(vertices, faces, inner_point, outer_point, n_angular):
    """Add an annular end cap."""
    base_idx = len(vertices)
    z_inner = inner_point[0]
    r_inner = inner_point[1]
    z_outer = outer_point[0]
    r_outer = outer_point[1]

    # Inner ring
    for j in range(n_angular):
        angle = 2 * np.pi * j / n_angular
        vertices.append([r_inner * np.cos(angle), r_inner * np.sin(angle), z_inner])

    # Outer ring
    for j in range(n_angular):
        angle = 2 * np.pi * j / n_angular
        vertices.append([r_outer * np.cos(angle), r_outer * np.sin(angle), z_outer])

    # Connect rings
    for j in range(n_angular):
        j_next = (j + 1) % n_angular
        idx_inner0 = base_idx + j
        idx_inner1 = base_idx + j_next
        idx_outer0 = base_idx + n_angular + j
        idx_outer1 = base_idx + n_angular + j_next
        faces.append([idx_inner0, idx_outer0, idx_inner1])
        faces.append([idx_inner1, idx_outer0, idx_outer1])


def _add_hole_mesh(vertices, faces, port: Port, depth: float, n_angular: int):
    """Add a tonehole cylinder."""
    base_idx = len(vertices)
    z = port.position
    r = port.radius

    # Top ring (bore surface)
    for j in range(n_angular):
        angle = 2 * np.pi * j / n_angular
        vertices.append([z, r * np.cos(angle), r * np.sin(angle)])

    # Bottom ring (hole bottom)
    for j in range(n_angular):
        angle = 2 * np.pi * j / n_angular
        vertices.append([z + depth, r * np.cos(angle), r * np.sin(angle)])

    # Side faces
    for j in range(n_angular):
        j_next = (j + 1) % n_angular
        idx_top0 = base_idx + j
        idx_top1 = base_idx + j_next
        idx_bot0 = base_idx + n_angular + j
        idx_bot1 = base_idx + n_angular + j_next
        faces.append([idx_top0, idx_top1, idx_bot0])
        faces.append([idx_top1, idx_bot1, idx_bot0])
