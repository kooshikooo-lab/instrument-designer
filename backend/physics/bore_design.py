"""Analytic tone-hole design physics (first-order, after Nederveen/Benade).

Pure physics — no optimization code here. These functions predict where tone
holes must go for a target scale, based on the standard acoustics of woodwind
air columns. The numerical optimizers in backend/inverse_design.py use this
layer for initialization and bounds, then refine against the full TMM.

Reference theory and conventions:
- Fletcher & Rossing, *The Physics of Musical Instruments*: an open-open pipe
  (flute) resonates at f_n = n·c/(2·L_eff); a closed-open pipe (clarinet/reed,
  quarter-wave) at odd f_n = n·c/(4·L_eff).
- Nederveen, *Acoustical Aspects of Woodwind Instruments*: tone-hole effective
  length and corrections.
- Benade & Murday (1967): open tone hole length corrections.
- UNSW flute acoustics (Wolfe): with holes open from the far end, the note is
  set by the distance from the blowing end to the FIRST OPEN HOLE; larger holes
  act closer to an acoustical short circuit ("sawn off" at the hole).
- Cross fingerings: closing holes *below* the first open hole extends the
  standing wave and flattens the pitch; this effect grows with frequency and
  with smaller holes. It is a key resource for chromatic notes on baroque and
  ethnic flutes.
- Speed of sound: c(T) ≈ 331.3 + 0.606·T (m/s) for dry air. Warm bore air during
  playing (22–30 °C, sometimes higher) can shift pitch by tens of cents, which
  is why instruments are warmed up before tuning and why makers design for a
  playing temperature rather than room temperature.
- Embouchure: the blowing end is not an ideal open end. The embouchure hole
  plus the player's lips add an end correction (of order a few mm to ~10 mm)
  that shortens the effective column. This is folded into the empirical
  calibration of the TMM rather than being modeled in detail here.
- Closed holes / pads: a closed tone hole is a small side cavity. Its volume
  adds compliance and lowers pitch slightly; a thick pad or key can modify that
  volume. The first-order effect is captured by the physical hole volume and
  chimney height; fine effects are left for the numerical optimizer.

Conventions: positions are measured from the FAR (bell) end, x=0 at the bell
and x=bore_length at the blowing end, matching TMMInstrument.
"""

from __future__ import annotations

import math
from typing import Sequence

from backend.tmm_acoustics import SPEED_OF_SOUND


def speed_of_sound_at(temperature_c: float, humidity: float = 0.0) -> float:
    """Speed of sound in air (mm/s) as a function of temperature.

    Dry-air approximation from the literature: c ≈ 331.3 + 0.606·T (m/s).
    Humidity raises it very slightly (≈ +0.1% at 100% RH at room temp), which
    we ignore at this order.

    Args:
        temperature_c: air temperature in °C.
        humidity: relative humidity in [0, 1] (ignored in this first-order model).

    Returns:
        Speed of sound in mm/s.
    """
    c_m_s = 331.3 + 0.606 * temperature_c
    # Very small humidity correction: ~ +0.6 m/s at 100% RH, 20°C
    if humidity > 0.0:
        c_m_s += 0.6 * humidity
    return c_m_s * 1000.0


