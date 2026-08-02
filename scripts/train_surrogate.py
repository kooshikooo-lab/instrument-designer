"""
Phase 2G surrogate training — runs on laptop OR Kaggle (free T4/P100 GPU).

Loads Phase 2F samples (output/surrogate/phase2f/samples_*.npz or .csv),
splits train/val, trains the JAX/Flax MLP surrogate with target
standardization + early stopping, saves model params + history to disk.

Usage:
    python scripts/train_surrogate.py --data output/surrogate/phase2f/samples_2000_seed42.npz \
        --out output/surrogate/phase2g --epochs 100 --batch 128

On Kaggle: upload the CSV, change --data to the CSV path, and run
(in Kaggle requires: numpy, jax, flax, optax — JAX preinstalled, add
flax/optax via pip if missing).
"""

from __future__ import annotations
import sys, os, time, json, argparse
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.surrogate import SurrogateConfig, SurrogateTrainer

TARGET_NAMES = ["final_rms_cents", "peak_error_cents", "median_offset_cents", "scale_rms_cents"]


def load_data(path: str):
    if path.endswith(".npz"):
        d = np.load(path)
        return d["inputs"], d["targets"]
    table = np.loadtxt(path, delimiter=",", skiprows=1)
    return table[:, :-4].astype(np.float32), table[:, -4:].astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Phase 2G surrogate training")
    parser.add_argument("--data", required=True, help="npz or csv of Phase 2F samples")
    parser.add_argument("--out", default=os.path.join("output", "surrogate", "phase2g"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden", type=str, default="256,256,128")
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--patience", type=int, default=0, help="early-stop epochs (0 = disable)")
    parser.add_argument("--weight-tail", type=float, default=0.0,
                        help="up-weight low-rms tail samples: w = 1 + k*max(0,1-rms/thr)")
    parser.add_argument("--weight-thr", type=float, default=50.0, help="rms cents threshold for tail weights")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    np.random.seed(args.seed)

    X, y = load_data(args.data)
    print(f"Loaded {X.shape[0]} samples (input {X.shape[1]} -> output {y.shape[1]})")

    # Target standardization (fit on train split only)
    rng = np.random.default_rng(args.seed)
    n = len(X)
    idx = rng.permutation(n)
    cut = int(n * (1 - args.val_fraction))
    train_idx, val_idx = idx[:cut], idx[cut:]

    y_mean = y[train_idx].mean(axis=0)
    y_std = y[train_idx].std(axis=0) + 1e-8
    y_tr = (y[train_idx] - y_mean) / y_std
    y_va = (y[val_idx] - y_mean) / y_std

    import jax.numpy as jnp
    train = [(jnp.array(x, dtype=jnp.float32), jnp.array(t, dtype=jnp.float32))
             for x, t in zip(X[train_idx], y_tr)]
    val = [(jnp.array(x, dtype=jnp.float32), jnp.array(t, dtype=jnp.float32))
           for x, t in zip(X[val_idx], y_va)]

    # Optional tail-weighting: up-weight samples with low final_rms (sparse,
    # elite region) using RAW targets, so the MLP spends more capacity there.
    sample_weights = None
    if args.weight_tail > 0:
        rms = y[train_idx, 0]
        thr = args.weight_thr
        sample_weights = 1.0 + args.weight_tail * np.maximum(0.0, 1.0 - rms / thr)
        n_w = int(np.sum(sample_weights > 1.0))
        print(f"tail weighting: {n_w}/{len(rms)} train samples up-weighted (max w={sample_weights.max():.1f})")

    hidden = tuple(int(h) for h in args.hidden.split(","))
    cfg = SurrogateConfig(hidden_dims=hidden, output_dim=4, input_dim=X.shape[1])
    trainer = SurrogateTrainer(cfg, learning_rate=args.lr)

    print(f"Training {hidden} MLP, {args.epochs} epochs, batch {args.batch}...")
    t0 = time.time()
    hist = trainer.train(train, val, epochs=args.epochs, batch_size=args.batch, verbose=False,
                         patience=args.patience or None, sample_weights=sample_weights)
    dt = time.time() - t0

    # Report in original units (cents^2) + standardized
    print(f"Trained in {dt:.1f}s")
    print(f"train loss (std): {hist['train_loss'][-1]:.4f}   first={hist['train_loss'][0]:.4f}")
    print(f"val   loss (std): {hist['val_loss'][-1]:.4f}   first={hist['val_loss'][0]:.4f}")

    # Baseline: predict-mean in standardized space
    base = float(np.mean((y_va) ** 2))
    print(f"baseline (predict-mean, std): {base:.4f}")
    print(f"val beats baseline: {hist['val_loss'][-1] < base}")

    # Save
    model_path = os.path.join(args.out, "surrogate_params.pkl")
    hist_path = os.path.join(args.out, "history.json")
    meta_path = os.path.join(args.out, "meta.json")
    trainer.save(model_path)
    with open(hist_path, "w") as f:
        json.dump({"train_loss": [float(v) for v in hist["train_loss"]],
                   "val_loss": [float(v) for v in hist["val_loss"]]}, f, indent=2)
    with open(meta_path, "w") as f:
        json.dump({
            "data": args.data, "n_samples": int(n), "input_dim": int(X.shape[1]),
            "output_dim": 4, "output_names": TARGET_NAMES, "hidden": list(hidden),
            "epochs": args.epochs, "batch": args.batch, "lr": args.lr,
            "val_final_std_loss": float(hist["val_loss"][-1]),
            "baseline_std_loss": base,
            "weight_tail": args.weight_tail, "weight_thr": args.weight_thr,
            "y_mean": y_mean.tolist(), "y_std": y_std.tolist(),
        }, f, indent=2)

    print(f"Saved model:    {model_path}")
    print(f"Saved history:  {hist_path}")
    print(f"Saved meta:     {meta_path}")


if __name__ == "__main__":
    main()
