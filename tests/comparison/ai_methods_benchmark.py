"""
Shared benchmark and runners that compare five AI/ML optimization families
head-to-head on a Bb-clarinet-family tuning task.

Families (from the AI-methods plan):

  1. Bayesian Optimization    - Gaussian-Process surrogate, sample-efficient
                                (botorch SingleTaskGP + qLogExpectedImprovement)
  2. Neural Surrogate Models  - MLP trained on TMM samples, then optimized offline
                                (PyTorch) and re-evaluated on the real objective
  3. Reinforcement Learning   - REINFORCE policy-gradient over sequential
                                 per-section bore-radius decisions
  4. Gradient-free methods    - CMA-ES, PSO, DE (global, no gradients)
  5. Top-k polish             - DE global search, then L-BFGS-B refinement of
                                 the top-k DE elites (robust local polish)

Common problem: a closed-top (clarinet-family) TMM instrument. The bore/hole
skeleton is fixed to the canonical chalumeau_C benchmark layout
(backend/benchmark_all.py) with the sequential hole placement used by
backend/jax_optimizer.py. The 6 bore radii are the decision variables; the
objective is the absolute RMS cents error over the six fingered chalumeau
notes (the canonical accuracy metric, SPEED_OF_SOUND = 346100 mm/s).

Every runner returns an AlgorithmResult (tests/comparison/comparison_framework.py)
with metrics ``rms_cents``, ``objective_evals`` and ``wall_time`` so the five
families can be compared on the same problem.

Run standalone to print the comparison table::

    python tests/comparison/ai_methods_benchmark.py
"""
import sys
import os
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from backend.jax_optimizer import eval_all  # noqa: E402
from comparison_framework import AlgorithmResult  # noqa: E402

# ---------------------------------------------------------------------------
# Shared benchmark: Bb-clarinet-family (closed-top) tuning problem
# ---------------------------------------------------------------------------
# Canonical chalumeau_C targets (backend/benchmark_all.py) on a closed-top
# instrument. Bore length + hole skeleton from sequential placement on that
# config (fixed here so the four families optimize the identical problem).
TARGETS = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
BORE_LENGTH = 330.8
HOLE_POSITIONS = [62.1, 92.3, 107.3, 131.4, 154.2]
HOLE_DIAMETERS = [7.0, 7.0, 7.0, 7.0, 7.0]
HOLE_LENGTHS = [3.75, 3.75, 3.75, 3.75, 3.75]
CLOSED_TOP = True
N_REGISTER = 1

RADIUS_MIN, RADIUS_MAX = 5.0, 15.0
N_BORE_CTRL = 6


def benchmark_objective(radii):
    """Absolute RMS cents error of a bore given the fixed Bb-clarinet skeleton.

    Decision variables are the 6 bore radii (mm). Lower is better; a
    well-tuned clarinet is below ~10 cents.
    """
    return eval_all(
        np.asarray(radii, dtype=float),
        BORE_LENGTH,
        HOLE_POSITIONS,
        HOLE_DIAMETERS,
        HOLE_LENGTHS,
        CLOSED_TOP,
        TARGETS,
        n_reg=N_REGISTER,
    )


def random_initial_design(rng):
    """Random Latin-hypercube-like initial design in [RADIUS_MIN, RADIUS_MAX]."""
    return rng.uniform(RADIUS_MIN, RADIUS_MAX, N_BORE_CTRL)


def _wrap(fn):
    """Run ``fn`` and normalize any exception into an AlgorithmResult."""
    name = fn.__name__.replace('run_', '').replace('_', ' ').title()
    t0 = time.time()
    try:
        metrics = fn()
        return AlgorithmResult(
            name=name,
            success=True,
            runtime_seconds=metrics['wall_time'],
            metrics=metrics,
            metadata={'method': fn.__name__},
        )
    except Exception as exc:  # pragma: no cover - defensive
        return AlgorithmResult(
            name=name,
            success=False,
            runtime_seconds=time.time() - t0,
            error=str(exc),
            metadata={'method': fn.__name__},
        )


# ---------------------------------------------------------------------------
# 1. Bayesian Optimization (Gaussian-Process surrogate)
# ---------------------------------------------------------------------------

