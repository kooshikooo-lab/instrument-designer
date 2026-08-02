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


def _sample_random(ranges, n_cp=6, n_holes=7):
    """Sample one random geometry, returning raw arrays."""
    bore_length = np.random.uniform(*ranges["bore_length"])
    radii = np.random.uniform(*ranges["bore_radius"], size=n_cp)
    hp = np.sort(np.random.uniform(*ranges["hole_position"], size=n_holes))
    hd = np.random.uniform(*ranges["hole_diameter"], size=n_holes)
    hl = np.random.uniform(*ranges["hole_length"], size=n_holes)
    outer_d = np.random.uniform(*ranges["outer_diameter"])
    closed_top = ranges["closed_top"]
    return bore_length, radii, hp, hd, hl, outer_d, closed_top


def _normalize(radii, bore_length, hp, hd, hl, outer_d, closed_top):
    return np.concatenate([
        radii / 15.0,
        hp / 400.0,
        hd / 10.0,
        hl / 5.0,
        [bore_length / 400.0, outer_d / 25.0, float(closed_top)],
    ])


def _target(ranges):
    """Return the 4 canonical metrics for a sampled geometry (fast direct eval)."""
    from backend.jax_optimizer import eval_metrics
    from backend.benchmark_all import INSTRUMENTS
    targets = INSTRUMENTS["bass_chalumeau_Bb"]["targets"]
    bore_length, radii, hp, hd, hl, outer_d, closed_top = _sample_random(ranges)
    try:
        m = eval_metrics(radii, bore_length, hp, hd, hl, closed_top,
                         targets=np.array(targets), outer_diameter_mm=outer_d)
        return _normalize(radii, bore_length, hp, hd, hl, outer_d, closed_top), np.array([
            m["final_rms_cents"], m["peak_error_cents"],
            m["median_offset_cents"], m["scale_rms_cents"],
        ])
    except Exception:
        return _normalize(radii, bore_length, hp, hd, hl, outer_d, closed_top), \
            np.array([1e10, 1e10, 0.0, 1e10])


def _playable_seeds(n_seeds=3):
    """Get playable (near-zero RMS) geometries from refine_sequential as perturbation anchors."""
    from backend.jax_optimizer import refine_sequential
    from backend.benchmark_all import INSTRUMENTS
    seeds = []
    names = ["bass_chalumeau_Bb", "chalumeau_C", "xaphoon_C"]
    for name in names[:n_seeds]:
        tgt = INSTRUMENTS[name]["targets"]
        cfg = {"targets": np.array(tgt), "closed_top": True,
               "bore_radius": 7.25, "outer_diameter": 22.0,
               "hole_diameter": 7.0, "hole_length": 3.5}
        try:
            rms, L, radii, hp, hd, hl, _ = refine_sequential(cfg, use_jax_bore=True, use_phase_cost=True)
            seeds.append({"L": L, "radii": np.asarray(radii, dtype=float),
                          "hp": np.asarray(hp, dtype=float), "hd": np.asarray(hd, dtype=float),
                          "hl": np.asarray(hl, dtype=float), "name": name, "rms": rms})
            print(f"  seed {name}: rms={rms:.3f} L={L:.1f}")
        except Exception as e:
            print(f"  seed {name} FAILED: {e}")
    return seeds


