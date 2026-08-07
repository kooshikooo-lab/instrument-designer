"""
Seed-robustness study for the top-k L-BFGS-B polish family.

Reproduces the robustness headline (min / mean / max across seeds) for the
top-k polish family (shared engine backend/optimization/topk_polish.py)
versus the plain gradient-free family, on the shared Bb-clarinet tuning task.
Run with::

    python tests/comparison/tune_topk_polish.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import ai_methods_benchmark as bench  # noqa: E402

SEEDS = range(5)


def study():
    plain = []
    topk = []
    for seed in SEEDS:
        plain_res = bench.run_gradient_free(seed=seed)
        topk_res = bench.run_topk_polish(seed=seed)
        plain.append(plain_res['rms_cents'])
        topk.append(topk_res['rms_cents'])
        print(
            f"seed {seed}: plain {plain_res['rms_cents']:7.3f}c "
            f"({plain_res['objective_evals']:>6} evals) | "
            f"topk {topk_res['rms_cents']:7.3f}c "
            f"({topk_res['objective_evals']:>6} evals) | "
            f"de {topk_res['de_best']:7.3f}c -> polish "
            f"{min(topk_res['polished'].values()):7.3f}c"
        )
    plain = np.array(plain)
    topk = np.array(topk)
    print()
    print(f"{'method':<14}{'min':>9}{'mean':>9}{'max':>9}")
    print(f"{'plain':<14}{plain.min():>9.3f}{plain.mean():>9.3f}{plain.max():>9.3f}")
    print(f"{'topk':<14}{topk.min():>9.3f}{topk.mean():>9.3f}{topk.max():>9.3f}")


if __name__ == '__main__':
    study()
