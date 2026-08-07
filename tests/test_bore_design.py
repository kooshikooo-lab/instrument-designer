"""Tests for backend.physics.bore_design.

These are physics-consistency tests: they verify that the analytic first-order
formulas behave like the standard woodwind-acoustics relations they encode.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.physics import bore_design as bd
from backend.tmm_acoustics import SPEED_OF_SOUND


def test_speed_of_sound_at_matches_literature():
    """c(T) = 331.3 + 0.606*T m/s; our function returns mm/s."""
    assert bd.speed_of_sound_at(0.0) == pytest.approx(331.3 * 1000.0, rel=1e-6)
    assert bd.speed_of_sound_at(20.0) == pytest.approx(343.42 * 1000.0, rel=1e-6)
    assert bd.speed_of_sound_at(24.0) == pytest.approx(345.844 * 1000.0, rel=1e-6)


def test_effective_length_open_open_vs_closed_open():
    """Open-open L_eff = c/(2f); closed-open L_eff = c/(4f)."""
    f = 261.63
    c = SPEED_OF_SOUND
    open_open = bd.effective_length_for_frequency(f, closed_top=False)
    closed_open = bd.effective_length_for_frequency(f, closed_top=True)
    assert open_open == pytest.approx(c / (2.0 * f), rel=1e-9)
    assert closed_open == pytest.approx(c / (4.0 * f), rel=1e-9)
    assert closed_open == pytest.approx(open_open / 2.0, rel=1e-9)


def test_end_corrections_are_positive_and_scale_with_radius():
    """Open-end and embouchure corrections are ~0.61 r."""
    d = 14.0
    corr = bd.open_end_correction(d)
    assert corr == pytest.approx(0.61 * d / 2.0, rel=1e-9)
    assert corr > 0.0
    assert bd.embouchure_end_correction(d) == pytest.approx(corr, rel=1e-9)


def test_tonehole_end_correction_positive_and_size_dependent():
    """Small holes relative to the bore have larger end corrections than large ones."""
    bore = 14.0
    small = bd.tonehole_end_correction(5.0, 3.0, bore)
    medium = bd.tonehole_end_correction(7.0, 3.0, bore)
    large = bd.tonehole_end_correction(13.0, 3.0, bore)
    assert 0.0 < large < medium < small
    # Large hole should approach the open-end correction of the bore.
    assert large < bd.open_end_correction(bore) * 1.5


def test_hole_positions_for_scale_increase_with_pitch():
    """Higher notes -> first open hole closer to blowing end -> larger position."""
    freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]
    positions = bd.hole_positions_for_scale(
        freqs, bore_length_mm=660.0, hole_diameter_mm=7.0,
        wall_thickness_mm=3.0, bore_diameter_mm=14.0,
    )
    assert len(positions) == len(freqs)
    # Higher frequency -> hole farther from bell (closer to mouth).
    assert all(positions[i] < positions[i + 1] for i in range(len(positions) - 1))
    # All inside the bore.
    assert all(0.0 <= p <= 660.0 for p in positions)


def test_hole_position_for_note_inside_bore():
    p = bd.hole_position_for_note(
        440.0, bore_length_mm=600.0, hole_diameter_mm=7.0,
        wall_thickness_mm=3.0, bore_diameter_mm=14.0,
    )
    assert 0.0 <= p <= 600.0


def test_closed_hole_compliance_volume():
    """Closed-hole volume grows with diameter, wall thickness, and pad height."""
    v1 = bd.closed_hole_compliance_volume(7.0, 3.0, 0.0)
    v2 = bd.closed_hole_compliance_volume(7.0, 5.0, 0.0)
    v3 = bd.closed_hole_compliance_volume(7.0, 3.0, 2.0)
    v4 = bd.closed_hole_compliance_volume(9.0, 3.0, 0.0)
    assert 0.0 < v1 < v2
    assert v3 == pytest.approx(v2, rel=1e-9)
    assert v4 > v1


def test_semitone_length_ratio():
    assert bd.semitone_length_ratio() == pytest.approx(2.0 ** (1.0 / 12.0), rel=1e-9)
