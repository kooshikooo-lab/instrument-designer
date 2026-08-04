"""Fundamental frequency extraction."""

from __future__ import annotations

import numpy as np
import librosa


def extract_f0(
    audio: np.ndarray,
    sr: float,
    method: str = "pyin",
    fmin: float = 65.41,
    fmax: float | None = None,
) -> dict:
    """Extract the fundamental frequency (f0) contour from audio.

    Args:
        audio: mono float32 audio signal
        sr: sample rate in Hz
        method: "pyin" (probabilistic YIN via librosa) or "autocorr"
            (simple autocorrelation fallback)
        fmin: minimum expected f0 (Hz)
        fmax: maximum expected f0 (Hz); defaults to sr/2

    Returns:
        dict with keys:
            - "f0": array of f0 estimates per frame (Hz), NaN where unvoiced
            - "frame_times": time axis for each frame (seconds)
            - "method": the method used
            - "sr": sample rate
    """
    if fmax is None:
        fmax = sr / 2.0

    if method == "pyin":
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y=audio,
            fmin=fmin,
            fmax=fmax,
            sr=sr,
        )
        return {
            "f0": f0,
            "frame_times": librosa.times_like(f0, sr=sr),
            "method": "pyin",
            "sr": sr,
            "voiced_flag": voiced_flag,
            "voiced_probs": voiced_probs,
        }
    elif method == "autocorr":
        frame_length = int(sr * 0.03)
        hop_length = int(sr * 0.01)
        n_frames = (len(audio) - frame_length) // hop_length + 1
        f0 = np.empty(n_frames, dtype=np.float32)
        f0[:] = np.nan
        times = np.empty(n_frames, dtype=np.float32)

        for i in range(n_frames):
            start = i * hop_length
            frame = audio[start : start + frame_length]
            if len(frame) < frame_length:
                break
            frame = frame - np.mean(frame)
            corr = np.correlate(frame, frame, mode="full")
            corr = corr[len(corr) // 2 :]
            # Find first peak after the minimum lag corresponding to fmax
            min_lag = max(1, int(sr / fmax))
            max_lag = int(sr / fmin)
            if min_lag >= len(corr):
                continue
            max_lag = min(max_lag, len(corr) - 1)
            if max_lag <= min_lag:
                continue
            # Find the first prominent peak after min_lag.
            # For a pure tone the autocorrelation is a cosine; the first
            # peak after the zero-lag region is at the signal period.
            segment = corr[min_lag:max_lag]
            if len(segment) < 3:
                continue
            # Require the peak to be larger than its neighbours to avoid
            # picking up the near-1.0 value at lag=1 for high frequencies.
            peak_idx = min_lag + np.argmax(segment)
            # Verify it is a local maximum (not at the edges).
            if peak_idx <= min_lag or peak_idx >= max_lag - 1:
                continue
            if corr[peak_idx] > 0.01:
                f0[i] = sr / peak_idx
            times[i] = i * hop_length / sr

        return {
            "f0": f0,
            "frame_times": times,
            "method": "autocorr",
            "sr": sr,
        }
    else:
        raise ValueError(
            f"Unknown f0 method: {method!r}. Use 'pyin' or 'autocorr'."
        )