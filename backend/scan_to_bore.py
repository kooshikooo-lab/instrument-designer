"""Reconstruct bore profiles from 3D scan meshes (STL).

Slices a mesh with planes perpendicular to its long axis and converts each
cross-section to an equivalent circular diameter (area-equivalent), producing
an (position, diameter) bore profile ready for TMMInstrument / tmm_instrument_from_radii.

Methodology (REFERENCE_CT_SCANNED_INSTRUMENTS.md):
  - Scans capture the EXTERNAL surface; the air column must be segmented out.
  - For a solid body mesh this module recovers the outer profile.
  - For an air-column mesh (hollow tube) it recovers the inner profile.
  - Wall thickness can be applied to convert outer -> estimated inner profile.
"""

from __future__ import annotations

import json
import math
from typing import Sequence

import numpy as np

try:
    import trimesh
except ImportError:
    trimesh = None


def _axis_vector(axis: str) -> np.ndarray:
    norm = {"x": [1.0, 0.0, 0.0], "y": [0.0, 1.0, 0.0], "z": [0.0, 0.0, 1.0]}
    if axis not in norm:
        raise ValueError(f"axis must be one of {sorted(norm)}")
    return np.asarray(norm[axis], dtype=float)


def _axis_index(axis: str) -> int:
    return {"x": 0, "y": 1, "z": 2}[axis]


def equivalent_diameter(area_mm2: float) -> float:
    """Equivalent circular diameter for a cross-section area (mm)."""
    if area_mm2 <= 0.0:
        return 0.0
    return 2.0 * math.sqrt(area_mm2 / math.pi)


def cross_section_diameter(
    mesh,
    position: float,
    axis: str = "z",
    retry_offset: float = 0.05,
) -> float:
    """Equivalent diameter of the mesh cross-section at a position along axis.

    Retries with a small plane offset if the plane lands exactly on a facet.
    """
    normal = _axis_vector(axis)
    origin = np.zeros(3)
    idx = _axis_index(axis)
    origin[idx] = position
    for offset in (0.0, retry_offset, -retry_offset):
        o = origin.copy()
        o[idx] += offset
        section = mesh.section(plane_origin=o, plane_normal=normal)
        if section is None or len(section.entities) == 0:
            continue
        flat, _ = section.to_2D()
        polys = flat.polygons_full
        if not polys:
            continue
        area = max(p.area for p in polys)
        if area > 0.0:
            return equivalent_diameter(area)
    return 0.0


def profile_from_mesh(
    mesh,
    axis: str = "z",
    step_mm: float = 5.0,
    start_mm: float | None = None,
    end_mm: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Slice a mesh along its long axis and return (positions, diameters).

    Positions are the slice offsets (mm) along the axis; diameters are
    area-equivalent diameters (mm). Returns empty arrays for a None mesh.
    """
    if mesh is None:
        return np.array([], dtype=float), np.array([], dtype=float)
    bounds = mesh.bounds
    idx = _axis_index(axis)
    lo = start_mm if start_mm is not None else float(bounds[0, idx])
    hi = end_mm if end_mm is not None else float(bounds[1, idx])
    positions = np.arange(lo, hi + step_mm, step_mm)
    diameters = np.asarray(
        [cross_section_diameter(mesh, float(p), axis=axis) for p in positions],
        dtype=float,
    )
    return positions, diameters


def bore_from_outer(
    positions: Sequence[float],
    outer_diameters: Sequence[float],
    wall_thickness_mm: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Approximate inner bore from an external profile by subtracting walls."""
    inner = np.maximum(
        np.asarray(outer_diameters, dtype=float) - 2.0 * wall_thickness_mm, 0.1
    )
    return np.asarray(positions, dtype=float), inner


def load_mesh(stl_path: str):
    """Load a mesh (STL) via trimesh; raises a clear error if unavailable."""
    if trimesh is None:
        raise ImportError("trimesh not installed; pip install 'instrument-designer[cad]'")
    return trimesh.load_mesh(stl_path, force="mesh")


def profile_to_json(
    positions: np.ndarray,
    diameters: np.ndarray,
    out_path: str,
    closed_top: bool = False,
) -> None:
    """Write a bore profile JSON (inner_positions/inner_diameters convention)."""
    payload = {
        "inner_positions": [float(p) for p in positions],
        "inner_diameters": [float(d) for d in diameters],
        "closed_top": bool(closed_top),
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Scan mesh -> bore profile")
    parser.add_argument("--stl", required=True, help="input STL mesh")
    parser.add_argument("--axis", default="z", choices=["x", "y", "z"])
    parser.add_argument("--step", type=float, default=5.0, help="slice spacing (mm)")
    parser.add_argument("--wall", type=float, default=0.0, help="wall thickness (mm); subtracts from outer profile")
    parser.add_argument("--out", required=True, help="output bore JSON")
    parser.add_argument("--closed-top", action="store_true")
    args = parser.parse_args(argv)

    mesh = load_mesh(args.stl)
    positions, diameters = profile_from_mesh(mesh, axis=args.axis, step_mm=args.step)
    if len(positions) == 0:
        print(f"[scan_to_bore] no cross-sections recovered from {args.stl}")
        return 2
    if args.wall > 0.0:
        positions, diameters = bore_from_outer(positions, diameters, args.wall)
    profile_to_json(positions, diameters, args.out, closed_top=args.closed_top)
    n = len(positions)
    print(
        f"[scan_to_bore] {n} slices, d={diameters.min():.2f}..{diameters.max():.2f}mm, "
        f"L={positions[-1] - positions[0]:.1f}mm -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
