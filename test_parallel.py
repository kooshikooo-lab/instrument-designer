"""Minimal test: does StarmapParallelization work on Windows?"""
import sys, os, time
sys.path.insert(0, '.')

from multiprocessing import Pool
from pymoo.parallelization import StarmapParallelization
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
import numpy as np


class DummyProblem(ElementwiseProblem):
    def __init__(self, runner=None):
        kwargs = dict(n_var=2, n_obj=1, xl=np.array([0.0, 0.0]), xu=np.array([5.0, 5.0]))
        if runner is not None:
            kwargs["elementwise_runner"] = runner
        super().__init__(**kwargs)

    def _evaluate(self, x, out, *args, **kwargs):
        time.sleep(0.5)
        out["F"] = [np.sum(x**2)]


if __name__ == '__main__':
    # --- Serial ---
    print("=== SERIAL ===")
    t0 = time.time()
    problem_s = DummyProblem()
    res = minimize(problem_s, GA(pop_size=10, sampling=FloatRandomSampling()), ("n_gen", 3), seed=42, verbose=False)
    t_serial = time.time() - t0
    print("Time: {:.1f}s".format(t_serial))
    print("Result: x={}, f={}".format(res.X, res.F))

    # --- Parallel ---
    print("\n=== PARALLEL (4 workers) ===")
    t0 = time.time()
    pool = Pool(4)
    runner = StarmapParallelization(pool.starmap)
    problem_p = DummyProblem(runner=runner)
    res = minimize(problem_p, GA(pop_size=10, sampling=FloatRandomSampling()), ("n_gen", 3), seed=42, verbose=False)
    pool.close()
    pool.join()
    t_parallel = time.time() - t0
    print("Time: {:.1f}s".format(t_parallel))
    print("Result: x={}, f={}".format(res.X, res.F))

    print("\nSpeedup: {:.2f}x".format(t_serial / t_parallel))
