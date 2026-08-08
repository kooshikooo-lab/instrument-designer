"""
Distributed benchmark for TMM evaluate throughput using dask.distributed.

Place this script in scripts/ and run it to measure distributed throughput
across LocalCluster or a remote Dask scheduler. The script uses the repo's
backend.tmm_acoustics.tmm_instrument_from_radii and runs many independent
find_resonance calls to measure evaluations/sec.

Usage:
  # Local quick run (uses LocalCluster)
  python scripts/bench_tmm_dask.py --local --tasks 200 --chunk 5 --nworkers 8

  # Connect to remote scheduler (replace address)
  python scripts/bench_tmm_dask.py --scheduler tcp://SCHEDULER:8786 --tasks 2000 --chunk 10

Notes:
- Prefer running workers with `--nthreads 1` (one thread per process) to avoid
  GIL contention and BLAS oversubscription. Set OMP_NUM_THREADS=1 and
  MKL_NUM_THREADS=1 in the environment before starting workers.

Output: prints total evaluations, elapsed time, and throughput (evals/sec).
"""

import argparse
import time
import numpy as np
from dask.distributed import Client, LocalCluster
from backend.tmm_acoustics import tmm_instrument_from_radii, Hole


def make_test_instrument():
    radii = np.linspace(3.5, 7.0, 50)
    bore_length = 300.0
    hole_positions = [40, 80, 120, 160, 200, 240]
    hole_diams = [7.0] * len(hole_positions)
    hole_lens = [3.75] * len(hole_positions)
    inst = tmm_instrument_from_radii(
        radii_mm=radii,
        bore_length_mm=bore_length,
        hole_positions_mm=hole_positions,
        hole_diameters_mm=hole_diams,
        hole_lengths_mm=hole_lens,
        cone_step=0.5,
    )
    return inst


def make_random_fingering(n_holes):
    import random
    return [random.choice([Hole.OPEN, Hole.CLOSED]) for _ in range(n_holes)]


def worker_task(inst, fingerings_chunk, wl_guess=400.0):
    # run find_resonance for each fingering in the chunk
    out = []
    for fg in fingerings_chunk:
        out.append(inst.find_resonance(wl_guess, fg, n_register=1))
    return out


def main(args):
    if args.local:
        # Create a LocalCluster with one thread per worker process
        cluster = LocalCluster(n_workers=args.nworkers or None, threads_per_worker=1)
        client = Client(cluster)
    else:
        if not args.scheduler:
            raise SystemExit("Provide --scheduler or use --local")
        client = Client(args.scheduler)

    print("Dask cluster connected:", client)

    # Build instrument locally and scatter to workers to avoid reserializing
    inst = make_test_instrument()
    inst_future = client.scatter(inst, broadcast=True)

    # prepare tasks: create many random fingerings and group into chunks
    fingerings = [ [make_random_fingering(inst.n_holes) for _ in range(args.chunk)] for _ in range(args.tasks) ]

    # warmup
    print("Warming up (one local call)...")
    _ = inst.find_resonance(400.0, fingerings[0][0], n_register=1)

    # Submit tasks
    print(f"Submitting {len(fingerings)} tasks (chunk size {args.chunk}) ...")
    t0 = time.perf_counter()
    futures = [ client.submit(worker_task, inst_future, chunk) for chunk in fingerings ]
    results = client.gather(futures)
    t1 = time.perf_counter()

    elapsed = t1 - t0
    total_evals = len(fingerings) * args.chunk
    print(f"Completed {total_evals} find_resonance calls in {elapsed:.3f}s")
    print(f"Throughput: {total_evals/elapsed:.1f} evaluations/sec")

    client.close()
    if args.local:
        cluster.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--local", action="store_true", help="Use LocalCluster on this machine")
    p.add_argument("--scheduler", type=str, default=None, help="Dask scheduler address (tcp://host:port)")
    p.add_argument("--tasks", type=int, default=200, help="Number of task submissions (chunks)")
    p.add_argument("--chunk", type=int, default=5, help="Number of find_resonance calls per task")
    p.add_argument("--nworkers", type=int, default=None, help="Number of workers for LocalCluster (optional)")
    args = p.parse_args()
    main(args)
