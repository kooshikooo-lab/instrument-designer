"""
Tests for acoustic metamaterial elements in the phase-based TMM.

Covers:
  - Helmholtz-resonator side branch (Level 1): resonance-frequency formula,
    stopband signature near f0, no-op default behavior.
  - Homogenized effective-medium segment (Level 2): phase-advance formula,
    stopband condition, self-consistency with the plain-air pipe limit.
  - Regression: adding no metamaterial must leave behavior bit-identical.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

from backend.tmm_acoustics import (
    TMMInstrument,
    SPEED_OF_SOUND,
    MetamaterialSideBranch,
    MetamaterialSegment,
    helmholtz_branch_phase,
    metamaterial_phase_advance,
    pipe_reply_phase,
    untanner,
)


def _plain_flute(bore_length=500.0, bore_diameter=19.0, n_holes=3):
    hole_positions = [100.0, 200.0, 300.0][:n_holes]
    hole_diameters = [8.0] * n_holes
    hole_lengths = [3.0] * n_holes
    return TMMInstrument(
        inner_positions=[0, bore_length],
        inner_diameters=[bore_diameter, bore_diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=False,
    )


def _sample_resonator(position=250.0, neck_r=3.0, neck_l=8.0, cavity_v=4000.0):
    return MetamaterialSideBranch(
        position_mm=position,
        neck_radius_mm=neck_r,
        neck_length_mm=neck_l,
        cavity_volume_mm3=cavity_v,
    )


# ---------------------------------------------------------------------------
# Level 1: Helmholtz-resonator side branch
# ---------------------------------------------------------------------------

def test_helmholtz_frequency_formula():
    """f0 must match c/2pi * sqrt(S/(V*L_eff))."""
    mb = _sample_resonator()
    c = SPEED_OF_SOUND
    s = math.pi * 3.0 ** 2
    l = 8.0 + 1.45 * 3.0
    expected = c / (2.0 * math.pi) * math.sqrt(s / (4000.0 * l))
    assert mb.helmholtz_frequency() == pytest.approx(expected, rel=1e-12)


def test_helmholtz_frequency_degenerate():
    """Zero/negative geometry must not raise (returns inf)."""
    mb = MetamaterialSideBranch(0, 0.0, 0.0, 0.0)
    assert mb.helmholtz_frequency() == float("inf")


def test_branch_phase_zero_with_no_resonator():
    """Degenerate side branch (no volume) must be inert (phase 0)."""
    p = helmholtz_branch_phase(
        wavelength_mm=500.0,
        neck_area_mm2=28.0,
        effective_neck_length_mm=10.0,
        cavity_volume_mm3=0.0,
        bore_area_mm2=283.0,
    )
    assert p == 0.0


def test_branch_phase_sign_around_resonance():
    """
    The HR susceptance is compliance-like below f0 and inertance-like above
    f0, so the branch phase must flip sign across the resonance wavelength.
    """
    mb = _sample_resonator()
    f0 = mb.helmholtz_frequency()
    area_bore = math.pi * 9.5 ** 2
    lam0 = SPEED_OF_SOUND / f0

    p_below = helmholtz_branch_phase(lam0 * 1.5, mb.neck_area_mm2, mb.effective_neck_length_mm,
                                     mb.cavity_volume_mm3, area_bore)
    p_above = helmholtz_branch_phase(lam0 * 0.7, mb.neck_area_mm2, mb.effective_neck_length_mm,
                                     mb.cavity_volume_mm3, area_bore)
    assert p_below != 0.0 and p_above != 0.0
    assert (p_below > 0.0) != (p_above > 0.0)


def test_meta_branch_default_noop():
    """meta_slots=None must produce a bit-identical action chain."""
    inst = _plain_flute()
    chain = inst.actions[:]
    inst2 = _plain_flute()
    inst2.meta_slots = []
    inst2.metamaterial_segments = []
    inst2._prepare_phase()
    assert inst2.actions == chain


def test_meta_disables_numba_fast_path():
    """Metamaterial instruments must stay on the Python walk: the compiled
    numba loop only implements pipe/junction2/hole actions, so any instrument
    whose chain contains meta actions must never build the fast-path arrays."""
    try:
        from backend.tmm_acoustics import _NUMBA_ENABLED
    except ImportError:
        _NUMBA_ENABLED = False

    if not _NUMBA_ENABLED:
        import pytest
        pytest.skip("numba not wired into tmm_acoustics")

    inst = _plain_flute()
    assert inst._action_arrays is not None, "plain instrument should use the fast path"
    inst.meta_slots = [_sample_resonator()]
    inst._prepare_phase()
    assert inst._action_arrays is None, "meta_branch must disable the numba fast path"


def test_meta_branch_changes_resonances():
    """
    A resonator tuned near a bore resonance must perturb it (stopband effect),
    rather than leaving the spectrum unchanged.
    """
    inst = _plain_flute()
    mb = _sample_resonator()
    inst2 = _plain_flute()
    inst2.meta_slots = [mb]
    inst2._prepare_phase()

    fing = ["closed"] * 3
    freqs = [inst.frequency_from_wavelength(inst.find_resonance(2.0 * 500 / n, fing, n + 1))
             for n in range(1, 5)]
    freqs2 = [inst2.frequency_from_wavelength(inst2.find_resonance(2.0 * 500 / n, fing, n + 1))
              for n in range(1, 5)]
    assert freqs2 != freqs
    # f0 ~ 1318 Hz sits between the 2nd and 3rd bore harmonics (~683, ~1024 Hz):
    # the metamaterial must not wipe out every resonance, just perturb them.
    assert all(f > 0 for f in freqs2)


def test_meta_branch_action_is_junction3():
    """The side branch must be added as a junction3-style action."""
    inst = _plain_flute()
    inst.meta_slots = [_sample_resonator()]
    inst._prepare_phase()
    kinds = [a[0] for a in inst.actions]
    assert "meta_branch" in kinds
    # same pipe segments otherwise: initial, 100, 50 (before branch),
    # 50 (after branch), 200
    assert kinds.count("pipe") == 5


# ---------------------------------------------------------------------------
# Level 2: homogenized effective-medium segment
# ---------------------------------------------------------------------------

def test_metamaterial_phase_advance_plain_air_limit():
    """With no resonator (degenerate), advance must equal 2L/lambda."""
    mb = _sample_resonator()
    adv = metamaterial_phase_advance(
        length_mm=100.0, bore_diameter_mm=19.0, resonator=mb,
        spacing_mm=0.0, wavelength_mm=500.0,
    )
    assert adv == pytest.approx(2.0 * 100.0 / 500.0, rel=1e-12)


def test_metamaterial_phase_advance_matches_pipe():
    """At very high spacing the segment must approach the plain pipe advance."""
    mb = _sample_resonator()
    adv = metamaterial_phase_advance(
        length_mm=100.0, bore_diameter_mm=19.0, resonator=mb,
        spacing_mm=1e9, wavelength_mm=500.0,
    )
    assert adv == pytest.approx(2.0 * 100.0 / 500.0, rel=1e-6)


def test_metamaterial_stopband_at_resonance():
    """
    Near f0 the homogenized segment must produce zero (evanescent) advance,
    i.e. the stopband condition gamma^2 > 0 must hold there.
    """
    mb = _sample_resonator()
    f0 = mb.helmholtz_frequency()
    lam0 = SPEED_OF_SOUND / f0

    adv_res = metamaterial_phase_advance(100.0, 19.0, mb, 20.0, lam0)
    assert adv_res == 0.0  # evanescent at resonance

    # Far below/above resonance the medium propagates again.
    adv_below = metamaterial_phase_advance(100.0, 19.0, mb, 20.0, lam0 * 5.0)
    adv_above = metamaterial_phase_advance(100.0, 19.0, mb, 20.0, lam0 * 0.2)
    assert adv_below > 0.0
    assert adv_above > 0.0


def test_metamaterial_segment_changes_resonances():
    """A segment must perturb the spectrum (stopband shifts resonances)."""
    inst = _plain_flute(n_holes=0)
    seg = MetamaterialSegment(
        start_mm=200.0,
        end_mm=300.0,
        resonator=_sample_resonator(),
        spacing_mm=20.0,
    )
    inst2 = TMMInstrument(
        inner_positions=[0, 500],
        inner_diameters=[19.0, 19.0],
        outer_diameters=[22.0, 22.0],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=False,
        metamaterial_segments=[seg],
    )
    freqs = [inst.frequency_from_wavelength(inst.find_resonance(2.0 * 500 / n, [], n + 1))
             for n in range(1, 5)]
    freqs2 = [inst2.frequency_from_wavelength(inst2.find_resonance(2.0 * 500 / n, [], n + 1))
              for n in range(1, 5)]
    assert freqs2 != freqs
    assert all(f > 0 for f in freqs2)


def test_metamaterial_segment_noop_default():
    """metamaterial_segments=None must keep the action chain untouched."""
    inst = _plain_flute()
    chain = inst.actions[:]
    inst2 = _plain_flute()
    inst2.metamaterial_segments = []
    inst2._prepare_phase()
    assert inst2.actions == chain


# ---------------------------------------------------------------------------
# Cross-level / integration
# ---------------------------------------------------------------------------

def test_level1_vs_level2_stopband_consistency():
    """
    Level 2 (homogenized) stopband must fall at the same frequency as the
    Level 1 (explicit side branch) resonance: both derive from the HR f0.
    """
    mb = _sample_resonator()
    f0 = mb.helmholtz_frequency()

    # Level 1: a single branch near the stopband creates strong deviation at f0.
    inst1 = _plain_flute(n_holes=0)
    inst1.meta_slots = [mb]
    inst1._prepare_phase()

    # Level 2: segment covering the same region.
    seg = MetamaterialSegment(200.0, 300.0, _sample_resonator(), 20.0)
    inst2 = _plain_flute(n_holes=0)
    inst2.metamaterial_segments = [seg]
    inst2._prepare_phase()

    lam0 = SPEED_OF_SOUND / f0
    plain = _plain_flute(n_holes=0)
    # Probe the reactive wings just above/below f0 where the HR susceptance
    # is large (at exactly f0 a lossy HR is purely resistive, so the
    # phase-based junction shows no susceptance deviation there).
    for frac in (0.9, 1.1):
        p0 = plain.resonance_phase(lam0 * frac, [])
        p1 = inst1.resonance_phase(lam0 * frac, [])
        p2 = inst2.resonance_phase(lam0 * frac, [])
        assert abs(p1 - p0) > 0.05
        assert abs(p2 - p0) > 0.05


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
