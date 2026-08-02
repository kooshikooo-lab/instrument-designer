"""
Pareto-front optimizer: intonation vs timbre for wind instruments.

Implements bi-objective optimization to explore the tradeoff between
intonation accuracy (RMS cents deviation) and timbre quality (bore
smoothness and radiation consistency). Based on:

- Ernoult et al. (2020) JASA: intonation and timbre are inherently at odds.
  Optimizing both requires a Pareto front approach.
- Petiot et al. (2025) JASA: NSGA-II bi-objective optimization for trumpets
  with Random Forest surrogate.
- Noreland et al. (2013): sequential greedy placement + global re-optim.

Timbre metric
-------------
Direct impedance-peak computation is too slow for optimization (pure Python
loops over the action chain).  Instead we use a *bore-geometry proxy* that
correlates with the a2/a1 impedance-peak-height ratio:

    timbre_cost = w_smooth * smoothness + w_consist * consistency

where

    smoothness  = std(dd)          (dd = second differences of bore radii)
    consistency = std(radiation)   (radiation_i = hole_area_i / bore_area_i)

Lower cost = smoother bore + more uniform hole radiation → more consistent
timbre across the playing range.

The intonation objective is the standard RMS-cents deviation computed by
``compute_intonation_objective``.

Two entry points
----------------
``pareto_sweep``   – weighted-sum sweep (fast, simple, 8 weight points).
``run_pareto``     – NSGA-II (thorough, population-based Pareto front).

Usage
-----
    from backend.pareto_optimizer import pareto_sweep, run_pareto
    from backend.benchmark_all import INSTRUMENTS

    cfg = INSTRUMENTS["chalumeau_C"]
    results = pareto_sweep(cfg)
    front, designs, dt = run_pareto(cfg, pop_size=30, n_gen=50)
"""
from __future__ import annotations

import math
import time
from collections.abc import Sequence

import numpy as np
from scipy.optimize import minimize as sp_min

from backend.tmm_acoustics import (
    SPEED_OF_SOUND,
    TMMInstrument,
    tmm_instrument_from_radii,
)

c = SPEED_OF_SOUND


# ============================================================================
# Bore-geometry timbre proxy
# ============================================================================

def _build_fingerings(n_holes: int, closed_top: bool) -> list[list[str]]:
    """Build cumulative fingering sets for a sequential-hole instrument.

    For *n_holes* tone holes, produces *n_holes* fingerings where hole *k*
    (0-indexed) is the (*k*+1)-th highest note: holes 0..k open, rest closed.
    If *closed_top* is True, prepends an "all closed" fingering for the
    fundamental (closed-top instruments have one extra note).

    Parameters
    ----------
    n_holes : int
        Number of tone holes.
    closed_top : bool
        Whether the instrument has a closed top (clarinet family).

    Returns
    -------
    list of list of str
        Each inner list contains "open" / "closed" strings, one per hole.
    """
    fingerings: list[list[str]] = []
    for k in range(n_holes):
        fingerings.append(["open"] * (k + 1) + ["closed"] * (n_holes - k - 1))
    if closed_top:
        fingerings.insert(0, ["closed"] * n_holes)
    return fingerings


# Public alias kept for benchmark_all.resolve_fingerings compatibility.
# Canonical implementation lives in _build_fingerings.
build_fingerings = _build_fingerings


def _bore_smoothness(radii: np.ndarray) -> float:
    """Second-difference standard deviation of bore radii.

    Measures how smoothly the bore tapers.  Lower values indicate a
    smoother profile (fewer abrupt diameter changes), which correlates
    with more consistent timbre across the playing range.

    Parameters
    ----------
    radii : ndarray of shape (n_cp,)
        Bore radii at the control-point positions (mm).

    Returns
    -------
    float
        Standard deviation of the second differences.  0 for constant bore.
    """
    if len(radii) < 3:
        return 0.0
    dd = np.diff(radii, n=2)
    return float(np.std(dd))


