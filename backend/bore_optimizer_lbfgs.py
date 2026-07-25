"""
L-BFGS-B bore optimizer with two-phase strategy.

Based on research findings:
- Noreland 2013: gradient-based (Levenberg-Marquardt) achieves <5 cents
- Ernoult 2020: SQP + adjoint gradients achieves sub-cent
- Every successful instrument optimizer uses gradient-based methods
- Two-phase is critical: Noreland says "little success omitting Phase 1"

Phase 1: Frequency accuracy only (simple, smooth objective)
Phase 2: Weighted sum (frequency + evenness + projection + smoothness penalty)

Usage:
    from backend.bore_optimizer_lbfgs import LBFGSBoreOptimizer

    opt = LBFGSBoreOptimizer(
        target_frequencies=[261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6],
        bore_length=0.66,
    )
    result = opt.run(verbose=True)
"""

import os
import time
import hashlib
import tempfile
import numpy as np
from scipy.optimize import minimize, differential_evolution
from scipy.signal import find_peaks

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")


def _pava_isotonic(x):
    """Find closest monotonically non-decreasing sequence via PAVA. O(n)."""
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


def _compute_impedance(bore_points, freq_range=(50, 3000), n_freqs=5000, temperature=20.0):
    """Compute impedance peaks for a bore profile. Returns peak_freqs, peak_mags."""
    from .mp_cache import cache_get, cache_set

    cache_key = (tuple(round(x, 12) for pt in bore_points for x in pt), freq_range, n_freqs, temperature)
    cache_hash = hashlib.md5(repr(cache_key).encode()).hexdigest()
    cached = cache_get(cache_hash)
    if cached is not None:
        return np.asarray(cached["peak_frequencies"]), np.asarray(cached["peak_magnitudes"])

    from openwind import ImpedanceComputation

    lines = [f"{pos} {rad}" for pos, rad in bore_points]
    csv_content = "\n".join(lines)
    tmp = os.path.join(tempfile.gettempdir(), f"lbfgs_bore_{cache_hash}.csv")
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

        peak_freqs = []
        peak_mags = []
        for p in peaks:
            if p == 0 or p == len(mag) - 1:
                peak_freqs.append(freq[p])
                peak_mags.append(mag[p])
                continue
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
        cache_set(cache_hash, result)
        return np.array(peak_freqs), np.array(peak_mags)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _match_peaks(peak_freqs, target_freqs):
    """Match each target to nearest peak. Returns (target, actual, error_hz, error_cents) list."""
    matched = []
    for tf in target_freqs:
        idx = np.argmin(np.abs(peak_freqs - tf))
        actual = peak_freqs[idx]
        error_cents = 1200.0 * np.log2(actual / tf) if tf > 0 and actual > 0 else 1e10
        matched.append((tf, actual, actual - tf, error_cents))
    return matched


