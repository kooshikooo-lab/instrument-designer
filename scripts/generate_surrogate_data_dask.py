"""Desktop-Dask bulk surrogate data generation (self-contained worker eval).

Port of the laptop's mixed-sampling scheme (Phase 2F.2) that does NOT depend on
a specific version of `backend` being installed on Dask workers. Each worker
reconstructs the 4 canonical metrics inline from the worker-available TMM
primitives (tmm_instrument_from_radii + TMMInstrument.compute_fingered_frequencies
+ backend.metrics.compute_metrics), so it runs against the shared mesh even when
workers have a stale/older backend package.

Output contract matches scripts/train_surrogate.py:
  CSV:  INPUT_NAMES | TARGET_NAMES   (28 input cols + 4 metric cols)
  npz:  inputs (N,28), targets (N,4), target_names, input_names, ranges

Usage (dry-run on 1 worker first, then scale):
  python scripts/generate_surrogate_data_dask.py --n 500 --scheduler tcp://100.100.66.117:8786
  python scripts/generate_surrogate_data_dask.py --n 50000 --scheduler tcp://100.100.66.117:8786

Mixed scheme: frac_playable of samples are small perturbations of playable
seeds from refine_sequential (bass_chalumeau_Bb / chalumeau_C / xaphoon_C);
the rest are pure-random geometry.
"""

from __future__ import annotations

import argparse
import os
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, ROOT)

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

N_CP = 6
N_HOLES = 7

# Authoritative targets (from backend/benchmark_all.py).
TARGETS_BASS_CHALUMEAU_BB = [233.1, 261.6, 293.7, 311.1, 349.2, 392.0, 440.0, 466.2]

# Playable-seed source instruments (name -> (targets, closed_top)).
SEED_INSTRUMENTS = {
    "bass_chalumeau_Bb": (TARGETS_BASS_CHALUMEAU_BB, True),
}


def _metrics_for_geometry(radii, bore_length, hp, hd, hl, outer_d, closed_top, targets):
    """Reconstruct the 4 canonical metrics from worker-available primitives.

    Equivalent to laptop backend.jax_optimizer.eval_metrics -> eval_cents, but
    only uses APIs present on the shared Dask mesh: tmm_instrument_from_radii,
    TMMInstrument.compute_fingered_frequencies, backend.metrics.compute_metrics.
    """
    from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
    from backend.metrics import compute_metrics

    inst = tmm_instrument_from_radii(
        np.asarray(radii, dtype=float),
        float(bore_length),
        list(map(float, hp)),
        list(map(float, hd)),
        list(map(float, hl)),
        outer_diameter_mm=float(outer_d),
        closed_top=closed_top,
        cone_step=0.5,
    )
    n_reg = 1 if closed_top else 2
    n_holes = len(hp)

    fingerings = []
    for k in range(n_holes):
        f = ["open"] * (k + 1) + ["closed"] * (n_holes - k - 1)
        fingerings.append(f)
    if closed_top:
        fingerings.insert(0, ["closed"] * n_holes)

    tw = [SPEED_OF_SOUND / f for f in targets]
    freqs = inst.compute_fingered_frequencies(tw, fingerings, n_reg)

    cents = []
    for a, t in zip(freqs, targets):
        if a is not None and a > 0 and np.isfinite(a) and t > 0:
            cents.append(1200.0 * np.log2(a / t))
        else:
            cents.append(1e10)
    m = compute_metrics(cents)
    return np.array(
        [m["final_rms_cents"], m["peak_error_cents"],
         m["median_offset_cents"], m["scale_rms_cents"]],
        dtype=float,
    )


def _sample_random(ranges, rng):
    bore_length = rng.uniform(*ranges["bore_length"])
    radii = rng.uniform(*ranges["bore_radius"], size=N_CP)
    hp = np.sort(rng.uniform(*ranges["hole_position"], size=N_HOLES))
    hd = rng.uniform(*ranges["hole_diameter"], size=N_HOLES)
    hl = rng.uniform(*ranges["hole_length"], size=N_HOLES)
    outer_d = rng.uniform(*ranges["outer_diameter"])
    return bore_length, radii, hp, hd, hl, outer_d