def _hole_radiation_consistency(
    hole_diameters: Sequence[float],
    bore_radius: float,
) -> float:
    """Standard deviation of per-hole radiation ratios.

    Each hole's radiation ratio is ``pi*(d/2)^2 / (pi*R^2) = (d/(2R))^2``.
    Lower standard deviation means more uniform radiation across all holes,
    which correlates with more consistent timbre between notes.

    Parameters
    ----------
    hole_diameters : sequence of float
        Diameters of each tone hole (mm).
    bore_radius : float
        Bore radius at the hole locations (mm).

    Returns
    -------
    float
        Standard deviation of the per-hole ``(d / 2R)^2`` ratios.
    """
    if not hole_diameters or bore_radius <= 0:
        return 0.0
    ratios = np.array([(d / (2.0 * bore_radius)) ** 2 for d in hole_diameters])
    return float(np.std(ratios))


def compute_timbre_cost(
    radii: np.ndarray,
    hole_diameters: Sequence[float],
    bore_radius: float,
    w_smooth: float = 1.0,
    w_consist: float = 0.5,
) -> float:
    """Bore-geometry timbre proxy (lower = better).

    Combines bore smoothness and hole-radiation consistency into a single
    scalar cost.  Both terms are non-negative; the weights control their
    relative importance.

    Parameters
    ----------
    radii : ndarray of shape (n_cp,)
        Bore radii at control-point positions (mm).
    hole_diameters : sequence of float
        Tone-hole diameters (mm).
    bore_radius : float
        Nominal bore radius (mm), used to normalise hole radiation.
    w_smooth : float, optional
        Weight for the bore-smoothness term.  Default 1.0.
    w_consist : float, optional
        Weight for the hole-radiation-consistency term.  Default 0.5.

    Returns
    -------
    float
        Combined timbre cost (dimensionless, lower is better).
    """
    smooth = _bore_smoothness(radii)
    consist = _hole_radiation_consistency(hole_diameters, bore_radius)
    return w_smooth * smooth + w_consist * consist


# ============================================================================
# Intonation objective
# ============================================================================

def compute_intonation_cost(
    inst: TMMInstrument,
    fingerings: list[list[str]],
    targets: Sequence[float],
    n_register: int = 1,
) -> float:
    """RMS cents deviation from target frequencies.

    Evaluates each fingering against its corresponding target frequency
    and returns the root-mean-square error in cents.

    Parameters
    ----------
    inst : TMMInstrument
        Fully constructed instrument (bore + holes).
    fingerings : list of list of str
        Fingering states ("open"/"closed") for each hole, one per note.
    targets : sequence of float
        Target frequencies in Hz, one per fingering.
    n_register : int, optional
        Register number (1 for fundamental, 2 for second register).
        Default 1.

    Returns
    -------
    float
        RMS cents error.  Returns 1e10 on failure.
    """
    tw = [c / f for f in targets]
    try:
        freqs = inst.compute_fingered_frequencies(tw, fingerings, n_register)
    except Exception:
        return 1e10

    cents = []
    for f, t in zip(freqs, targets):
        if f > 0 and math.isfinite(f):
            cents.append(1200.0 * math.log2(f / t))

    if not cents:
        return 1e10
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    return float(np.sqrt(np.mean(ca ** 2)))


# ============================================================================
# Combined bi-objective evaluation
# ============================================================================

