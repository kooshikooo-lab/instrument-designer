"""Three-tier inverse design for wind instruments: sound analysis -> scale optimization -> timbre matching.

Tier 1: Analyze a WAV file to extract fundamental frequency, harmonic frequencies,
and spectral envelope. Tier 2: Design a playable scale via NSGA-II, delegating
to the generative agent. Tier 3: Match timbre by optimizing bore radii to match
the harmonic amplitude envelope extracted from the target sound.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.io import wavfile
from scipy.signal import welch

from backend.tmm_acoustics import SPEED_OF_SOUND, TMMInstrument, tmm_instrument_from_radii

try:
    from backend.physics.losses import KeefeLoss
except ImportError:
    KeefeLoss = None

from backend.physics.bore_design import hole_positions_for_scale

try:
    from backend.generative_agent import design_from_sound as _generative_design
except ImportError:
    _generative_design = None


# =============================================================================
# Tier 1: Sound Analysis
# =============================================================================


def synthesize_harmonic(
    fundamental_hz: float,
    n_harmonics: int = 8,
    duration_s: float = 1.0,
    sample_rate: int = 44100,
    amplitudes: np.ndarray | None = None,
    odd_only: bool = False,
) -> np.ndarray:
    if amplitudes is None:
        amplitudes = 1.0 / np.arange(1, n_harmonics + 1, dtype=float)
    if len(amplitudes) < n_harmonics:
        fallback = 1.0 / np.arange(len(amplitudes) + 1, n_harmonics + 1, dtype=float)
        amplitudes = np.concatenate([amplitudes, fallback])
    t = np.linspace(0.0, duration_s, int(sample_rate * duration_s), endpoint=False)
    signal = np.zeros_like(t)
    for n in range(1, n_harmonics + 1):
        if odd_only and n % 2 == 0:
            continue
        signal += amplitudes[n - 1] * np.sin(2.0 * math.pi * n * fundamental_hz * t)
    peak = np.max(np.abs(signal))
    if peak > 0.0:
        signal = signal / peak * 0.95
    return signal


def save_synthetic_wav(filepath: str, samples: np.ndarray, sample_rate: int = 44100) -> None:
    samples_int = np.clip(samples * 32767.0, -32768.0, 32767.0).astype(np.int16)
    wavfile.write(filepath, sample_rate, samples_int)


def analyze_wav(filepath: str) -> dict:
    sample_rate, data = wavfile.read(filepath)
    if data.ndim > 1:
        data = data[:, 0]
    if np.issubdtype(data.dtype, np.integer):
        data_float = data.astype(np.float64) / float(np.iinfo(data.dtype).max)
    else:
        data_float = data.astype(np.float64)
    duration_s = len(data_float) / sample_rate

    nperseg = min(4096, len(data_float) // 4)
    if nperseg < 256:
        nperseg = 256
    freqs, psd = welch(data_float, fs=sample_rate, nperseg=nperseg, scaling='density')
    spectrum_mags = np.sqrt(psd)

    n = len(data_float)
    min_lag = int(sample_rate / 2000.0)
    max_lag = int(sample_rate / 50.0)
    if max_lag > n - 1:
        max_lag = n - 2
    if min_lag >= max_lag:
        min_lag = max(1, max_lag - 1)
    data_centered = data_float - np.mean(data_float)
    energy = np.sum(data_centered ** 2)
    if energy < 1e-30:
        return {
            'sample_rate': sample_rate,
            'duration_s': duration_s,
            'fundamental_hz': 0.0,
            'confidence': 0.0,
            'harmonic_frequencies': np.array([], dtype=float),
            'harmonic_amplitudes': np.array([], dtype=float),
            'spectrum_frequencies': freqs,
            'spectrum_magnitudes': spectrum_mags,
            'envelope_frequencies': freqs,
            'envelope_magnitudes': spectrum_mags,
        }
    corr = np.zeros(max_lag - min_lag + 1)
    for lag in range(min_lag, max_lag + 1):
        corr[lag - min_lag] = np.sum(data_centered[:n - lag] * data_centered[lag:])
    corr = corr / energy
    if np.max(corr) <= 0.0:
        f0 = 0.0
        confidence = 0.0
    else:
        peak_idx = int(np.argmax(corr))
        lag_peak = min_lag + peak_idx
        if 0 < peak_idx < len(corr) - 1:
            a = corr[peak_idx - 1]
            b = corr[peak_idx]
            c_val = corr[peak_idx + 1]
            denom = a - 2.0 * b + c_val
            if abs(denom) > 1e-15:
                delta = (a - c_val) / (2.0 * denom)
                lag_peak = int(round(peak_idx + delta)) + min_lag
        f0 = sample_rate / lag_peak if lag_peak > 0 else 0.0
        confidence = float(corr[peak_idx])
        if f0 < 20.0 or f0 > 2000.0:
            f0 = 0.0
            confidence = 0.0

    n_harmonics_max = 20
    harmonic_freqs_list: list[float] = []
    harmonic_amps_list: list[float] = []
    if f0 > 0.0:
        for h in range(1, n_harmonics_max + 1):
            target = f0 * h
            search_half = f0 * 0.25
            lo = target - search_half
            hi = target + search_half
            mask = (freqs >= lo) & (freqs <= hi)
            if np.any(mask):
                idx_range = np.where(mask)[0]
                local_max_idx = idx_range[np.argmax(spectrum_mags[idx_range])]
                harmonic_freqs_list.append(float(freqs[local_max_idx]))
                harmonic_amps_list.append(float(spectrum_mags[local_max_idx]))
            else:
                break
    harmonic_frequencies = np.array(harmonic_freqs_list, dtype=float)
    harmonic_amplitudes = np.array(harmonic_amps_list, dtype=float)

    window_hz = 100.0
    bin_width = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    window_bins = max(1, int(window_hz / bin_width))
    envelope = np.copy(spectrum_mags)
    half = window_bins // 2
    for i in range(len(envelope)):
        lo = max(0, i - half)
        hi = min(len(envelope), i + half + 1)
        envelope[i] = float(np.max(spectrum_mags[lo:hi]))

    return {
        'sample_rate': sample_rate,
        'duration_s': duration_s,
        'fundamental_hz': f0,
        'confidence': confidence,
        'harmonic_frequencies': harmonic_frequencies,
        'harmonic_amplitudes': harmonic_amplitudes,
        'spectrum_frequencies': freqs,
        'spectrum_magnitudes': spectrum_mags,
        'envelope_frequencies': freqs,
        'envelope_magnitudes': envelope,
    }


# =============================================================================
# Tier 2: Scale Optimization (generative agent, with numpy-GA fallback)
# =============================================================================

_DIATONIC_STEPS = [0, 2, 4, 5, 7, 9, 11]  # major scale within an octave


def _scale_targets(fundamental_hz: float, harmonic_frequencies: np.ndarray | None) -> list[float]:
    """Target note frequencies for successive hole fingerings.

    Builds a major-scale ladder starting at the recorded fundamental. The
    harmonic series (overblow targets) is not used here: hole-ladder design
    targets adjacent scale steps, not harmonic overtones.
    """
    if fundamental_hz <= 0.0:
        fundamental_hz = 261.63
    return [fundamental_hz * 2.0 ** (s / 12.0) for s in _DIATONIC_STEPS]


def _fingering_ladder(hole_count: int) -> list[list[str]]:
    """All-closed, then progressively opening holes from the bottom."""
    sets = [['closed'] * hole_count]
    for k in range(1, hole_count + 1):
        fing = ['closed'] * hole_count
        for i in range(k):
            fing[i] = 'open'
        sets.append(fing)
    return sets


def _project_positions(u: np.ndarray, spacing: float = 0.03) -> np.ndarray:
    """Project sorted fractions [0,1] into a feasible min-spaced layout."""
    n = len(u)
    s = np.sort(np.clip(u, 0.0, 1.0))
    lo = spacing * np.arange(n) + spacing / 2.0
    hi = 1.0 - spacing * np.arange(n) - spacing / 2.0
    s = np.maximum(s, lo)
    s = np.minimum(s, hi)
    for i in range(n - 2, -1, -1):
        s[i] = min(s[i], s[i + 1] - spacing)
    for i in range(1, n):
        s[i] = max(s[i], s[i - 1] + spacing)
    return s


def _decode_chromosome(x: np.ndarray, hole_count: int) -> dict:
    """Decode GA chromosome -> min-spaced hole positions, diameters, length."""
    positions_frac = _project_positions(x[:hole_count])
    diameters = np.maximum(x[hole_count:2 * hole_count], 1.0)
    length = x[2 * hole_count]
    positions = [float(p * length) for p in positions_frac]
    return {
        'bore_length_mm': float(length),
        'hole_positions_mm': positions,
        'hole_diameters_mm': [float(d) for d in diameters],
        'hole_lengths_mm': [3.0] * hole_count,
        'closed_top': False,
        'bore_length': float(length),
        'hole_positions': positions,
        'hole_diameters': [float(d) for d in diameters],
        'hole_lengths': [3.0] * hole_count,
        'bore_radii': np.linspace(7.0, 9.0, 6).tolist(),
    }


def _scale_fitness(x: np.ndarray, hole_count: int, targets: list[float],
                   loss: Any) -> float:
    """Weighted RMS cents error via the resonance-phase model.

    For the progressive hole ladder (holes opening from the bell) the vented
    fundamental is the phase-2 resonance of the effective column — the model
    satisfies p(w) = 1 + 2*L_eff/w, so the phase at the target wavelength gives
    a smooth pitch error directly:

        f_res = f_target / (p - 1)   =>   cents = -1200*log2(p - 1)

    (Verified against find_resonance to within ~1 cent, and it is continuous,
    so the GA can optimize without the branch-jumping of peak search.) The
    all-closed fundamental gets double weight: it is the bore-length anchor.
    """
    try:
        cand = _decode_chromosome(x, hole_count)
        inst = tmm_instrument_from_radii(
            radii_mm=np.linspace(7.0, 9.0, 6),
            bore_length_mm=cand['bore_length_mm'],
            hole_positions_mm=cand['hole_positions_mm'],
            hole_diameters_mm=cand['hole_diameters_mm'],
            hole_lengths_mm=cand['hole_lengths_mm'],
            closed_top=False,
            loss_model=loss,
        )
        ladder = _fingering_ladder(hole_count)
        n_notes = min(len(targets), len(ladder))
        if n_notes == 0:
            return 1e10
        weights = [2.0] + [1.0] * (n_notes - 1)
        sq = []
        for t, fing, w in zip(targets[:n_notes], ladder[:n_notes], weights):
            if t <= 0.0:
                continue
            p = inst.resonance_phase(inst.speed_of_sound / t, fing)
            if not (p > 1.0):
                return 1e10
            cents = -1200.0 * math.log2(p - 1.0)
            sq.append(w * cents * cents)
        if not sq:
            return 1e10
        return float(np.mean(sq))
    except Exception:
        return 1e10


def _fundamental_length(fundamental_hz: float, hole_count: int, loss: Any,
                        step_mm: float = 2.0) -> float:
    """Grid-search bore length that plays the all-closed fundamental on pitch.

    The all-closed note is set almost entirely by bore length, so it is solved
    first (cheap 1-D sweep), then the GA refines holes and length together.
    """
    c = SPEED_OF_SOUND
    nominal = c / (2.0 * fundamental_hz) if fundamental_hz > 0 else 500.0
    lengths = np.arange(0.85 * nominal, 1.15 * nominal, step_mm)
    fracs = np.linspace(0.12, 0.5, hole_count)
    best, best_err = nominal, 1e18
    for L in lengths:
        inst = tmm_instrument_from_radii(
            radii_mm=np.linspace(7.0, 9.0, 6),
            bore_length_mm=float(L),
            hole_positions_mm=(fracs * L).tolist(),
            hole_diameters_mm=[7.0] * hole_count,
            hole_lengths_mm=[3.0] * hole_count,
            closed_top=False,
            loss_model=loss,
        )
        wl = inst.find_resonance(
            c / fundamental_hz, ['closed'] * hole_count, n_register=2
        )
        f = inst.frequency_from_wavelength(wl)
        err = abs(1200.0 * math.log2(f / fundamental_hz)) if f > 0 else 1e18
        if err < best_err:
            best, best_err = L, err
    return float(best)


def design_scale_numpy_ga(
    fundamental_hz: float,
    harmonic_frequencies: np.ndarray | None = None,
    hole_count: int = 6,
    n_candidates: int = 2,
    pop_size: int = 50,
    n_gen: int = 50,
    rng: np.random.Generator | None = None,
) -> dict:
    """Self-contained numpy genetic algorithm for hole-position/diameter design.

    Fallback for Tier 2 when the generative agent is unavailable. Two stages:
    1. Grid-search bore length so the all-closed fundamental is on pitch.
    2. GA over min-spaced hole positions + diameters (length refined in a tight
       band) so successive fingerings play a major-scale ladder, scored by
       weighted absolute-pitch error in cents.
    """
    rng = rng if rng is not None else np.random.default_rng(42)
    c = SPEED_OF_SOUND
    targets = _scale_targets(fundamental_hz, harmonic_frequencies)
    loss = _get_loss_model(None)
    length0 = _fundamental_length(fundamental_hz, hole_count, loss)

    # Physics-grounded seed: the note of fingering k is set by the distance
    # from the blowing end to the first open hole (hole k-1, opening from the
    # bell). Seed the population around those analytic positions rather than
    # uniform random, and bound the search around them.
    hole_freqs = targets[1:hole_count + 1]
    analytic_mm = hole_positions_for_scale(
        hole_freqs, bore_length_mm=length0, hole_diameter_mm=7.0,
        wall_thickness_mm=3.0, bore_diameter_mm=14.0, closed_top=False,
    )
    analytic_frac = np.clip(np.asarray(analytic_mm) / length0, 0.0, 1.0)
    pos_lo = max(0.02, float(np.min(analytic_frac)) - 0.05)
    pos_hi = min(0.65, float(np.max(analytic_frac)) + 0.05)
    if pos_hi <= pos_lo:
        pos_lo, pos_hi = 0.02, 0.65

    # chromosome: [positions_frac * hole_count, diameters, length]
    n_var = 2 * hole_count + 1
    xl = np.concatenate([
        np.full(hole_count, pos_lo), np.full(hole_count, 4.0),
        np.array([length0 - 20.0]),
    ])
    xu = np.concatenate([
        np.full(hole_count, pos_hi), np.full(hole_count, 11.0),
        np.array([length0 + 20.0]),
    ])

    n_seed = max(2, int(0.6 * pop_size))
    pop = rng.random((pop_size, n_var)) * (xu - xl) + xl
    seed_pos = np.clip(
        np.repeat(analytic_frac[None, :], n_seed, axis=0)
        + rng.normal(0.0, 0.02, size=(n_seed, hole_count)),
        pos_lo, pos_hi,
    )
    pop[:n_seed, :hole_count] = seed_pos
    pop[:n_seed, hole_count:2 * hole_count] = np.clip(
        7.0 + rng.normal(0.0, 1.5, size=(n_seed, hole_count)), 4.0, 11.0
    )
    pop[:n_seed, 2 * hole_count] = length0 + rng.normal(0.0, 5.0, size=n_seed)
    fitness = np.array([_scale_fitness(p, hole_count, targets, loss) for p in pop])

    length_scale = 40.0  # mutation sigma for length band (mm)
    for gen in range(n_gen):
        order = np.argsort(fitness)
        elites = pop[order[:max(2, pop_size // 5)]].copy()
        children: list[np.ndarray] = []
        while len(children) < pop_size - len(elites):
            a = pop[order[rng.integers(0, max(1, pop_size // 2))]]
            b = pop[order[rng.integers(0, max(1, pop_size // 2))]]
            mask = rng.random(n_var) < 0.5
            child = np.where(mask, a, b)
            mutate = rng.random(n_var) < (1.0 / n_var)
            noise = np.full(n_var, 0.03 * (xu - xl))
            noise[-1] = length_scale
            child = child + mutate * rng.normal(0.0, noise)
            child = np.clip(child, xl, xu)
            children.append(child)
        pop = np.vstack([elites, np.asarray(children)])
        fitness = np.array([_scale_fitness(p, hole_count, targets, loss) for p in pop])

    order = np.argsort(fitness)
    candidates = [_decode_chromosome(pop[i], hole_count) for i in order[:n_candidates]]
    best = candidates[0]

    # Verification pass: play the final design with the peak finder and report
    # per-note pitch error (the phase fitness is smooth; this confirms pitch).
    ladder = _fingering_ladder(hole_count)
    verif_inst = tmm_instrument_from_radii(
        radii_mm=np.linspace(7.0, 9.0, 6),
        bore_length_mm=best['bore_length_mm'],
        hole_positions_mm=best['hole_positions_mm'],
        hole_diameters_mm=best['hole_diameters_mm'],
        hole_lengths_mm=best['hole_lengths_mm'],
        closed_top=False,
        loss_model=loss,
    )
    n_notes = min(len(targets), len(ladder))
    target_wavelengths = [verif_inst.speed_of_sound / t for t in targets[:n_notes]]
    played = verif_inst.compute_fingered_frequencies(
        target_wavelengths, ladder[:n_notes], n_register=2
    )
    cents_error = [
        (1200.0 * math.log2(p / t)) if t > 0.0 and p > 0.0 else 1e6
        for t, p in zip(targets[:n_notes], played)
    ]

    return {
        'method': 'numpy_ga',
        'fundamental_hz': float(fundamental_hz),
        'target_frequencies': [round(t, 3) for t in targets],
        'fitness': [float(fitness[i]) for i in order[:n_candidates]],
        'cents_error': [round(c, 2) for c in cents_error],
        'candidates': candidates,
        'geometry': {
            'bore_length': best['bore_length_mm'],
            'hole_positions': best['hole_positions_mm'],
            'hole_diameters': best['hole_diameters_mm'],
            'hole_lengths': best['hole_lengths_mm'],
            'closed_top': False,
            'bore_radii': np.linspace(7.0, 9.0, 6).tolist(),
        },
    }


def design_scale(
    fundamental_hz: float,
    harmonic_frequencies: np.ndarray | None = None,
    label: str = '',
    hole_count: int = 6,
    n_candidates: int = 2,
) -> dict:
    if _generative_design is not None:
        input_data: dict[str, Any] = {
            'fundamental_hz': fundamental_hz,
            'harmonic_frequencies': (
                harmonic_frequencies.tolist()
                if harmonic_frequencies is not None
                else []
            ),
            'label': label,
            'hole_count': hole_count,
            'n_candidates': n_candidates,
        }
        return _generative_design(input_data)
    return design_scale_numpy_ga(
        fundamental_hz=fundamental_hz,
        harmonic_frequencies=harmonic_frequencies,
        hole_count=hole_count,
        n_candidates=n_candidates,
    )


# =============================================================================
# Tier 3: Timbre Matching
# =============================================================================


def _get_loss_model(loss_model: Any = None) -> Any:
    if loss_model is not None:
        return loss_model
    if KeefeLoss is not None:
        return KeefeLoss()
    return None


def estimate_harmonic_magnitudes(
    inst: TMMInstrument,
    n_harmonics: int = 8,
    loss_model: Any = None,
) -> np.ndarray:
    loss = _get_loss_model(loss_model)
    c = SPEED_OF_SOUND

    segments: list[tuple[float, float]] = []
    for action in inst.actions:
        if action[0] == 'pipe':
            _, seg_length, seg_diameter = action
            if seg_diameter > 0.0 and seg_length > 0.0:
                segments.append((seg_length, seg_diameter / 2.0))

    r_bell = segments[-1][1] if segments else 1.0

    if inst.closed_top:
        f0_guess = c / (4.0 * inst.length)
    else:
        f0_guess = c / (2.0 * inst.length)

    magnitudes = np.zeros(n_harmonics, dtype=float)
    for h in range(1, n_harmonics + 1):
        f = h * f0_guess
        wavelength = c / f
        cum_loss = 1.0
        for length_mm, radius in segments:
            if loss is not None and radius > 0.0:
                lf = loss.bore_loss(length_mm, radius, wavelength)
                cum_loss *= abs(lf)
        k = 2.0 * math.pi / wavelength
        rad_loss = math.exp(-0.5 * (k * r_bell) ** 2)
        round_trip = cum_loss * cum_loss * rad_loss
        magnitudes[h - 1] = round_trip

    if magnitudes[0] > 0.0:
        magnitudes = magnitudes / magnitudes[0]
    return magnitudes


def build_target_envelope(
    analysis: dict,
    n_harmonics: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    harm_freqs = analysis.get('harmonic_frequencies', np.array([], dtype=float))
    harm_amps = analysis.get('harmonic_amplitudes', np.array([], dtype=float))
    fundamental = analysis.get('fundamental_hz', 0.0)

    if len(harm_freqs) == 0 or fundamental <= 0.0:
        freqs = np.arange(1.0, float(n_harmonics) + 1.0)
        amps = 1.0 / freqs
        return (freqs * 100.0, amps)

    n_avail = min(len(harm_freqs), n_harmonics)
    freqs = np.zeros(n_harmonics, dtype=float)
    amps = np.zeros(n_harmonics, dtype=float)
    for i in range(n_harmonics):
        if i < n_avail:
            freqs[i] = float(harm_freqs[i])
            amps[i] = max(float(harm_amps[i]), 1e-30)
        else:
            freqs[i] = fundamental * float(i + 1)
            amps[i] = amps[i - 1] * (float(i) / float(i + 1))
    if amps[0] > 0.0:
        amps = amps / amps[0]
    return (freqs, amps)


def match_timbre(
    best_candidate: dict,
    analysis: dict,
    n_gen: int = 20,
    pop_size: int = 30,
) -> dict:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.optimize import minimize
    from pymoo.termination import get_termination

    loss = _get_loss_model(None)

    bore_length = float(
        best_candidate.get('bore_length_mm', best_candidate.get('bore_length', 600.0))
    )
    hole_positions: list[float] = best_candidate.get('hole_positions_mm', best_candidate.get('hole_positions', []))
    hole_diameters: list[float] = best_candidate.get('hole_diameters_mm', best_candidate.get('hole_diameters', []))
    hole_lengths: list[float] = best_candidate.get('hole_lengths_mm', best_candidate.get('hole_lengths', []))
    closed_top = bool(best_candidate.get('closed_top', False))

    target_freqs, target_mags = build_target_envelope(analysis, n_harmonics=8)

    n_cp = 6
    r_min = 3.0
    r_max = 15.0

    class _TimbreProblem(ElementwiseProblem):
        def __init__(self_):
            super().__init__(n_var=n_cp, n_obj=1, xl=r_min, xu=r_max)

        def _evaluate(self_, x, out, *args, **kwargs):
            radii = np.maximum(x, 1e-6)
            inst = tmm_instrument_from_radii(
                radii_mm=radii,
                bore_length_mm=bore_length,
                hole_positions_mm=hole_positions,
                hole_diameters_mm=hole_diameters,
                hole_lengths_mm=hole_lengths,
                closed_top=closed_top,
                loss_model=loss,
            )
            est_mags = estimate_harmonic_magnitudes(inst, n_harmonics=8, loss_model=loss)
            n_min = min(len(est_mags), len(target_mags))
            if n_min == 0:
                out['F'] = np.array([1e10])
                return
            se = (est_mags[:n_min] - target_mags[:n_min]) ** 2
            out['F'] = np.array([float(np.mean(se))])

    initial_radii_arr = np.linspace(7.0, 9.0, n_cp)
    inst_init = tmm_instrument_from_radii(
        radii_mm=initial_radii_arr,
        bore_length_mm=bore_length,
        hole_positions_mm=hole_positions,
        hole_diameters_mm=hole_diameters,
        hole_lengths_mm=hole_lengths,
        closed_top=closed_top,
        loss_model=loss,
    )
    est_init = estimate_harmonic_magnitudes(inst_init, n_harmonics=8, loss_model=loss)
    n_min = min(len(est_init), len(target_mags))
    cost_init = float(np.mean((est_init[:n_min] - target_mags[:n_min]) ** 2)) if n_min > 0 else 1e10

    algorithm = NSGA2(pop_size=pop_size)
    termination = get_termination('n_gen', n_gen)
    res = minimize(_TimbreProblem(), algorithm, termination, seed=42, verbose=False)

    radii_opt = np.maximum(res.X, 1e-6)
    cost_opt = float(res.F[0]) if hasattr(res.F, '__len__') else float(res.F)

    inst_opt = tmm_instrument_from_radii(
        radii_mm=radii_opt,
        bore_length_mm=bore_length,
        hole_positions_mm=hole_positions,
        hole_diameters_mm=hole_diameters,
        hole_lengths_mm=hole_lengths,
        closed_top=closed_top,
        loss_model=loss,
    )
    est_opt = estimate_harmonic_magnitudes(inst_opt, n_harmonics=8, loss_model=loss)

    return {
        'tier3_success': bool(cost_opt < cost_init * 1.1),
        'tier3_cost_initial': float(cost_init),
        'tier3_cost_optimized': float(cost_opt),
        'bore_radii_initial': initial_radii_arr.tolist(),
        'bore_radii_optimized': radii_opt.tolist(),
        'target_envelope': {
            'frequencies': target_freqs.tolist(),
            'magnitudes': target_mags.tolist(),
        },
        'estimated_envelope': {
            'initial': est_init.tolist(),
            'optimized': est_opt.tolist(),
        },
    }


# =============================================================================
# Full Pipeline
# =============================================================================


def design_from_sound(
    filepath: str,
    n_candidates: int = 2,
    hole_count: int = 6,
    run_tier3: bool = True,
    label: str = '',
) -> dict:
    tier1 = analyze_wav(filepath)
    f0 = tier1['fundamental_hz']
    harm_freqs = tier1['harmonic_frequencies']

    tier2 = design_scale(
        fundamental_hz=f0,
        harmonic_frequencies=harm_freqs,
        label=label,
        hole_count=hole_count,
        n_candidates=n_candidates,
    )

    tier3: dict[str, Any] = {}
    final_geometry: dict[str, Any] = {}
    if run_tier3:
        candidates = tier2.get('candidates', [])
        if candidates:
            best = candidates[0]
            tier3 = match_timbre(best, tier1)
            if tier3.get('tier3_success', False):
                final_geometry = {
                    'bore_length': best.get('bore_length', 600.0),
                    'hole_positions': best.get('hole_positions', []),
                    'hole_diameters': best.get('hole_diameters', []),
                    'hole_lengths': best.get('hole_lengths', []),
                    'closed_top': best.get('closed_top', False),
                    'bore_radii': tier3.get('bore_radii_optimized', []),
                }
            else:
                final_geometry = {
                    'bore_length': best.get('bore_length', 600.0),
                    'hole_positions': best.get('hole_positions', []),
                    'hole_diameters': best.get('hole_diameters', []),
                    'hole_lengths': best.get('hole_lengths', []),
                    'closed_top': best.get('closed_top', False),
                    'bore_radii': best.get('bore_radii', tier2.get('bore_radii', [])),
                }
        else:
            final_geometry = tier2.get('geometry', {})

    return {
        'tier1': tier1,
        'tier2': tier2,
        'tier3': tier3,
        'final_geometry': final_geometry,
    }
