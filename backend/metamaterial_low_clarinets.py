"""
Low-clarinet family metamaterial models: shared geometries + design helpers.

Single source of truth for the compact low-clarinet metamaterial program, so
tests, benchmarks and the STL exporter all agree on the geometries.

Geometries are grounded in this repo's own folded-instrument presets
(``backend/cadquery_export.py``: ``bass_clarinet_7hole_folded`` and the folded
paperclip contra/octocontra family) and the bass-clarinet spec research
(``research/bass_clarinet_specifications.md``):

    bass            Bb   1211.3 mm x 25 mm   closed-top  7-hole + register hole
    contra_alto     Eb   1600.0 mm x 32 mm   closed-top  plain tube
    contra_bass     Bb   1900.0 mm x 38 mm   closed-top  plain tube
    octocontra_alt  EEb  2200.0 mm x 42 mm   closed-top  plain tube
    octocontra_bas  BBB  2600.0 mm x 48 mm   closed-top  plain tube

Low-register-extension mechanism (Level 1/2 HR side branches, see
chat-logs/2026-08-03-metamaterial-implementation-research.md):

  Below the HR resonance f0 the side branch is compliance-like, so a
  resonator array near the closed (reed) end acts as distributed compliance
  that lengthens the tube (Re(k_eff) > k_air) -> lower fundamental at the same
  physical length. Above f0 the medium turns evanescent (stopband), so f0 is
  placed above the notes we keep. Units match the phase TMM: mm, mm/s.
"""

import math

from backend.tmm_acoustics import (
    SPEED_OF_SOUND,
    MetamaterialSegment,
    MetamaterialSideBranch,
    TMMInstrument,
)

# Neck geometry shared by every design below (printable, matches the parity
# sweep used to validate the metamaterial machinery).
DEFAULT_NECK_RADIUS_MM = 4.0
DEFAULT_NECK_LENGTH_MM = 8.0
HR_NECK_END_CORRECTION_FACTOR = 1.45

#: Low-clarinet family geometries (all closed-top, folded paperclip).
#: ``holes`` are (position_mm, diameter_mm, chimney_mm) from the open (bell) end.
LOW_CLARINETS = {
    "bass": {
        "name": "Bass clarinet Bb",
        "bore_length_mm": 1211.3,
        "bore_diameter_mm": 25.0,
        "outer_diameter_mm": 37.0,
        "wall_thickness_mm": 6.0,
        "bend_radius_mm": 50.0,
        "holes": [(80.0, 2.5, 3.0)] + [(p, 11.0, 5.0) for p in (
            175.9, 292.9, 337.5, 444.6, 532.0, 609.8, 636.4)],
        "low_note": ("D2", 73.416),
        "extension_target_hz": 58.27,  # Bb1 (concert), low-C equivalent
        "source": "config/bass_clarinet_7hole.json; cadquery bass_clarinet_7hole_folded",
    },
    "contra_alto": {
        "name": "Contra-alto clarinet Eb",
        "bore_length_mm": 1600.0,
        "bore_diameter_mm": 32.0,
        "outer_diameter_mm": 44.0,
        "wall_thickness_mm": 6.0,
        "bend_radius_mm": 70.0,
        "holes": [],
        "low_note": ("Eb1", None),
        "extension_target_hz": 0.8 * SPEED_OF_SOUND / (4.0 * 1600.0),  # ~3.9 st lower
        "source": "cadquery contra_alto_clarinet_Eb (Leblanc paperclip)",
    },
    "contra_bass": {
        "name": "Contra-bass clarinet Bb",
        "bore_length_mm": 1900.0,
        "bore_diameter_mm": 38.0,
        "outer_diameter_mm": 52.0,
        "wall_thickness_mm": 7.0,
        "bend_radius_mm": 80.0,
        "holes": [],
        "low_note": ("Bb0", None),
        "extension_target_hz": 0.8 * SPEED_OF_SOUND / (4.0 * 1900.0),
        "source": "cadquery contra_bass_clarinet_Bb (Leblanc 340 paperclip)",
    },
    "octocontra_alto": {
        "name": "Octo-contra-alto clarinet EEb",
        "bore_length_mm": 2200.0,
        "bore_diameter_mm": 42.0,
        "outer_diameter_mm": 58.0,
        "wall_thickness_mm": 8.0,
        "bend_radius_mm": 90.0,
        "holes": [],
        "low_note": ("EEb0", None),
        "extension_target_hz": 0.8 * SPEED_OF_SOUND / (4.0 * 2200.0),
        "source": "cadquery octo_contra_alto_clarinet_EEb",
    },
    "octocontrabass": {
        "name": "Octo-contrabass clarinet BBB",
        "bore_length_mm": 2600.0,
        "bore_diameter_mm": 48.0,
        "outer_diameter_mm": 66.0,
        "wall_thickness_mm": 9.0,
        "bend_radius_mm": 100.0,
        "holes": [],
        "low_note": ("BBB0", None),
        "extension_target_hz": 0.8 * SPEED_OF_SOUND / (4.0 * 2600.0),
        "source": "cadquery octo_contra_bass_clarinet_BBB",
    },
    "subcontrabass": {
        "name": "Sub-contrabass clarinet BBBb",
        "bore_length_mm": 3000.0,
        "bore_diameter_mm": 55.0,
        "outer_diameter_mm": 75.0,
        "wall_thickness_mm": 10.0,
        "bend_radius_mm": 110.0,
        "holes": [],
        "low_note": ("BBb0", None),
        "extension_target_hz": 0.8 * SPEED_OF_SOUND / (4.0 * 3000.0),
        "source": "family extrapolation (deepest woodwind beyond the octocontras)",
    },
}


