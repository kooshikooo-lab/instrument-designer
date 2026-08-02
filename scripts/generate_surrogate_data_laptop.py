"""
Laptop-only Phase 2F training-data generation (no Dask/desktop workers).

Generates samples with direct per-geometry TMM evaluation (Petiot-correct:
geometry -> intonation descriptors, no per-sample optimization) and persists
them to output/ as npz + CSV for Phase 2G surrogate training (local or Kaggle).
"""

from __future__ import annotations
import sys, os, time, argparse
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.surrogate import generate_training_data

RANGES = {
    "bore_radius": (4.0, 15.0),
    "bore_length": (300.0, 400.0),
    "hole_position": (30.0, 350.0),
    "hole_diameter": (5.0, 10.0),
    "hole_length": (2.0, 5.0),
    "outer_diameter": (20.0, 25.0),
    "closed_top": True,
}

TARGET_NAMES = [
    "final_rms_cents",
    "peak_error_cents",
    "median_offset_cents",
    "scale_rms_cents",
]

INPUT_NAMES = (
    [f"radius_cp{i}" for i in range(6)]
    + [f"hole_pos{i}" for i in range(7)]
    + [f"hole_diam{i}" for i in range(7)]
    + [f"hole_len{i}" for i in range(7)]
    + ["bore_length", "outer_diameter", "closed_top"]
)


def main():
    parser = argparse.ArgumentParser(description="Phase 2F laptop-only data generation")
    parser.add_argument("--n", type=int, default=2000, help="number of samples")
    parser.add_argument("--out", default=os.path.join("output", "surrogate", "phase2f"),
                        help="output directory")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    np.random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    print(f"Generating {args.n} samples (laptop, direct TMM eval)...")
    t0 = time.time()
    data = generate_training_data(args.n, bore_param_ranges=RANGES, verbose=False)
    dt = time.time() - t0
    rate = args.n / dt

    inputs = np.array([x for x, _ in data], dtype=np.float32)
    targets = np.array([t for _, t in data], dtype=np.float32)

    # Column-stack (inputs | targets) for CSV
    table = np.concatenate([inputs, targets], axis=1)
    header = ",".join(INPUT_NAMES + TARGET_NAMES)

    npz_path = os.path.join(args.out, f"samples_{args.n}_seed{args.seed}.npz")
    csv_path = os.path.join(args.out, f"samples_{args.n}_seed{args.seed}.csv")

    np.savez_compressed(npz_path, inputs=inputs, targets=targets,
                        target_names=np.array(TARGET_NAMES),
                        input_names=np.array(INPUT_NAMES),
                        ranges=_flat_ranges(RANGES))
    np.savetxt(csv_path, table, delimiter=",", header=header, comments="")

    bad = int((targets[:, 0] >= 1e9).sum())
    print(f"Done: {len(data)} samples in {dt:.1f}s ({rate:.1f} samples/s)")
    print(f"  npz:  {npz_path}")
    print(f"  csv:  {csv_path}")
    print(f"  penalty targets: {bad}")
    print(f"  final_rms cents: min={targets[:,0].min():.1f} mean={targets[:,0].mean():.1f} max={targets[:,0].max():.1f}")


def _flat_ranges(ranges):
    return np.array([[ranges[k][0], ranges[k][1]] for k in ranges if isinstance(ranges[k], tuple)])


if __name__ == "__main__":
    main()