class LBFGSBoreOptimizer:
    """
    L-BFGS-B bore optimizer with two-phase strategy.
    
    Phase 1: Frequency accuracy only (RMS cents error)
    Phase 2: Weighted sum of (frequency + evenness + projection + smoothness)
    
    Uses PAVA repair after each gradient step to enforce monotonicity.
    """

    def __init__(
        self,
        target_frequencies,
        n_control_points=12,
        bore_length=None,
        min_radius=0.003,
        max_radius=0.025,
        temperature=20.0,
        freq_range=None,
        n_freqs=5000,
        seed=42,
        # Phase 2 weights
        weight_evenness=0.3,
        weight_projection=0.1,
        weight_smoothness=10.0,
    ):
        self.target_freqs = np.array(sorted(target_frequencies))
        self.n_cp = n_control_points
        self.min_r = min_radius
        self.max_r = max_radius
        self.temperature = temperature
        self.n_freqs = n_freqs
        self.seed = seed
        self.weight_evenness = weight_evenness
        self.weight_projection = weight_projection
        self.weight_smoothness = weight_smoothness

        if bore_length is None:
            v = 331.3 + 0.606 * temperature
            fundamental = min(target_frequencies)
            self.bore_length = v / (4 * fundamental)
        else:
            self.bore_length = bore_length

        if freq_range is None:
            min_freq = max(50, min(target_frequencies) * 0.25)
            max_freq = max(target_frequencies) * 3.5
            self.freq_range = (min_freq, max_freq)
        else:
            self.freq_range = freq_range

        self.bounds = [(min_radius, max_radius)] * n_control_points

    def _radii_to_bore(self, radii):
        """Convert radius array to bore_points list."""
        positions = np.linspace(0, self.bore_length, len(radii))
        return list(zip(positions.tolist(), radii.tolist()))

    def _compute_freq_rms(self, radii):
        """Phase 1 objective: RMS cents error after global offset removal."""
        bore = self._radii_to_bore(radii)
        peak_freqs, _ = _compute_impedance(bore, self.freq_range, self.n_freqs, self.temperature)
        if len(peak_freqs) < 2:
            return 1e10

        matched = _match_peaks(peak_freqs, self.target_freqs)
        raw_cents = np.array([abs(m[3]) for m in matched])
        # Global offset removal
        offset = np.median(np.array([m[3] for m in matched]))
        corrected = np.abs(np.array([m[3] for m in matched]) - offset)
        return float(np.sqrt(np.mean(corrected ** 2)))

    def _compute_full_objective(self, radii):
        """Phase 2 objective: weighted sum of all quality metrics."""
        bore = self._radii_to_bore(radii)
        peak_freqs, peak_mags = _compute_impedance(bore, self.freq_range, self.n_freqs, self.temperature)
        if len(peak_freqs) < 2:
            return 1e10

        matched = _match_peaks(peak_freqs, self.target_freqs)
        raw_cents = np.array([m[3] for m in matched])
        offset = np.median(raw_cents)
        corrected = np.abs(raw_cents - offset)
        freq_rms = float(np.sqrt(np.mean(corrected ** 2)))

        # Evenness: std of matched peak magnitude ratios
        n_use = min(len(self.target_freqs), len(peak_freqs))
        if n_use > 1:
            matched_mags = np.array([m[1] for m in matched[:n_use]])
            diffs = np.diff(matched_mags)
            mean_diff = np.mean(diffs)
            evenness = float(np.std(diffs / mean_diff)) if mean_diff > 1e-6 else 10.0
        else:
            evenness = 10.0

        # Projection: average peak magnitude (higher is better)
        projection = float(-np.mean(peak_mags[:n_use]) / 1e6) if n_use > 0 else 10.0

        # Smoothness: penalize large jumps
        jumps = np.abs(np.diff(radii))
        smoothness = float(np.sum(np.maximum(0, jumps - (self.max_r - self.min_r) * 0.1)))

        return freq_rms + self.weight_evenness * evenness + self.weight_projection * projection + self.weight_smoothness * smoothness

    def _initial_guess(self):
        """Generate initial guess: monotonic bore from low-frequency approximation."""
        # For closed-open pipe: bore radius ~ constant near target
        # Use a slight taper from mouthpiece to bell
        radii = np.linspace(self.min_r + 0.002, self.max_r * 0.6, self.n_cp)
        return _pava_isotonic(radii)

    def _callback(self, xk):
        """Print progress during optimization."""
        pass  # Could add verbose callback here

    def run(self, verbose=True, phase2=True):
        """
        Run two-phase L-BFGS-B optimization.
        
        Phase 1: Frequency accuracy only
        Phase 2: Full weighted objective (optional)
        
        Returns dict with results.
        """
        np.random.seed(self.seed)
        x0 = self._initial_guess()

        if verbose:
            print(f"  L-BFGS-B Two-Phase Optimizer")
            print(f"  Bore length: {self.bore_length*1000:.0f}mm")
            print(f"  Control points: {self.n_cp}")
            print(f"  Targets: {self.target_freqs.tolist()}")
            print(f"  Bounds: [{self.min_r*1000:.1f}, {self.max_r*1000:.1f}]mm")
            print()

        # ─── Phase 1: Frequency accuracy only ───
        t0 = time.time()
        if verbose:
            print("  Phase 1: Frequency accuracy only...")

        n_evals_p1 = [0]

        def p1_objective(x):
            n_evals_p1[0] += 1
            radii = _pava_isotonic(np.clip(x, self.min_r, self.max_r))
            return self._compute_freq_rms(radii)

        result1 = minimize(
            p1_objective, x0, method='L-BFGS-B',
            jac='2-point',
            bounds=self.bounds,
            options={'maxiter': 200, 'ftol': 1e-12, 'gtol': 1e-8},
        )
        t1 = time.time()
        if verbose:
            print(f"  Phase 1 done: {n_evals_p1[0]} evals, {t1-t0:.1f}s")
            print(f"  Phase 1 RMS: {result1.fun:.4f} cents")

        # ─── Phase 2: Full weighted objective ───
        if phase2:
            if verbose:
                print()
                print("  Phase 2: Full weighted objective...")

            n_evals_p2 = [0]

            def p2_objective(x):
                n_evals_p2[0] += 1
                radii = _pava_isotonic(np.clip(x, self.min_r, self.max_r))
                return self._compute_full_objective(radii)

            result2 = minimize(
                p2_objective, result1.x, method='L-BFGS-B',
                jac='2-point',
                bounds=self.bounds,
                options={'maxiter': 300, 'ftol': 1e-12, 'gtol': 1e-8},
            )
            t2 = time.time()
            best_x = result2.x
            best_val = result2.fun
            total_evals = n_evals_p1[0] + n_evals_p2[0]
            total_time = t2 - t0
        else:
            best_x = result1.x
            best_val = result1.fun
            total_evals = n_evals_p1[0]
            total_time = t1 - t0

        # Enforce monotonicity on final result
        best_radii = _pava_isotonic(np.clip(best_x, self.min_r, self.max_r))

        # Final evaluation
        bore = self._radii_to_bore(best_radii)
        peak_freqs, peak_mags = _compute_impedance(bore, self.freq_range, self.n_freqs, self.temperature)
        matched = _match_peaks(peak_freqs, self.target_freqs)

        raw_cents = np.array([m[3] for m in matched])
        offset = np.median(raw_cents)
        corrected = np.abs(raw_cents - offset)
        final_rms = float(np.sqrt(np.mean(corrected ** 2)))

        if verbose:
            print()
            print(f"  {'='*60}")
            print(f"  RESULTS")
            print(f"  {'='*60}")
            print(f"  Total evals: {total_evals}")
            print(f"  Wall time: {total_time:.1f}s")
            print(f"  Final RMS: {final_rms:.4f} cents")
            print(f"  Global offset: {offset:+.1f} cents")
            print()
            print(f"  {'Target':>8s}  {'Actual':>8s}  {'Error':>8s}  {'Status'}")
            print(f"  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}")
            for tf, actual, _, ec in matched:
                corrected_ec = ec - offset
                status = "OK" if abs(corrected_ec) < 5 else "WARN" if abs(corrected_ec) < 20 else "FAIL"
                print(f"  {tf:8.1f}  {actual:8.1f}  {ec:+8.1f}  {status}")
            print()
            print(f"  Bore: {self.bore_length*1000:.0f}mm, entry={best_radii[0]*1000:.2f}mm, exit={best_radii[-1]*1000:.2f}mm")

        return {
            "rms_cents": final_rms,
            "global_offset": offset,
            "matched_frequencies": [(m[0], m[1], m[3]) for m in matched],
            "bore_profile": [(float(p), float(r)) for p, r in zip(
                np.linspace(0, self.bore_length, len(best_radii)), best_radii
            )],
            "n_evaluations": total_evals,
            "wall_time": total_time,
            "phase1_result": result1.fun if phase2 else None,
            "variables": best_radii.tolist(),
        }


def main():
    """Quick test on Bb clarinet."""
    targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]

    print("="*60)
    print("  L-BFGS-B TWO-PHASE OPTIMIZER TEST")
    print("  Bb Clarinet (odd harmonics)")
    print("="*60)

    opt = LBFGSBoreOptimizer(
        targets,
        n_control_points=12,
        bore_length=0.66,
        min_radius=0.005,
        max_radius=0.020,
        seed=42,
    )
    result = opt.run(verbose=True, phase2=True)

    print()
    print(f"  FINAL: {result['rms_cents']:.4f} cents RMS in {result['wall_time']:.1f}s")


if __name__ == "__main__":
    main()
