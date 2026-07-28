"""Weight sweep using Dask scatter for proper serialization."""
import sys, json, time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, r"C:\instrument-designer")

from distributed import Client
from backend.benchmark_all import INSTRUMENTS

WEIGHTS = [1.0, 0.95, 0.9, 0.85, 0.8, 0.7, 0.5]

def _task(item):
    import sys; sys.path.insert(0, r"C:\instrument-designer")
    from backend.jax_optimizer import jax_two_phase_optimize
    inst_name, cfg_dict, w = item
    try:
        result = jax_two_phase_optimize(
            targets=cfg_dict["targets"],
            bore_radius=cfg_dict["bore_radius"],
            outer_diameter=cfg_dict["outer_diameter"],
            hole_diameter=cfg_dict["hole_diameter"],
            hole_length=cfg_dict["hole_length"],
            closed_top=cfg_dict["closed_top"],
            verbose=False, use_jax_bore=False, w_int=w,
        )
        return {"inst": inst_name, "w": w, "cost": result["final_cost"]}
    except Exception as e:
        return {"inst": inst_name, "w": w, "cost": 1e10, "error": str(e)[:100]}

def main():
    client = Client("tcp://127.0.0.1:8786", timeout=10)
    info = client.scheduler_info()
    print(f"Workers: {len(info['workers'])}, Threads: {info['total_threads']}")

    # Build tasks as plain dicts (not cfg objects with complex types)
    tasks = []
    for name, cfg in INSTRUMENTS.items():
        if cfg.get("_chromatic", False):
            continue
        cfg_dict = {
            "targets": list(cfg["targets"]),
            "bore_radius": float(cfg["bore_radius"]),
            "outer_diameter": float(cfg["outer_diameter"]),
            "hole_diameter": float(cfg["hole_diameter"]),
            "hole_length": float(cfg["hole_length"]),
            "closed_top": bool(cfg["closed_top"]),
        }
        for w in WEIGHTS:
            tasks.append((name, cfg_dict, w))

    print(f"Total tasks: {len(tasks)}")

    # Submit in batches to avoid serialization issues
    BATCH = 14  # 2 workers * 7 weights
    all_results = []
    t0 = time.time()

    for i in range(0, len(tasks), BATCH):
        batch = tasks[i:i+BATCH]
        futures = client.map(_task, batch)
        batch_results = client.gather(futures)
        all_results.extend(batch_results)
        done = min(i+BATCH, len(tasks))
        elapsed = time.time() - t0
        print(f"  [{done}/{len(tasks)}] {elapsed:.0f}s", flush=True)

    client.close()
    dt = time.time() - t0
    print(f"\nCompleted in {dt:.1f}s\n")

    # Organize
    by_inst = {}
    for r in all_results:
        name = r["inst"]
        if name not in by_inst:
            by_inst[name] = {}
        by_inst[name][r["w"]] = r["cost"]

    # Print table
    print(f"{'Instrument':<22}", end="")
    for w in WEIGHTS:
        print(f" w={w:.2f}", end="")
    print()
    print(f"{'-'*22}", end="")
    for _ in WEIGHTS:
        print(f" {'-'*6}", end="")
    print()

    for name in sorted(by_inst.keys()):
        print(f"{name:<22}", end="")
        for w in WEIGHTS:
            cost = by_inst[name].get(w, 1e10)
            if cost < 1e5:
                print(f" {cost:>5.2f}c", end="")
            else:
                print(f"   FAIL", end="")
        print()

    # Save
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).parent / f"weight_sweep_{ts}.json"
    with open(out, "w") as f:
        json.dump(by_inst, f, indent=2)
    print(f"\nSaved to {out}")

if __name__ == "__main__":
    main()
