"""Metamaterial design-knob optimizer for low clarinets.

Tunes HR parameters (f0, spacing, neck_r, neck_l, start_frac) to
minimize a composite cost that balances:
  - fundamental accuracy (primary)
  - 12th intonation deviation from 3:1 (secondary)
  - stopband coverage (tertiary, wider is better)
  - cavity volume (quaternary, smaller is more printable)

Uses differential evolution for global search, then L-BFGS-B for
local refinement (same two-phase pattern as the existing optimizers).
"""
import time
import math
import numpy as np
from scipy.optimize import differential_evolution, minimize
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..tmm_acoustics import SPEED_OF_SOUND
from ..metamaterial_low_clarinets import (
    LOW_CLARINETS,
    all_closed_fingers,
    make_hr_segment,
    make_low_clarinet,
    fundamental,
    registers,
    stopband_bounds,
    cavity_volume_for_f0,
    DEFAULT_NECK_RADIUS_MM,
    DEFAULT_NECK_LENGTH_MM,
)
from .base import Optimizer, OptimizationResult


@dataclass
class MetamaterialResult:
    key: str
    target_hz: float
    best_f0: float
    best_spacing: float
    best_neck_r: float
    best_neck_l: float
    best_start_frac: float
    achieved_f1: float
    cents_error: float
    twelfth_cents: float
    stopband_lo: Optional[float]
    stopband_hi: Optional[float]
    coverage_hz: float
    cavity_v_mm3: float
    n_resonators: int
    cost: float
    rms_cents: float
    wall_time: float
    n_evaluations: int


