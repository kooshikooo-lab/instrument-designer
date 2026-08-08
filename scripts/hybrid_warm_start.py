"""
Hybrid warm-start design search (Phase 2H production path).

Uses the trained surrogate as a coarse steering layer over a candidate pool,
then refines the top-k with the real TMM optimizer (`refine_sequential`).

This is the approved production use of the surrogate (see Discussion #23 close-out):
surrogate ranks, `refine_sequential` finishes. It is NOT a replacement for the
real optimizer — it reduces the number of bad local optima the optimizer lands in.

Usage:
    python scripts/hybrid_warm_start.py \
        --model output/surrogate/phase2g_mixed10k/surrogate_params.pkl \
        --meta  output/surrogate/phase2g_mixed10k/meta.json \
        --instrument bass_chalumeau_Bb \
        --pool 2000 --top-k 10 --out output/surrogate/hybrid/results.json
"""
from __future__ import annotations
import sys, os, time, json, argparse
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.surrogate import SurrogateTrainer, SurrogateConfig
from backend.benchmark_all import INSTRUMENTS


def decode(x):
    """Normalized 30-dim -> physical geometry."""
    radii = x[0:6] * 15.0
    hp = x[6:13] * 400.0
    hd = x[13:20] * 10.0
    hl = x[20:27] * 5.0
    L = x[27] * 400.0
    outer_d = x[28] * 25.0
    return radii, L, hp, hd, hl, outer_d


def load_model(meta_path, params_path):
    with open(meta_path) as f:
        meta = json.load(f)
    cfg = SurrogateConfig(hidden_dims=tuple(meta["hidden"]), output_dim=4,
                          input_dim=meta["input_dim"])
    trainer = SurrogateTrainer.load(params_path, cfg)
    y_mean = np.array(meta["y_mean"])
    y_std = np.array(meta["y_std"])
    return trainer, y_mean, y_std, meta


def refine_from(pool_x, idx, targets):
    """Refine one candidate with the real optimizer; return refined rms cents or None."""
    from backend.jax_optimizer import refine_sequential
    radii, L, hp, hd, hl, outer_d = decode(pool_x[idx])
    cfg = {
        "targets": targets, "closed_top": True,
        "bore_radius": float(np.mean(radii)),
        "bore_length": float(L),
        "outer_diameter": float(outer_d),
        "hole_diameter": 7.0, "hole_length": 3.5,
    }
    try:
        rms, *_ = refine_sequential(cfg, use_jax_bore=True, use_phase_cost=True)
        return float(rms) * 1200.0
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Hybrid surrogate warm-start design search")
    parser.add_argument("--model", required=True, help="path to surrogate_params.pkl")
    parser.add_argument("--meta", required=True, help="path to meta.json")
    parser.add_argument("--instrument", default="bass_chalumeau_Bb")
    parser.add_argument("--pool", type=int, default=2000, help="candidate pool size")
    parser.add_argument("--top-k", type=int, default=10, help="how many to refine")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", default=os.path.join("output", "surrogate", "hybrid", "results.json"))
    parser.add_argument("--random-baseline", action="store_true",
                        help="also refine k random designs for comparison")
    args = parser.parse_args()

    trainer, y_mean, y_std, meta = load_model(args.meta, args.model)
    targets = np.array(INSTRUMENTS[args.instrument]["targets"])

    rng = np.random.default_rng(args.seed)
    pool = rng.uniform(0, 1, (args.pool, meta["input_dim"])).astype(np.float32)
    preds = np.asarray(trainer.predict(pool)) * y_std + y_mean

    top_idx = np.argsort(preds[:, 0])[: args.top_k]

    print(f"Refining top-{args.top_k} of {args.pool} surrogate-ranked designs "
          f"for {args.instrument}...")
    t0 = time.time()
    results = []
    for i in top_idx:
        r = refine_from(pool, i, targets)
        results.append({"surrogate_rms_cents": round(float(preds[i, 0]), 1),
                        "refined_rms_cents": r})
        print(f"  surrogate={preds[i,0]:7.1f}c  refined={'%7.1fc' % r if r else 'FAIL'}")
    dt = time.time() - t0

    ok = [r["refined_rms_cents"] for r in results if r["refined_rms_cents"] is not None]
    summary = {
        "instrument": args.instrument,
        "pool": args.pool, "top_k": args.top_k,
        "n_refined": len(ok), "n_zero": int(sum(1 for r in ok if r < 1.0)),
        "mean_refined_rms_cents": float(np.mean(ok)) if ok else None,
        "best_refined_rms_cents": float(np.min(ok)) if ok else None,
        "refine_time_s": round(dt, 1),
        "model": args.model,
        "results": results,
    }

    baseline = None
    if args.random_baseline:
        rand_idx = rng.choice(args.pool, size=args.top_k, replace=False)
        base = []
        for i in rand_idx:
            r = refine_from(pool, i, targets)
            base.append(r)
        bok = [r for r in base if r is not None]
        baseline = {
            "n_refined": len(bok), "n_zero": int(sum(1 for r in bok if r < 1.0)),
            "mean_refined_rms_cents": float(np.mean(bok)) if bok else None,
            "best_refined_rms_cents": float(np.min(bok)) if bok else None,
        }
        summary["random_baseline"] = baseline
        print(f"\nwarm-start: n_zero={summary['n_zero']}/{len(ok)} "
              f"mean={summary['mean_refined_rms_cents']:.1f}c")
        print(f"random:     n_zero={baseline['n_zero']}/{len(bok)} "
              f"mean={baseline['mean_refined_rms_cents']:.1f}c")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()
