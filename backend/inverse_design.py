"""
Inverse design: sound → instrument design.

Three-tier architecture:
  Tier 1 — Sound analysis: extract fundamental, harmonic frequencies, envelope
  Tier 2 — Scale optimization: bore length + hole positions (via existing NSGA-II)
  Tier 3 — Timbre matching: optimize bore RADII to match the harmonic amplitude
           envelope from the source sound (impedance peak magnitudes)

The three tiers are exposed as separate functions and as a combined pipeline,
allowing the UI to show intermediate results and let the user tune parameters.

Usage:
    from backend.inverse_design import (
        analyze_wav,                # Tier 1
        design_scale,               # Tier 2 (delegates to agent)
        match_timbre,               # Tier 3
        design_from_sound,          # all three tiers
    )
    analysis = analyze_wav("recording.wav")
    result = design_from_sound("recording.wav")
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import scipy.signal
from scipy.io import wavfile

from backend.tmm_acoustics import TMMInstrument, SPEED_OF_SOUND
from backend.physics.losses import KeefeLoss

_c = SPEED_OF_SOUND  # 346100 mm/s

# ── Constants ────────────────────────────────────────────────────────────────
MIN_HARMONIC_RATIO = 0.05       # minimum peak amplitude (relative) as harmonic
HARMONIC_TOLERANCE = 0.03       # fractional tolerance for harmonic matching
MIN_FUNDAMENTAL_HZ = 30.0       # lowest playable fundamental
MAX_FUNDAMENTAL_HZ = 2000.0     # highest playable fundamental
N_TIER3_RADII = 6               # bore control points for timbre optimization


# =============================================================================
# Tier 1 — Sound analysis
# =============================================================================

def analyze_wav(filepath: str) -> dict:
    """Read a WAV file and extract spectral features.

    Returns dict with keys:
        sample_rate, duration_s,
        fundamental_hz, confidence,
        harmonic_frequencies, harmonic_amplitudes,    (peak values)
        spectrum_frequencies, spectrum_magnitudes,     (full FFT)
        envelope_frequencies, envelope_magnitudes      (smoothed spectral envelope)
    """
    sample_rate, samples = wavfile.read(filepath)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)

    duration = len(samples) / sample_rate
    result = {"sample_rate": sample_rate, "duration_s": duration}

    # Power spectrum via Welch's method
    freqs, mags = _power_spectrum(samples, sample_rate)
    result["spectrum_frequencies"] = freqs.tolist()
    result["spectrum_magnitudes"] = mags.tolist()

    # Smooth spectral envelope (moving maximum)
    envelope = _spectral_envelope(freqs, mags)
    result["envelope_frequencies"] = freqs.tolist()
    result["envelope_magnitudes"] = envelope.tolist()

    # Fundamental estimation via autocorrelation
    fundamental, confidence = _estimate_fundamental(samples, sample_rate)
    result["fundamental_hz"] = fundamental
    result["confidence"] = confidence

    # Extract harmonic peaks matched to fundamental
    peaks_f, peaks_m = _find_spectral_peaks(freqs, mags)
    harm_f, harm_m = _match_harmonics(peaks_f, peaks_m, fundamental)
    result["harmonic_frequencies"] = harm_f
    result["harmonic_amplitudes"] = harm_m

    return result


def _power_spectrum(samples: np.ndarray, sample_rate: int,
                    n_fft: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Compute power spectrum magnitude via Welch's method."""
    if n_fft is None:
        n_fft = 2 ** int(math.ceil(math.log2(len(samples))))
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)
    _, psd = scipy.signal.welch(samples, sample_rate,
                                nperseg=min(4096, len(samples)),
                                return_onesided=True)
    psd_interp = np.interp(freqs, np.linspace(0, sample_rate / 2, len(psd)), psd)
    return freqs, np.sqrt(psd_interp)


