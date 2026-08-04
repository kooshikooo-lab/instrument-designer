"""
Dask-parallel, deep-budget variants of the four AI/ML optimization families.

Companion to ``ai_methods_benchmark.py`` (the fast, serial, always-runnable
pytest suite). This module runs the same Bb-clarinet tuning problem with
larger budgets so the surrogate families get enough samples to converge, and
dispatches the embarrassingly-parallel objective evaluations to Dask workers.

Dask availability is optional: every runner accepts a batch evaluator, and if
no client is available a serial batch evaluator is used. This means the deep
run works with a remote scheduler (the laptop worker), a local cluster, or
with Dask entirely absent::

    python tests/comparison/run_ai_compare_dask.py --scheduler tcp://host:8786
    python tests/comparison/run_ai_compare_dask.py --local-workers 8
    python tests/comparison/run_ai_compare_dask.py --no-dask
"""
import os
import sys
import time
import math

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from ai_methods_benchmark import (  # noqa: E402
    TARGETS, BORE_LENGTH, HOLE_POSITIONS, HOLE_DIAMETERS, HOLE_LENGTHS,
    CLOSED_TOP, N_REGISTER, RADIUS_MIN, RADIUS_MAX, N_BORE_CTRL,
    benchmark_objective, build_report, AlgorithmResult,
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# Self-contained task spec sent to Dask workers (plain picklable values only,
# so workers do not need this module or ai_methods_benchmark importable).
_WORKER_SPEC = {
    'repo_root': REPO_ROOT,
    'bore_length': BORE_LENGTH,
    'hole_positions': HOLE_POSITIONS,
    'hole_diameters': HOLE_DIAMETERS,
    'hole_lengths': HOLE_LENGTHS,
    'closed_top': CLOSED_TOP,
    'targets': TARGETS,
    'n_register': N_REGISTER,
}


def _worker_objective(radii, spec):
    """Evaluate RMS cents on a Dask worker (fully self-contained)."""
    import sys
    if spec['repo_root'] not in sys.path:
        sys.path.insert(0, spec['repo_root'])
    import numpy as np
    from backend.jax_optimizer import eval_all
    return eval_all(
        np.asarray(radii, dtype=float),
        spec['bore_length'], spec['hole_positions'], spec['hole_diameters'],
        spec['hole_lengths'], spec['closed_top'], spec['targets'],
        n_reg=spec['n_register'],
    )


def make_client(scheduler=None, n_workers=None):
    """Create a Dask client or return None (serial fallback).

    Preference order:
      1. ``scheduler`` address (e.g. the laptop worker over the LAN)
      2. a local Dask cluster on this machine
      3. ``None`` -> serial execution
    """
    try:
        from distributed import Client
    except ImportError:
        return None

    if scheduler:
        try:
            client = Client(scheduler, timeout=8, set_as_default=False)
            client.scheduler_info()
            return client
        except Exception as exc:  # pragma: no cover - depends on environment
            print(f"[dask] could not reach scheduler {scheduler}: {exc}")
            return None

    try:
        import logging
        from distributed.deploy import LocalCluster
        n_workers = n_workers or min(8, os.cpu_count() or 1)
        cluster = LocalCluster(
            n_workers=n_workers,
            threads_per_worker=1,
            processes=True,
            dashboard_address=None,
            silence_logs=logging.ERROR,
        )
        return Client(cluster, set_as_default=False)
    except Exception as exc:  # pragma: no cover - depends on environment
        print(f"[dask] could not start local cluster: {exc}")
        return None


class _BatchEvaluator:
    """Evaluate a list of radius vectors in parallel (or serially)."""

    def __init__(self, client):
        self.client = client

    def __call__(self, batch):
        batch = [list(np.asarray(x, dtype=float)) for x in batch]
        if self.client is None:
            return [benchmark_objective(x) for x in batch]
        futures = self.client.map(_worker_objective, batch, [_WORKER_SPEC] * len(batch))
        return list(self.client.gather(futures))


def _wrap(fn, name):
    t0 = time.time()
    try:
        metrics = fn()
        return AlgorithmResult(
            name=name, success=True, runtime_seconds=metrics['wall_time'],
            metrics=metrics,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return AlgorithmResult(
            name=name, success=False, runtime_seconds=time.time() - t0,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# 1. Bayesian Optimization (GP surrogate), q-batch + parallel evals
# ---------------------------------------------------------------------------

def run_bayesian_optimization(batch_eval, n_init=16, n_iter=100, q=4, seed=42):
    from botorch.models import SingleTaskGP
    from botorch.fit import fit_gpytorch_mll
    from botorch.acquisition import qLogExpectedImprovement
    from botorch.optim import optimize_acqf
    from gpytorch.mlls import ExactMarginalLogLikelihood
    import torch

    torch.set_num_threads(max(2, (os.cpu_count() or 4) // 2))
    rng = np.random.default_rng(seed)
    t0 = time.time()

    X = rng.uniform(RADIUS_MIN, RADIUS_MAX, (n_init, N_BORE_CTRL))
    Y = np.array(batch_eval(X))

    def norm(x):
        return (np.asarray(x, float) - RADIUS_MIN) / (RADIUS_MAX - RADIUS_MIN)

    def denorm(x):
        return np.asarray(x, float) * (RADIUS_MAX - RADIUS_MIN) + RADIUS_MIN

    Xn = torch.tensor(norm(X), dtype=torch.float64)
    Yt = torch.tensor(Y[:, None], dtype=torch.float64)
    bounds_t = torch.tensor([[0.0] * N_BORE_CTRL, [1.0] * N_BORE_CTRL], dtype=torch.float64)

    for _ in range(n_iter):
        model = SingleTaskGP(Xn, Yt)
        mll = ExactMarginalLogLikelihood(model.likelihood, model)
        fit_gpytorch_mll(mll, options={'maxiter': 20, 'disp': False})
        acq = qLogExpectedImprovement(model, best_f=Yt.min().item())
        cand, _ = optimize_acqf(acq, bounds=bounds_t, q=q, num_restarts=2, raw_samples=32)
        x_new = denorm(cand.detach().numpy())
        y_new = np.array(batch_eval(x_new))
        Xn = torch.cat([Xn, torch.tensor(norm(x_new), dtype=torch.float64)])
        Yt = torch.cat([Yt, torch.tensor(y_new[:, None], dtype=torch.float64)])

    return {
        'rms_cents': float(Yt.min().item()),
        'objective_evals': int(len(Xn)),
        'wall_time': time.time() - t0,
    }


# ---------------------------------------------------------------------------
# 2. Neural Surrogate Models (MLP trained on parallel-sampled data)
# ---------------------------------------------------------------------------

def run_neural_surrogate(batch_eval, n_samples=700, n_de_iter=40, seed=42):
    import torch
    import torch.nn as nn
    from scipy.optimize import differential_evolution
    from scipy.stats import qmc

    t0 = time.time()

    sampler = qmc.LatinHypercube(d=N_BORE_CTRL, seed=seed)
    Xs = sampler.random(n_samples) * (RADIUS_MAX - RADIUS_MIN) + RADIUS_MIN
    Ys = np.array(batch_eval(Xs))

    X_mean, X_std = Xs.mean(0), Xs.std(0) + 1e-8
    Y_mean, Y_std = Ys.mean(), Ys.std() + 1e-8
    Xn = torch.tensor((Xs - X_mean) / X_std, dtype=torch.float32)
    Yn = torch.tensor(((Ys - Y_mean) / Y_std)[:, None], dtype=torch.float32)

    class MLP(nn.Module):
        def __init__(self, d, hidden=128):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(d, hidden), nn.ReLU(),
                nn.Linear(hidden, hidden), nn.ReLU(),
                nn.Linear(hidden, 1),
            )

        def forward(self, x):
            return self.net(x)

    torch.manual_seed(seed)
    model = MLP(N_BORE_CTRL)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = nn.MSELoss()
    model.train()
    for _ in range(800):
        opt.zero_grad()
        loss = loss_fn(model(Xn), Yn)
        loss.backward()
        opt.step()
    model.eval()

    def surrogate(x):
        xt = torch.tensor((np.asarray(x, float) - X_mean) / X_std, dtype=torch.float32)
        with torch.no_grad():
            return float(model(xt).item() * Y_std + Y_mean)

    res = differential_evolution(
        surrogate, [(RADIUS_MIN, RADIUS_MAX)] * N_BORE_CTRL,
        maxiter=n_de_iter, popsize=10, seed=seed, polish=True,
    )
    best_rms = float(batch_eval([res.x])[0])

    return {
        'rms_cents': best_rms,
        'objective_evals': n_samples + 1,
        'wall_time': time.time() - t0,
        'surrogate_train_samples': n_samples,
    }


# ---------------------------------------------------------------------------
# 3. Reinforcement Learning (batched REINFORCE over sequential decisions)
# ---------------------------------------------------------------------------

def run_reinforcement_learning(batch_eval, n_episodes=800, batch_size=64,
                               n_bins=8, seed=0):
    rng = np.random.default_rng(seed)
    bins = np.linspace(RADIUS_MIN, RADIUS_MAX, n_bins)
    logits = np.zeros((N_BORE_CTRL, n_bins))
    lr = 0.2
    t0 = time.time()
    best_rms = float('inf')
    n_evals = 0

    while n_evals < n_episodes:
        count = min(batch_size, n_episodes - n_evals)
        episodes = []
        for _ in range(count):
            config = np.zeros(N_BORE_CTRL)
            actions = []
            for step in range(N_BORE_CTRL):
                p = np.exp(logits[step] - logits[step].max())
                p /= p.sum()
                action = int(rng.choice(n_bins, p=p))
                actions.append(action)
                config[step] = bins[action]
            episodes.append((config, actions))

        rmses = batch_eval([ep[0] for ep in episodes])
        n_evals += count
        rewards = -np.asarray(rmses)
        baseline = rewards.mean()  # batch baseline reduces REINFORCE variance

        for (config, actions), r in zip(episodes, rewards):
            best_rms = min(best_rms, -r)
            for step in range(N_BORE_CTRL):
                p = np.exp(logits[step] - logits[step].max())
                p /= p.sum()
                onehot = np.zeros(n_bins)
                onehot[actions[step]] = 1.0
                logits[step] += lr * (r - baseline) * (onehot - p)

    return {
        'rms_cents': float(best_rms),
        'objective_evals': n_evals,
        'wall_time': time.time() - t0,
        'n_episodes': n_episodes,
        'n_bins': n_bins,
    }


# ---------------------------------------------------------------------------
# 4. Gradient-free methods (CMA-ES, PSO, DE) with batch evaluation
# ---------------------------------------------------------------------------

def _run_cma_es(batch_eval, max_evals=2000, seed=42):
    import cma

    es = cma.CMAEvolutionStrategy(
        [10.0] * N_BORE_CTRL, 2.5,
        {'bounds': [RADIUS_MIN, RADIUS_MAX], 'verbose': -9, 'seed': seed, 'popsize': 16},
    )
    while not es.stop() and es.countevals < max_evals:
        X = es.ask()
        es.tell(X, batch_eval(X))
    return es.result.fbest, es.countevals


def _run_pso(batch_eval, n_particles=30, n_iter=40, seed=7):
    rng = np.random.default_rng(seed)
    pos = rng.uniform(RADIUS_MIN, RADIUS_MAX, (n_particles, N_BORE_CTRL))
    vel = np.zeros_like(pos)
    pbest = pos.copy()
    pbest_val = np.array(batch_eval(pos))
    gbest_idx = int(pbest_val.argmin())
    gbest = pbest[gbest_idx].copy()
    gbest_val = pbest_val[gbest_idx]
    n_evals = n_particles
    w, c1, c2 = 0.7, 1.5, 1.5

    for _ in range(n_iter):
        r1, r2 = rng.random((2, n_particles, N_BORE_CTRL))
        vel = w * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest[None, :] - pos)
        pos = np.clip(pos + vel, RADIUS_MIN, RADIUS_MAX)
        vals = np.array(batch_eval(pos))
        n_evals += n_particles
        better = vals < pbest_val
        pbest[better] = pos[better]
        pbest_val[better] = vals[better]
        if pbest_val.min() < gbest_val:
            gbest_idx = int(pbest_val.argmin())
            gbest = pbest[gbest_idx].copy()
            gbest_val = pbest_val[gbest_idx]

    return float(gbest_val), n_evals


def _run_de(batch_eval, maxiter=40, popsize=15, seed=42):
    """Classic rand/1/bin differential evolution with batch evaluation.

    Implemented here (instead of scipy's ``workers=``) so populations are
    evaluated through the Dask batch evaluator from the client process.
    """
    rng = np.random.default_rng(seed)
    bounds = [(RADIUS_MIN, RADIUS_MAX)] * N_BORE_CTRL
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    F, CR = 0.7, 0.9

    pop = rng.uniform(lo, hi, (popsize, N_BORE_CTRL))
    fit = np.array(batch_eval(pop))
    n_evals = popsize

    for _ in range(maxiter):
        trials = np.empty_like(pop)
        for i in range(popsize):
            idxs = [j for j in range(popsize) if j != i]
            a, b, c = pop[rng.choice(idxs, 3, replace=False)]
            mutant = np.clip(a + F * (b - c), lo, hi)
            cross = rng.random(N_BORE_CTRL) < CR
            trials[i] = np.where(cross, mutant, pop[i])
        trial_fits = np.array(batch_eval(trials))
        n_evals += popsize
        better = trial_fits < fit
        pop[better] = trials[better]
        fit[better] = trial_fits[better]

    best_idx = int(fit.argmin())
    return float(fit[best_idx]), n_evals


def run_gradient_free(batch_eval, seed=42):
    t0 = time.time()
    cma_rms, cma_evals = _run_cma_es(batch_eval, seed=seed)
    pso_rms, pso_evals = _run_pso(batch_eval, seed=seed)
    de_rms, de_evals = _run_de(batch_eval, seed=seed)
    return {
        'rms_cents': float(min(cma_rms, pso_rms, de_rms)),
        'objective_evals': cma_evals + pso_evals + de_evals,
        'wall_time': time.time() - t0,
        'cma_es_rms': cma_rms, 'cma_es_evals': cma_evals,
        'pso_rms': pso_rms, 'pso_evals': pso_evals,
        'de_rms': de_rms, 'de_evals': de_evals,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

FAMILIES = {
    'bayesian_optimization': run_bayesian_optimization,
    'neural_surrogate': run_neural_surrogate,
    'reinforcement_learning': run_reinforcement_learning,
    'gradient_free': run_gradient_free,
}


def make_batch_evaluator(client):
    """Return a batch evaluator for the given (possibly None) client."""
    return _BatchEvaluator(client)


def run_deep_comparison(client, families=FAMILIES):
    """Run all families with deep budgets through the given client.

    ``client`` may be a Dask Client or ``None`` (serial fallback).
    Returns a list of (family_name, AlgorithmResult).
    """
    batch_eval = make_batch_evaluator(client)
    results = []
    for name, runner in families.items():
        results.append((name, _wrap(lambda r=runner, b=batch_eval: r(b), name)))
    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Dask-parallel AI method comparison')
    parser.add_argument('--scheduler', default=None, help='remote scheduler address, e.g. tcp://host:8786')
    parser.add_argument('--local-workers', type=int, default=None, help='local Dask workers (default: min(8, cpus))')
    parser.add_argument('--no-dask', action='store_true', help='force serial execution (no Dask)')
    args = parser.parse_args()

    client = None
    if not args.no_dask:
        client = make_client(scheduler=args.scheduler, n_workers=args.local_workers)
    mode = 'serial (no Dask)' if client is None else 'Dask'
    print(f"[run_ai_compare_dask] execution mode: {mode}")

    results = run_deep_comparison(client)
    print('\n' + build_report(results))
    for name, res in results:
        if not res.success:
            print(f"  [{name}] FAILED: {res.error}")

    if client is not None:
        client.close()
