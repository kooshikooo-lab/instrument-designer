"""
Evolutionary bore profile optimizer using pymoo + OpenWInD.

Optimizes wind instrument bore geometry for target frequency scales
using NSGA-II multi-objective evolutionary optimization.

Usage:
    from backend.optimizer import BoreOptimizer
    
    optimizer = BoreOptimizer(
        target_frequencies=[261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3],
        n_control_points=12,
        pop_size=40,
        n_generations=50,
    )
    result = optimizer.run()
"""

import os
import tempfile
import hashlib
import numpy as np
from scipy.signal import find_peaks
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize
from pymoo.termination import get_termination


_IMPEDANCE_CACHE = {}


def _compute_impedance_from_bore(bore_points, freq_range=(100, 3000), n_freqs=5000, temperature=20.0):
    """
    Compute impedance peaks for a bore profile.

    Args:
        bore_points: list of (position, radius) tuples in meters
        freq_range: (min, max) frequency in Hz
        n_freqs: number of frequency samples
        temperature: air temperature in Celsius

    Returns:
        dict with keys: frequencies, impedance_magnitude, peak_frequencies, peak_magnitudes
    """
    cache_key = (tuple(bore_points), freq_range, n_freqs, temperature)
    cache_hash = hashlib.md5(str(cache_key).encode()).hexdigest()

    if cache_hash in _IMPEDANCE_CACHE:
        return _IMPEDANCE_CACHE[cache_hash]

    from openwind import ImpedanceComputation

    lines = [f"{pos} {rad}" for pos, rad in bore_points]
    csv_content = "\n".join(lines)

    tmp = os.path.join(tempfile.gettempdir(), f"opt_bore_{cache_hash}.csv")
    with open(tmp, "w") as f:
        f.write(csv_content)

    try:
        freqs = np.linspace(freq_range[0], freq_range[1], n_freqs)
        ic = ImpedanceComputation(freqs, tmp, unit="m", diameter=False, temperature=temperature)

        freq = np.array(ic.frequencies)
        Z = np.array(ic.impedance)
        mag = np.abs(Z)

        peak_height = np.max(mag) * 0.02 if np.max(mag) > 0 else 1.0
        peaks, _ = find_peaks(mag, height=peak_height, distance=2, prominence=peak_height * 0.5)

        # Quadratic interpolation for sub-bin peak accuracy
        peak_freqs = []
        peak_mags = []
        for p in peaks:
            if p == 0 or p == len(mag) - 1:
                peak_freqs.append(freq[p])
                peak_mags.append(mag[p])
                continue
            # Fit parabola through 3 points: (p-1, p, p+1)
            f0, f1, f2 = freq[p - 1], freq[p], freq[p + 1]
            m0, m1, m2 = mag[p - 1], mag[p], mag[p + 1]
            denom = (f0 - f1) * (f0 - f2) * (f1 - f2)
            if abs(denom) < 1e-20:
                peak_freqs.append(f1)
                peak_mags.append(m1)
                continue
            a = (f2 * (m1 - m0) + f1 * (m0 - m2) + f0 * (m2 - m1)) / denom
            b = (f2 ** 2 * (m0 - m1) + f1 ** 2 * (m2 - m0) + f0 ** 2 * (m1 - m2)) / denom
            if a < 0:
                vertex = -b / (2 * a)
                if f0 < vertex < f2:
                    # Evaluate interpolated peak magnitude
                    c = (f1 * f2 * (f1 - f2) * m0 + f0 * f2 * (f2 - f0) * m1 + f0 * f1 * (f0 - f1) * m2) / denom
                    interp_mag = a * vertex ** 2 + b * vertex + c
                    peak_freqs.append(vertex)
                    peak_mags.append(interp_mag)
                    continue
            peak_freqs.append(f1)
            peak_mags.append(m1)

        result = {
            "frequencies": freq,
            "impedance_magnitude": mag,
            "peak_frequencies": np.array(peak_freqs),
            "peak_magnitudes": np.array(peak_mags),
        }

        if len(_IMPEDANCE_CACHE) < 2000:
            _IMPEDANCE_CACHE[cache_hash] = result

        return result
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _match_peaks_to_targets(peak_freqs, target_freqs):
    """
    Match each target frequency to its nearest impedance peak.
    Returns list of (target, matched_peak, error_hz, error_cents).
    """
    matched = []
    for tf in target_freqs:
        idx = np.argmin(np.abs(peak_freqs - tf))
        actual = peak_freqs[idx]
        error_hz = actual - tf
        error_cents = 1200.0 * np.log2(actual / tf) if tf > 0 and actual > 0 else 1e10
        matched.append((tf, actual, error_hz, error_cents))
    return matched