def evaluate_bi_objective(
    radii: np.ndarray,
    bore_length: float,
    hole_positions: list[float],
    hole_diameters: list[float],
    hole_lengths: list[float],
    closed_top: bool,
    targets: Sequence[float],
    bore_radius: float,
    outer_diameter: float,
    n_register: int | None = None,
    loss_model: object | None = None,
) -> tuple[float, float]:
    """Evaluate both intonation and timbre for a candidate instrument.

    Parameters
    ----------
    radii : ndarray of shape (n_cp,)
        Bore radii at control-point positions (mm).
    bore_length : float
        Total bore length (mm).
    hole_positions : list of float
        Tone-hole positions from the bell end (mm).
    hole_diameters : list of float
        Tone-hole diameters (mm).
    hole_lengths : list of float
        Tone-hole chimney lengths (mm).
    closed_top : bool
        Whether the instrument has a closed top.
    targets : sequence of float
        Target frequencies in Hz, one per note.
    bore_radius : float
        Nominal bore radius (mm), used for timbre normalisation.
    outer_diameter : float
        Outer bore diameter (mm).
    n_register : int or None, optional
        Register number.  Auto-detected from *closed_top* if None.
    loss_model : object or None, optional
        Viscothermal loss model (e.g. KeefeLoss).  None for lossless.

    Returns
    -------
    tuple of (float, float)
        ``(intonation_cost, timbre_cost)``.  Both are lower-is-better.
        Returns ``(1e10, 1e10)`` on construction failure.
    """
    if n_register is None:
        n_register = 1 if closed_top else 2

    try:
        inst = tmm_instrument_from_radii(
            radii, bore_length, hole_positions, hole_diameters, hole_lengths,
            outer_diameter_mm=outer_diameter, closed_top=closed_top,
            cone_step=0.5, loss_model=loss_model,
        )
    except Exception:
        return 1e10, 1e10

    n_holes = len(hole_positions)
    fingerings = _build_fingerings(n_holes, closed_top)
    intonation = compute_intonation_cost(inst, fingerings, targets, n_register)
    timbre = compute_timbre_cost(radii, hole_diameters, bore_radius)
    return intonation, timbre


# ============================================================================
# Weighted-sum Pareto sweep
# ============================================================================

def pareto_sweep(
    cfg: dict,
    n_cp: int = 6,
    seed: int = 42,
    n_weights: int = 8,
    maxiter: int = 100,
    verbose: bool = True,
    loss_model: object | None = None,
) -> list[tuple[float, float, float, float]]:
    """Weighted-sum Pareto sweep: vary intonation/timbre weight.

    First runs the standard intonation-only pipeline (sequential placement
    + DE re-optim + 4-stage L-BFGS-B) to find a good starting point, then
    re-optimizes with weighted ``w * intonation + (1-w) * timbre`` to
    trace the Pareto front.

    Parameters
    ----------
    cfg : dict
        Instrument configuration (must contain ``"closed_top"``,
        ``"targets"``, ``"bore_radius"``, ``"outer_diameter"``,
        ``"hole_diameter"``, ``"hole_length"``).
    n_cp : int, optional
        Number of bore control points.  Default 6.
    seed : int, optional
        Random seed for reproducibility.  Default 42.
    n_weights : int, optional
        Number of weight points to sample (evenly spaced 0..1).  Default 8.
    maxiter : int, optional
        Maximum L-BFGS-B iterations per weight point.  Default 100.
    verbose : bool, optional
        Print progress table.  Default True.
    loss_model : object or None, optional
        Viscothermal loss model.  Default None (lossless).

    Returns
    -------
    list of (float, float, float, float)
        One tuple per weight: ``(w_intonation, intonation_rms, timbre_cost,
        bore_length_mm)``.
    """
    from backend.jax_optimizer import refine_sequential

    closed_top = cfg["closed_top"]
    targets = cfg["targets"]
    bore_r = cfg["bore_radius"]
    od = cfg["outer_diameter"]
    n_register = 1 if closed_top else 2

    # Phase 1: standard intonation-only optimization to find good init
    if verbose:
        print("  Phase 1: Intonation-only optimisation (baseline)...")
    rms_init, L_init, radii_init, hp_init, hd_init, _hl_init, _ = refine_sequential(
        cfg, verbose=False, use_jax_bore=False,
    )
    if verbose:
        print(f"    Baseline: RMS={rms_init:.4f}c, L={L_init:.1f}mm, "
              f"{len(hp_init)} holes")

    # Derive n_h from actual placed holes (sequential places len(targets)-1)
    n_h = len(hp_init)
    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9

    # Pack baseline into a single design vector for re-optimization
    x_baseline = np.concatenate([
        radii_init, np.array(hp_init), np.array(hd_init),
    ])

    def combined_obj(x: np.ndarray, w_int: float) -> float:
        """Weighted sum: ``w_int * intonation + (1-w_int) * timbre``."""
        radii = np.maximum(x[:n_cp], 0.1)
        hp = sorted(x[n_cp:n_cp + n_h].tolist())
        hd = x[n_cp + n_h:n_cp + 2 * n_h].tolist()
        hl = [cfg["hole_length"]] * n_h

        intonation, timbre = evaluate_bi_objective(
            radii, L_init, hp, hd, hl, closed_top, targets, bore_r, od,
            n_register, loss_model,
        )
        if intonation >= 1e10 or timbre >= 1e10:
            return 1e10
        return w_int * intonation + (1.0 - w_int) * timbre

    bounds = (
        [(3.0, 15.0)] * n_cp
        + [(30.0, L_init * 1.3)] * n_h
        + [(hd_min, hd_max)] * n_h
    )

    weights = np.linspace(0.0, 1.0, n_weights).tolist()
    results: list[tuple[float, float, float, float]] = []

    # Phase 2: sweep different intonation/timbre weights
    if verbose:
        print(f"  Phase 2: Pareto sweep ({n_weights} weights)...")
    for w_int in weights:
        r = sp_min(
            combined_obj, x_baseline.copy(), args=(w_int,), method="L-BFGS-B",
            bounds=bounds, options={"maxiter": maxiter, "ftol": 1e-10},
        )

        x_opt = r.x
        radii = np.maximum(x_opt[:n_cp], 0.1)
        hp = sorted(x_opt[n_cp:n_cp + n_h].tolist())
        hd = x_opt[n_cp + n_h:n_cp + 2 * n_h].tolist()
        hl = [cfg["hole_length"]] * n_h

        intonation, timbre = evaluate_bi_objective(
            radii, L_init, hp, hd, hl, closed_top, targets, bore_r, od,
            n_register, loss_model,
        )
        results.append((w_int, intonation, timbre, L_init))

    if verbose:
        print(f"\n  {'w_int':>6s}  {'Intonation':>12s}  {'Timbre':>12s}  {'Bore L':>8s}")
        print(f"  {'-'*6}  {'-'*12}  {'-'*12}  {'-'*8}")
        for w, intl, timb, L in results:
            intl_s = f"{intl:.4f}" if intl < 1e5 else "FAIL"
            print(f"  {w:6.2f}  {intl_s:>12s}  {timb:12.6f}  {L:8.1f}mm")

    return results