def _normalize(radii, bore_length, hp, hd, hl, outer_d, closed_top):
    return np.concatenate([
        np.asarray(radii, dtype=float) / 15.0,
        np.asarray(hp, dtype=float) / 400.0,
        np.asarray(hd, dtype=float) / 10.0,
        np.asarray(hl, dtype=float) / 5.0,
        [bore_length / 400.0, outer_d / 25.0, float(closed_top)],
    ])


def _playable_seeds(n_seeds=3):
    """Playable geometries from refine_sequential as perturbation anchors."""
    from backend.jax_optimizer import refine_sequential

    seeds = []
    for name, (tgt, closed_top) in list(SEED_INSTRUMENTS.items())[:n_seeds]:
        cfg = {"targets": np.array(tgt, dtype=float), "closed_top": closed_top,
               "bore_radius": 7.25, "outer_diameter": 22.0,
               "hole_diameter": 7.0, "hole_length": 3.5}
        try:
            rms, L, radii, hp, hd, hl, _ = refine_sequential(
                cfg, use_jax_bore=True, use_phase_cost=True)
            seeds.append({"L": float(L),
                          "radii": np.asarray(radii, dtype=float),
                          "hp": np.asarray(hp, dtype=float),
                          "hd": np.asarray(hd, dtype=float),
                          "hl": np.asarray(hl, dtype=float),
                          "rms": float(rms)})
        except Exception as e:
            print(f"  seed {name} FAILED: {e}")
    return seeds


def _sample_near_seed(seed, rng):
    L = seed["L"] * (1 + rng.normal(0, 0.02))
    radii = np.clip(seed["radii"] * (1 + rng.normal(0, 0.05, size=len(seed["radii"]))), 4.0, 15.0)
    hp = np.asarray(seed["hp"], dtype=float)
    hd = np.asarray(seed["hd"], dtype=float)
    hl = np.asarray(seed["hl"], dtype=float)
    if len(hp) < N_HOLES:
        hp = np.pad(hp, (0, N_HOLES - len(hp)), mode="edge")
        hd = np.pad(hd, (0, N_HOLES - len(hd)), mode="edge")
        hl = np.pad(hl, (0, N_HOLES - len(hl)), mode="edge")
    else:
        hp, hd, hl = hp[:N_HOLES], hd[:N_HOLES], hl[:N_HOLES]
    hp = np.sort(np.clip(hp + rng.normal(0, 4.0, size=N_HOLES), 30.0, 350.0))
    hd = np.clip(hd * (1 + rng.normal(0, 0.08, size=N_HOLES)), 4.0, 12.0)
    hl = np.clip(hl * (1 + rng.normal(0, 0.08, size=N_HOLES)), 2.0, 5.0)
    outer_d = 22.0
    return L, radii, hp, hd, hl, outer_d


def _generate_batch(batch_id, n_samples, frac_playable, seeds, seed):
    """One batch of samples: (inputs Nx28, targets Nx4). `seeds` is a
    list of JSON-serializable seed lists [L, radii, hp, hd, hl].
    `seed` is the global RNG seed; per-batch seed = seed + batch_id * 7919.
    """
    rng = np.random.RandomState(seed=seed + batch_id * 7919)
    seed_dicts = [_to_seed_dict(s) for s in seeds] if seeds else []
    inputs = []
    targets = []
    n_play = int(n_samples * frac_playable)
    for i in range(n_samples):
        if i < n_play and seed_dicts:
            L, radii, hp, hd, hl, outer_d = _sample_near_seed(seed_dicts[i % len(seed_dicts)], rng)
        else:
            L, radii, hp, hd, hl, outer_d = _sample_random(RANGES, rng)
        tgt = _metrics_for_geometry(radii, L, hp, hd, hl, outer_d, True,
                                    TARGETS_BASS_CHALUMEAU_BB)
        inputs.append(_normalize(radii, L, hp, hd, hl, outer_d, True))
        targets.append(tgt)
    return np.asarray(inputs, dtype=np.float32), np.asarray(targets, dtype=np.float32)


