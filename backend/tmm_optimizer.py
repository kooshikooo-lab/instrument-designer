"""
L-BFGS-B bore optimizer using TMM phase-based acoustics.

Replaces OpenWInD impulse-response method with TMM phase resonance
for much faster evaluation (~100x speedup). Supports both flute
(open-open) and clarinet (closed-open) bore optimization.

Design variables:
  - Bore radii at evenly-spaced control points
  - Optional: hole diameters, hole positions, hole lengths

Objective:
  - RMS cents error between resonant frequencies and targets

Features:
  - PAVA monotonicity repair for bore profile
  - Two-phase workflow (Phase 1: 1st register, Phase 2: full)
  - Gradient via finite differences (TMM doesn't provide analytical)
  - Support for both cylindrical and conical bores

Usage:
    from backend.tmm_optimizer import TMMBoreOptimizer

    optimizer = TMMBoreOptimizer(
        target_frequencies=[261.6, 784.8, 1308.0],
        n_control_points=12,
        bore_length=650.0,  # mm
        hole_positions=[60, 100, 150, ...],
        hole_diameters=[7.0, 7.0, 7.0, ...],
        hole_lengths=[3.75, 3.75, 3.75, ...],
        closed_top=False,
    )
    result = optimizer.run(verbose=True)
"""

import os
import time
import math
import numpy as np
from scipy.optimize import minimize
from typing import List, Tuple, Dict, Optional

from .tmm_acoustics import (
    TMMInstrument, tmm_instrument_from_radii, SPEED_OF_SOUND, Hole,
)


# ============================================================================
# PAVA isotonic regression
# ============================================================================

def _pava_isotonic(x: np.ndarray) -> np.ndarray:
    """Find the closest monotonically non-decreasing sequence via PAVA."""
    n = len(x)
    vals = []
    sizes = []
    for v in x:
        vals.append(float(v))
        sizes.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            merged = (vals[-2] * sizes[-2] + vals[-1] * sizes[-1]) / (sizes[-2] + sizes[-1])
            vals[-2] = merged
            sizes[-2] += sizes[-1]
            vals.pop()
            sizes.pop()
    result = np.empty(n, dtype=float)
    idx = 0
    for v, s in zip(vals, sizes):
        result[idx:idx + s] = v
        idx += s
    return result


# ============================================================================
# Cost function
# ============================================================================

def _tmm_objective(
    x: np.ndarray,
    bore_length_mm: float,
    target_freqs: np.ndarray,
    hole_positions_mm: List[float],
    hole_diameters_mm: List[float],
    hole_lengths_mm: List[float],
    closed_top: bool,
    outer_diameter_mm: float,
    n_fingering_holes: int,
    cone_step: float,
    fingering_sets: List[List[str]],
    target_wavelengths: np.ndarray,
    register: int,
) -> float:
    """
    TMM-based objective: RMS cents error for a bore profile.

    The design variable x is the array of bore radii (mm) at
    evenly-spaced control points.
    """
    # Apply PAVA for monotonicity (clarinets are roughly cylindrical,
    # but we still enforce non-decreasing for robustness)
    radii = _pava_isotonic(x)

    # Ensure minimum radius
    radii = np.maximum(radii, 1.0)

    try:
        inst = tmm_instrument_from_radii(
            radii_mm=radii,
            bore_length_mm=bore_length_mm,
            hole_positions_mm=hole_positions_mm,
            hole_diameters_mm=hole_diameters_mm,
            hole_lengths_mm=hole_lengths_mm,
            outer_diameter_mm=outer_diameter_mm,
            closed_top=closed_top,
            cone_step=cone_step,
        )
    except Exception:
        return 1e10

    errors = []
    for i, (fingerings, target_freq) in enumerate(zip(fingering_sets, target_freqs)):
        try:
            wl = inst.find_resonance(
                wavelength_near=target_wavelengths[i],
                fingerings=fingerings,
                n_register=register,
            )
            actual_freq = inst.frequency_from_wavelength(wl)
            if actual_freq <= 0 or not math.isfinite(actual_freq):
                errors.append(1e6)
            else:
                cents = 1200.0 * math.log2(actual_freq / target_freq)
                errors.append(cents)
        except Exception:
            errors.append(1e6)

    errors = np.array(errors)

    # Check for catastrophic failures
    if np.any(np.abs(errors) > 1e5):
        return 1e10

    # RMS after global offset correction (tuning tolerance)
    global_offset = np.median(errors)
    corrected = errors - global_offset
    rms = float(np.sqrt(np.mean(corrected ** 2)))

    # Penalty for insufficient working fingerings
    n_failures = np.sum(np.abs(errors) > 1e4)
    if n_failures > 0:
        rms += 1000.0 * n_failures

    return rms


# ============================================================================
# Optimizer
# ============================================================================