def make_low_clarinet(
    key: str,
    meta_slots=None,
    metamaterial_segments=None,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> TMMInstrument:
    """Build a phase-TMM model of a low clarinet (unfolded length; the fold
    preserves the acoustic length so 1D modeling is exact for the layout)."""
    spec = LOW_CLARINETS[key]
    holes = spec["holes"]
    return TMMInstrument(
        inner_positions=[0, spec["bore_length_mm"]],
        inner_diameters=[spec["bore_diameter_mm"], spec["bore_diameter_mm"]],
        outer_diameters=[spec["outer_diameter_mm"], spec["outer_diameter_mm"]],
        hole_positions=[h[0] for h in holes],
        hole_diameters=[h[1] for h in holes],
        hole_lengths=[h[2] for h in holes],
        closed_top=True,
        speed_of_sound=speed_of_sound,
        meta_slots=meta_slots,
        metamaterial_segments=metamaterial_segments,
    )


def all_closed_fingers(key: str):
    """'closed' fingering for every hole (register-1 all-closed note)."""
    return ["closed"] * len(LOW_CLARINETS[key]["holes"])


def analytic_f1(key: str, speed_of_sound: float = SPEED_OF_SOUND) -> float:
    """Quarter-wave closed-open fundamental c/(4L) of the plain tube."""
    return speed_of_sound / (4.0 * LOW_CLARINETS[key]["bore_length_mm"])


def cavity_volume_for_f0(
    f0_hz: float,
    neck_r_mm: float = DEFAULT_NECK_RADIUS_MM,
    neck_l_mm: float = DEFAULT_NECK_LENGTH_MM,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> float:
    """Cavity volume (mm^3) that tunes the HR to f0 (mm-consistent units)."""
    s = math.pi * neck_r_mm ** 2
    l_eff = neck_l_mm + HR_NECK_END_CORRECTION_FACTOR * neck_r_mm
    return s / (l_eff * (2.0 * math.pi * f0_hz / speed_of_sound) ** 2)


def hr_f0(
    cavity_v_mm3: float,
    neck_r_mm: float = DEFAULT_NECK_RADIUS_MM,
    neck_l_mm: float = DEFAULT_NECK_LENGTH_MM,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> float:
    """HR resonance from cavity volume (inverse of cavity_volume_for_f0)."""
    return speed_of_sound / (2.0 * math.pi) * math.sqrt(
        math.pi * neck_r_mm ** 2
        / (cavity_v_mm3 * (neck_l_mm + HR_NECK_END_CORRECTION_FACTOR * neck_r_mm))
    )


def make_hr_segment(
    key: str,
    f0_hz: float,
    spacing_mm: float,
    start_frac: float = 0.9,
    neck_r_mm: float = DEFAULT_NECK_RADIUS_MM,
    neck_l_mm: float = DEFAULT_NECK_LENGTH_MM,
) -> tuple:
    """Homogenized metamaterial segment near the closed end plus its HR cell.

    Returns (MetamaterialSegment, MetamaterialSideBranch). The array occupies
    [L*start_frac, L] (the closed/reed end, where pressure loading is maximum).
    """
    spec = LOW_CLARINETS[key]
    start = spec["bore_length_mm"] * start_frac
    end = spec["bore_length_mm"]
    v = cavity_volume_for_f0(f0_hz, neck_r_mm, neck_l_mm)
    mb = MetamaterialSideBranch(
        position_mm=start, neck_radius_mm=neck_r_mm,
        neck_length_mm=neck_l_mm, cavity_volume_mm3=v,
    )
    seg = MetamaterialSegment(start, end, mb, spacing_mm)
    return seg, mb


def phase_at(inst: TMMInstrument, fingers, freq_hz: float) -> float:
    """Resonance phase at a frequency (1.0 = fundamental, 2.0 = 12th)."""
    return inst.resonance_phase(SPEED_OF_SOUND / freq_hz, fingers)


def fundamental(inst: TMMInstrument, fingers) -> float:
    """Register-1 (all-closed) frequency in Hz."""
    wl = inst.find_resonance(4.0 * inst.length, fingers, 1)
    return inst.frequency_from_wavelength(wl)


def registers(inst: TMMInstrument, fingers, n: int = 3):
    """First n register frequencies (Hz); closed-open = odd harmonics."""
    return [inst.frequency_from_wavelength(
        inst.find_resonance(4.0 * inst.length / (2 * r - 1), fingers, r))
        for r in range(1, n + 1)]


def twelfth_deviation(inst: TMMInstrument, fingers) -> float:
    """Register-2 vs register-1 ratio in cents relative to a perfect 12th (3:1).

    Positive = the 12th is sharp. Near-closed-end compliance arrays stretch
    this ratio (the low-register extension trades against 12th intonation).
    """
    r = registers(inst, fingers, 2)
    return 1200.0 * math.log2((r[1] / r[0]) / 3.0)


def _gamma2(freq_hz, bore_diameter_mm, v_mm3, neck_r_mm, neck_l_mm, spacing_mm,
            speed_of_sound, rho=1.2e-9):
    """Propagation-constant condition gamma^2 (mm-2); > 0 => stopband."""
    c = speed_of_sound
    omega = 2.0 * math.pi * freq_hz
    a = math.pi * (bore_diameter_mm / 2.0) ** 2
    s_n = math.pi * neck_r_mm ** 2
    l_n = neck_l_mm + HR_NECK_END_CORRECTION_FACTOR * neck_r_mm
    m_ac = rho * l_n / s_n
    c_ac = v_mm3 / (rho * c * c)
    denom = omega * m_ac - 1.0 / (omega * c_ac)
    if denom == 0.0:
        return float("inf")
    return -omega * omega / (c * c) + omega * rho / (a * spacing_mm * denom)


def stopband_bounds(
    key: str,
    f0_hz: float,
    spacing_mm: float,
    start_frac: float = 0.9,
    neck_r_mm: float = DEFAULT_NECK_RADIUS_MM,
    neck_l_mm: float = DEFAULT_NECK_LENGTH_MM,
) -> tuple:
    """[f_lo, f_hi] of the evanescent band for a homogenized segment.

    gamma^2 > 0 inside (f_lo, f_hi). f_lo is just above f0 (the HR resonance);
    f_hi is the upper bandgap edge, found by bisection.
    """
    spec = LOW_CLARINETS[key]
    v = cavity_volume_for_f0(f0_hz, neck_r_mm, neck_l_mm)

    def g(f):
        return _gamma2(f, spec["bore_diameter_mm"], v, neck_r_mm, neck_l_mm,
                       spacing_mm, SPEED_OF_SOUND)

    # Start a hair above f0: exactly at f0 the shunt denom is 0 and floating
    # point can land on either side, reporting a spurious non-stopband.
    lo, hi = f0_hz * (1.0 + 1e-6), max(f0_hz * 100.0, 1e6)
    if g(lo) <= 0.0:
        return (None, None)  # no stopband above f0 at this spacing
    for _ in range(140):
        mid = 0.5 * (lo + hi)
        if g(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return (f0_hz, lo)


def tune_f0_to_fundamental(
    key: str,
    target_hz: float,
    spacing_mm: float = 30.0,
    start_frac: float = 0.9,
    lo_hz: float = 120.0,
    hi_hz: float = 1200.0,
    tol_hz: float = 0.05,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> tuple:
    """Bisection on HR f0 to hit a target all-closed fundamental.

    Lower f0 = more compliance loading = lower fundamental. Returns
    (f0_hz, MetamaterialSegment, achieved_f1).
    """
    fingers = all_closed_fingers(key)

    def f1_at(f0):
        seg, _ = make_hr_segment(key, f0, spacing_mm, start_frac)
        inst = make_low_clarinet(key, metamaterial_segments=[seg],
                                 speed_of_sound=speed_of_sound)
        return fundamental(inst, fingers)

    if f1_at(lo_hz) > target_hz:
        raise ValueError(f"key={key}: even f0={lo_hz} Hz cannot reach "
                         f"target {target_hz:.2f} Hz (achieved {f1_at(lo_hz):.2f})")
    for _ in range(80):
        mid = 0.5 * (lo_hz + hi_hz)
        f = f1_at(mid)
        if abs(f - target_hz) < tol_hz:
            break
        if f > target_hz:  # need more loading -> lower f0
            hi_hz = mid
        else:
            lo_hz = mid
    seg, _ = make_hr_segment(key, mid, spacing_mm, start_frac)
    return mid, seg, f1_at(mid)


def explicit_hr_array(
    key: str,
    f0_hz: float,
    spacing_mm: float,
    start_frac: float = 0.9,
    neck_r_mm: float = DEFAULT_NECK_RADIUS_MM,
    neck_l_mm: float = DEFAULT_NECK_LENGTH_MM,
) -> TMMInstrument:
    """Level 1 instrument: explicit HR side-branch array matching a
    homogenized design (f0, spacing) over the closed-end segment."""
    spec = LOW_CLARINETS[key]
    start = spec["bore_length_mm"] * start_frac
    end = spec["bore_length_mm"]
    v = cavity_volume_for_f0(f0_hz, neck_r_mm, neck_l_mm)
    slots, i = [], 0
    while True:
        pos = start + i * spacing_mm + spacing_mm / 2.0
        if pos > end:
            break
        slots.append(MetamaterialSideBranch(
            position_mm=pos, neck_radius_mm=neck_r_mm,
            neck_length_mm=neck_l_mm, cavity_volume_mm3=v))
        i += 1
    return make_low_clarinet(key, meta_slots=slots)


def resonator_f0(slot: MetamaterialSideBranch) -> float:
    """Resonance frequency of an explicit HR side branch."""
    return hr_f0(slot.cavity_volume_mm3, slot.neck_radius_mm,
                 slot.neck_length_mm)


def graded_f0_schedule(n: int, f0_start_hz: float, f0_stop_hz: float,
                       profile: str = "linear") -> list:
    """Per-resonator HR resonance frequencies for a graded array.

    Linear profile interpolates f0 linearly across the array; geometric
    profile interpolates the f0 ratio geometrically (constant semitone steps).
    With ``f0_start == f0_stop`` both collapse to a uniform array.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if profile == "linear":
        if n == 1:
            return [f0_start_hz]
        return [f0_start_hz + (f0_stop_hz - f0_start_hz) * i / (n - 1)
                for i in range(n)]
    if profile == "geometric":
        if n == 1:
            return [f0_start_hz]
        r = (f0_stop_hz / f0_start_hz) ** (1.0 / (n - 1))
        return [f0_start_hz * r ** i for i in range(n)]
    raise ValueError(f"unknown profile: {profile!r} (use 'linear' or 'geometric')")


def graded_hr_array(
    key: str,
    f0_start_hz: float,
    f0_stop_hz: float,
    spacing_mm: float,
    start_frac: float = 0.9,
    neck_r_mm: float = DEFAULT_NECK_RADIUS_MM,
    neck_l_mm: float = DEFAULT_NECK_LENGTH_MM,
    profile: str = "linear",
) -> TMMInstrument:
    """Level 1 graded HR array over the closed-end segment.

    Each resonator's cavity volume is tuned so its resonance sweeps
    ``f0_start -> f0_stop`` along the array (IOP 2025 graded HR arrays:
    non-uniform resonators broaden the attenuation band vs a uniform array).
    Homogenized (Level 2) segments hold a single f0, so graded designs are
    explicit-array (Level 1) only. With ``f0_start == f0_stop`` this reduces
    to the uniform ``explicit_hr_array``.
    """
    spec = LOW_CLARINETS[key]
    start = spec["bore_length_mm"] * start_frac
    end = spec["bore_length_mm"]
    schedule = graded_f0_schedule(
        int((end - start) // spacing_mm) or 1, f0_start_hz, f0_stop_hz,
        profile)
    slots = []
    for i, f0 in enumerate(schedule):
        pos = start + i * spacing_mm + spacing_mm / 2.0
        if pos > end:
            break
        v = cavity_volume_for_f0(f0, neck_r_mm, neck_l_mm)
        slots.append(MetamaterialSideBranch(
            position_mm=pos, neck_radius_mm=neck_r_mm,
            neck_length_mm=neck_l_mm, cavity_volume_mm3=v))
    return make_low_clarinet(key, meta_slots=slots)


def array_resonance_band(slots) -> tuple:
    """(f0_min, f0_max) resonance-frequency band spanned by an explicit array."""
    f0s = [resonator_f0(s) for s in slots]
    if not f0s:
        return (None, None)
    return (min(f0s), max(f0s))


def tune_f0_to_fundamental_l1(
    key: str,
    target_hz: float,
    spacing_mm: float = 30.0,
    start_frac: float = 0.9,
    lo_hz: float = 120.0,
    hi_hz: float = 2000.0,
    tol_hz: float = 0.05,
) -> tuple:
    """L1-based tuner: bisection on f0 using the EXPLICIT HR array (the
    physical model). L2 gives a fast conservative first guess; this refines
    the design so the printed array actually hits the target note.

    Returns (f0_hz, n_resonators, achieved_f1, instrument).
    """
    fingers = all_closed_fingers(key)

    def f1_at(f0):
        inst = explicit_hr_array(key, f0, spacing_mm, start_frac)
        return fundamental(inst, fingers)

    if f1_at(lo_hz) > target_hz:
        raise ValueError(f"key={key}: even f0={lo_hz} Hz cannot reach "
                         f"target {target_hz:.2f} Hz via the explicit array")
    for _ in range(90):
        mid = 0.5 * (lo_hz + hi_hz)
        f = f1_at(mid)
        if abs(f - target_hz) < tol_hz:
            break
        if f > target_hz:  # need more loading -> lower f0
            hi_hz = mid
        else:
            lo_hz = mid
    inst = explicit_hr_array(key, mid, spacing_mm, start_frac)
    spec = LOW_CLARINETS[key]
    seg_len = spec["bore_length_mm"] * (1.0 - start_frac)
    n = int(seg_len // spacing_mm)
    return mid, n, f1_at(mid), inst
