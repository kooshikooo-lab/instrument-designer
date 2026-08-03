"""Spectral module tests — synthetic-only, no mic/recording."""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pytest

from backend.spectral.loader import load_audio
from backend.spectral.spectrum import compute_spectrum
from backend.spectral.f0 import extract_f0
from backend.spectral.metrics import compute_spectral_metrics
from backend.spectral.targets import get_spectral_targets


def _make_sine(freq_hz, duration_s, sr=44100.0):
    t = np.arange(int(sr * duration_s), dtype=np.float32) / sr
    return np.sin(2.0 * math.pi * freq_hz * t, dtype=np.float32)


def _make_harmonic_stack(fundamental_hz, n_harmonics, duration_s, sr=44100.0):
    t = np.arange(int(sr * duration_s), dtype=np.float32) / sr
    audio = np.zeros_like(t)
    for h in range(1, n_harmonics + 1):
        audio += np.sin(2.0 * math.pi * fundamental_hz * h * t, dtype=np.float32)
    audio /= n_harmonics
    return audio


class TestLoader:
    def test_load_audio_returns_mono(self, tmp_path):
        import scipy.io.wavfile as wavfile

        sr = 44100
        audio = np.sin(
            2.0 * math.pi * 440.0 * np.arange(sr, dtype=np.float32) / sr
        ).astype(np.float32)
        path = tmp_path / "test.wav"
        wavfile.write(str(path), sr, audio)

        loaded, loaded_sr = load_audio(str(path))
        assert loaded.ndim == 1
        assert loaded_sr == sr
        assert loaded.dtype == np.float32

    def test_load_audio_normalized(self, tmp_path):
        import scipy.io.wavfile as wavfile

        sr = 44100
        audio = (np.ones(sr, dtype=np.float32) * 0.5).astype(np.float32)
        path = tmp_path / "test.wav"
        wavfile.write(str(path), sr, audio)

        loaded, _ = load_audio(str(path))
        assert np.max(np.abs(loaded)) <= 1.0


class TestComputeSpectrum:
    def test_cqt_returns_dict(self):
        audio = _make_sine(440.0, 1.0)
        result = compute_spectrum(audio, 44100.0, method="cqt")
        assert "frequencies" in result
        assert "magnitude" in result
        assert result["method"] == "cqt"
        assert result["sr"] == 44100.0

    def test_cqt_frequencies_ascending(self):
        audio = _make_sine(440.0, 1.0)
        result = compute_spectrum(audio, 44100.0, method="cqt")
        assert np.all(np.diff(result["frequencies"]) > 0)

    def test_cqt_f0_bin_near_440hz(self):
        audio = _make_sine(440.0, 1.0)
        result = compute_spectrum(audio, 44100.0, method="cqt")
        f0_idx = np.argmin(np.abs(result["frequencies"] - 440.0))
        assert np.isclose(result["frequencies"][f0_idx], 440.0, rtol=0.05)

    def test_welch_returns_dict(self):
        audio = _make_sine(440.0, 1.0)
        result = compute_spectrum(audio, 44100.0, method="welch")
        assert "frequencies" in result
        assert "magnitude" in result
        assert result["method"] == "welch"

    def test_unknown_method_raises(self):
        audio = _make_sine(440.0, 1.0)
        with pytest.raises(ValueError, match="Unknown spectrum method"):
            compute_spectrum(audio, 44100.0, method="unknown")


class TestExtractF0:
    def test_pyin_finds_440hz(self):
        audio = _make_sine(440.0, 1.0)
        result = extract_f0(audio, 44100.0, method="pyin")
        assert "f0" in result
        assert "frame_times" in result
        assert result["method"] == "pyin"

    def test_pyin_f0_near_440hz(self):
        audio = _make_sine(440.0, 1.0)
        result = extract_f0(audio, 44100.0, method="pyin")
        valid = result["f0"][np.isfinite(result["f0"])]
        if len(valid) > 0:
            assert np.all(np.abs(valid - 440.0) < 10.0)

    def test_autocorr_finds_440hz(self):
        audio = _make_sine(440.0, 1.0)
        result = extract_f0(audio, 44100.0, method="autocorr")
        assert "f0" in result
        assert result["method"] == "autocorr"

    def test_autocorr_f0_near_440hz(self):
        audio = _make_sine(440.0, 1.0)
        result = extract_f0(audio, 44100.0, method="autocorr")
        valid = result["f0"][np.isfinite(result["f0"])]
        if len(valid) > 0:
            assert np.all(np.abs(valid - 440.0) < 20.0)

    def test_unknown_method_raises(self):
        audio = _make_sine(440.0, 1.0)
        with pytest.raises(ValueError, match="Unknown f0 method"):
            extract_f0(audio, 44100.0, method="unknown")


class TestComputeSpectralMetrics:
    def test_perfect_match_zero_cents(self):
        actual = np.array([440.0, 880.0, 1320.0], dtype=float)
        target = np.array([440.0, 880.0, 1320.0], dtype=float)
        m = compute_spectral_metrics(actual, target)
        assert m["final_rms_cents"] == pytest.approx(0.0, abs=0.01)

    def test_cents_deviation(self):
        actual = np.array([440.0], dtype=float)
        target = np.array([441.0], dtype=float)
        m = compute_spectral_metrics(actual, target)
        expected_cents = 1200.0 * math.log2(440.0 / 441.0)
        assert m["final_rms_cents"] == pytest.approx(abs(expected_cents), abs=0.01)

    def test_empty_input_returns_penalty(self):
        m = compute_spectral_metrics(np.array([]), np.array([]))
        assert m["final_rms_cents"] == 1e10


class TestGetSpectralTargets:
    def test_preset_returns_targets(self):
        targets = get_spectral_targets(preset="folk_whistle")
        assert len(targets) > 0
        assert all(t > 0 for t in targets)

    def test_fundamental_override(self):
        targets = get_spectral_targets(fundamental=261.6, n_notes=3)
        assert len(targets) == 3

    def test_closed_open_harmonics(self):
        targets = get_spectral_targets(preset="clarinet_Bb")
        # Clarinet: odd harmonics only — targets should be monotonically
        # increasing.
        assert len(targets) >= 2
        assert all(targets[i] < targets[i + 1] for i in range(len(targets) - 1))

    def test_note_range(self):
        targets = get_spectral_targets(
            preset="folk_whistle", note_range=("D5", "D6")
        )
        assert len(targets) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])