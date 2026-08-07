"""Tests for inverse design from WAV (Tier 1 sound analysis + Tier 3 timbre matching).

Covers the self-contained stages of backend.inverse_design:
- synthesize_harmonic / save_synthetic_wav / analyze_wav (f0 recovery accuracy)
- estimate_harmonic_magnitudes (bounded, decaying envelope — regression for the
  1/round_trip inversion bug)
- match_timbre (well-conditioned cost, finite improvement)
"""
import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.inverse_design import (
    synthesize_harmonic,
    save_synthetic_wav,
    analyze_wav,
    build_target_envelope,
    estimate_harmonic_magnitudes,
    match_timbre,
)
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND


def _make_candidate(bore_length=600.0, closed_top=False, n_holes=6):
    return {
        "bore_length_mm": bore_length,
        "hole_positions_mm": [float(bore_length * (i + 1) / (n_holes + 1)) for i in range(n_holes)],
        "hole_diameters_mm": [8.0] * n_holes,
        "hole_lengths_mm": [3.0] * n_holes,
        "closed_top": closed_top,
    }


def _make_inst(radii=None, bore_length=600.0):
    if radii is None:
        radii = np.linspace(7.0, 9.0, 6)
    cand = _make_candidate(bore_length=bore_length)
    return tmm_instrument_from_radii(
        radii_mm=radii,
        bore_length_mm=bore_length,
        hole_positions_mm=cand["hole_positions_mm"],
        hole_diameters_mm=cand["hole_diameters_mm"],
        hole_lengths_mm=cand["hole_lengths_mm"],
        closed_top=cand["closed_top"],
    )


# ---------------------------------------------------------------------------
# Tier 1: sound analysis
# ---------------------------------------------------------------------------

def test_synthesize_harmonic_shape():
    sig = synthesize_harmonic(220.0, n_harmonics=8, duration_s=1.0, sample_rate=44100)
    assert sig.ndim == 1
    assert len(sig) == 44100
    assert np.max(np.abs(sig)) <= 1.0


def test_synthesize_odd_only_skips_even_harmonics():
    odd = synthesize_harmonic(220.0, n_harmonics=6, odd_only=True)
    all_h = synthesize_harmonic(220.0, n_harmonics=6, odd_only=False)
    # Odd-only spectrum: fft at even multiples of 220 should be ~0
    ft = np.fft.rfft(odd)
    freqs = np.fft.rfftfreq(len(odd), 1.0 / 44100)
    def _mag(f):
        idx = int(np.argmin(np.abs(freqs - f)))
        return abs(ft[idx])
    assert _mag(440.0) < _mag(660.0) * 0.1  # 2nd harmonic suppressed vs 3rd


def test_analyze_wav_recovers_f0(tmp_path):
    f0 = 220.0
    path = str(tmp_path / "clar.wav")
    save_synthetic_wav(path, synthesize_harmonic(f0, n_harmonics=10, odd_only=True))
    analysis = analyze_wav(path)
    assert analysis["fundamental_hz"] > 0.0
    cents_err = abs(1200.0 * math.log2(analysis["fundamental_hz"] / f0))
    assert cents_err < 20.0, f"f0 recovery off by {cents_err:.1f} cents"


def test_analyze_wav_flute_f0(tmp_path):
    f0 = 261.63
    path = str(tmp_path / "flute.wav")
    save_synthetic_wav(path, synthesize_harmonic(f0, n_harmonics=12, odd_only=False))
    analysis = analyze_wav(path)
    cents_err = abs(1200.0 * math.log2(analysis["fundamental_hz"] / f0))
    assert cents_err < 20.0


def test_analyze_wav_returns_harmonics_and_envelope(tmp_path):
    f0 = 220.0
    path = str(tmp_path / "h.wav")
    save_synthetic_wav(path, synthesize_harmonic(f0, n_harmonics=8))
    a = analyze_wav(path)
    assert len(a["harmonic_frequencies"]) >= 5
    assert len(a["spectrum_frequencies"]) == len(a["spectrum_magnitudes"])
    assert len(a["envelope_frequencies"]) == len(a["envelope_magnitudes"])
    assert a["sample_rate"] == 44100


# ---------------------------------------------------------------------------
# Tier 3: timbre matching + magnitude model
# ---------------------------------------------------------------------------