def _spectral_envelope(freqs: np.ndarray, mags: np.ndarray,
                        window_hz: float = 100.0) -> np.ndarray:
    """Smooth spectral envelope via running maximum filter."""
    window_bins = max(3, int(window_hz / (freqs[1] - freqs[0])) | 1)  # odd
    envelope = scipy.signal.order_filter(mags, np.ones(window_bins), window_bins - 1)
    # Smooth with 3-point moving average
    kernel = np.ones(3) / 3
    return np.convolve(envelope, kernel, mode="same")


def _estimate_fundamental(samples: np.ndarray,
                          sample_rate: int) -> tuple[float, float]:
    """Estimate fundamental via normalized autocorrelation."""
    sos = scipy.signal.butter(4, 2000, "lp", fs=sample_rate, output="sos")
    filtered = scipy.signal.sosfilt(sos, samples)

    n = len(filtered)
    corr = np.correlate(filtered, filtered, mode="full")
    corr = corr[n - 1:] / corr[n - 1]

    min_lag = int(sample_rate / MAX_FUNDAMENTAL_HZ)
    max_lag = int(sample_rate / MIN_FUNDAMENTAL_HZ)
    if max_lag >= len(corr):
        max_lag = len(corr) - 1

    search = corr[min_lag:max_lag + 1]
    if len(search) == 0:
        return 440.0, 0.0

    peak_idx = int(np.argmax(search)) + min_lag
    confidence = float(search[peak_idx - min_lag])
    if confidence < 0.1:
        return 440.0, confidence

    # Parabolic interpolation
    if peak_idx > 0 and peak_idx < len(corr) - 1:
        a, b, c2 = corr[peak_idx - 1], corr[peak_idx], corr[peak_idx + 1]
        if a + c2 - 2 * b != 0:
            delta = (a - c2) / (2 * (a + c2 - 2 * b))
            peak_idx += delta
    fundamental = sample_rate / peak_idx
    return float(fundamental), float(confidence)


def _find_spectral_peaks(freqs: np.ndarray, mags: np.ndarray
                         ) -> tuple[list[float], list[float]]:
    """Find significant peaks in the magnitude spectrum."""
    mag_max = mags.max()
    mags_n = mags / mag_max if mag_max > 0 else mags

    peaks, _ = scipy.signal.find_peaks(
        mags_n, height=MIN_HARMONIC_RATIO,
        distance=max(3, int(len(freqs) / 2000)),
        prominence=0.02,
    )
    return [float(freqs[p]) for p in peaks], [float(mags_n[p]) for p in peaks]


def _match_harmonics(peak_freqs: list[float], peak_mags: list[float],
                     fundamental: float) -> tuple[list[float], list[float]]:
    """Match spectral peaks to nearest harmonic of the fundamental."""
    if not peak_freqs or fundamental <= 0:
        return [], []
    matched = {}
    for f, m in zip(peak_freqs, peak_mags):
        hn = round(f / fundamental)
        if hn < 1:
            continue
        error = abs(f - hn * fundamental) / (hn * fundamental)
        if error < HARMONIC_TOLERANCE:
            if hn not in matched or m > matched[hn][1]:
                matched[hn] = (f, m)
    harmonics = sorted(matched.items())
    return [h[1][0] for h in harmonics], [h[1][1] for h in harmonics]


def validate_physical_series(frequencies: list[float],
                             fundamental: float) -> tuple[bool, str]:
    """Check if a set of frequencies forms a realizable harmonic series."""
    if len(frequencies) < 2:
        return False, "Need at least 2 harmonics"
    for f in frequencies:
        n = round(f / fundamental)
        if n < 1:
            continue
        error = abs(f - n * fundamental) / (n * fundamental)
        if error > HARMONIC_TOLERANCE * 2:
            return False, f"Peak at {f:.1f} Hz is {error*100:.1f}% from harmonic {n}"

    odd_strong = True
    for n in range(2, min(len(frequencies) * 2 + 1, 10)):
        if n % 2 == 0:
            expected_f = n * fundamental
            has_peak = any(abs(f - expected_f) / expected_f < HARMONIC_TOLERANCE
                           for f in frequencies)
            if has_peak:
                odd_strong = False
                break
    pipe_type = "closed-open" if odd_strong else "open-open"
    return True, f"Valid: {pipe_type}"


