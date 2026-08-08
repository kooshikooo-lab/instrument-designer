"""Create a genuinely non-watertight STL target for the Phase 0.3 mesh-repair
proof, and report its mesh-gate status.

The previous target (xaphoon_C) now exports watertight, so this generator
pokes a visible hole through a known-good solid STL so the Fusion Mesh
workspace repair has something real to fix.

Usage:
    python scripts/gui_automation/make_nonwatertight_target.py [--out PATH]

Writes a non-watertight STL and prints its check_mesh_repair_gate dict.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import numpy as np  # noqa: E402
import trimesh  # noqa: E402

from backend.stl_verifier import check_mesh_repair_gate  # noqa: E402

FUSION_OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "test_output", "fusion"
)
SOURCE = os.path.join(FUSION_OUT, "koncovka_C.stl")
DEFAULT_OUT = os.path.join(FUSION_OUT, "nonwatertight_target.stl")


def punch_hole(mesh: trimesh.Trimesh, center, radius) -> trimesh.Trimesh:
    """Delete faces whose centroid is within radius of center (open-shell).
    The hole is a genuine opening: the mesh becomes non-watertight AND the
    remaining surface is a single connected shell with a boundary ring."""
    fc = mesh.triangles_center
    dist = np.linalg.norm(fc - np.asarray(center, dtype=float), axis=1)
    keep = dist > radius
    faces = mesh.faces[keep]
    vertices = mesh.vertices
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--radius", type=float, default=12.0)
    args = ap.parse_args()

    src = trimesh.load(args.source, force="mesh")
    print(f"source: {args.source} faces={len(src.faces)} watertight={src.is_watertight}")

    # Punch a hole on the side wall, away from the mouthpiece end. The mesh
    # is a low-poly tube with face centroids on a few discrete z-bands, so
    # pick the exact band (middle of the barrel) as the hole center.
    fc = src.triangles_center
    bands = np.unique(np.round(fc[:, 2], 1))
    mid_band = float(bands[len(bands) // 2])
    wall_r = float(np.median(np.linalg.norm(fc[:, :2], axis=1)))
    center = np.array([wall_r, 0.0, mid_band])
    punched = punch_hole(src, center, args.radius)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    punched.export(args.out)
    gate = check_mesh_repair_gate(args.out)
    print(f"wrote : {args.out} faces={len(punched.faces)}")
    print(f"gate  : {gate}")
    if gate["passed"]:
        print("ERROR: target unexpectedly passed the repair gate")
        return 1
    print("OK: target is non-watertight (gate fails as intended)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