def effective_length_for_frequency(
    frequency_hz: float,
    closed_top: bool = False,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> float:
    """Acoustic effective length (mm) whose fundamental is frequency_hz.

    Open-open (flute): half-wave, L_eff = c/(2f).
    Closed-open (clarinet): quarter-wave, L_eff = c/(4f).
    """
    if frequency_hz <= 0.0:
        return 0.0
    return speed_of_sound / (4.0 * frequency_hz) if closed_top \
        else speed_of_sound / (2.0 * frequency_hz)


def open_end_correction(bore_diameter_mm: float) -> float:
    """End correction of a cylindrical open end (~0.61 r)."""
    return 0.61 * bore_diameter_mm / 2.0


def embouchure_end_correction(bore_diameter_mm: float) -> float:
    """First-order blowing-end correction for a flute-like embouchure.

    The embouchure hole plus lip coverage acts as an imperfect open end. The
    correction is of order the bore radius; for a detailed flute head-joint
    model the cork cavity and riser tube must also be included.
    """
    return 0.61 * bore_diameter_mm / 2.0


def tonehole_effective_chimney(hole_diameter_mm: float, wall_thickness_mm: float) -> float:
    """Effective chimney height of a tone hole: t + 0.75·d_h (Rochester lab)."""
    return wall_thickness_mm + 0.75 * hole_diameter_mm


def tonehole_end_correction(
    hole_diameter_mm: float,
    wall_thickness_mm: float,
    bore_diameter_mm: float,
) -> float:
    """Extra effective length beyond the hole center for an OPEN tone hole.

    An open hole is not a perfect pressure node: the standing wave extends past
    it by an amount that grows as the hole gets smaller (less of a short
    circuit). In the limit of a very large hole it approaches the open-end
    correction of the pipe (~0.61·r_bore). Nederveen & Jansen (1998) give the
    inner end correction as varying from ~0.82·r_h for tiny holes down to
    ~0.16·r_h for holes as large as the bore.

    Model:
    - bore-radius-like radiation for a poorly-venting small hole;
    - hole-radius-like radiation for a large hole;
    - chimney mass amplified by the bore/hole radius ratio (small holes behave
      like longer side branches).
    """
    r_h = hole_diameter_mm / 2.0
    r_b = bore_diameter_mm / 2.0
    if r_h <= 0.0 or r_b <= 0.0:
        return 0.0
    openness = min(1.0, r_h / r_b)  # 1 = hole as big as the bore
    return (
        0.61 * r_b * (1.0 - openness)
        + 0.61 * r_h * openness
        + (wall_thickness_mm / 2.0) * (r_b / r_h)
    )


def closed_hole_compliance_volume(
    hole_diameter_mm: float,
    wall_thickness_mm: float,
    pad_height_mm: float = 0.0,
) -> float:
    """Acoustic volume (mm³) of a closed tone-hole cavity.

    A closed hole adds a small compliance at the bore wall. A pad or key above
    the hole traps an extra volume (pad_height mm above the hole mouth). The
    volume is approximate; exact values depend on pad shape and key cup.
    """
    r_h = hole_diameter_mm / 2.0
    if r_h <= 0.0:
        return 0.0
    effective_length = wall_thickness_mm + pad_height_mm
    return math.pi * r_h * r_h * effective_length


def hole_position_for_note(
    frequency_hz: float,
    bore_length_mm: float,
    hole_diameter_mm: float,
    wall_thickness_mm: float,
    bore_diameter_mm: float,
    closed_top: bool = False,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> float:
    """Position (mm from the bell end) of the first open hole for a target note.

    The note the instrument plays is set by the effective length from the
    blowing end to the first open hole: L_eff = hole_distance + end_correction.
    """
    L_eff = effective_length_for_frequency(frequency_hz, closed_top, speed_of_sound)
    if L_eff <= 0.0:
        return bore_length_mm / 2.0
    delta = tonehole_end_correction(
        hole_diameter_mm, wall_thickness_mm, bore_diameter_mm
    )
    dist_from_mouth = L_eff - delta
    return max(0.0, min(bore_length_mm, bore_length_mm - dist_from_mouth))


def hole_positions_for_scale(
    frequencies_hz: Sequence[float],
    bore_length_mm: float,
    hole_diameter_mm: float,
    wall_thickness_mm: float,
    bore_diameter_mm: float,
    closed_top: bool = False,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> list[float]:
    """First-open-hole positions for a rising scale (each higher note uses the
    next hole closer to the blowing end). Returns positions from the bell end."""
    return [
        hole_position_for_note(
            f, bore_length_mm, hole_diameter_mm, wall_thickness_mm,
            bore_diameter_mm, closed_top, speed_of_sound,
        )
        for f in frequencies_hz
    ]


def semitone_length_ratio() -> float:
    """Rough guide: one semitone ~ 5.6% of the effective length."""
    return 2.0 ** (1.0 / 12.0)