def test_estimate_harmonic_magnitudes_bounded():
    """Regression: magnitudes must be finite, positive, and decay with harmonic index."""
    inst = _make_inst()
    em = estimate_harmonic_magnitudes(inst, n_harmonics=8)
    assert np.all(np.isfinite(em))
    assert np.all(em >= 0.0)
    assert em[0] == 1.0
    assert np.all(np.diff(em) <= 1e-9), f"envelope should not grow: {em}"


def test_estimate_magnitudes_response_to_geometry():
    """A wider bell should radiate differently than a narrow one (model is sensitive)."""
    wide = _make_inst(radii=np.full(6, 15.0))
    narrow = _make_inst(radii=np.full(6, 5.0))
    em_wide = estimate_harmonic_magnitudes(wide, n_harmonics=8)
    em_narrow = estimate_harmonic_magnitudes(narrow, n_harmonics=8)
    # At minimum, results differ (model responds to geometry)
    assert not np.allclose(em_wide, em_narrow)


def test_build_target_envelope_normalized():
    from backend.inverse_design import analyze_wav
    analysis = analyze_wav(None) if False else None  # placeholder guard
    # Direct test without file: build from a synthetic analysis dict
    analysis = {
        "fundamental_hz": 220.0,
        "harmonic_frequencies": np.array([220.0, 440.0, 660.0, 880.0]),
        "harmonic_amplitudes": np.array([1.0, 0.5, 0.25, 0.125]),
    }
    freqs, amps = build_target_envelope(analysis, n_harmonics=8)
    assert len(freqs) == 8
    assert len(amps) == 8
    assert amps[0] == 1.0
    assert np.all(amps >= 0.0)
    # Missing harmonics get extrapolated, not zeroed
    assert amps[7] > 0.0


def test_match_timbre_cost_well_conditioned(tmp_path):
    """Cost must be finite and small (regression for 1/round_trip inversion bug)."""
    f0 = 261.63
    path = str(tmp_path / "flute.wav")
    save_synthetic_wav(path, synthesize_harmonic(f0, n_harmonics=12, odd_only=False))
    analysis = analyze_wav(path)
    result = match_timbre(_make_candidate(), analysis, n_gen=5, pop_size=10)
    assert np.isfinite(result["tier3_cost_initial"])
    assert np.isfinite(result["tier3_cost_optimized"])
    assert result["tier3_cost_initial"] < 1.0, f"cost too large: {result['tier3_cost_initial']}"
    assert len(result["bore_radii_optimized"]) == 6


def test_design_scale_numpy_ga_returns_candidates():
    """Tier-2 numpy-GA fallback must produce a playable, in-tune scale."""
    from backend.inverse_design import _fingering_ladder, design_scale_numpy_ga
    from backend.physics.losses import KeefeLoss

    result = design_scale_numpy_ga(261.63, None, hole_count=6, pop_size=50, n_gen=30)
    assert result["method"] == "numpy_ga"
    assert len(result["candidates"]) == 2
    cand = result["candidates"][0]
    assert len(cand["hole_positions_mm"]) == 6
    assert len(cand["hole_diameters_mm"]) == 6
    assert len(result["target_frequencies"]) == 7
    assert np.all(np.isfinite(result["fitness"]))

    from backend.tmm_acoustics import tmm_instrument_from_radii

    inst = tmm_instrument_from_radii(
        np.linspace(7.0, 9.0, 6), cand["bore_length_mm"],
        cand["hole_positions_mm"], cand["hole_diameters_mm"],
        cand["hole_lengths_mm"], closed_top=False,
        loss_model=KeefeLoss(),
    )
    target_wavelengths = [SPEED_OF_SOUND / t for t in result["target_frequencies"]]
    played = inst.compute_fingered_frequencies(
        target_wavelengths, _fingering_ladder(6), n_register=2
    )
    cents = [1200.0 * math.log2(p / t) for t, p in zip(result["target_frequencies"], played)]
    rms = float(np.sqrt(np.mean(np.square(cents))))
    assert rms < 10.0, f"scale not in tune: RMS {rms:.1f}c"
    assert max(abs(c) for c in cents) < 15.0, f"worst note off by {max(abs(c) for c in cents):.1f}c"


def test_design_scale_falls_back_without_agent():
    """design_scale must use the numpy GA when generative_agent is missing."""
    import backend.inverse_design as inv

    original = inv._generative_design
    inv._generative_design = None
    try:
        result = inv.design_scale(261.63, hole_count=4, n_candidates=1)
        assert result["method"] == "numpy_ga"
        assert result["geometry"]["closed_top"] is False
    finally:
        inv._generative_design = original
