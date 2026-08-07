"""Render a side-by-side comparison of two STLs with bbox overlays.

Usage:
    python scripts/compare_stl_renders.py a.stl b.stl --label-a "Design A" --label-b "Design B" -o compare.png
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.stl_verifier import (  # noqa: E402
    compose_compare_grid,
    render_with_dimensions,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stl_a", help="first STL path")
    ap.add_argument("stl_b", help="second STL path")
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    ap.add_argument("-o", "--output", default="compare.png")
    ap.add_argument("--cols", type=int, default=2)
    args = ap.parse_args()

    label_a = args.label_a or os.path.basename(args.stl_a)
    label_b = args.label_b or os.path.basename(args.stl_b)

    cells = []
    for path, label in ((args.stl_a, label_a), (args.stl_b, label_b)):
        views = render_with_dimensions(path)
        cells.append({"label": label, "png": views["isometric"]})

    png = compose_compare_grid(cells, cols=args.cols)
    with open(args.output, "wb") as f:
        f.write(png)
    print(f"wrote {args.output} ({len(png)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
