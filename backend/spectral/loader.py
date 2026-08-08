"""Audio file loading for spectral analysis."""

from __future__ import annotations

import numpy as np
import scipy.io.wavfile as wavfile


def load_audio(path: str, target_sr: float = 44100.0) -> tuple[np.ndarray, float]:
    """Load a WAV file and resample to target sample rate.

    Returns:
        audio: mono float32 array normalized to [-1, 1]
        sr: actual sample rate of the loaded audio
    """
    sr, data = wavfile.read(path)
    if data.dtype == np.int16:
        audio = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        audio = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        audio = (data.astype(np.float32) - 128.0) / 128.0
    else:
        audio = data.astype(np.float32)

    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    if sr != target_sr:
        import scipy.signal as signal
        num_samples = int(len(audio) * target_sr / sr)
        audio = signal.resample(audio, num_samples)
        sr = target_sr

    return audio, sr