def run_bayesian_optimization(n_init=8, n_iter=30, seed=42):
    """botorch SingleTaskGP + qLogExpectedImprovement on the TMM objective."""
    from botorch.models import SingleTaskGP
    from botorch.fit import fit_gpytorch_mll
    from botorch.acquisition import qLogExpectedImprovement
    from botorch.optim import optimize_acqf
    from gpytorch.mlls import ExactMarginalLogLikelihood
    import torch

    rng = np.random.default_rng(seed)
    t0 = time.time()

    X = rng.uniform(RADIUS_MIN, RADIUS_MAX, (n_init, N_BORE_CTRL))
    Y = np.array([benchmark_objective(x) for x in X])

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
        fit_gpytorch_mll(mll, options={'maxiter': 30, 'disp': False})
        acq = qLogExpectedImprovement(model, best_f=Yt.min().item())
        cand, _ = optimize_acqf(
            acq, bounds=bounds_t, q=1, num_restarts=2, raw_samples=32,
        )
        x_new = denorm(cand.detach().numpy()[0])
        y_new = benchmark_objective(x_new)
        Xn = torch.cat([Xn, torch.tensor(norm([x_new]), dtype=torch.float64)])
        Yt = torch.cat([Yt, torch.tensor([[y_new]], dtype=torch.float64)])

    return {
        'rms_cents': float(Yt.min().item()),
        'objective_evals': int(len(Xn)),
        'wall_time': time.time() - t0,
    }


# ---------------------------------------------------------------------------
# 2. Neural Surrogate Models
# ---------------------------------------------------------------------------

def run_neural_surrogate(n_samples=180, n_de_iter=25, seed=42):
    """Train an MLP on TMM samples, optimize the surrogate, re-evaluate."""
    import torch
    import torch.nn as nn
    from scipy.optimize import differential_evolution
    from scipy.stats import qmc

    t0 = time.time()

    sampler = qmc.LatinHypercube(d=N_BORE_CTRL, seed=seed)
    Xs = sampler.random(n_samples) * (RADIUS_MAX - RADIUS_MIN) + RADIUS_MIN
    Ys = np.array([benchmark_objective(x) for x in Xs])

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
    for _ in range(600):
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
    best_rms = benchmark_objective(res.x)

    return {
        'rms_cents': float(best_rms),
        'objective_evals': n_samples + 1,
        'wall_time': time.time() - t0,
        'surrogate_train_samples': n_samples,
    }


# ---------------------------------------------------------------------------
# 3. Reinforcement Learning (REINFORCE over sequential decisions)
# ---------------------------------------------------------------------------

def run_reinforcement_learning(n_episodes=150, n_bins=8, seed=0):
    """REINFORCE policy-gradient: build the bore section by section.

    Each episode constructs a full 6-radius bore via 6 sequential discrete
    decisions (one per bore section), then receives reward ``-rms_cents``.
    A small per-step softmax policy is trained with the vanilla REINFORCE
    update. Reported RMS is the best bore discovered over all episodes.
    """
    rng = np.random.default_rng(seed)
    bins = np.linspace(RADIUS_MIN, RADIUS_MAX, n_bins)
    logits = np.zeros((N_BORE_CTRL, n_bins))  # softmax policy per step
    lr = 0.3
    t0 = time.time()
    best_rms = float('inf')

    for _ in range(n_episodes):
        config = np.zeros(N_BORE_CTRL)
        for step in range(N_BORE_CTRL):
            p = np.exp(logits[step] - logits[step].max())
            p /= p.sum()
            action = rng.choice(n_bins, p=p)
            config[step] = bins[action]

        rms = benchmark_objective(config)
        best_rms = min(best_rms, rms)
        reward = -rms  # REINFORCE, zero baseline

        for step in range(N_BORE_CTRL):
            p = np.exp(logits[step] - logits[step].max())
            p /= p.sum()
            action = int(np.argmin(np.abs(bins - config[step])))
            onehot = np.zeros(n_bins)
            onehot[action] = 1.0
            logits[step] += lr * reward * (onehot - p)

    return {
        'rms_cents': float(best_rms),
        'objective_evals': n_episodes,
        'wall_time': time.time() - t0,
        'n_episodes': n_episodes,
        'n_bins': n_bins,
    }


# ---------------------------------------------------------------------------
# 4. Gradient-free methods: CMA-ES, PSO, DE
# ---------------------------------------------------------------------------

def _run_cma_es(max_evals=600, seed=42):
    import cma

    es = cma.CMAEvolutionStrategy(
        [10.0] * N_BORE_CTRL, 2.5,
        {'bounds': [RADIUS_MIN, RADIUS_MAX], 'verbose': -9, 'seed': seed, 'popsize': 16},
    )
    while not es.stop() and es.countevals < max_evals:
        X = es.ask()
        es.tell(X, [benchmark_objective(x) for x in X])
    return es.result.fbest, es.countevals


