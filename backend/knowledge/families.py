"""Instrument family constraints and specifications."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.knowledge.materials import (
    BoreType,
    ExcitationType,
    MaterialType,
    MaterialProperties,
)


@dataclass
class FamilyConstraints:
    """Physical constraints for an instrument family."""
    family: str
    bore_type: BoreType
    excitation: ExcitationType
    closed_top: bool
    typical_bore_radius_mm: tuple[float, float]
    typical_length_mm: tuple[float, float]
    typical_hole_count: tuple[int, int]
    typical_hole_diameter_mm: tuple[float, float]
    harmonic_series: str = "all"
    description: str = ""
    key_acoustic_challenges: list[str] = field(default_factory=list)
    materials: list[MaterialType] = field(default_factory=list)
    fingering_complexity: str = "moderate"
    octave_range: tuple[float, float] = (1.0, 3.0)


INSTRUMENT_FAMILIES: dict[str, FamilyConstraints] = {
    "clarinet": FamilyConstraints(
        family="Clarinet",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.REED,
        closed_top=True,
        typical_bore_radius_mm=(7.0, 8.0),
        typical_length_mm=(400, 1000),
        typical_hole_count=(17, 24),
        typical_hole_diameter_mm=(3.0, 8.0),
        harmonic_series="odd",
        description="Single-reed cylindrical bore with closed top. Odd harmonics only, register key breaks 12th.",
        key_acoustic_challenges=[
            "Register break at 12th requires careful bore taper",
            "Closed top means odd harmonics only — timbre is hollow",
            "Tone hole placement must balance intonation and fingering",
            "Bell flare affects low-note radiation efficiency",
        ],
        materials=[MaterialType.WOOD, MaterialType.PLASTIC, MaterialType.BRASS, MaterialType.CARBON_FIBER],
        fingering_complexity="high",
        octave_range=(2.5, 4.0),
    ),
    "saxophone": FamilyConstraints(
        family="Saxophone",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.REED,
        closed_top=True,
        typical_bore_radius_mm=(8.0, 18.0),
        typical_length_mm=(600, 1500),
        typical_hole_count=(18, 24),
        typical_hole_diameter_mm=(4.0, 14.0),
        harmonic_series="all",
        description="Single-reed conical bore. All harmonics present. Conical taper avoids register break.",
        key_acoustic_challenges=[
            "Conical bore must be precise for even intonation across range",
            "Large tone holes needed for conical geometry",
            "Octave key mechanism is mechanically complex",
            "Neck/bore junction critical for response",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER, MaterialType.CARBON_FIBER],
        fingering_complexity="moderate",
        octave_range=(2.5, 3.5),
    ),
    "flute": FamilyConstraints(
        family="Flute",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(8.5, 10.0),
        typical_length_mm=(600, 750),
        typical_hole_count=(14, 17),
        typical_hole_diameter_mm=(5.0, 12.0),
        harmonic_series="all",
        description="Edge-tone excitation on open cylindrical bore. All harmonics. Headjoint critical.",
        key_acoustic_challenges=[
            "Headjoint geometry (embouchure, chimney, riser) dominates timbre",
            "Open-open pipe means register break at octave (easier than clarinet)",
            "Tone holes must be precisely placed for cross-fingering stability",
            "Lip plate and riser geometry affect resistance and projection",
        ],
        materials=[MaterialType.SILVER, MaterialType.BRASS, MaterialType.WOOD, MaterialType.PLASTIC, MaterialType.CARBON_FIBER],
        fingering_complexity="moderate",
        octave_range=(3.0, 3.5),
    ),
    "recorder": FamilyConstraints(
        family="Recorder",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(5.0, 12.0),
        typical_length_mm=(300, 600),
        typical_hole_count=(8, 10),
        typical_hole_diameter_mm=(4.0, 9.0),
        harmonic_series="all",
        description="Fipple flute with tapered bore. Simple fingering, limited dynamics.",
        key_acoustic_challenges=[
            "Tapered bore (reverse cone) balances low/high register tuning",
            "Windway geometry fixes air speed — limited dynamic range",
            "Thumb hole and pinky holes manage register breaks",
            "Labium edge sharpness critical for response",
        ],
        materials=[MaterialType.PLASTIC, MaterialType.WOOD, MaterialType.BAMBOO],
        fingering_complexity="simple",
        octave_range=(2.0, 2.5),
    ),
    "folk_flute": FamilyConstraints(
        family="Folk Flute",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(6.0, 10.0),
        typical_length_mm=(300, 600),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(5.0, 9.0),
        harmonic_series="all",
        description="Simple cylindrical bore fipple or end-blown flute. 6 holes, diatonic scale.",
        key_acoustic_challenges=[
            "Cylindrical bore + 6 holes limits to diatonic scale + cross-fingerings",
            "End correction varies with bell flare — affects low notes",
            "Limited venting for chromatic notes",
        ],
        materials=[MaterialType.BAMBOO, MaterialType.WOOD, MaterialType.PVC, MaterialType.PLASTIC],
        fingering_complexity="simple",
        octave_range=(2.0, 2.5),
    ),
    "shakuhachi": FamilyConstraints(
        family="Shakuhachi",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(8.0, 10.0),
        typical_length_mm=(450, 550),
        typical_hole_count=(5, 5),
        typical_hole_diameter_mm=(8.0, 12.0),
        harmonic_series="all",
        description="Japanese end-blown bamboo flute. 5 holes, rich timbre via meri/kari technique.",
        key_acoustic_challenges=[
            "Meru/kari (lowering/raising pitch by head tilt) requires bore to support pitch bending",
            "Root end (natural bamboo) creates irregular bore — part of timbre",
            "Utaguchi (blowing edge) angle and depth critical for response",
        ],
        materials=[MaterialType.BAMBOO, MaterialType.WOOD],
        fingering_complexity="moderate",
        octave_range=(2.5, 3.0),
    ),
    "oboe": FamilyConstraints(
        family="Oboe",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.DOUBLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(4.0, 8.0),
        typical_length_mm=(600, 700),
        typical_hole_count=(20, 25),
        typical_hole_diameter_mm=(2.0, 6.0),
        harmonic_series="all",
        description="Double-reed conical bore. High impedance reed, complex keywork.",
        key_acoustic_challenges=[
            "Double reed impedance must match conical bore for even response",
            "Very small tone holes — manufacturing precision critical",
            "Reed making is a separate skill; reed variability dominates timbre",
            "Half-hole technique requires precise hole sizing",
        ],
        materials=[MaterialType.WOOD, MaterialType.PLASTIC],
        fingering_complexity="high",
        octave_range=(2.5, 3.0),
    ),
    "bassoon": FamilyConstraints(
        family="Bassoon",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.DOUBLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.0, 20.0),
        typical_length_mm=(2400, 2800),
        typical_hole_count=(22, 28),
        typical_hole_diameter_mm=(3.0, 10.0),
        harmonic_series="all",
        description="Double-reed conical bore, folded tube. Complex keywork for long bore.",
        key_acoustic_challenges=[
            "Folded bore introduces impedance irregularities at U-bend",
            "Very long bore — low notes need large holes or keys",
            "Register key (whisper key) prevents overblowing to 2nd register",
            "Wing joint and boot joint dimensions affect stability",
        ],
        materials=[MaterialType.WOOD, MaterialType.PLASTIC],
        fingering_complexity="high",
        octave_range=(3.0, 3.5),
    ),
    "trumpet": FamilyConstraints(
        family="Trumpet",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.5, 7.5),
        typical_length_mm=(1300, 1500),
        typical_hole_count=(3, 3),
        typical_hole_diameter_mm=(12.0, 18.0),
        harmonic_series="all",
        description="Lip-reed excitation on conical bore with piston valves. Bell flare is key.",
        key_acoustic_challenges=[
            "Bell flare rate determines timbre projection and intonation",
            "Valve ports create impedance discontinuities — must be compensated",
            "Leadpipe taper critical for high-note response",
            "Mouthpiece cup depth/backbore affects playability dramatically",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER, MaterialType.BELL_METAL],
        fingering_complexity="moderate",
        octave_range=(3.0, 3.5),
    ),
    "trombone": FamilyConstraints(
        family="Trombone",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(6.5, 8.0),
        typical_length_mm=(2700, 3000),
        typical_hole_count=(1, 2),
        typical_hole_diameter_mm=(10.0, 18.0),
        harmonic_series="all",
        description="Slide trombone — continuous pitch via slide. No valves.",
        key_acoustic_challenges=[
            "Slide tube must be perfectly straight and smooth for low friction",
            "Bell flare dominates projection — material matters most here",
            "Slide positions are non-uniform (shorter at high end)",
            "Water key placement affects intonation",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER, MaterialType.BELL_METAL],
        fingering_complexity="moderate",
        octave_range=(2.5, 3.0),
    ),
    "french_horn": FamilyConstraints(
        family="French Horn",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.5, 9.5),
        typical_length_mm=(3600, 4000),
        typical_hole_count=(3, 4),
        typical_hole_diameter_mm=(12.0, 20.0),
        harmonic_series="all",
        description="Lip-reed conical bore with rotary valves. Very long bore, small bore.",
        key_acoustic_challenges=[
            "Long bore + small radius = high impedance → difficult high notes",
            "Rotary valves add more impedance than piston valves",
            "Hand in bell is part of acoustic design — affects intonation",
            "Conical taper must be very precise over 4m length",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER, MaterialType.BELL_METAL],
        fingering_complexity="moderate",
        octave_range=(3.5, 4.0),
    ),
    "tuba": FamilyConstraints(
        family="Tuba",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(10.0, 25.0),
        typical_length_mm=(4500, 6000),
        typical_hole_count=(3, 5),
        typical_hole_diameter_mm=(18.0, 30.0),
        harmonic_series="all",
        description="Largest brass instrument. Wide bore, massive bell, 3-5 valves.",
        key_acoustic_challenges=[
            "Huge air volume required — player lung capacity is limiting factor",
            "Valve port size must scale with bore diameter",
            "Bell size vs portability tradeoff",
            "Pedal tones (fundamental) require massive bore",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER, MaterialType.BELL_METAL],
        fingering_complexity="moderate",
        octave_range=(3.0, 3.5),
    ),
    "didgeridoo": FamilyConstraints(
        family="Didgeridoo",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(15.0, 35.0),
        typical_length_mm=(1000, 1800),
        typical_hole_count=(0, 0),
        typical_hole_diameter_mm=(0, 0),
        harmonic_series="odd",
        description="Traditional Australian drone instrument. No tone holes — pitch via vocal tract.",
        key_acoustic_challenges=[
            "Natural termite-hollowed bore is irregular — part of signature timbre",
            "Vocal tract impedance couples to bore — player is part of instrument",
            "Circular breathing technique required for continuous sound",
            "No finger holes means no pitch change — only timbre variation",
        ],
        materials=[MaterialType.BAMBOO, MaterialType.WOOD],
        fingering_complexity="simple",
        octave_range=(0.5, 1.0),
    ),
    "ocarina": FamilyConstraints(
        family="Ocarina",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(15.0, 30.0),
        typical_length_mm=(80, 180),
        typical_hole_count=(8, 12),
        typical_hole_diameter_mm=(4.0, 10.0),
        harmonic_series="all",
        description="Vessel flute (Helmholtz resonator). Pitch determined by total hole area.",
        key_acoustic_challenges=[
            "Pitch depends on total open hole area, not hole positions",
            "Limited volume → limited dynamic range",
            "Intonation depends on hole size ratios, not placement",
            "Chamber geometry affects higher modes",
        ],
        materials=[MaterialType.PLASTIC, MaterialType.WOOD, MaterialType.BAMBOO],
        fingering_complexity="moderate",
        octave_range=(1.0, 2.0),
    ),
    "kazoo": FamilyConstraints(
        family="Kazoo",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.REED,
        closed_top=False,
        typical_bore_radius_mm=(10.0, 15.0),
        typical_length_mm=(100, 200),
        typical_hole_count=(0, 0),
        typical_hole_diameter_mm=(0, 0),
        harmonic_series="all",
        description="Membrane resonator. Modulates voice, not a true wind instrument.",
        key_acoustic_challenges=[
            "Not a true wind instrument (membrane modifies voice)",
            "Pitch is determined by singer, not bore",
            "Membrane tension affects timbre",
        ],
        materials=[MaterialType.PLASTIC, MaterialType.ALUMINUM],
        fingering_complexity="simple",
        octave_range=(0, 0),
    ),
}


def _family_lowest_note(family: str) -> tuple[float, int]:
    """Get the lowest note frequency and octave range for an instrument family."""
    from backend.tmm_acoustics import SPEED_OF_SOUND
    c = SPEED_OF_SOUND

    FAMILY_LOWEST_NOTE = {
        "clarinet":     (146.83, 3),
        "saxophone":    (174.61, 3),
        "flute":        (261.63, 3),
        "recorder":     (523.25, 2),
        "folk_flute":   (392.00, 2),
        "shakuhachi":   (293.66, 2),
        "oboe":         (233.08, 3),
        "bassoon":      (58.27, 3),
        "trumpet":      (164.81, 3),
        "trombone":     (77.78, 3),
        "french_horn":  (87.31, 3),
        "tuba":         (43.65, 3),
        "didgeridoo":   (65.41, 1),
        "ocarina":      (392.00, 2),
        "kazoo":        (261.63, 1),
    }

    if family in FAMILY_LOWEST_NOTE:
        return FAMILY_LOWEST_NOTE[family]

    constraints = INSTRUMENT_FAMILIES.get(family)
    if constraints:
        bore_len = sum(constraints.typical_length_mm) / 2
        closed = constraints.closed_top
        fundamental = c / (4.0 * bore_len) if closed else c / (2.0 * bore_len)
        octaves = max(int(sum(constraints.octave_range) / 2), 1)
        return (fundamental, octaves)

    return (261.63, 2)


def get_acoustic_challenges(
    mouthpiece_family: str,
    body_family: str,
) -> list[str]:
    """Get acoustic challenges for a hybrid instrument combination."""
    mp = INSTRUMENT_FAMILIES.get(mouthpiece_family)
    body = INSTRUMENT_FAMILIES.get(body_family)
    challenges = []
    if mp:
        challenges.extend([f"Mouthpiece ({mp.family}): {c}" for c in mp.key_acoustic_challenges])
    if body:
        challenges.extend([f"Body ({body.family}): {c}" for c in body.key_acoustic_challenges])
    if mp and body:
        if mp.harmonic_series != body.harmonic_series:
            challenges.append(
                f"Harmonic mismatch: mouthpiece excites {mp.harmonic_series} harmonics, "
                f"body naturally supports {body.harmonic_series}"
            )
        if mp.bore_type != body.bore_type:
            challenges.append(
                f"Bore type mismatch: {mp.bore_type.value} mouthpiece → {body.bore_type.value} body"
            )
    return challenges


def suggest_material(
    family: str,
    budget: str = "medium",
    purpose: str = "performance",
) -> MaterialType:
    """Suggest appropriate material based on instrument family and constraints."""
    constraints = INSTRUMENT_FAMILIES.get(family)
    if not constraints or not constraints.materials:
        return MaterialType.PLASTIC

    if purpose == "education" or budget == "low":
        if MaterialType.PLASTIC in constraints.materials:
            return MaterialType.PLASTIC
        if MaterialType.PVC in constraints.materials:
            return MaterialType.PVC

    if purpose == "experimental":
        if MaterialType.PLASTIC in constraints.materials:
            return MaterialType.PLASTIC

    if budget == "high":
        priority = [MaterialType.SILVER, MaterialType.BELL_METAL, MaterialType.BRASS, MaterialType.WOOD]
    else:
        priority = [MaterialType.BRASS, MaterialType.WOOD, MaterialType.PLASTIC, MaterialType.PVC]

    for mat in priority:
        if mat in constraints.materials:
            return mat

    return constraints.materials[0]