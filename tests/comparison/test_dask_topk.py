"""
Tests for the dask-parallel top-k polish runner.

Covers the two execution modes and their equivalence:

  - serial fallback: ``client=None`` runs entirely in-process and must
    produce the same metric keys as the shared engine
  - dask path: DE population evaluations dispatch to a local Dask cluster;
    scipy's ``differential_evolution`` forces ``updating='deferred'`` under
    ``workers``, which is deterministic given a seed, so a dask run must
    reproduce a serial run with ``updating='deferred'`` exactly
  - availability: ``make_client`` returns ``None`` (never raises) when dask
    or a scheduler is unreachable, so the comparison suite degrades to serial

Marked ``comparison`` / ``slow`` so the default suite stays fast; run with
``pytest tests/comparison/test_dask_topk.py -m comparison``.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import numpy as np
import pytest
from dask_topk import make_client, run_topk_polish_dask
from scipy.optimize import differential_evolution

from backend.optimization.topk_polish import topk_polish

pytestmark = [
    pytest.mark.comparison,
    pytest.mark.slow,
]

BOUNDS = [(-3.0, 3.0)] * 4


def _sphere(x):
    return float(np.sum(np.asarray(x, float) ** 2))


@pytest.fixture(scope="module")
def dask_client():
    """A local Dask cluster for the parallel-mode tests."""
    client = make_client(n_workers=2)
    if client is None:
        pytest.skip("no local Dask cluster available")
    yield client
    client.close()


def test_serial_fallback_matches_engine():
    """client=None must behave exactly like calling the engine with workers=1."""
    res = run_topk_polish_dask(
        _sphere, BOUNDS, client=None, popsize=6, maxiter=5, n_polish=3, seed=42,
    )
    ref = topk_polish(
        _sphere, BOUNDS, popsize=6, maxiter=5, n_polish=3, seed=42, workers=1,
    )
    assert res["rms_cents"] == pytest.approx(ref["rms_cents"], abs=1e-12)
    assert res["objective_evals"] == ref["objective_evals"]
    assert res["radii"] == ref["radii"]


def test_dask_parallel_matches_serial_deferred(dask_client):
    """Dask DE uses updating='deferred'; a serial deferred run must match it."""
    res_dask = run_topk_polish_dask(
        _sphere, BOUNDS, client=dask_client, popsize=6, maxiter=5, n_polish=3, seed=7,
    )
    # Serial workers=1 defaults to updating='immediate', so re-run the DE the
    # way scipy runs it under a workers callable to get an exact comparison.
    rng_ref = differential_evolution(
        _sphere, BOUNDS, maxiter=5, popsize=6, seed=7,
        polish=False, tol=1e-6, mutation=(0.5, 1.0), recombination=0.7,
        updating="deferred",
    )
    # de_best is rounded to 4 dp by the engine, so compare at that precision.
    assert res_dask["de_best"] == pytest.approx(float(rng_ref.fun), abs=5e-5)
    assert res_dask["rms_cents"] <= res_dask["de_best"] + 1e-9
    assert res_dask["objective_evals"] > 0


def test_dask_parallel_deterministic(dask_client):
    """Same seed through the dask path must reproduce the same result."""
    r1 = run_topk_polish_dask(
        _sphere, BOUNDS, client=dask_client, popsize=6, maxiter=5, n_polish=3, seed=42,
    )
    r2 = run_topk_polish_dask(
        _sphere, BOUNDS, client=dask_client, popsize=6, maxiter=5, n_polish=3, seed=42,
    )
    assert r1["rms_cents"] == pytest.approx(r2["rms_cents"], abs=1e-12)
    assert r1["radii"] == r2["radii"]


def test_make_client_returns_none_without_dask(monkeypatch):
    """make_client must degrade to None (serial) when dask is unavailable."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "distributed" or name.startswith("distributed."):
            raise ImportError("dask unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert make_client() is None
    assert make_client("tcp://127.0.0.1:8786") is None


def test_make_client_returns_none_on_unreachable_scheduler():
    """An unreachable scheduler address must not raise -- falls back to None."""
    assert make_client("tcp://127.0.0.1:1") is None
