"""Global fingering-chart optimizer for clarinet.

Instead of sequential hole placement (Bordeaux method), this optimizer:
1. Takes a complete fingering chart (N notes × M holes binary matrix)
2. Optimizes ALL hole positions simultaneously using differential evolution
3. Objective = weighted RMS of cents error across ALL fingerings

This matches the modern approach described by Debut, Kergomard, Dalmont et al.
"""
import math, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
from typing import List, Tuple

try:
    from .tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND


class GlobalFingeringOptimizer:
    """Optimize all hole positions simultaneously over a complete fingering chart."""

    def __init__(
        self,
        targets_hz: List[float],
        fingering_chart: List[List[str]],
        bore_radius: float = 12.5,
        outer_diameter: float = 37.0,
        hole_diameter: float = 11.0,
        hole_length: float = 5.0,
        closed_top: bool = True,
        n_register: int = 2,
        bore_length: float = None,
        n_bore_cp: int = 0,
        fixed_holes: List[Tuple[float, float, float]] = None,
        hole_diameters: List[float] = None,
        hole_lengths: List[float] = None,
        register_weights: Tuple[float, float] = (0.15, 1.0),
    ):
        """
        Args:
            targets_hz: target frequencies for each fingering (1st register)
            fingering_chart: list of [N x M] binary states ("open"/"closed") 
            bore_radius: uniform bore radius in mm
            outer_diameter: instrument outer diameter in mm
            hole_diameter: tonehole diameter in mm (uniform, used if hole_diameters not given)
            hole_length: tonehole chimney height in mm (uniform, used if hole_lengths not given)
            closed_top: True for clarinets
            n_register: primary register to optimize for (default 2 = 2nd register)
            bore_length: fixed bore length (None = auto from fundamental)
            n_bore_cp: bore control points (0 = uniform)
            fixed_holes: list of (position, diameter, length) for holes NOT being optimized
            hole_diameters: per-hole diameters (one per free hole, overrides hole_diameter)
            hole_lengths: per-hole chimney heights (one per free hole, overrides hole_length)
            register_weights: (w1, w2) weights for 1st/2nd register in cost function
                              default (0.15, 1.0): 2nd register dominates
        """
        self.targets = targets_hz
        self.fingering_chart = fingering_chart
        self.n_notes = len(targets_hz)
        self.n_holes = len(fingering_chart[0])
        self.n_free_holes = self.n_holes - len(fixed_holes or [])
        self.bore_radius = bore_radius
        self.outer_diameter = outer_diameter
        self.hole_diameter = hole_diameter
        self.hole_length = hole_length
        self.hole_diameters = hole_diameters
        self.hole_lengths = hole_lengths
        self.closed_top = closed_top
        self.n_register = n_register
        self.n_bore_cp = n_bore_cp
        self.fixed_holes = fixed_holes or []
        self.register_weights = register_weights
        self.targets_2nd = [f * 3.0 for f in targets_hz]  # 3rd harmonic
        
        self.n_fixed = len(self.fixed_holes)
        
        if bore_length is None:
            c = SPEED_OF_SOUND
            self.bore_length = c / (4 * targets_hz[0]) if closed_top else c / (2 * targets_hz[0])
        else:
            self.bore_length = bore_length
    
    def _evaluate(self, free_positions, verbose=False, return_both=False):
        """Evaluate weighted RMS cents error across both registers.
        
        The primary objective is 2nd register (3rd harmonic) where holes are effective.
        1st register acts as a regularizer with smaller weight.
        
        free_positions: positions of the free (variable) holes, sorted
        return_both: if True, return (rms_1st, rms_2nd, combined)
        Returns: combined cost (or tuple if return_both)
        """
        all_pos = sorted(list(free_positions) + [h[0] for h in self.fixed_holes])
        if self.hole_diameters:
            free_dias = list(self.hole_diameters[:len(free_positions)])
        else:
            free_dias = [self.hole_diameter] * len(free_positions)
        if self.hole_lengths:
            free_lens = list(self.hole_lengths[:len(free_positions)])
        else:
            free_lens = [self.hole_length] * len(free_positions)
        all_dia = free_dias + [h[1] for h in self.fixed_holes]
        all_len = free_lens + [h[2] for h in self.fixed_holes]
        
        idx = np.argsort(all_pos)
        all_pos_s = [all_pos[i] for i in idx]
        all_dia_s = [all_dia[i] for i in idx]
        all_len_s = [all_len[i] for i in idx]
        
        free_count = len(free_positions)
        
        radii = np.full(10 if self.n_bore_cp == 0 else self.n_bore_cp, self.bore_radius)
        
        try:
            inst = tmm_instrument_from_radii(
                radii, self.bore_length, all_pos_s, all_dia_s, all_len_s,
                self.outer_diameter, closed_top=self.closed_top, cone_step=0.5,
            )
        except:
            return (1e10, 1e10, 1e10) if return_both else 1e10
        
        cents_1st = []
        cents_2nd = []
        
        for note_idx in range(self.n_notes):
            chart_row = self.fingering_chart[note_idx]
            fingering = []
            free_idx = 0
            for pos in all_pos_s:
                if pos in [h[0] for h in self.fixed_holes]:
                    fh_idx = [h[0] for h in self.fixed_holes].index(pos)
                    fingering.append(chart_row[free_count + fh_idx])
                else:
                    fingering.append(chart_row[free_idx])
                    free_idx += 1
            
            try:
                for reg, cents_arr, targets in [
                    (1, cents_1st, self.targets),
                    (2, cents_2nd, self.targets_2nd),
                ]:
                    wl = inst.find_resonance(SPEED_OF_SOUND / targets[note_idx],
                                             fingering, reg)
                    actual = inst.frequency_from_wavelength(wl)
                    if actual > 0 and math.isfinite(actual):
                        cents_arr.append(1200.0 * math.log2(actual / targets[note_idx]))
                    else:
                        cents_arr.append(1e6)
            except:
                cents_1st.append(1e6)
                cents_2nd.append(1e6)
        
        c1 = np.array(cents_1st)
        c2 = np.array(cents_2nd)
        
        if np.any(np.abs(c1) > 1e5) or np.any(np.abs(c2) > 1e5):
            return (1e10, 1e10, 1e10) if return_both else 1e10
        
        offset_1 = np.median(c1)
        offset_2 = np.median(c2)
        rms_1 = float(np.sqrt(np.mean((c1 - offset_1) ** 2)))
        rms_2 = float(np.sqrt(np.mean((c2 - offset_2) ** 2)))
        
        w1, w2 = self.register_weights
        combined = w1 * rms_1 + w2 * rms_2
        
        if verbose:
            print(f"  Reg1: RMS={rms_1:.2f}c offset={offset_1:+.0f}c (w={w1})")
            print(f"  Reg2: RMS={rms_2:.2f}c offset={offset_2:+.0f}c (w={w2})")
            print(f"  Combined: {combined:.4f}")
        
        if return_both:
            return rms_1, rms_2, combined
        return combined
    
    def _objective(self, x):
        """Objective for DE: x = hole positions (unsorted)."""
        if hasattr(x, 'tolist'):
            x = x.tolist()
        free_pos = sorted(x)
        return self._evaluate(free_pos)
    
    def optimize(self, initial_positions=None, bounds_per_hole=40, verbose=True, use_de=True):
        """Run global optimization.
        
        Args:
            initial_positions: starting guess for free hole positions
            bounds_per_hole: ±mm range for each hole around initial guess
            use_de: use Differential Evolution phase (default True)
            
        Returns:
            dict of results
        """
        t0 = time.time()
        n_free = self.n_free_holes
        GAP = 8
        
        if initial_positions is None:
            initial_positions = [
                i * self.bore_length / (n_free + 1) 
                for i in range(1, n_free + 1)
            ]
        else:
            initial_positions = sorted(initial_positions[:n_free])
        
        if verbose:
            print(f"  GlobalFingeringOptimizer")
            print(f"  Notes: {self.n_notes}, Free holes: {n_free}, Fixed holes: {self.n_fixed}")
            print(f"  Bore: {self.bore_length:.0f}mm × {self.bore_radius}mm radius")
            print(f"  Initial: {[f'{p:.0f}' for p in initial_positions]}")
            print(f"  Register: {self.n_register}")
            print()
        
        if use_de:
            # Build bounds for DE
            bounds = []
            for i in range(n_free):
                lo = max(GAP, initial_positions[i] - bounds_per_hole)
                if i > 0:
                    lo = max(lo, bounds[-1][0] + GAP)
                hi = min(self.bore_length - GAP, initial_positions[i] + bounds_per_hole)
                if i < n_free - 1:
                    hi = min(hi, initial_positions[i+1] + bounds_per_hole - GAP)
                if lo >= hi:
                    lo, hi = hi - 10, hi + 10
                bounds.append((lo, hi))
            
            if verbose:
                print(f"  Bounds: {bounds}")
                print(f"  Phase 1: Differential Evolution ({max(20, n_free*2)} iter)")
            
            popsize = max(8, n_free * 2)
            de_result = differential_evolution(
                self._objective, bounds,
                seed=42,
                maxiter=min(30, max(10, n_free*2)), popsize=popsize,
                tol=1e-4, mutation=(0.5, 1.0), recombination=0.7,
                polish=True,
            )
            best_pos = sorted(de_result.x.tolist())
            best_cost = de_result.fun
            if verbose:
                print(f"    DE: cost={best_cost:.4f}")
                print(f"    Holes: {[f'{p:.0f}' for p in best_pos]}")
        else:
            best_pos = initial_positions
            best_cost = self._objective(best_pos)
            if verbose:
                print(f"    (skipping DE, initial cost={best_cost:.4f})")
        
        # Phase 2: L-BFGS-B refinement
        if verbose:
            print(f"  Phase 2: L-BFGS-B refinement")
        
        def make_refine_bounds(holes):
            ref_bounds = []
            for i in range(n_free):
                lo = GAP if i == 0 else holes[i-1] + GAP
                lo = max(lo, holes[i] - 10)
                hi = self.bore_length - GAP if i == n_free-1 else holes[i+1] - GAP
                hi = min(hi, holes[i] + 10)
                if lo >= hi: lo, hi = hi-5, hi+5
                ref_bounds.append((lo, hi))
            return ref_bounds
        
        ref_bounds = make_refine_bounds(best_pos)
        r = minimize(self._objective, np.array(best_pos), method='L-BFGS-B',
                     bounds=ref_bounds, options={"maxiter": 200, "ftol": 1e-8})
        best_pos = sorted(r.x.tolist())
        best_cost = r.fun
        
        if verbose:
            print(f"    L-BFGS-B: cost={best_cost:.4f}")
            print(f"    Holes: {[f'{p:.0f}' for p in best_pos]}")
        
        # Final eval with verbose
        if verbose:
            print(f"\n  Final evaluation:")
        r1, r2, combined = self._evaluate(best_pos, verbose=verbose, return_both=True)
        
        dt = time.time() - t0
        
        return {
            "success": combined < 50.0,
            "bore_length_mm": self.bore_length,
            "free_hole_positions": best_pos,
            "final_rms_1st_cents": r1,
            "final_rms_2nd_cents": r2,
            "final_rms_cents": combined,
            "wall_time": dt,
        }


