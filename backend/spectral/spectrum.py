"""Spectral analysis: CQT and Welch spectrogram."""

from __future__ import annotations

import numpy as np
import librosa
import scipy.signal as signal


def compute_spectrum(
    audio: np.ndarray,
    sr: float,
    method: str = "cqt",
    fmin: float = 65.41,
    fmax: float | None = None,
    n_bins: int = 84,
    hop_length: int = 512,
) -> dict:
    """Compute a spectral representation of the audio.

    Args:
        audio: mono float32 audio signal
        sr: sample rate in Hz
        method: "cqt" (constant-Q transform via librosa) or "welch" (power spectral density)
        fmin: minimum frequency for CQT (default: C2 = 65.41 Hz)
        fmax: maximum frequency for CQT (default: sr/2)
        n_bins: number of CQT bins (default: 84, covers ~7 octaves)
        hop_length: hop length for CQT frames

    Returns:
        dict with keys:
            - "frequencies": array of frequency bins (Hz)
            - "magnitude": magnitude spectrum (shape depends on method)
            - "method": the method used
            - "sr": sample rate
    """
    if fmax is None:
        fmax = sr / 2.0

    if method == "cqt":
        cqt = librosa.cqt(
            y=audio,
            sr=sr,
            fmin=fmin,
            n_bins=n_bins,
            hop_length=hop_length,
            filter_scale=1.0,
            norm=1,
            sparsity=0.01,
        )
        magnitude = np.abs(cqt)
        frequencies = librosa.cqt_frequencies(
            n_bins=n_bins, fmin=fmin, bins_per_octave=12
        )
        return {
            "frequencies": frequencies,
            "magnitude": magnitude,
            "method": "cqt",
            "sr": sr,
            "hop_length": hop_length,
        }
    elif method == "welch":
        freqs, psd = signal.welch(
            audio,
            fs=sr,
            nperseg=min(4096, len(audio)),
            noverlap=None,
            scaling="density",
        )
        mask = (freqs >= fmin) & (freqs <= fmax)
        return {
            "frequencies": freqs[mask],
            "magnitude": np.sqrt(psd[mask]),
            "method": "welch",
            "sr": sr,
        }
    else:
        raise ValueError(f"Unknown spectrum method: {method!r}. Use 'cqt' or 'welch'.")