def _sample_near_seed(seed, n_holes=7):
    """Perturb a playable seed geometry (small relative noise)."""
    L = seed["L"] * (1 + np.random.normal(0, 0.02))
    radii = np.clip(seed["radii"] * (1 + np.random.normal(0, 0.05)), 4.0, 15.0)
    # Pad/truncate seed hole arrays to a consistent n_holes
    hp = np.asarray(seed["hp"], dtype=float)
    hd = np.asarray(seed["hd"], dtype=float)
    hl = np.asarray(seed["hl"], dtype=float)
    if len(hp) < n_holes:
        hp = np.pad(hp, (0, n_holes - len(hp)), mode="edge")
        hd = np.pad(hd, (0, n_holes - len(hd)), mode="edge")
        hl = np.pad(hl, (0, n_holes - len(hl)), mode="edge")
    else:
        hp, hd, hl = hp[:n_holes], hd[:n_holes], hl[:n_holes]
    hp = np.sort(np.clip(hp + np.random.normal(0, 4.0, size=n_holes), 30.0, 350.0))
    hd = np.clip(hd * (1 + np.random.normal(0, 0.08)), 4.0, 12.0)
    hl = np.clip(hl * (1 + np.random.normal(0, 0.08)), 2.0, 5.0)
    outer_d = 22.0
    closed_top = True
    return L, radii, hp, hd, hl, outer_d, closed_top


def generate_mixed_data(n_samples, ranges, seed=42, frac_playable=0.5, n_seeds=3):
    """Half random geometries, half small perturbations of playable designs."""
    from backend.jax_optimizer import eval_metrics
    from backend.benchmark_all import INSTRUMENTS
    from backend.metrics import compute_metrics
    rng = np.random.RandomState(seed)

    targets = np.array(INSTRUMENTS["bass_chalumeau_Bb"]["targets"])
    print("  computing playable seeds...")
    seeds = _playable_seeds(n_seeds)
    data = []
    n_play = int(n_samples * frac_playable)
    for i in range(n_samples):
        if i < n_play and seeds:
            L, radii, hp, hd, hl, outer_d, closed_top = _sample_near_seed(
                seeds[i % len(seeds)])
        else:
            L, radii, hp, hd, hl, outer_d, closed_top = _sample_random(ranges)
        try:
            m = eval_metrics(radii, L, hp, hd, hl, closed_top,
                             targets=targets, outer_diameter_mm=outer_d)
            tgt = np.array([m["final_rms_cents"], m["peak_error_cents"],
                            m["median_offset_cents"], m["scale_rms_cents"]])
        except Exception:
            tgt = np.array([1e10, 1e10, 0.0, 1e10])
        data.append((_normalize(radii, L, hp, hd, hl, outer_d, closed_top), tgt))
    return data


def main():
    parser = argparse.ArgumentParser(description="Phase 2F laptop-only data generation")
    parser.add_argument("--n", type=int, default=2000, help="number of samples")
    parser.add_argument("--out", default=os.path.join("output", "surrogate", "phase2f"),
                        help="output directory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", default="random", choices=["random", "mixed"],
                        help="random = pure random geometry; mixed = random + perturbations of playable designs")
    parser.add_argument("--frac-playable", type=float, default=0.5)
    parser.add_argument("--n-seeds", type=int, default=3)
    args = parser.parse_args()

    np.random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    print(f"Generating {args.n} samples (laptop, direct TMM eval, mode={args.mode})...")
    t0 = time.time()
    if args.mode == "mixed":
        data = generate_mixed_data(args.n, RANGES, seed=args.seed,
                                   frac_playable=args.frac_playable, n_seeds=args.n_seeds)
    else:
        data = generate_training_data(args.n, bore_param_ranges=RANGES, verbose=False)
    dt = time.time() - t0
    rate = args.n / dt

    inputs = np.array([x for x, _ in data], dtype=np.float32)
    targets = np.array([t for _, t in data], dtype=np.float32)

    # Column-stack (inputs | targets) for CSV
    table = np.concatenate([inputs, targets], axis=1)
    header = ",".join(INPUT_NAMES + TARGET_NAMES)

    tag = args.mode if args.mode == "random" else f"mixed{int(args.frac_playable*100)}"
    npz_path = os.path.join(args.out, f"samples_{args.n}_{tag}_seed{args.seed}.npz")
    csv_path = os.path.join(args.out, f"samples_{args.n}_{tag}_seed{args.seed}.csv")

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