# =============================================================================
# Tier 2 — Scale optimization (delegates to generative agent)
# =============================================================================

def design_scale(fundamental_hz: float,
                 harmonic_frequencies: list[float] | None = None,
                 label: str = "",
                 hole_count: int = 6,
                 n_candidates: int = 2) -> dict:
    """Design an instrument whose scale is rooted at the given fundamental.

    Delegates to the generative agent's NSGA-II optimizer.  The result is a
    bore geometry with hole positions that play a 12-TET scale starting from
    the detected fundamental.

    Returns
    -------
    dict with keys from _result_to_dict plus "analysis".
    """
    from backend.generative_agent import get_agent, _result_to_dict

    agent = get_agent()
    result_gr = agent.design_from_sound(
        fundamental_hz=fundamental_hz,
        label=label,
        n_candidates=n_candidates,
    )
    result = _result_to_dict(result_gr)
    result["tier"] = 2
    result["analysis"] = {
        "fundamental_hz": fundamental_hz,
        "n_harmonics_detected": len(harmonic_frequencies or []),
        "harmonic_frequencies": harmonic_frequencies or [],
    }
    return result


# =============================================================================
# Tier 3 — Timbre matching
# =============================================================================

def build_target_envelope(analysis: dict, n_harmonics: int = 8) -> np.ndarray:
    """Build a target impedance-magnitude envelope from the sound analysis.

    Takes the detected harmonic amplitudes and interpolates a smooth target
    envelope over the frequency range.  The envelope represents the RELATIVE
    strength of each harmonic that the instrument should produce.

    Returns np.ndarray of shape (n_freqs,) — target magnitudes on the
    frequency grid used by the impedance computation.
    """
    harm_f = np.array(analysis.get("harmonic_frequencies", []))
    harm_m = np.array(analysis.get("harmonic_amplitudes", []))
    fundamental = analysis.get("fundamental_hz", 440.0)

    if len(harm_f) < 2:
        # Fallback: 1/n decay from fundamental
        f_targets = np.array([n * fundamental for n in range(1, n_harmonics + 1)])
        m_targets = 1.0 / np.arange(1, n_harmonics + 1, dtype=float)
        return f_targets, m_targets / m_targets[0]

    # Use detected harmonics, fill missing with interpolated
    all_n = np.arange(1, n_harmonics + 1)
    max_n = int(harm_f[-1] / fundamental)
    freqs_full = np.array([n * fundamental for n in range(1, max_n + 1)])
    mags_full = np.zeros(max_n)
    for n in range(1, max_n + 1):
        # Find detected harmonic closest to this n*f0
        idx = np.argmin(np.abs(harm_f / fundamental - n))
        closest_n = round(harm_f[idx] / fundamental)
        if abs(closest_n - n) <= 1 and n <= len(harm_m):
            mags_full[n - 1] = harm_m[idx]
        else:
            # Interpolate
            mags_full[n - 1] = np.interp(n * fundamental, harm_f, harm_m,
                                         left=0, right=0)

    # Keep only the harmonics we want, normalize
    mags_full = mags_full[:n_harmonics]
    if mags_full[0] > 0:
        mags_full = mags_full / mags_full[0]

    return freqs_full[:n_harmonics], mags_full


