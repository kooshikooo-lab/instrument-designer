from __future__ import annotations

import math

import numpy as np
import scipy.signal
from scipy.io import wavfile

MIN_HARMONIC_RATIO = 0.05
HARMONIC_TOLERANCE = 0.03
MIN_FUNDAMENTAL_HZ = 30.0
MAX_FUNDAMENTAL_HZ = 2000.0


def analyze_wav(filepath: str) -> dict:
    """Read a WAV file and extract spectral features.

    Returns dict with keys:
        sample_rate, duration_s,
        fundamental_hz, confidence,
        harmonic_frequencies, harmonic_amplitudes,
        spectrum_frequencies, spectrum_magnitudes,
        envelope_frequencies, envelope_magnitudes
    """
    sample_rate, samples = wavfile.read(filepath)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)

    duration = len(samples) / sample_rate
    result = {"sample_rate": sample_rate, "duration_s": duration}

    freqs, mags = _power_spectrum(samples, sample_rate)
    result["spectrum_frequencies"] = freqs.tolist()
    result["spectrum_magnitudes"] = mags.tolist()

    envelope = _spectral_envelope(freqs, mags)
    result["envelope_frequencies"] = freqs.tolist()
    result["envelope_magnitudes"] = envelope.tolist()

    fundamental, confidence = _estimate_fundamental(samples, sample_rate)
    result["fundamental_hz"] = fundamental
    result["confidence"] = confidence

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
    window_bins = max(3, int(window_hz / (freqs[1] - freqs[0])) | 1)
    envelope = scipy.signal.order_filter(mags, np.ones(window_bins), window_bins - 1)
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
    """Check if frequencies form a realizable harmonic series."""
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
