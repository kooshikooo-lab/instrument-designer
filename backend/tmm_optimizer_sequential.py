"""
Sequential bore optimizer with tone holes.

Based on the Bordeaux group method (Noreland, Guilloteau, Ernoult):
1. Phase 1: Optimize bore length from all-closed fingering
2. Phase 2: Add holes bottom-to-top, optimizing each one
3. Phase 3: Simultaneous refinement of all parameters

This avoids the local minima that plague simultaneous optimization.

Key fixes over previous code:
- Bore length is a FREE variable (not auto-calculated from fundamental)
- Sequential hole addition (not all-at-once)
- Fewer control points (3-5 for 6-8 holes, not 12-20)
- PAVA removed (bore isn't necessarily monotonic)
- Initial bore from physics: L = c/(4*f) for closed-open, c/(2*f) for open-open
"""

import time
import math
import numpy as np
from scipy.optimize import minimize, differential_evolution
from typing import List, Optional, Dict, Tuple

try:
    from .tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND, TMMInstrument
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND, TMMInstrument


# ============================================================================
# Phase 1: Bore length optimization (all holes closed)
# ============================================================================

def _bore_objective_all_closed(
    bore_length,
    target_freq: float,
    bore_radius: float,
    outer_diameter: float,
    closed_top: bool,
    n_register: int,
) -> float:
    """Objective: find bore length that gives correct fundamental with all holes closed.
    n_register should already be the correct phase register (2 for open-open, 1 for closed-open)."""
    bore_length = float(np.asarray(bore_length).item())
    radii = np.array([bore_radius])
    try:
        inst = tmm_instrument_from_radii(
            radii, bore_length,
            [], [], [],  # no holes
            outer_diameter, closed_top=closed_top, cone_step=0.5,
        )
        wl = inst.find_resonance(
            SPEED_OF_SOUND / target_freq,
            [],  # all closed = no fingering
            n_register,
        )
        actual = inst.frequency_from_wavelength(wl)
        if actual <= 0 or not math.isfinite(actual):
            return 1e10
        return abs(1200.0 * math.log2(actual / target_freq))
    except Exception:
        return 1e10


def optimize_bore_length(
    target_freq: float,
    bore_radius: float,
    outer_diameter: float = 22.0,
    closed_top: bool = True,
    n_register: int = 1,
    verbose: bool = True,
) -> float:
    """Find optimal bore length for a given fundamental frequency."""
    # Initial estimate
    c = SPEED_OF_SOUND
    if closed_top:
        L_init = c / (4.0 * target_freq)
    else:
        L_init = c / (2.0 * target_freq)

    if verbose:
        print(f"  Phase 1: Bore length from fundamental {target_freq:.1f} Hz")
        print(f"    Initial estimate: {L_init:.1f} mm")

    # Search around initial estimate
    bounds = [(L_init * 0.7, L_init * 1.3)]
    result = minimize(
        _bore_objective_all_closed,
        x0=[L_init],
        args=(target_freq, bore_radius, outer_diameter, closed_top, n_register),
        method='L-BFGS-B',
        bounds=bounds,
        options={"maxiter": 100, "ftol": 1e-6},
    )

    best_L = result.x[0]
    best_err = result.fun

    if verbose:
        print(f"    Optimized: {best_L:.1f} mm (error: {best_err:.1f} cents)")

    return best_L


# ============================================================================
# Phase 2: Sequential hole addition
# ============================================================================

