"""Core TMM math functions — phase-based resonance calculations.

Pure math with no instrument state. Ported from chalumier's ResonanceMath.kt.
"""
from __future__ import annotations

import math
from typing import Optional

from backend.physics.losses import KeefeLoss, NoLoss


# Matches chalumier's SPEED_OF_SOUND exactly (mm/s)
SPEED_OF_SOUND = 346100.0

FOUR_PI = 4.0 * math.pi


def circle_area(diameter: float) -> float:
    """Cross-sectional area of a circle from diameter."""
    r = diameter / 2.0
    return math.pi * r * r


def tanner(phase: float) -> float:
    """Convert phase to tangent domain."""
    return math.tan(phase * math.pi)


def untanner(x: float) -> float:
    """Convert from tangent domain back to phase."""
    return math.atan(x) / math.pi


def pipe_reply_phase(phase_end: float, length_on_wavelength: float) -> float:
    """Advance phase through a pipe segment of given length/wavelength (lossless)."""
    return phase_end + length_on_wavelength * 2.0


def pipe_reply_phase_with_loss(
    phase_end: float,
    length: float,
    radius: float,
    wavelength: float,
    loss_model=None,
) -> float:
    """Advance phase through a pipe segment with optional viscothermal losses.

    Args:
        phase_end: incoming phase (real number)
        length: segment length in mm
        radius: bore radius in mm
        wavelength: acoustic wavelength in mm
        loss_model: optional loss model (KeefeLoss or None)

    Returns:
        Phase after propagation including loss-induced phase shift
    """
    phase = phase_end + 2.0 * length / wavelength

    if loss_model is not None and radius > 0 and length > 0:
        loss_factor = loss_model.bore_loss(length, radius, wavelength)
        if isinstance(loss_factor, complex):
            phase += -loss_factor.imag

    return phase


def junction2_reply_phase(a0: float, a1: float, p1: float) -> float:
    """
    Phase reply for pipe 0 of a two-pipe junction.
    a0 = area of pipe 0, a1 = area of pipe 1, p1 = relative phase reply of pipe 1.
    """
    shift = math.floor(p1 + 0.5)
    return untanner(a1 / a0 * tanner(p1 - shift)) + shift


def junction3_reply_phase(a0: float, a1: float, a2: float, p1: float, p2: float) -> float:
    """
    Phase reply for pipe 0 of a three-pipe junction.
    Used for tone holes: a0 = bore area, a1 = bore area, a2 = hole area.
    """
    shift1 = math.floor(p1 + 0.5)
    shift2 = math.floor(p2 + 0.5)
    return untanner(
        a1 / a0 * tanner(p1 - shift1) + a2 / a0 * tanner(p2 - shift2)
    ) + shift1 + shift2


def end_flange_length_correction(outer_diameter: float, inner_diameter: float) -> float:
    """End correction for a pipe with a flange (bell). From Nederveen / chalumier."""
    a = inner_diameter / 2.0
    w = (outer_diameter - inner_diameter) / 2.0
    return a * (0.821 - 0.13 * (0.42 + w / a) ** (-0.54))


def hole_length_correction(hole_diameter: float, bore_diameter: float, closed: bool) -> float:
    """Length correction for a tone hole. Per Nederveen p.63-64. Returns 0 for closed holes."""
    if closed:
        return 0.0
    outer_correction = 0.7
    inner_correction = 1.3 - 0.9 * hole_diameter / bore_diameter
    a = hole_diameter / 2.0
    return a * (inner_correction + outer_correction)