def _composite_cost(
    f0: float,
    spacing: float,
    neck_r: float,
    neck_l: float,
    start_frac: float,
    key: str,
    target_hz: float,
    weight_12th: float = 0.5,
    weight_coverage: float = 0.2,
    weight_volume: float = 0.1,
) -> Tuple[float, Dict[str, float]]:
    """Composite cost for a metamaterial design.

    Returns (cost, metrics_dict).
    """
    fingers = all_closed_fingers(key)
    seg, _ = make_hr_segment(key, f0, spacing, start_frac, neck_r, neck_l)
    inst = make_low_clarinet(key, metamaterial_segments=[seg])
    f1 = fundamental(inst, fingers)
    r = registers(inst, fingers, 3)

    cents = 1200.0 * math.log2(f1 / target_hz) if f1 > 0 else 1e6
    twelfth = r[1] / r[0] if r[0] > 0 else 0.0
    twelfth_cents = 1200.0 * math.log2(twelfth / 3.0)

    lo, hi = stopband_bounds(key, f0, spacing, start_frac, neck_r, neck_l)
    coverage = (hi - lo) if (lo is not None and hi is not None and hi > lo) else 0.0

    v = cavity_volume_for_f0(f0, neck_r, neck_l)
    n = max(1, int((inst.length * (1.0 - start_frac)) // spacing))

    cost = abs(cents)
    cost += weight_12th * abs(twelfth_cents)
    cost -= weight_coverage * coverage * 0.01  # reward wider stopband
    cost += weight_volume * v * 1e-6  # penalize large cavities

    metrics = {
        "cents": cents,
        "twelfth_cents": twelfth_cents,
        "coverage_hz": coverage,
        "cavity_v_mm3": v,
        "n_resonators": n,
        "f1": f1,
        "reg2": r[1] if len(r) > 1 else 0.0,
        "reg3": r[2] if len(r) > 2 else 0.0,
    }
    return cost, metrics


class MetamaterialOptimizer(Optimizer):
    """Optimize HR design knobs for a low clarinet metamaterial design.

    Parameters tuned:
      - f0 (Hz): HR resonance frequency
      - spacing (mm): resonator spacing
      - neck_r (mm): neck radius
      - neck_l (mm): neck length
      - start_frac (0-1): fraction of bore from closed end to array start
    """

    def __init__(
        self,
        key: str,
        target_hz: float,
        weight_12th: float = 0.5,
        weight_coverage: float = 0.2,
        weight_volume: float = 0.1,
        max_time_seconds: float = 120.0,
    ):
        self.key = key
        self.target_hz = target_hz
        self.weight_12th = weight_12th
        self.weight_coverage = weight_coverage
        self.weight_volume = weight_volume
        self.max_time = max_time_seconds
        self._n_evaluations = 0
        self._t0 = 0.0

    def evaluate(self, params: Dict[str, float]) -> float:
        self._n_evaluations += 1
        f0 = params["f0"]
        spacing = params["spacing"]
        neck_r = params["neck_r"]
        neck_l = params["neck_l"]
        start_frac = params["start_frac"]
        if spacing <= 0 or neck_r <= 0 or neck_l <= 0:
            return 1e10
        if start_frac <= 0.0 or start_frac >= 0.99:
            return 1e10
        cost, _ = _composite_cost(
            f0, spacing, neck_r, neck_l, start_frac,
            self.key, self.target_hz,
            self.weight_12th, self.weight_coverage, self.weight_volume,
        )
        return cost

    def optimize(self, verbose: bool = False) -> OptimizationResult:
        self._t0 = time.time()
        spec = LOW_CLARINETS[self.key]
        base_f1 = SPEED_OF_SOUND / (4.0 * spec["bore_length_mm"])
        base_f0 = base_f1 * 3.0  # rough HR estimate

        bounds = [
            (base_f0 * 0.3, base_f0 * 6.0),       # f0
            (15.0, 80.0),                            # spacing
            (2.0, 8.0),                              # neck_r
            (3.0, 20.0),                             # neck_l
            (0.7, 0.98),                             # start_frac
        ]

        def de_objective(x):
            return self.evaluate({
                "f0": x[0], "spacing": x[1], "neck_r": x[2],
                "neck_l": x[3], "start_frac": x[4],
            })

        time_budget = self.max_time * 0.7
        de_result = differential_evolution(
            de_objective, bounds, seed=42, maxiter=80, tol=1e-6,
            polish=False,
        )

        best_x = de_result.x
        best_cost = de_result.fun

        lb = [b[0] for b in bounds]
        ub = [b[1] for b in bounds]
        lbfgs_bounds = [(lo * 0.8, hi * 1.2) for lo, hi in zip(lb, ub)]

        def lb_objective(x):
            return self.evaluate({
                "f0": x[0], "spacing": x[1], "neck_r": x[2],
                "neck_l": x[3], "start_frac": x[4],
            })

        result_lb = minimize(
            lb_objective, best_x, method="L-BFGS-B",
            bounds=lbfgs_bounds, options={"maxiter": 200, "ftol": 1e-8},
        )

        best_x = result_lb.x
        best_cost = result_lb.fun

        dt = time.time() - self._t0
        f0, spacing, neck_r, neck_l, start_frac = best_x
        _, metrics = _composite_cost(
            f0, spacing, neck_r, neck_l, start_frac,
            self.key, self.target_hz,
            self.weight_12th, self.weight_coverage, self.weight_volume,
        )

        return OptimizationResult(
            success=best_cost < 50.0,
            parameters={
                "f0": f0, "spacing": spacing, "neck_r": neck_r,
                "neck_l": neck_l, "start_frac": start_frac,
            },
            cost=best_cost,
            rms_cents=abs(metrics["cents"]),
            peak_cents=abs(metrics["twelfth_cents"]),
            n_evaluations=self._n_evaluations,
            wall_time=dt,
            metadata={
                "key": self.key,
                "target_hz": self.target_hz,
                "achieved_f1": metrics["f1"],
                "cents": metrics["cents"],
                "twelfth_cents": metrics["twelfth_cents"],
                "coverage_hz": metrics["coverage_hz"],
                "cavity_v_mm3": metrics["cavity_v_mm3"],
                "n_resonators": metrics["n_resonators"],
                "stopband_lo": stopband_bounds(
                    self.key, f0, spacing, start_frac, neck_r, neck_l)[0],
                "stopband_hi": stopband_bounds(
                    self.key, f0, spacing, start_frac, neck_r, neck_l)[1],
            },
        )


def optimize_family(
    keys: Optional[List[str]] = None,
    weight_12th: float = 0.5,
    weight_coverage: float = 0.2,
    weight_volume: float = 0.1,
    max_time_seconds: float = 120.0,
) -> Dict[str, MetamaterialResult]:
    """Run metamaterial optimization across the low clarinet family."""
    if keys is None:
        keys = list(LOW_CLARINETS.keys())

    results = {}
    for key in keys:
        spec = LOW_CLARINETS[key]
        target = spec["extension_target_hz"]
        opt = MetamaterialOptimizer(
            key=key,
            target_hz=target,
            weight_12th=weight_12th,
            weight_coverage=weight_coverage,
            weight_volume=weight_volume,
            max_time_seconds=max_time_seconds,
        )
        result = opt.optimize(verbose=False)
        params = result.parameters
        meta = result.metadata
        results[key] = MetamaterialResult(
            key=key,
            target_hz=target,
            best_f0=params["f0"],
            best_spacing=params["spacing"],
            best_neck_r=params["neck_r"],
            best_neck_l=params["neck_l"],
            best_start_frac=params["start_frac"],
            achieved_f1=meta["achieved_f1"],
            cents_error=meta["cents"],
            twelfth_cents=meta["twelfth_cents"],
            stopband_lo=meta["stopband_lo"],
            stopband_hi=meta["stopband_hi"],
            coverage_hz=meta["coverage_hz"],
            cavity_v_mm3=meta["cavity_v_mm3"],
            n_resonators=meta["n_resonators"],
            cost=result.cost,
            rms_cents=result.rms_cents,
            wall_time=result.wall_time,
            n_evaluations=result.n_evaluations,
        )
    return results


def print_family_results(results: Dict[str, MetamaterialResult]):
    """Print optimized results for the family."""
    W = 100
    print("=" * W)
    print("METAMATERIAL OPTIMIZATION RESULTS (low clarinet family)")
    print("=" * W)
    print(f"{'key':<16} {'target':>8} {'f1':>8} {'f1 err':>8} "
          f"{'12th(c)':>8} {'cov(Hz)':>8} {'cav(mm3)':>10} {'N':>3} "
          f"{'f0':>7} {'sp':>6} {'r':>5} {'l':>5} {'frac':>6} {'time':>6}")
    print("-" * W)
    for key, r in results.items():
        sb = f"{r.stopband_lo:.0f}-{r.stopband_hi:.0f}" if r.stopband_lo else "none"
        print(f"{key:<16} {r.target_hz:>8.2f} {r.achieved_f1:>8.2f} "
              f"{r.cents_error:>+8.1f} {r.twelfth_cents:>+8.1f} "
              f"{r.coverage_hz:>8.0f} {r.cavity_v_mm3:>10.0f} {r.n_resonators:>3} "
              f"{r.best_f0:>7.1f} {r.best_spacing:>6.1f} {r.best_neck_r:>5.1f} "
              f"{r.best_neck_l:>5.1f} {r.best_start_frac:>6.2f} "
              f"{r.wall_time:>5.1f}s")
    return results
