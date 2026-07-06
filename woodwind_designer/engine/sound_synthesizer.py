import os
import tempfile
import struct
import math
import hashlib
from dataclasses import dataclass
from typing import Optional

import numpy as np

SAMPLE_RATE = 44100
MAX_AMPLITUDE = 0.9
_CACHE_DIR = None

def _get_cache_dir():
    global _CACHE_DIR
    if _CACHE_DIR is None:
        _CACHE_DIR = tempfile.mkdtemp(suffix="_audio_cache")
    return _CACHE_DIR


def _note_to_freq(note: str) -> float:
    note = note.strip().upper()
    name_map = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
                "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
                "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11}
    note_name = note[:-1]
    octave = int(note[-1])
    semitone = name_map.get(note_name, 9)
    return 440.0 * (2.0 ** ((semitone - 9 + (octave - 4) * 12) / 12.0))


def _adsr_envelope(n_samples: int, attack: float = 0.05, decay: float = 0.1,
                   sustain: float = 0.7, release: float = 0.2) -> np.ndarray:
    sr = SAMPLE_RATE
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s = n_samples - a - d - r
    env = np.ones(n_samples)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0:
        env[a:a + d] = np.linspace(1, sustain, d)
    if r > 0 and s > 0:
        env[-r:] = np.linspace(sustain, 0, r)
    elif r > 0:
        env[-r:] = np.linspace(env[-r], 0, r)
    return env


def _vibrato(n_samples: int, rate: float = 5.0, depth: float = 0.02) -> np.ndarray:
    t = np.arange(n_samples) / SAMPLE_RATE
    return 1.0 + depth * np.sin(2 * math.pi * rate * t)


def _noise_floor(n_samples: int, level: float = 0.005) -> np.ndarray:
    return np.random.uniform(-level, level, n_samples)


def synthesize_from_peaks(peak_freqs: list[float], duration: float = 2.0,
                          sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    wave = np.zeros(n)
    env = _adsr_envelope(n)
    vib = _vibrato(n)
    noise = _noise_floor(n, 0.003)
    for i, f0 in enumerate(peak_freqs):
        if f0 <= 0:
            continue
        amp = 1.0 / (i + 1)
        partial = amp * np.sin(2 * math.pi * f0 * t * vib)
        harmonics = 3 if f0 < 300 else 2
        for h in range(2, harmonics + 1):
            partial += (amp / h) * np.sin(2 * math.pi * f0 * h * t * vib)
        wave += partial
    if len(peak_freqs) > 0:
        wave /= max(np.max(np.abs(wave)), 1e-6)
    wave = wave * env * MAX_AMPLITUDE + noise * env
    wave = np.clip(wave, -1.0, 1.0)
    return (wave * 32767).astype(np.int16)


def synthesize_tone(frequency: float, duration: float = 2.0,
                    instrument_type: str = "flute",
                    sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    env = _adsr_envelope(n)
    vib = _vibrato(n)
    noise = _noise_floor(n, 0.003)
    if instrument_type in ("flute", "fipple", "whistle", "recorder"):
        harmonics = [1.0, 0.3, 0.1, 0.05]
    elif instrument_type in ("reed", "clarinet", "shawm"):
        harmonics = [1.0, 0.0, 0.5, 0.0, 0.25, 0.0, 0.12]
    elif instrument_type in ("brass", "trumpet", "horn"):
        harmonics = [1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1]
    else:
        harmonics = [1.0, 0.5, 0.3, 0.15, 0.1, 0.05]
    wave = np.zeros(n)
    for h, amp in enumerate(harmonics, 1):
        wave += amp * np.sin(2 * math.pi * frequency * h * t * vib)
    wave /= max(np.max(np.abs(wave)), 1e-6)
    wave = wave * env * MAX_AMPLITUDE + noise * env
    wave = np.clip(wave, -1.0, 1.0)
    return (wave * 32767).astype(np.int16)


def synthesize_from_note(note: str, duration: float = 2.0,
                         instrument_type: str = "flute") -> np.ndarray:
    freq = _note_to_freq(note)
    return synthesize_tone(freq, duration, instrument_type)


def write_wav(filepath: str, samples: np.ndarray, sample_rate: int = SAMPLE_RATE):
    n = len(samples)
    with open(filepath, "wb") as f:
        data = samples.tobytes()
        data_size = len(data)
        f.write(struct.pack("<4sI4s", b"RIFF", 36 + data_size, b"WAVE"))
        f.write(struct.pack("<4sI", b"fmt ", 16))
        f.write(struct.pack("<HH", 1, 1))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<IHH", sample_rate * 2, 2, 16))
        f.write(struct.pack("<4sI", b"data", data_size))
        f.write(data)


def generate_audio_file(cache_key: str, samples: np.ndarray,
                        sample_rate: int = SAMPLE_RATE) -> str:
    cache_dir = _get_cache_dir()
    path = os.path.join(cache_dir, f"{cache_key}.wav")
    if not os.path.exists(path):
        write_wav(path, samples, sample_rate)
    return path


def generate_from_peaks(peak_freqs: list[float], duration: float = 2.0) -> str:
    key = hashlib.md5(str(sorted(peak_freqs)).encode()).hexdigest()[:12]
    samples = synthesize_from_peaks(peak_freqs, duration)
    return generate_audio_file(f"peaks_{key}", samples)


def generate_from_note(note: str, instrument_type: str = "flute",
                       duration: float = 2.0) -> str:
    key = hashlib.md5(f"{note}_{instrument_type}_{duration}".encode()).hexdigest()[:12]
    samples = synthesize_from_note(note, duration, instrument_type)
    return generate_audio_file(f"note_{key}", samples)


def generate_from_freq(frequency: float, instrument_type: str = "flute",
                       duration: float = 2.0) -> str:
    key = hashlib.md5(f"{frequency:.1f}_{instrument_type}_{duration}".encode()).hexdigest()[:12]
    samples = synthesize_tone(frequency, duration, instrument_type)
    return generate_audio_file(f"freq_{key}", samples)