def _hole_objective(
    params: np.ndarray,
    bore_radii: np.ndarray,
    bore_length: float,
    hole_diameter: float,
    hole_length: float,
    outer_diameter: float,
    closed_top: bool,
    target_freq: float,
    target_wavelength: float,
    existing_holes: List[Dict],  # Already-placed holes
    n_register: int,
) -> float:
    """
    Objective for placing a single new hole.
    
    Fingering strategy depends on instrument type:
    - Closed-open (clarinets): existing holes CLOSED, new hole open
      (Bordeaux method - closing holes extends effective bore)
    - Open-open (sax/flute): existing holes OPEN, new hole open
      (each hole creates independent resonator)
    """
    hole_position = params[0]

    # Build hole list: existing + new
    positions = [h["position"] for h in existing_holes] + [hole_position]
    diameters = [h["diameter"] for h in existing_holes] + [hole_diameter]
    lengths = [h["length"] for h in existing_holes] + [hole_length]

    # Sort by position
    sorted_idx = np.argsort(positions)
    positions = [positions[i] for i in sorted_idx]
    diameters = [diameters[i] for i in sorted_idx]
    lengths = [lengths[i] for i in sorted_idx]

    # Fingering depends on instrument type
    new_idx = list(sorted_idx).index(len(existing_holes))
    
    if closed_top:
        # Closed-open (clarinets): Bordeaux method
        # All existing holes CLOSED, new hole OPEN
        fingering_sorted = ["closed"] * len(positions)
        fingering_sorted[new_idx] = "open"
    else:
        # Open-open (sax/flute): Ernoult (2021) method
        # Evaluate ONLY with the new hole — no other holes present
        # Each hole is independent - place using single-hole evaluation
        positions = [positions[new_idx]]
        diameters = [diameters[new_idx]]
        lengths = [lengths[new_idx]]
        fingering_sorted = ["open"]

    try:
        inst = tmm_instrument_from_radii(
            bore_radii, bore_length,
            positions, diameters, lengths,
            outer_diameter, closed_top=closed_top, cone_step=0.5,
        )
        wl = inst.find_resonance(target_wavelength, fingering_sorted, n_register)
        actual = inst.frequency_from_wavelength(wl)
        if actual <= 0 or not math.isfinite(actual):
            return 1e10
        return abs(1200.0 * math.log2(actual / target_freq))
    except Exception:
        return 1e10


def optimize_hole_position(
    bore_radii: np.ndarray,
    bore_length: float,
    hole_diameter: float,
    hole_length: float,
    outer_diameter: float,
    closed_top: bool,
    target_freq: float,
    existing_holes: List[Dict],
    n_register: int = 1,
    verbose: bool = True,
    hole_index: int = 0,
) -> Dict:
    """Optimize position of a single hole, keeping bore and existing holes fixed."""
    target_wavelength = SPEED_OF_SOUND / target_freq

    # Bounds: hole must be between last hole (or 0) and bore end
    if existing_holes:
        min_pos = existing_holes[-1]["position"] + 10  # At least 10mm gap
    else:
        min_pos = 20.0  # At least 20mm from top
    max_pos = bore_length - 20.0  # At least 20mm from end

    if min_pos >= max_pos:
        min_pos = max_pos - 1

    bounds = [(min_pos, max_pos)]

    result = minimize(
        _hole_objective,
        x0=[(min_pos + max_pos) / 2],
        args=(bore_radii, bore_length, hole_diameter, hole_length,
              outer_diameter, closed_top, target_freq, target_wavelength,
              existing_holes, n_register),
        method='L-BFGS-B',
        bounds=bounds,
        options={"maxiter": 100, "ftol": 1e-4},
    )

    # Also try a few random starts
    best_pos = result.x[0]
    best_err = result.fun
    for _ in range(5):
        trial_pos = np.random.uniform(min_pos, max_pos)
        r2 = minimize(
            _hole_objective,
            x0=[trial_pos],
            args=(bore_radii, bore_length, hole_diameter, hole_length,
                  outer_diameter, closed_top, target_freq, target_wavelength,
                  existing_holes, n_register),
            method='L-BFGS-B',
            bounds=bounds,
            options={"maxiter": 50, "ftol": 1e-4},
        )
        if r2.fun < best_err:
            best_err = r2.fun
            best_pos = r2.x[0]

    hole = {
        "position": best_pos,
        "diameter": hole_diameter,
        "length": hole_length,
    }

    if verbose:
        print(f"    Hole {hole_index}: pos={best_pos:.1f}mm, "
              f"err={best_err:.1f} cents")

    return hole