class TMMBoreOptimizer:
    """
    Gradient-based bore optimizer using TMM phase resonance + L-BFGS-B.

    Much faster than OpenWInD-based optimizers (~100x per evaluation),
    enabling optimization of more design variables (bore + holes).
    """

    def __init__(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_control_points: int = 12,
        bore_length: Optional[float] = None,
        min_radius: float = 1.0,
        max_radius: float = 15.0,
        temperature: float = 20.0,
        hole_positions: Optional[List[float]] = None,
        hole_diameters: Optional[List[float]] = None,
        hole_lengths: Optional[List[float]] = None,
        closed_top: bool = False,
        outer_diameter: float = 22.0,
        cone_step: float = 0.5,
        n_register: int = 1,
    ):
        self.target_freqs = np.array(sorted(target_frequencies))
        self.fingering_sets = fingering_sets
        self.n_cp = n_control_points
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.closed_top = closed_top
        self.outer_diameter = outer_diameter
        self.cone_step = cone_step
        self.n_register = n_register

        # Speed of sound at temperature
        self.speed_of_sound = 331300.0 + 606.0 * temperature  # mm/s

        # Bore length: auto-calculate from fundamental if not provided
        if bore_length is None:
            fundamental = min(target_frequencies)
            if closed_top:
                # Clarinet: quarter-wave
                self.bore_length = self.speed_of_sound / (4.0 * fundamental)
            else:
                # Flute: half-wave
                self.bore_length = self.speed_of_sound / (2.0 * fundamental)
        else:
            self.bore_length = bore_length

        # Hole geometry
        if hole_positions is not None:
            self.hole_positions = list(hole_positions)
            self.hole_diameters = list(hole_diameters)
            self.hole_lengths = list(hole_lengths)
        else:
            # Default: no holes (just bore optimization)
            self.hole_positions = []
            self.hole_diameters = []
            self.hole_lengths = []

        # Compute initial wavelength guesses for each fingering
        self._target_wavelengths = self._compute_initial_wavelengths()

    def _compute_initial_wavelengths(self) -> np.ndarray:
        """Compute initial wavelength guesses from target frequencies."""
        wls = []
        for freq in self.target_freqs:
            if self.closed_top:
                wl = self.speed_of_sound / freq
            else:
                wl = self.speed_of_sound / freq
            wls.append(wl)
        return np.array(wls)

    def _make_initial_guess(self, method: str = "cylindrical") -> np.ndarray:
        """Create initial guess for bore radii."""
        if method == "flat":
            midpoint = (self.min_radius + self.max_radius) / 2.0
            return np.full(self.n_cp, midpoint)

        elif method == "cylindrical":
            # Cylindrical bore at ~14.5mm diameter = 7.25mm radius
            return np.full(self.n_cp, 7.25)

        elif method == "random":
            raw = np.random.uniform(self.min_radius, self.max_radius, self.n_cp)
            return _pava_isotonic(raw)

        else:
            raise ValueError(f"Unknown method: {method}")

    def run(
        self,
        verbose: bool = True,
        method: str = "L-BFGS-B",
        maxiter: int = 300,
        initial_guess: str = "cylindrical",
        known_good_radii: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Run L-BFGS-B optimization using TMM acoustics.

        Args:
            verbose: print progress
            method: scipy.optimize method
            maxiter: maximum iterations
            initial_guess: "flat", "cylindrical", or "random"
            known_good_radii: if provided, use as initial guess

        Returns dict with: best_bore, best_objective, iterations, etc.
        """
        if known_good_radii is not None:
            x0 = np.array(known_good_radii, dtype=float)
            if verbose:
                print(f"  Using seeded initial guess")
        else:
            x0 = self._make_initial_guess(initial_guess)

        bounds = [(self.min_radius, self.max_radius)] * self.n_cp

        def objective(x):
            return _tmm_objective(
                x, self.bore_length, self.target_freqs,
                self.hole_positions, self.hole_diameters, self.hole_lengths,
                self.closed_top, self.outer_diameter,
                len(self.hole_positions), self.cone_step,
                self.fingering_sets, self._target_wavelengths,
                self.n_register,
            )

        # Progress callback
        iteration_count = [0]
        best_val = [float('inf')]
        if verbose:
            def _callback(xk):
                iteration_count[0] += 1
                if iteration_count[0] % 10 == 0:
                    obj = objective(xk)
                    if obj < best_val[0]:
                        best_val[0] = obj
                    print(f"    iter {iteration_count[0]:4d}: obj={obj:.2f} cents (best={best_val[0]:.2f})")
            cb = _callback
        else:
            cb = None

        t0 = time.time()

        if verbose:
            print(f"  TMM Bore Optimizer")
            print(f"  Method: {method}")
            print(f"  Control points: {self.n_cp}")
            print(f"  Bore length: {self.bore_length:.1f} mm")
            print(f"  Holes: {len(self.hole_positions)}")
            print(f"  Target harmonics: {len(self.target_freqs)}")
            print(f"  Register: {self.n_register}")
            print(f"  Starting optimization...")

        opts = {"maxiter": maxiter, "ftol": 1e-6}
        if method == "L-BFGS-B":
            opts["gtol"] = 1e-4

        result = minimize(
            objective,
            x0,
            method=method,
            bounds=bounds if method == "L-BFGS-B" else None,
            callback=cb,
            options=opts,
        )

        wall_time = time.time() - t0

        # Final result
        final_radii = _pava_isotonic(result.x)
        final_radii = np.maximum(final_radii, 1.0)

        # Build final instrument and compute all frequencies
        inst = tmm_instrument_from_radii(
            final_radii, self.bore_length,
            self.hole_positions, self.hole_diameters, self.hole_lengths,
            self.outer_diameter, self.closed_top, self.cone_step,
        )

        matched = []
        all_errors = []
        for i, (fingerings, target_freq) in enumerate(zip(self.fingering_sets, self.target_freqs)):
            try:
                wl = inst.find_resonance(
                    self._target_wavelengths[i], fingerings, self.n_register,
                )
                actual_freq = inst.frequency_from_wavelength(wl)
                cents = 1200.0 * math.log2(actual_freq / target_freq) if actual_freq > 0 else 1e10
                matched.append({
                    "target": float(target_freq),
                    "actual": float(actual_freq),
                    "error_cents": float(cents),
                })
                all_errors.append(cents)
            except Exception:
                matched.append({
                    "target": float(target_freq),
                    "actual": 0.0,
                    "error_cents": 1e10,
                })
                all_errors.append(1e10)

        all_errors = np.array(all_errors)
        global_offset = float(np.median(all_errors))
        corrected_errors = np.abs(all_errors - global_offset)
        final_rms = float(np.sqrt(np.mean(corrected_errors ** 2)))

        if verbose:
            print(f"\n  Optimization complete:")
            print(f"    RMS cents error: {final_rms:.2f}")
            print(f"    Global offset: {global_offset:.2f} cents")
            print(f"    Wall time: {wall_time:.1f}s")
            print(f"    Success: {result.success}")
            print(f"\n  Per-note errors (cents):")
            for m in matched:
                print(f"    {m['target']:8.1f} Hz -> {m['actual']:8.1f} Hz  ({m['error_cents']:+.1f})")

        return {
            "success": result.success,
            "message": str(result.message),
            "best_radii": final_radii.tolist(),
            "best_objective": float(result.fun),
            "final_rms_cents": final_rms,
            "global_offset_cents": global_offset,
            "matched_frequencies": matched,
            "iterations": result.nit,
            "function_evaluations": result.nfev,
            "wall_time": wall_time,
            "bore_length_mm": self.bore_length,
            "method": method,
        }


# ============================================================================
# Two-phase optimization
# ============================================================================

def run_two_phase_tmm(
    target_frequencies: List[float],
    fingering_sets: List[List[str]],
    n_control_points: int = 12,
    bore_length: Optional[float] = None,
    closed_top: bool = False,
    hole_positions: Optional[List[float]] = None,
    hole_diameters: Optional[List[float]] = None,
    hole_lengths: Optional[List[float]] = None,
    temperature: float = 20.0,
    verbose: bool = True,
) -> Dict:
    """
    Two-phase TMM optimization following Noreland (2013).

    Phase 1: Optimize 1st register only (first 3 harmonics)
    Phase 2: Full instrument optimization (seeded from Phase 1)
    """
    target_freqs = sorted(target_frequencies)

    if verbose:
        print("=" * 60)
        print("TWO-PHASE TMM OPTIMIZATION")
        print("=" * 60)

    # Phase 1: 1st register only
    phase1_n = min(3, len(target_freqs))
    phase1_targets = target_freqs[:phase1_n]
    phase1_fingerings = fingering_sets[:phase1_n]

    if verbose:
        print(f"\n--- Phase 1: 1st Register ({phase1_n} harmonics) ---")

    opt1 = TMMBoreOptimizer(
        target_frequencies=phase1_targets,
        fingering_sets=phase1_fingerings,
        n_control_points=n_control_points,
        bore_length=bore_length,
        closed_top=closed_top,
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        temperature=temperature,
    )

    result1 = opt1.run(verbose=verbose, method="L-BFGS-B", maxiter=200)

    # Phase 2: Full instrument
    if verbose:
        print(f"\n--- Phase 2: Full Instrument ({len(target_freqs)} harmonics) ---")

    opt2 = TMMBoreOptimizer(
        target_frequencies=target_freqs,
        fingering_sets=fingering_sets,
        n_control_points=n_control_points,
        bore_length=bore_length,
        closed_top=closed_top,
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        temperature=temperature,
    )

    phase1_radii = np.array(result1["best_radii"])
    result2 = opt2.run(
        verbose=verbose, method="L-BFGS-B", maxiter=300,
        known_good_radii=phase1_radii,
    )

    # Use whichever is better
    if result1["final_rms_cents"] < result2["final_rms_cents"]:
        if verbose:
            print(f"\n  Phase 1 ({result1['final_rms_cents']:.2f} cents) "
                  f"better than Phase 2 ({result2['final_rms_cents']:.2f} cents)")
        return result1

    return result2