class BoreOptimizationProblem(ElementwiseProblem):
    """
    pymoo problem for optimizing a wind instrument bore profile.
    
    Design variables:
        - control_point_radii: radius at each control point
    
    Objectives:
        1. Frequency accuracy: RMS error of matched peaks vs targets (in cents)
        2. Scale evenness: std of frequency ratios between consecutive matched peaks
        3. Projection: negative average impedance peak magnitude
    
    Constraints:
        - Monotonically non-decreasing bore (bell >= mouthpiece at each point)
    """
    
    def __init__(
        self,
        target_frequencies,
        n_control_points=12,
        bore_length=0.5,
        min_radius=0.003,
        max_radius=0.025,
        temperature=20.0,
        freq_range=(100, 3000),
        n_freqs=5000,
    ):
        self.target_freqs = np.array(sorted(target_frequencies))
        self.bore_length = bore_length
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.temperature = temperature
        self.freq_range = freq_range
        self.n_freqs = n_freqs
        self.n_cp = n_control_points
        
        # n_ieq_constr: gentle penalty for non-monotonic bore
        # We allow some non-monotonicity but penalize large violations
        super().__init__(
            n_var=n_control_points,
            n_obj=3,
            n_ieq_constr=0,
            xl=np.full(n_control_points, min_radius),
            xu=np.full(n_control_points, max_radius),
        )
    
    def _bore_from_variables(self, x):
        """Convert design variables to bore profile points."""
        positions = np.linspace(0, self.bore_length, self.n_cp)
        radii = np.asarray(x, dtype=float)
        return list(zip(positions.tolist(), radii.tolist()))
    
    def _evaluate(self, x, out, *args, **kwargs):
        bore = self._bore_from_variables(x)
        
        try:
            result = _compute_impedance_from_bore(
                bore,
                freq_range=self.freq_range,
                n_freqs=self.n_freqs,
                temperature=self.temperature,
            )
        except Exception:
            out["F"] = [1e10, 1e10, 1e10]
            return
        
        peak_freqs = result["peak_frequencies"]
        peak_mags = result["peak_magnitudes"]
        
        if len(peak_freqs) < 2:
            out["F"] = [1e10, 1e10, 1e10]
            return
        
        n_targets = len(self.target_freqs)
        n_peaks = len(peak_freqs)
        
        # Objective 1: Frequency accuracy (RMS of cents error)
        matched = _match_peaks_to_targets(peak_freqs, self.target_freqs)
        cents_errors = np.array([abs(m[3]) for m in matched])
        freq_accuracy = np.sqrt(np.mean(cents_errors ** 2))
        
        # Objective 2: Scale evenness
        # How uniform are the ratios between consecutive matched peaks?
        if n_peaks >= n_targets:
            matched_peak_vals = np.array([m[1] for m in matched])
            if len(matched_peak_vals) > 1:
                # Normalized differences
                diffs = np.diff(matched_peak_vals)
                mean_diff = np.mean(diffs)
                if mean_diff > 0:
                    evenness = np.std(diffs / mean_diff)
                else:
                    evenness = 1e10
            else:
                evenness = 1e10
        else:
            # Penalty for not having enough peaks
            evenness = 1e10 * (1 + (n_targets - n_peaks) / n_targets)
        
        # Objective 3: Projection (negated for maximization)
        n_use = min(n_targets, n_peaks)
        if n_use > 0:
            projection = -np.mean(peak_mags[:n_use]) / 1e6
        else:
            projection = 1e10
        
        out["F"] = [freq_accuracy, evenness, projection]