def estimate_harmonic_magnitudes(inst: TMMInstrument,
                                 n_harmonics: int = 8,
                                 loss_model: KeefeLoss | None = None) -> np.ndarray:
    """Estimate relative impedance peak magnitudes for a TMMInstrument.

    Combines three loss mechanisms to produce a spectral envelope:
    1. Bore viscothermal losses (Keefe) — small but frequency-dependent
    2. Radiation loss at the open end — proportional to (f*r/c)²
    3. Effective radius sensitivity — narrower bores → more high-freq rolloff

    The combined model gives the optimizer a clear signal: wider bore = brighter
    (less high-frequency attenuation), narrower bore = darker.

    Returns np.ndarray of shape (n_harmonics,) — relative magnitudes (1st = 1).
    """
    if loss_model is None:
        loss_model = KeefeLoss()

    f0 = _c / (2.0 * inst.length) if not inst.closed_top else _c / (4.0 * inst.length)

    # Compute effective radius (weighted average, smaller segments = more weight)
    total_weight = 0.0
    weighted_radius = 0.0
    for action in inst.actions:
        if action[0] == "pipe":
            _, seg_length, seg_diameter = action
            radius = seg_diameter / 2.0
            if radius > 0 and seg_length > 0:
                # Weight by 1/radius — narrower sections have more influence
                w = seg_length / max(radius, 0.1)
                weighted_radius += radius * w
                total_weight += w
    eff_radius = weighted_radius / max(total_weight, 1e-6)

    magnitudes = np.ones(n_harmonics)

    for h in range(1, n_harmonics + 1):
        freq = f0 * h
        wl = _c / freq

        # 1. Bore viscothermal losses
        cum_loss = 1.0
        for action in inst.actions:
            if action[0] == "pipe":
                _, seg_length, seg_diameter = action
                radius = seg_diameter / 2.0
                if radius > 0 and seg_length > 0:
                    lf = loss_model.bore_loss(seg_length, radius, wl)
                    if isinstance(lf, (complex, np.complexfloating)):
                        cum_loss *= abs(lf)
                    else:
                        cum_loss *= float(lf)

        # 2. Radiation loss at open end (unflanged pipe approximation)
        # Radiation resistance: Zr_real ∝ (k*r)² = (2πf*r/c)²
        k_r = (2 * np.pi * freq * eff_radius / _c)  # k * r
        rad_loss = np.exp(-0.5 * k_r ** 2)  # -0.5 is empirical

        # 3. Combined round-trip: bore losses (forward+back) * radiation
        round_trip = cum_loss ** 2 * rad_loss

        # Normalize magnitude: cap at 1.0
        magnitudes[h - 1] = min(1.0, max(0.001, round_trip))

    # Normalize to first harmonic = 1
    if magnitudes[0] > 0:
        magnitudes = magnitudes / magnitudes[0]
    return magnitudes


def _timbre_cost(radii: np.ndarray,
                 hole_positions: list[float],
                 hole_diameters: list[float],
                 bore_length: float,
                 n_holes: int,
                 closed_top: bool,
                 target_mags: np.ndarray,
                 n_harmonics: int,
                 loss_model: KeefeLoss) -> float:
    """Cost: RMS deviation between target and estimated harmonic magnitudes."""
    # Build instrument with these radii
    n_cp = N_TIER3_RADII
    # Interpolate from n_cp control points to full bore profile
    n_segments = max(n_cp * 2, 10)
    pos = np.linspace(0, bore_length, n_segments)
    cp_pos = np.linspace(0, bore_length, n_cp)
    diameters = np.interp(pos, cp_pos, radii) * 2.0  # radius→diameter

    try:
        inst = TMMInstrument(
            inner_positions=pos.tolist(),
            inner_diameters=diameters.tolist(),
            outer_diameters=[d + 14.0 for d in diameters],  # wall thickness ~7mm
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=[3.75] * n_holes,
            closed_top=closed_top,
            loss_model=loss_model,
        )
        estimated = estimate_harmonic_magnitudes(inst, n_harmonics, loss_model)
    except Exception:
        return 1e10

    # RMS error between estimated and target magnitudes
    n = min(len(estimated), len(target_mags))
    if n < 2:
        return 1e10
    return float(np.sqrt(np.mean((estimated[:n] - target_mags[:n]) ** 2)))


