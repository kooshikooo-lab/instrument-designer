"""Dask-parallel runner for the top-k polish optimization family.

Wraps ``backend/optimization/topk_polish.py`` so the embarrassingly-parallel
DE population evaluations dispatch to Dask workers while the L-BFGS-B polish
step stays serial (it is inherently sequential). Falls back to plain serial
execution when no scheduler or local cluster is reachable, so the comparison
suite stays runnable everywhere:

    python tests/comparison/dask_topk.py                 # prints a small demo
    pytest tests/comparison/test_dask_topk.py -m comparison

Companion to the desktop's ``ai_methods_dask.py`` (PR #62, deep-budget dask
variants of the four surrogate families); this module is the self-contained
dask path for the 5th family (top-k polish) on the laptop branch.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from backend.optimization.topk_polish import topk_polish


def make_client(scheduler=None, n_workers=None):
    """Create a Dask client or return ``None`` for serial fallback.

    Preference order (mirrors the desktop's ``ai_methods_dask.py``):
      1. an explicit ``scheduler`` address (e.g. a worker over the LAN)
      2. a local Dask cluster on this machine
      3. ``None`` -> serial execution (objectives evaluated in-process)
    """
    try:
        from distributed import Client
    except ImportError:  # pragma: no cover - dask absent
        return None

    if scheduler:
        try:
            client = Client(scheduler, timeout=8, set_as_default=False)
            client.scheduler_info()
            return client
        except Exception as exc:  # noqa: BLE001 - fallback to serial is the point
            print(f"[dask] could not reach scheduler {scheduler}: {exc}")
            return None

    try:
        import logging

        from distributed.deploy import LocalCluster
        n_workers = n_workers or min(4, os.cpu_count() or 1)
        cluster = LocalCluster(
            n_workers=n_workers,
            threads_per_worker=1,
            processes=True,
            dashboard_address=None,
            silence_logs=logging.ERROR,
        )
        return Client(cluster, set_as_default=False)
    except Exception as exc:  # noqa: BLE001 - fallback to serial is the point
        print(f"[dask] could not start local cluster: {exc}")
        return None


def dask_map(client):
    """Return a map-like callable that scipy ``differential_evolution`` accepts.

    Signature matches ``map(func, iterable)``; Dask futures are gathered so
    the caller sees plain results in the same order as the input batch.
    """
    def _map(func, iterable):
        futures = client.map(func, list(iterable))
        return client.gather(futures)
    return _map


def run_topk_polish_dask(objective, bounds, client=None, **kwargs):
    """Run top-k polish with Dask-parallel DE; serial fallback via client=None.

    ``client`` is a Dask client from :func:`make_client` (or ``None`` for
    in-process execution). Returns the same metric-keyed dict as the shared
    engine (``rms_cents``, ``objective_evals``, ``wall_time``, ...).
    """
    workers = dask_map(client) if client is not None else 1
    return topk_polish(objective, bounds, workers=workers, **kwargs)


if __name__ == "__main__":
    def _sphere(x):
        return float(np.sum(np.asarray(x, float) ** 2))

    _client = make_client(n_workers=2)
    _res = run_topk_polish_dask(
        _sphere, [(-3.0, 3.0)] * 4, client=_client,
        popsize=6, maxiter=5, n_polish=3, seed=42,
    )
    print(
        f"rms={_res['rms_cents']:.6f} evals={_res['objective_evals']} "
        f"client={'dask' if _client is not None else 'serial'}"
    )
    if _client is not None:
        _client.close()