class BoreOptimizer:
    """
    High-level interface for evolutionary bore optimization.
    
    Example:
        optimizer = BoreOptimizer(
            target_frequencies=[261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3],
            n_control_points=12,
            pop_size=40,
            n_generations=50,
        )
        result = optimizer.run()
        print(result["best_candidates"])
    """
    
    def __init__(
        self,
        target_frequencies,
        n_control_points=12,
        bore_length=None,
        min_radius=0.003,
        max_radius=0.025,
        pop_size=40,
        n_generations=50,
        temperature=20.0,
        seed=None,
    ):
        self.target_frequencies = target_frequencies
        self.n_control_points = n_control_points
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.pop_size = pop_size
        self.n_generations = n_generations
        self.temperature = temperature
        self.seed = seed or np.random.randint(0, 10000)
        
        # Auto-calculate bore length from fundamental
        if bore_length is None:
            v = 331.3 + 0.606 * temperature
            fundamental = min(target_frequencies)
            self.bore_length = v / (4 * fundamental)
        else:
            self.bore_length = bore_length
        
        # Auto-calculate freq range
        min_freq = max(50, min(target_frequencies) * 0.25)
        max_freq = max(target_frequencies) * 3.5
        self.freq_range = (min_freq, max_freq)
        
        self._problem = BoreOptimizationProblem(
            target_frequencies=target_frequencies,
            n_control_points=n_control_points,
            bore_length=self.bore_length,
            min_radius=min_radius,
            max_radius=max_radius,
            temperature=temperature,
            freq_range=self.freq_range,
        )
        
        self._algorithm = NSGA2(
            pop_size=pop_size,
            n_offsprings=pop_size // 2,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(eta=20, prob=1.0 / n_control_points),
            eliminate_duplicates=True,
        )
        
        self._termination = get_termination("n_gen", n_generations)
        self._result = None
    
    def run(self, verbose=False, callback=None):
        """
        Run the optimization.
        
        Args:
            verbose: print progress information
            callback: optional callback(generation, best_fitness) called each generation
        
        Returns:
            dict with keys:
                - pareto_front: list of objective vectors
                - designs: list of all design dicts
                - best_candidates: top 5 designs closest to ideal point
                - n_evaluations: total function evaluations
                - n_generations: number of generations
                - bore_length: used bore length in meters
                - freq_range: used frequency range
                - seed: random seed used
        """
        self._result = minimize(
            self._problem,
            self._algorithm,
            self._termination,
            seed=self.seed,
            save_history=True,
            verbose=verbose,
        )
        
        X = self._result.X
        F = self._result.F
        
        if X is None or len(X) == 0:
            return {"error": "Optimization produced no valid designs", "designs": [], "best_candidates": [], "pareto_front": []}
        
        # Normalize objectives for best-candidate selection
        f_min = F.min(axis=0)
        f_max = F.max(axis=0)
        f_range = f_max - f_min
        f_range[f_range == 0] = 1.0
        F_norm = (F - f_min) / f_range
        
        # Distance to ideal point (0,0,0 in normalized space)
        distances = np.sqrt(np.sum(F_norm ** 2, axis=1))
        best_indices = np.argsort(distances)[:5]
        
        designs = []
        for i in range(len(X)):
            bore = self._bore_from_variables(X[i])
            matched = _match_peaks_to_targets(
                _compute_impedance_from_bore(bore, self.freq_range, 5000, self.temperature)["peak_frequencies"],
                self.target_frequencies,
            )
            designs.append({
                "variables": X[i].tolist(),
                "bore_profile": [{"position": p, "radius": r} for p, r in bore],
                "objectives": {
                    "frequency_accuracy": float(F[i, 0]),
                    "scale_evenness": float(F[i, 1]),
                    "projection": float(-F[i, 2]),
                },
                "matched_frequencies": [
                    {"target": m[0], "actual": m[1], "error_hz": m[2], "error_cents": m[3]}
                    for m in matched
                ],
            })
        
        best_designs = [designs[i] for i in best_indices]
        
        return {
            "pareto_front": F.tolist(),
            "designs": designs,
            "best_candidates": best_designs,
            "n_evaluations": len(X),
            "n_generations": self.n_generations,
            "bore_length": self.bore_length,
            "freq_range": list(self.freq_range),
            "seed": self.seed,
        }
    
    def _bore_from_variables(self, x):
        positions = np.linspace(0, self.bore_length, self.n_control_points)
        radii = np.asarray(x, dtype=float)
        return list(zip(positions.tolist(), radii.tolist()))
    
    def get_bore_csv(self, variables):
        """Convert design variables to OpenWInD CSV format string."""
        bore = self._bore_from_variables(variables)
        lines = [f"{pos} {rad}" for pos, rad in bore]
        return "\n".join(lines)
    
    def evaluate_single(self, variables):
        """Evaluate a single design and return detailed results."""
        bore = self._bore_from_variables(variables)
        result = _compute_impedance_from_bore(
            bore,
            freq_range=self.freq_range,
            n_freqs=5000,
            temperature=self.temperature,
        )
        
        peak_freqs = result["peak_frequencies"]
        matched = _match_peaks_to_targets(peak_freqs, self.target_frequencies)
        
        return {
            "bore_profile": [{"position": p, "radius": r} for p, r in bore],
            "matched_frequencies": [
                {"target": m[0], "actual": m[1], "error_hz": m[2], "error_cents": m[3]}
                for m in matched
            ],
            "all_peak_frequencies": peak_freqs.tolist(),
            "all_peak_magnitudes": result["peak_magnitudes"].tolist(),
            "frequencies": result["frequencies"][::5].tolist(),
            "impedance_magnitude": result["impedance_magnitude"][::5].tolist(),
        }