# ======================================================================
# Demo: 2nd-register optimization for chromatic clarinet
# ======================================================================
if __name__ == "__main__":
    print("="*60)
    print("GLOBAL FINGERING OPTIMIZER — 2nd Register Optimization")
    print("="*60)
    
    FIXED_REGISTER = [(80.0, 2.5, 3.0)]
    
    # Diatonic: 7-hole D major (proven working case for 2nd register)
    N_FREE = 7
    N_FIXED = 1
    
    targets = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
    names = ["D2","E2","F#2","G2","A2","B2","C#3","D3"]
    
    chart = []
    for i in range(8):
        row = ["closed"] * (N_FREE + N_FIXED)
        for j in range(i):
            row[j] = "open"
        row[N_FREE] = "closed"
        chart.append(row)
    
    print(f"\n  Fingerings: {len(chart)} notes")
    print(f"  Primary: 2nd register (3rd harmonic @ 220-440Hz)")
    print(f"  Regularizer: 1st register (fundamental @ 73-147Hz)")
    print(f"  Weights (1st, 2nd): (0.15, 1.0)")
    
    opt = GlobalFingeringOptimizer(
        targets_hz=targets,
        fingering_chart=chart,
        bore_radius=12.5,
        outer_diameter=37.0,
        hole_diameter=11.0,
        hole_length=5.0,
        closed_top=True,
        n_register=2,
        bore_length=1211.3,
        fixed_holes=FIXED_REGISTER,
        register_weights=(0.15, 1.0),
    )
    
    result = opt.optimize(initial_positions=[180, 300, 346, 455, 545, 624, 652], 
                          bounds_per_hole=80, verbose=True)
    print(f"\n  Result:")
    print(f"    Reg1 RMS={result['final_rms_1st_cents']:.2f}c")
    print(f"    Reg2 RMS={result['final_rms_2nd_cents']:.2f}c")
    print(f"    Combined={result['final_rms_cents']:.2f}")
    print(f"    Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