# ============================================================================
# Full sequential optimizer
# ============================================================================

class SequentialBoreOptimizer:
    """
    Sequential bore optimizer based on Bordeaux method.

    Phase 1: Bore length from fundamental
    Phase 2: Holes added bottom-to-top, one at a time
    Phase 3: Simultaneous refinement (optional)
    """

    def __init__(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        bore_radius: float = 7.25,
        outer_diameter: float = 22.0,
        closed_top: bool = True,
        n_register: int = 1,
        hole_diameter: float = 7.0,
        hole_length: float = 3.75,
        bore_length_bounds: Tuple[float, float] = (100.0, 2000.0),
        n_bore_cp: int = 0,
        bore_radius_bounds: Tuple[float, float] = (2.0, 20.0),
    ):
        self.target_freqs = target_frequencies
        self.fingering_sets = fingering_sets
        self.bore_radius = bore_radius
        self.outer_diameter = outer_diameter
        self.closed_top = closed_top
        self.n_register = n_register
        self.hole_diameter = hole_diameter
        self.hole_length = hole_length
        self.bore_length_bounds = bore_length_bounds
        self.n_bore_cp = n_bore_cp
        self.bore_radius_bounds = bore_radius_bounds

    def run(self, verbose: bool = True) -> Dict:
        """Run the sequential optimization."""
        t_start = time.time()

        if verbose:
            print(f"  Sequential Bore Optimizer")
            print(f"  Target notes: {len(self.target_freqs)}")
            print(f"  Bore radius: {self.bore_radius:.1f} mm")
            print(f"  Closed top: {self.closed_top}")
            print()

        # Phase 1: Bore length from fundamental (lowest note)
        fundamental = min(self.target_freqs)
        bore_length = optimize_bore_length(
            fundamental, self.bore_radius, self.outer_diameter,
            self.closed_top, self.n_register, verbose,
        )

        # Create uniform bore profile
        bore_radii = np.full(10, self.bore_radius)

        # Phase 2: Add holes one at a time, bottom-to-top
        if verbose:
            print(f"\n  Phase 2: Sequential hole placement")
            print(f"    Bore: {bore_length:.0f}mm x {self.bore_radius:.1f}mm")

        existing_holes = []
        sorted_targets = sorted(self.target_freqs)
        # Skip the fundamental (lowest note) - it's played with all holes closed
        # Place holes for notes above the fundamental
        notes_needing_holes = sorted_targets[1:]
        
        # For open-open instruments (sax/flute), place holes from HIGHEST to LOWEST
        # (furthest from bell to closest to bell)
        # This follows Ernoult (2021) - each hole is placed independently
        if not self.closed_top:
            notes_needing_holes = list(reversed(notes_needing_holes))

        for i, target_freq in enumerate(notes_needing_holes):
            if verbose:
                print(f"\n    Adding hole for {target_freq:.1f} Hz "
                      f"(note {i+1}/{len(notes_needing_holes)})")

            hole = optimize_hole_position(
                bore_radii, bore_length,
                self.hole_diameter, self.hole_length,
                self.outer_diameter, self.closed_top,
                target_freq, existing_holes,
                self.n_register, verbose, i,
            )
            existing_holes.append(hole)
        
        # For open-open: reverse hole order to match fingering_sets convention
        # (lowest note = hole 0, highest note = last hole)
        if not self.closed_top:
            existing_holes = list(reversed(existing_holes))

        # Phase 3: Multi-stage refinement with L-BFGS-B
        if verbose:
            bore_desc = f"{self.n_bore_cp} segments" if self.n_bore_cp > 0 else "uniform"
            print(f"\n  Phase 3: L-BFGS-B refinement (bore: {bore_desc})")

        all_positions = [h["position"] for h in existing_holes]
        all_diameters = [h["diameter"] for h in existing_holes]
        all_lengths = [h["length"] for h in existing_holes]

        sorted_idx = np.argsort(all_positions)
        all_positions = [all_positions[i] for i in sorted_idx]
        all_diameters = [all_diameters[i] for i in sorted_idx]
        all_lengths = [all_lengths[i] for i in sorted_idx]

        n_cp = self.n_bore_cp
        if n_cp > 0:
            bore_radii = np.full(n_cp, self.bore_radius)
        else:
            bore_radii = np.full(max(len(all_positions) + 2, 4), self.bore_radius)

        def _refine_objective(x):
            bl = x[0]
            if n_cp > 0:
                br = list(x[1:1+n_cp])
                positions = list(x[1+n_cp:1+n_cp+len(all_positions)])
            else:
                br = bore_radii
                positions = list(x[1:1+len(all_positions)])
            try:
                inst = tmm_instrument_from_radii(
                    br, bl, positions, all_diameters, all_lengths,
                    self.outer_diameter, closed_top=self.closed_top, cone_step=0.5,
                )
                target_wavelengths = [SPEED_OF_SOUND / f for f in self.target_freqs]
                freqs = inst.compute_fingered_frequencies(
                    target_wavelengths, self.fingering_sets, self.n_register,
                )
                cents = []
                for a, t in zip(freqs, self.target_freqs):
                    if a > 0 and math.isfinite(a):
                        cents.append(1200.0 * math.log2(a / t))
                    else:
                        cents.append(1e10)
                c = np.array(cents)
                offset = np.median(c)
                return float(np.sqrt(np.mean((c - offset) ** 2)))
            except Exception:
                return 1e10

        # Build tight non-crossing bounds for holes
        GAP = 5.0
        n_h = len(all_positions)
        hole_lo = [0.0] * n_h
        hole_hi = [bore_length] * n_h
        for i in range(n_h):
            hole_lo[i] = (all_positions[i-1] + GAP) if i > 0 else 20.0
            hole_hi[i] = (all_positions[i+1] - GAP) if i < n_h-1 else (bore_length - 20.0)
            hole_lo[i] = max(hole_lo[i], all_positions[i] - 20)
            hole_hi[i] = min(hole_hi[i], all_positions[i] + 20)
            if hole_lo[i] > hole_hi[i]:
                hole_lo[i] = all_positions[i] - 1
                hole_hi[i] = all_positions[i] + 1

        # Bore radii bounds
        bore_bounds_list = [self.bore_radius_bounds] * n_cp if n_cp > 0 else []

        # Stage 1: Bore length only (1 variable)
        if verbose:
            print(f"    Stage 1: Bore length")
        bore_len_bounds = [(bore_length * 0.85, bore_length * 1.15)]
        r1 = minimize(lambda x: _refine_objective(np.concatenate(
            [x, bore_radii, all_positions] if n_cp > 0 else [x, all_positions])),
            [bore_length], method='L-BFGS-B', bounds=bore_len_bounds,
            options={"maxiter": 100, "ftol": 1e-8})
        bore_length = r1.x[0]
        if verbose:
            print(f"      bore={bore_length:.1f}mm cost={r1.fun:.4f}")

        # Stage 2: Bore radii only (n_cp variables)
        if n_cp > 0:
            if verbose:
                print(f"    Stage 2: Bore radii ({n_cp} segments)")
            r2 = minimize(
                lambda x: _refine_objective(np.concatenate(
                    [[bore_length], x, all_positions])),
                bore_radii, method='L-BFGS-B', bounds=bore_bounds_list,
                options={"maxiter": 200, "ftol": 1e-8})
            bore_radii = list(r2.x)
            if verbose:
                print(f"      cost={r2.fun:.4f}")

        # Stage 3: Hole positions only (n_h variables, L-BFGS-B with ordering)
        if verbose:
            print(f"    Stage 3: Hole positions ({n_h} holes)")
        hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)]
        x0_holes = np.array(all_positions)
        r3 = minimize(
            lambda x: _refine_objective(np.concatenate(
                [[bore_length], bore_radii, x] if n_cp > 0 else [[bore_length], x])),
            x0_holes, method='L-BFGS-B', bounds=hole_bounds,
            options={"maxiter": 200, "ftol": 1e-8},
        )
        all_positions = list(r3.x)
        if verbose:
            print(f"      cost={r3.fun:.4f}")

        # Stage 4: Simultaneous fine-tune (all variables)
        if verbose:
            print(f"    Stage 4: Simultaneous")
        if n_cp > 0:
            all_bounds = bore_len_bounds + bore_bounds_list + hole_bounds
            x0_all = np.concatenate([[bore_length], bore_radii, all_positions])
        else:
            all_bounds = bore_len_bounds + hole_bounds
            x0_all = np.concatenate([[bore_length], all_positions])
        r4 = minimize(_refine_objective, x0_all, method='L-BFGS-B',
                      bounds=all_bounds,
                      options={"maxiter": 300, "ftol": 1e-10})
        bore_length = r4.x[0]
        if n_cp > 0:
            bore_radii = list(r4.x[1:1+n_cp])
            all_positions = list(r4.x[1+n_cp:1+n_cp+n_h])
        else:
            all_positions = list(r4.x[1:1+n_h])
        if verbose:
            print(f"      cost={r4.fun:.4f}")

        # Final evaluation
        bore_radii_list = list(bore_radii) if not isinstance(bore_radii, list) else bore_radii
        inst = tmm_instrument_from_radii(
            bore_radii_list, bore_length,
            all_positions, all_diameters, all_lengths,
            self.outer_diameter, closed_top=self.closed_top, cone_step=0.5,
        )

        target_wavelengths = [SPEED_OF_SOUND / f for f in self.target_freqs]
        freqs = inst.compute_fingered_frequencies(
            target_wavelengths, self.fingering_sets, self.n_register,
        )

        cents_errors = []
        for actual, target in zip(freqs, self.target_freqs):
            if actual > 0 and math.isfinite(actual):
                cents_errors.append(1200.0 * math.log2(actual / target))
            else:
                cents_errors.append(1e10)

        cents_arr = np.array(cents_errors)
        offset = np.median(cents_arr)
        corrected = cents_arr - offset
        rms = float(np.sqrt(np.mean(corrected ** 2)))
        peak = float(np.max(np.abs(corrected)))

        wall_time = time.time() - t_start

        if verbose:
            print(f"\n  Final result:")
            print(f"    Bore length: {bore_length:.1f} mm")
            if n_cp > 0:
                print(f"    Bore profile: {n_cp} segments, radii={[f'{r:.1f}' for r in bore_radii_list]}")
            print(f"    Holes: {len(all_positions)}")
            for i, (pos, diam) in enumerate(zip(all_positions, all_diameters)):
                print(f"      Hole {i}: pos={pos:.1f}mm, dia={diam:.1f}mm")
            print(f"    RMS: {rms:.2f} cents | Peak: {peak:.2f} cents")
            print(f"    Time: {wall_time:.1f}s")

        return {
            "success": rms < 50.0,
            "bore_length_mm": bore_length,
            "bore_radii": bore_radii_list,
            "hole_positions": all_positions,
            "hole_diameters": all_diameters,
            "hole_lengths": all_lengths,
            "final_rms_cents": rms,
            "peak_error_cents": peak,
            "wall_time": wall_time,
            "matched_frequencies": [
                {"target": t, "actual": a, "error_cents": c}
                for t, a, c in zip(self.target_freqs, freqs, cents_errors)
            ],
        }