def match_timbre(best_candidate: dict,
                 analysis: dict,
                 n_gen: int = 20,
                 pop_size: int = 30) -> dict:
    """Tier 3: optimize bore radii to match the sound's harmonic envelope.

    Takes the best candidate from Tier 2 and re-optimizes the bore profile
    (6 radius control points) while keeping hole positions/diameters fixed.
    The objective is to match the RELATIVE harmonic magnitudes from the sound.

    Parameters
    ----------
    best_candidate : dict
        Best candidate result from Tier 2 (keys: hole_positions_mm, etc.)
    analysis : dict
        Sound analysis dict from analyze_wav().
    n_gen : int
        Number of NSGA-II generations for timbre optimization.
    pop_size : int
        Population size.

    Returns
    -------
    dict with keys:
        tier3_success, tier3_cost,
        bore_radii_initial, bore_radii_optimized,
        target_envelope, estimated_envelope_initial, estimated_envelope_optimized
    """
    target_freqs, target_mags = build_target_envelope(analysis)
    n_harmonics = len(target_mags)

    # Get geometry from best candidate
    hole_positions = best_candidate.get("hole_positions_mm", [])
    hole_diameters = best_candidate.get("hole_diameters_mm", [])
    bore_radii_init = best_candidate.get("bore_radii", [7.25] * N_TIER3_RADII)
    bore_length = best_candidate.get("bore_length_mm", 500.0)
    closed_top = False
    n_holes = len(hole_positions)

    if len(bore_radii_init) != N_TIER3_RADII:
        bore_radii_init = [float(np.mean(bore_radii_init))] * N_TIER3_RADII

    loss_model = KeefeLoss()

    # Evaluate initial cost
    cost_init = _timbre_cost(
        np.array(bore_radii_init), hole_positions, hole_diameters,
        bore_length, n_holes, closed_top, target_mags, n_harmonics, loss_model,
    )

    # NSGA-II optimization of bore radii
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import Problem
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.lhs import LHS
        from pymoo.optimize import minimize
    except ImportError:
        return {
            "tier3_success": False,
            "tier3_error": "pymoo not installed",
            "bore_radii_initial": bore_radii_init,
            "target_envelope": target_mags.tolist(),
            "estimated_envelope_initial": [],
        }

    class TimbreProblem(Problem):
        def __init__(self):
            xl = np.array([3.0] * N_TIER3_RADII)
            xu = np.array([15.0] * N_TIER3_RADII)
            super().__init__(n_var=N_TIER3_RADII, n_obj=1, xl=xl, xu=xu)

        def _evaluate(self, X, out, *args, **kwargs):
            costs = np.array([
                _timbre_cost(x, hole_positions, hole_diameters,
                            bore_length, n_holes, closed_top,
                            target_mags, n_harmonics, loss_model)
                for x in X
            ])
            out["F"] = costs[:, None]

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.2, eta=10),
    )

    try:
        res = minimize(TimbreProblem(), algorithm, ("n_gen", n_gen), verbose=False)
        radii_best = res.X
        cost_best = float(res.F[0])
    except Exception as e:
        return {
            "tier3_success": False,
            "tier3_error": str(e),
            "bore_radii_initial": bore_radii_init,
            "target_envelope": target_mags.tolist(),
            "estimated_envelope_initial": [],
        }

    # Evaluate final magnitudes
    n_segments = max(N_TIER3_RADII * 2, 10)
    pos = np.linspace(0, bore_length, n_segments)
    cp_pos = np.linspace(0, bore_length, N_TIER3_RADII)
    diameters_best = np.interp(pos, cp_pos, radii_best) * 2.0

    try:
        inst_best = TMMInstrument(
            inner_positions=pos.tolist(),
            inner_diameters=diameters_best.tolist(),
            outer_diameters=[d + 14.0 for d in diameters_best],
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=[3.75] * n_holes,
            closed_top=closed_top,
            loss_model=loss_model,
        )
        estimated_best = estimate_harmonic_magnitudes(inst_best, n_harmonics, loss_model)
    except Exception:
        estimated_best = []

    return {
        "tier3_success": cost_best < cost_init,
        "tier3_cost_initial": float(cost_init),
        "tier3_cost_optimized": float(cost_best),
        "bore_radii_initial": bore_radii_init,
        "bore_radii_optimized": radii_best.tolist() if hasattr(radii_best, 'tolist') else list(radii_best),
        "target_envelope_frequencies": target_freqs.tolist(),
        "target_envelope_magnitudes": target_mags.tolist(),
        "estimated_envelope_initial": [],
        "estimated_envelope_optimized": estimated_best.tolist() if hasattr(estimated_best, 'tolist') else list(estimated_best),
    }