def _run_pso(n_particles=20, n_iter=20, seed=7):
    rng = np.random.default_rng(seed)
    pos = rng.uniform(RADIUS_MIN, RADIUS_MAX, (n_particles, N_BORE_CTRL))
    vel = np.zeros_like(pos)
    pbest = pos.copy()
    pbest_val = np.array([benchmark_objective(p) for p in pos])
    gbest_idx = int(pbest_val.argmin())
    gbest = pbest[gbest_idx].copy()
    gbest_val = pbest_val[gbest_idx]
    n_evals = n_particles
    w, c1, c2 = 0.7, 1.5, 1.5

    for _ in range(n_iter):
        r1, r2 = rng.random((2, n_particles, N_BORE_CTRL))
        vel = w * vel + c1 * r1 * (pbest - pos) + c2 * r2 * (gbest[None, :] - pos)
        pos = np.clip(pos + vel, RADIUS_MIN, RADIUS_MAX)
        vals = np.array([benchmark_objective(p) for p in pos])
        n_evals += n_particles
        better = vals < pbest_val
        pbest[better] = pos[better]
        pbest_val[better] = vals[better]
        if pbest_val.min() < gbest_val:
            gbest_idx = int(pbest_val.argmin())
            gbest = pbest[gbest_idx].copy()
            gbest_val = pbest_val[gbest_idx]

    return float(gbest_val), n_evals


def _run_de(maxiter=15, popsize=8, seed=42):
    from scipy.optimize import differential_evolution

    res = differential_evolution(
        benchmark_objective, [(RADIUS_MIN, RADIUS_MAX)] * N_BORE_CTRL,
        maxiter=maxiter, popsize=popsize, seed=seed, polish=True, tol=1e-6,
    )
    return float(res.fun), int(res.nfev)


def run_gradient_free(seed=42, max_evals=600):
    """Run CMA-ES, PSO and DE; report the family best with per-method detail.

    ``max_evals`` scales the CMA-ES budget (the family-best driver) so the
    acceptance retry policy can run this family longer on a failed screen.
    """
    t0 = time.time()
    cma_rms, cma_evals = _run_cma_es(max_evals=max_evals, seed=seed)
    pso_rms, pso_evals = _run_pso(seed=seed)
    de_rms, de_evals = _run_de(seed=seed)
    best = min(cma_rms, pso_rms, de_rms)
    return {
        'rms_cents': float(best),
        'objective_evals': cma_evals + pso_evals + de_evals,
        'wall_time': time.time() - t0,
        'cma_es_rms': cma_rms, 'cma_es_evals': cma_evals,
        'pso_rms': pso_rms, 'pso_evals': pso_evals,
        'de_rms': de_rms, 'de_evals': de_evals,
    }


# ---------------------------------------------------------------------------
# 5. Top-k polish: DE global search + L-BFGS-B refinement of top-k elites
# ---------------------------------------------------------------------------

def run_topk_polish(seed=42, popsize=15, maxiter=60, n_polish=5):
    """DE global + L-BFGS-B polish of the n_polish best elite candidates.

    Thin runner over the shared generic engine (backend/optimization/
    topk_polish.py), which matches the comparison framework's metric keys.
    Tuning evidence on this contract: top-k polish scored 5.9-7.7c RMS vs a
    9.6c single-restart gradient-free baseline. ``maxiter`` is the dominant
    budget knob the acceptance retry policy scales on a failed screen.
    """
    from backend.optimization.topk_polish import topk_polish

    return topk_polish(
        benchmark_objective,
        [(RADIUS_MIN, RADIUS_MAX)] * N_BORE_CTRL,
        popsize=popsize, maxiter=maxiter, n_polish=n_polish, seed=seed,
    )


# ---------------------------------------------------------------------------
# Orchestration + report
# ---------------------------------------------------------------------------

FAMILIES = {
    'bayesian_optimization': run_bayesian_optimization,
    'neural_surrogate': run_neural_surrogate,
    'reinforcement_learning': run_reinforcement_learning,
    'gradient_free': run_gradient_free,
    'topk_polish': run_topk_polish,
}


def run_all_families():
    """Run all five families and return a list of AlgorithmResult."""
    return [(name, _wrap(fn)) for name, fn in FAMILIES.items()]


def build_report(results):
    """Format a plain-text comparison table from (name, AlgorithmResult) pairs."""
    lines = [
        'AI/ML optimization family comparison - Bb clarinet tuning',
        '=' * 78,
        f"{'Family':<26}{'RMS (cents)':>13}{'Objective evals':>16}{'Wall time (s)':>14}",
        '-' * 78,
    ]
    for _, res in results:
        if not res.success:
            lines.append(f"{res.name:<26}{'FAILED':>13}{'':>16}{res.runtime_seconds:>14.1f}")
            continue
        lines.append(
            f"{res.name:<26}{res.metrics['rms_cents']:>13.2f}"
            f"{res.metrics['objective_evals']:>16d}{res.metrics['wall_time']:>14.1f}"
        )
    lines += [
        '-' * 78,
        'Lower RMS is better. Families are not required to reach the same RMS;',
        'the table shows the sample-efficiency / depth tradeoff of each family.',
        '',
    ]
    return '\n'.join(lines)


def main():
    results = run_all_families()
    print(build_report(results))
    for name, res in results:
        if not res.success:
            print(f"  [{name}] FAILED: {res.error}")


if __name__ == '__main__':
    main()