# ============================================================================
# Powell+L-BFGS-B optimizer (corrected)
# ============================================================================

class CorrectedPowellOptimizer:
    """
    Corrected Powell+L-BFGS-B optimizer with:
    - Free bore length (not auto-calculated)
    - Reasonable control points (5-8, not 12-20)
    - Bore length as a design variable
    """

    def __init__(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_control_points: int = 6,
        bore_length: Optional[float] = None,
        bore_length_bounds: Tuple[float, float] = (100.0, 2000.0),
        min_radius: float = 4.0,
        max_radius: float = 15.0,
        hole_positions: Optional[List[float]] = None,
        hole_diameters: Optional[List[float]] = None,
        hole_lengths: Optional[List[float]] = None,
        closed_top: bool = True,
        outer_diameter: float = 22.0,
        n_register: int = 1,
    ):
        self.target_freqs = target_frequencies
        self.fingering_sets = fingering_sets
        self.n_cp = n_control_points
        self.bore_length_bounds = bore_length_bounds
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.hole_positions = list(hole_positions or [])
        self.hole_diameters = list(hole_diameters or [])
        self.hole_lengths = list(hole_lengths or [])
        self.closed_top = closed_top
        self.outer_diameter = outer_diameter
        self.n_register = n_register

        # Auto-calculate bore length if not provided
        if bore_length is None:
            fundamental = min(target_frequencies)
            c = SPEED_OF_SOUND
            if closed_top:
                self.bore_length_init = c / (4.0 * fundamental)
            else:
                self.bore_length_init = c / (2.0 * fundamental)
        else:
            self.bore_length_init = bore_length

        self._target_wavelengths = np.array([
            SPEED_OF_SOUND / f for f in self.target_freqs
        ])

    def _objective(self, x: np.ndarray) -> float:
        """Objective: bore radii + bore length as design variables."""
        bore_length = x[0]
        radii = np.maximum(x[1:], self.min_radius)

        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length,
                self.hole_positions, self.hole_diameters, self.hole_lengths,
                self.outer_diameter, self.closed_top, 0.5,
            )
        except Exception:
            return 1e10

        errors = []
        for i, (fingerings, target_freq) in enumerate(zip(self.fingering_sets, self.target_freqs)):
            try:
                wl = inst.find_resonance(
                    self._target_wavelengths[i], fingerings, self.n_register,
                )
                actual = inst.frequency_from_wavelength(wl)
                if actual <= 0 or not math.isfinite(actual):
                    errors.append(1e6)
                else:
                    errors.append(1200.0 * math.log2(actual / target_freq))
            except Exception:
                errors.append(1e6)

        errors = np.array(errors)
        if np.any(np.abs(errors) > 1e5):
            return 1e10
        offset = np.median(errors)
        corrected = errors - offset
        return float(np.sqrt(np.mean(corrected ** 2)))

    def run(self, verbose: bool = True, maxiter: int = 600) -> Dict:
        """Run Powell + L-BFGS-B with bore length as free variable."""
        t0 = time.time()

        if verbose:
            print(f"  Corrected Powell+L-BFGS-B Optimizer")
            print(f"  Control points: {self.n_cp}")
            print(f"  Bore length init: {self.bore_length_init:.0f} mm")
            print(f"  Bore length bounds: {self.bore_length_bounds}")
            print(f"  Holes: {len(self.hole_positions)}")
            print(f"  Fingerings: {len(self.fingering_sets)}")

        # Design variables: [bore_length, radius_1, ..., radius_n]
        x0 = np.concatenate([
            [self.bore_length_init],
            np.full(self.n_cp, self.bore_radius_init),
        ])

        bounds = [
            self.bore_length_bounds,
        ] + [(self.min_radius, self.max_radius)] * self.n_cp

        # Phase 1: Powell
        powell_budget = maxiter * 2 // 3
        if verbose:
            print(f"\n  Phase 1: Powell ({powell_budget} maxiter)...")
        result_powell = minimize(
            self._objective, x0,
            method='Powell',
            bounds=bounds,
            options={"maxiter": powell_budget, "ftol": 1e-8},
        )
        if verbose:
            print(f"    Powell: {result_powell.fun:.4f} cents ({result_powell.nit} iters)")

        # Phase 2: L-BFGS-B
        lbfgs_budget = maxiter - powell_budget
        if verbose:
            print(f"  Phase 2: L-BFGS-B ({lbfgs_budget} maxiter)...")
        result_lbfgs = minimize(
            self._objective, result_powell.x,
            method='L-BFGS-B',
            bounds=bounds,
            options={"maxiter": lbfgs_budget, "ftol": 1e-10, "gtol": 1e-6},
        )
        if verbose:
            print(f"    L-BFGS-B: {result_lbfgs.fun:.4f} cents ({result_lbfgs.nit} iters)")

        # Pick best
        best = result_powell if result_powell.fun < result_lbfgs.fun else result_lbfgs
        best_bore_length = best.x[0]
        best_radii = np.maximum(best.x[1:], self.min_radius)

        # Evaluate
        inst = tmm_instrument_from_radii(
            best_radii, best_bore_length,
            self.hole_positions, self.hole_diameters, self.hole_lengths,
            self.outer_diameter, self.closed_top, 0.5,
        )
        freqs = inst.compute_fingered_frequencies(
            self._target_wavelengths, self.fingering_sets, self.n_register,
        )

        cents_errors = []
        for actual, target in zip(freqs, self.target_freqs):
            if actual > 0 and math.isfinite(actual):
                cents_errors.append(1200.0 * math.log2(actual / target))
            else:
                cents_errors.append(1e10)

        cents_arr = np.array(cents_errors)
        offset = np.median(cents_arr)
        corrected = cents_arr - offset
        rms = float(np.sqrt(np.mean(corrected ** 2)))
        peak = float(np.max(np.abs(corrected)))
        wall_time = time.time() - t0

        if verbose:
            print(f"\n  Best: {best.fun:.4f} cents")
            print(f"  Bore length: {best_bore_length:.1f} mm")
            print(f"  RMS: {rms:.2f} cents | Peak: {peak:.2f} cents")
            print(f"  Time: {wall_time:.1f}s")

        return {
            "success": rms < 50.0,
            "bore_length_mm": best_bore_length,
            "bore_radii": best_radii.tolist(),
            "hole_positions": self.hole_positions,
            "hole_diameters": self.hole_diameters,
            "hole_lengths": self.hole_lengths,
            "final_rms_cents": rms,
            "peak_error_cents": peak,
            "wall_time": wall_time,
            "matched_frequencies": [
                {"target": t, "actual": a, "error_cents": c}
                for t, a, c in zip(self.target_freqs, freqs, cents_errors)
            ],
        }

    @property
    def bore_radius_init(self):
        return self.bore_radius if hasattr(self, 'bore_radius') else 7.25


# ============================================================================
# Demo
# ============================================================================

if __name__ == "__main__":
    print("Sequential + Corrected Optimizer Demo")
    print("=" * 50)

    # Chalumeau in C: diatonic major scale
    targets = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]  # C4 D4 E4 F4 G4 A4
    names = ["C4", "D4", "E4", "F4", "G4", "A4"]

    print(f"\nChalumeau in C: {', '.join(names)}")
    print(f"Targets: {', '.join(f'{t:.1f}' for t in targets)}")

    # Sequential optimizer
    print("\n--- Sequential Optimizer ---")
    seq = SequentialBoreOptimizer(
        target_frequencies=targets,
        fingering_sets=[
            ["closed"] * 6,  # C4: all closed
            ["open", "closed", "closed", "closed", "closed", "closed"],  # D4
            ["open", "open", "closed", "closed", "closed", "closed"],  # E4
            ["open", "open", "open", "closed", "closed", "closed"],  # F4
            ["open", "open", "open", "open", "closed", "closed"],  # G4
            ["open", "open", "open", "open", "open", "closed"],  # A4
        ],
        bore_radius=7.25,
        closed_top=True,
        hole_diameter=7.0,
    )
    result_seq = seq.run(verbose=True)