def _to_seed_dict(s):
    """Convert a JSON-safe seed list back into a dict of arrays."""
    return {
        "L": s[0],
        "radii": np.asarray(s[1]),
        "hp": np.asarray(s[2]),
        "hd": np.asarray(s[3]),
        "hl": np.asarray(s[4]),
    }


def main():
    parser = argparse.ArgumentParser(description="Desktop-Dask bulk surrogate data generation")
    parser.add_argument("--n", type=int, default=2000, help="total number of samples")
    parser.add_argument("--scheduler", default="tcp://100.100.66.117:8786")
    parser.add_argument("--out", default=os.path.join("output", "surrogate", "phase2f"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--frac-playable", type=float, default=0.5)
    parser.add_argument("--n-seeds", type=int, default=3)
    parser.add_argument("--batch", type=int, default=250)
    parser.add_argument("--no-dask", action="store_true", help="run locally (no scheduler)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Compute playable seeds locally (refine_sequential needs a working
    # backend; do it on the launching process, then ship the arrays).
    print("Computing playable seeds...")
    seed_dicts = _playable_seeds(args.n_seeds)
    seed_payload = [
        [s["L"], s["radii"].tolist(), s["hp"].tolist(), s["hd"].tolist(), s["hl"].tolist()]
        for s in seed_dicts
    ]
    print(f"  {len(seed_payload)} playable seeds")

    t0 = time.time()
    if args.no_dask or len(seed_payload) == 0:
        X = np.zeros((0, len(INPUT_NAMES)), dtype=np.float32)
        Y = np.zeros((0, 4), dtype=np.float32)
        n_batches = (args.n + args.batch - 1) // args.batch
        for b in range(n_batches):
            n = min(args.batch, args.n - b * args.batch)
            xb, yb = _generate_batch(b, n, args.frac_playable, seed_payload, args.seed)
            X = np.concatenate([X, xb]) if len(X) else xb
            Y = np.concatenate([Y, yb]) if len(Y) else yb
    else:
        from dask.distributed import Client, as_completed
        with Client(args.scheduler, timeout="30s") as client:
            print(f"Connected to {len(client.scheduler_info()['workers'])} workers")
            n_batches = (args.n + args.batch - 1) // args.batch
            futures = {
                client.submit(_generate_batch, b, min(args.batch, args.n - b * args.batch),
                              args.frac_playable, seed_payload, args.seed, pure=False): b
                for b in range(n_batches)
            }
            parts = []
            done = 0
            for fut, _ in as_completed(futures, with_results=True):
                xb, yb = fut.result()
                parts.append((xb, yb))
                done += len(xb)
                elapsed = time.time() - t0
                print(f"  {done}/{args.n} samples ({elapsed:.1f}s)", flush=True)
            X = np.concatenate([p[0] for p in parts], axis=0)
            Y = np.concatenate([p[1] for p in parts], axis=0)
    dt = time.time() - t0
    rate = len(X) / dt if dt > 0 else 0.0

    # Persist npz + CSV (train_surrogate.py-compatible).
    table = np.concatenate([X, Y], axis=1)
    header = ",".join(INPUT_NAMES + TARGET_NAMES)
    npz_path = os.path.join(args.out, f"samples_{args.n}_dask_seed{args.seed}.npz")
    csv_path = os.path.join(args.out, f"samples_{args.n}_dask_seed{args.seed}.csv")
    np.savez_compressed(npz_path, inputs=X, targets=Y,
                        target_names=np.array(TARGET_NAMES),
                        input_names=np.array(INPUT_NAMES))
    np.savetxt(csv_path, table, delimiter=",", header=header, comments="")

    bad = int((Y[:, 0] >= 1e9).sum())
    print(f"Done: {len(X)} samples in {dt:.1f}s ({rate:.1f} samples/s)")
    print(f"  npz: {npz_path}")
    print(f"  csv: {csv_path}")
    print(f"  penalty targets: {bad}")
    if len(Y):
        print(f"  final_rms: min={Y[:,0].min():.1f} mean={Y[:,0].mean():.1f} max={Y[:,0].max():.1f}")
        print(f"  median_offset: mean={np.mean(np.abs(Y[:,2])):.1f}")


if __name__ == "__main__":
    main()
