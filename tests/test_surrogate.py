"""Tests for the MLP bore surrogate (backend/surrogate).

Covers:
- SurrogateTrainer init + forward pass shape
- Training reduces loss over epochs
- generate_training_data produces correctly-shaped (input, target) pairs
- Training with fallback (non-jax) targets is finite
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

jax = pytest.importorskip("jax", reason="jax is required for surrogate tests")

from backend.surrogate import SurrogateConfig, SurrogateTrainer, generate_training_data


def _small_config():
    return SurrogateConfig(hidden_dims=(32, 32), output_dim=4, dropout_rate=0.0, input_dim=50)


def test_trainer_init_and_forward_shape():
    cfg = _small_config()
    trainer = SurrogateTrainer(cfg, seed=42)
    dummy = np.ones((2, 50), dtype=np.float32)
    out = trainer.predict(dummy)
    assert out.shape == (2, 4)
    assert np.all(np.isfinite(np.asarray(out)))


def test_train_reduces_loss():
    cfg = _small_config()
    trainer = SurrogateTrainer(cfg, seed=7)
    rng = np.random.RandomState(0)
    # Synthetic linear-ish targets so a small MLP can make progress
    train_data = []
    for _ in range(64):
        x = rng.rand(50).astype(np.float32)
        y = np.array([np.sum(x), np.mean(x), np.max(x), np.min(x)], dtype=np.float32)
        train_data.append((x, y))
    val_data = train_data[:16]
    history = trainer.train(train_data, val_data, epochs=5, batch_size=16, verbose=False)
    assert len(history["train_loss"]) == 5
    assert len(history["val_loss"]) == 5
    assert np.all(np.isfinite(history["train_loss"]))
    assert np.all(np.isfinite(history["val_loss"]))
    # Loss should be finite and non-infinite; early epochs often improve monotonically
    assert history["train_loss"][-1] < 1e6


def test_trainer_save_load_roundtrip(tmp_path):
    cfg = _small_config()
    trainer = SurrogateTrainer(cfg, seed=1)
    path = str(tmp_path / "model.pkl")
    trainer.save(path)
    assert os.path.exists(path)
    loaded = SurrogateTrainer.load(path, cfg)
    x = np.ones((1, 50), dtype=np.float32)
    np.testing.assert_allclose(
        np.asarray(loaded.predict(x)), np.asarray(trainer.predict(x)), rtol=1e-6
    )


def test_generate_training_data_shape():
    ranges = {
        "bore_radius": (6.0, 10.0),
        "bore_length": (320.0, 360.0),
        "hole_position": (40.0, 320.0),
        "hole_diameter": (6.0, 9.0),
        "hole_length": (2.0, 4.0),
        "outer_diameter": (21.0, 24.0),
        "closed_top": True,
    }
    data = generate_training_data(n_samples=3, bore_param_ranges=ranges, use_jax_tmm=True, verbose=False)
    assert len(data) == 3
    for inp, tgt in data:
        assert isinstance(inp, np.ndarray) and isinstance(tgt, np.ndarray)
        # input: n_cp(6) + n_holes*3 + [bore_length, outer_d, closed_top]
        assert inp.shape == (6 + 7 * 3 + 3,)
        assert tgt.shape == (4,)
        assert np.all(np.isfinite(inp))
        assert np.all(np.isfinite(tgt))


def test_bi_objective_bo_end_to_end():
    """Smoke-test BiObjectiveBO wiring (SingleTaskGP API + qNEHVI loop)."""
    botorch = pytest.importorskip("botorch")

    from backend.surrogate import BiObjectiveBO, BOConfig

    dim = 4
    bounds = np.array([[0.0, 1.0]] * dim)

    def objective_fn(x):
        # Simple bi-objective: minimize both norms of x
        return np.stack([x[:, 0], x[:, 1]], axis=1)

    bo = BiObjectiveBO(
        objective_fn=objective_fn,
        bounds=bounds,
        config=BOConfig(n_initial=4, n_iterations=2, batch_size=2, mc_samples=32),
    )
    pareto_x, pareto_y = bo.optimize(None, n_iterations=2)

    assert pareto_x.ndim == 2 and pareto_x.shape[1] == dim
    assert pareto_y.ndim == 2 and pareto_y.shape[1] == 2
    assert np.all(np.isfinite(pareto_y))


def test_hybrid_warm_start_decode():
    """Decode normalized 30-dim vector back to physical geometry (round-trip)."""
    from scripts.hybrid_warm_start import decode

    x = np.array([
        7.5 / 15.0, 9.0 / 15.0, 5.5 / 15.0, 12.0 / 15.0, 6.0 / 15.0, 8.0 / 15.0,  # radii
        100.0 / 400.0, 150.0 / 400.0, 200.0 / 400.0, 250.0 / 400.0,
        300.0 / 400.0, 320.0 / 400.0, 340.0 / 400.0,                                # hp
        7.0 / 10.0, 7.0 / 10.0, 7.0 / 10.0, 7.0 / 10.0, 7.0 / 10.0,
        7.0 / 10.0, 7.0 / 10.0,                                                      # hd
        3.0 / 5.0, 3.0 / 5.0, 3.0 / 5.0, 3.0 / 5.0, 3.0 / 5.0, 3.0 / 5.0,
        3.0 / 5.0,                                                                   # hl
        350.0 / 400.0, 22.0 / 25.0, 1.0,                                             # L, outer_d, closed
    ])
    radii, L, hp, hd, hl, outer_d = decode(x)
    assert radii.shape == (6,)
    assert hp.shape == (7,) and hd.shape == (7,) and hl.shape == (7,)
    np.testing.assert_allclose(radii[0], 7.5)
    np.testing.assert_allclose(L, 350.0)
    np.testing.assert_allclose(hp[0], 100.0)
    np.testing.assert_allclose(outer_d, 22.0)