# =============================================================================
# Combined pipeline
# =============================================================================

def design_from_sound(filepath: str,
                      n_candidates: int = 2,
                      hole_count: int = 6,
                      run_tier3: bool = True,
                      label: str = "") -> dict:
    """Full three-tier inverse design from a WAV file.

    1. Analyze sound → extract fundamental + harmonic envelope
    2. Design scale → optimize hole positions for playable scale
    3. Match timbre → optimize bore radii to match harmonic envelope

    Parameters
    ----------
    filepath : str
        Path to 16-bit WAV file (A=440 tuned recommended).
    n_candidates : int
        Number of scale-optimization candidates (Tier 2).
    hole_count : int
        Number of tone holes.
    run_tier3 : bool
        If True, run timbre matching after scale optimization.
    label : str
        Optional label for the design.

    Returns
    -------
    dict with keys:
        tier1 (analysis), tier2 (scale result), tier3 (timbre result, optional),
        final_geometry (combined best result)
    """
    # Tier 1
    analysis = analyze_wav(filepath)
    if analysis["confidence"] < 0.1:
        return {"error": "Could not estimate fundamental", "analysis": analysis}

    fundamental = analysis["fundamental_hz"]
    harm_f = analysis["harmonic_frequencies"]
    display_label = label or f"Inverse: {filepath.split('/')[-1]}"

    # Tier 2
    tier2 = design_scale(
        fundamental_hz=fundamental,
        harmonic_frequencies=harm_f,
        label=display_label,
        hole_count=hole_count,
        n_candidates=n_candidates,
    )

    result = {
        "tier1": {
            "sample_rate": analysis["sample_rate"],
            "duration_s": analysis["duration_s"],
            "fundamental_hz": fundamental,
            "confidence": analysis["confidence"],
            "n_harmonics": len(harm_f),
            "harmonic_frequencies": harm_f,
            "harmonic_amplitudes": analysis["harmonic_amplitudes"],
        },
        "tier2": tier2,
    }

    # Tier 3 (optional, uses best candidate from Tier 2)
    if run_tier3 and tier2.get("best") and tier2.get("candidates"):
        best_candidate = tier2["candidates"][0]
        tier3 = match_timbre(best_candidate, analysis)
        result["tier3"] = tier3

        # Build final geometry combining Tier 2 holes + Tier 3 bore profile
        result["final_geometry"] = {
            "bore_length_mm": best_candidate.get("bore_length_mm", 500.0),
            "bore_radii": tier3.get("bore_radii_optimized", []),
            "hole_positions_mm": best_candidate.get("hole_positions_mm", []),
            "hole_diameters_mm": best_candidate.get("hole_diameters_mm", []),
            "intonation_rms_cents": best_candidate.get("intonation_rms_cents", 0),
            "timbre_match_cost": tier3.get("tier3_cost_initial", 0),
        }

    return result


# =============================================================================
# Sound synthesis (for testing without WAV files)
# =============================================================================

def synthesize_harmonic(fundamental_hz: float, n_harmonics: int = 8,
                        duration_s: float = 1.0, sample_rate: int = 44100,
                        amplitudes: list[float] | None = None,
                        odd_only: bool = False) -> np.ndarray:
    """Generate a synthetic harmonic sound (WAV-compatible samples)."""
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    signal = np.zeros_like(t)
    if amplitudes is None:
        amplitudes = [1.0 / (n + 1) for n in range(1, n_harmonics + 1)]
    for n in range(1, n_harmonics + 1):
        if odd_only and n % 2 == 0:
            continue
        idx = n - 1
        amp = amplitudes[idx] if idx < len(amplitudes) else 0.1 / n
        signal += amp * np.sin(2 * math.pi * fundamental_hz * n * t)
    peak = np.max(np.abs(signal))
    return signal / peak if peak > 0 else signal


def save_synthetic_wav(filepath: str, samples: np.ndarray, sample_rate: int = 44100):
    """Save float samples as 16-bit WAV."""
    wavfile.write(filepath, sample_rate, np.int16(samples * 32767))