# ============================================================================
# NSGA-II bi-objective optimization
# ============================================================================

def run_pareto(
    cfg: dict,
    n_cp: int = 6,
    seed: int = 42,
    pop_size: int = 30,
    n_gen: int = 50,
    verbose: bool = True,
    loss_model: object | None = None,
) -> tuple[list[tuple[float, float]], list[np.ndarray], float]:
    """NSGA-II bi-objective optimisation (intonation vs timbre).

    Uses pymoo's NSGA-II with Latin Hypercube Sampling, SBX crossover,
    and polynomial mutation to explore the full Pareto front.

    Parameters
    ----------
    cfg : dict
        Instrument configuration (see ``pareto_sweep`` for required keys).
    n_cp : int, optional
        Number of bore control points.  Default 6.
    seed : int, optional
        Random seed for reproducibility.  Default 42.
    pop_size : int, optional
        Population size per generation.  Default 30.
    n_gen : int, optional
        Number of generations.  Default 50.
    verbose : bool, optional
        Print pymoo convergence output.  Default True.
    loss_model : object or None, optional
        Viscothermal loss model.  Default None (lossless).

    Returns
    -------
    pareto_points : list of (float, float)
        ``(intonation, timbre)`` pairs on the Pareto front, sorted by
        increasing intonation.
    pareto_designs : list of ndarray
        Design vectors corresponding to each Pareto point.
    elapsed : float
        Optimisation time in seconds.
    """
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import Problem
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.lhs import LHS
        from pymoo.optimize import minimize as moo_minimize
    except ImportError:
        print("  pymoo not installed — skipping NSGA-II.")
        print("  Install with: pip install pymoo")
        return [], [], 0.0

    closed_top = cfg["closed_top"]
    targets = cfg["targets"]
    bore_r = cfg["bore_radius"]
    od = cfg["outer_diameter"]
    n_h = len(targets) - (1 if closed_top else 0)
    n_register = 1 if closed_top else 2

    wl_min = c / max(targets)
    L_est = wl_min / 2.0 * 1.2

    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9

    class ParetoProblem(Problem):
        """Two-objective problem: (intonation, timbre)."""

        def __init__(self) -> None:
            n_vars = n_cp + n_h + n_h
            xl = np.array(
                [3.0] * n_cp + [30.0] * n_h + [hd_min] * n_h
            )
            xu = np.array(
                [15.0] * n_cp + [L_est * 1.3] * n_h + [hd_max] * n_h
            )
            super().__init__(n_var=n_vars, n_obj=2, xl=xl, xu=xu)

        def _evaluate(self, X: np.ndarray, out: dict, *args, **kwargs) -> None:
            F = np.full((X.shape[0], 2), 1e10)
            for i in range(X.shape[0]):
                x = X[i]
                radii = np.maximum(x[:n_cp], 0.1)
                hp = sorted(x[n_cp:n_cp + n_h].tolist())
                hd = x[n_cp + n_h:n_cp + 2 * n_h].tolist()
                hl = [cfg["hole_length"]] * n_h

                intonation, timbre = evaluate_bi_objective(
                    radii, L_est, hp, hd, hl, closed_top, targets,
                    bore_r, od, n_register, loss_model,
                )
                if intonation < 1e10 and timbre < 1e10:
                    F[i, 0] = intonation
                    F[i, 1] = timbre

            out["F"] = F

    problem = ParetoProblem()
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
    )

    t0 = time.time()
    res = moo_minimize(
        problem, algorithm, ("n_gen", n_gen), seed=seed, verbose=verbose,
    )
    elapsed = time.time() - t0

    F = res.F
    X = res.X

    # Extract Pareto-optimal points (non-dominated set)
    pareto_idx: list[int] = []
    for i in range(len(F)):
        dominated = False
        for j in range(len(F)):
            if i == j:
                continue
            if (F[j, 0] <= F[i, 0] and F[j, 1] <= F[i, 1]
                    and (F[j, 0] < F[i, 0] or F[j, 1] < F[i, 1])):
                dominated = True
                break
        if not dominated:
            pareto_idx.append(i)

    pareto_idx.sort(key=lambda i: F[i, 0])

    if verbose:
        print(f"\n  Pareto front: {len(pareto_idx)} points ({elapsed:.1f}s)")
        print(f"  {'Intonation':>12s}  {'Timbre':>12s}")
        print(f"  {'-'*12}  {'-'*12}")
        for i in pareto_idx:
            print(f"  {F[i, 0]:12.4f}  {F[i, 1]:12.6f}")

    pareto_points = [(F[i, 0], F[i, 1]) for i in pareto_idx]
    pareto_designs = [X[i] for i in pareto_idx]
    return pareto_points, pareto_designs, elapsed


# ============================================================================
# CLI entry point
# ============================================================================

if __name__ == "__main__":
    from backend.benchmark_all import INSTRUMENTS

    print("=" * 70)
    print("  PARETO FRONT: Intonation vs Timbre")
    print("=" * 70)

    cfg = INSTRUMENTS["chalumeau_C"]
    print(f"\n--- {cfg['desc']} ---")
    print(f"  closed_top={cfg['closed_top']}, "
          f"{len(cfg['targets'])} targets, "
          f"{len(cfg['targets']) - 1} holes")

    print("\n  Weighted-sum sweep:")
    pareto_sweep(cfg, n_weights=5, maxiter=80, verbose=True)

    print("\n  NSGA-II Pareto front:")
    front, designs, dt = run_pareto(
        cfg, pop_size=20, n_gen=30, verbose=True,
    )
