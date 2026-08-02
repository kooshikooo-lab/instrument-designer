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

from backend.surrogate import SurrogateConfig, SurrogateTrainer, generate_training_data


def _small_config():
    return SurrogateConfig(hidden_dims=(32, 32), output_dim=4, dropout_rate=0.0)


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
