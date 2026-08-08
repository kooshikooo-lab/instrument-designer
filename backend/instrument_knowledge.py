"""Structured acoustic knowledge base for computational wind instrument design.

Provides instrument families, hybrid definitions, scales, and material
properties with physically reasonable acoustic parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Self


__all__ = [
    "BoreType",
    "ExcitationType",
    "MaterialType",
    "InstrumentFamily",
    "HybridInstrument",
    "Scale",
    "Material",
    "INSTRUMENT_FAMILIES",
    "HYBRID_INSTRUMENTS",
    "SCALES",
    "MATERIALS",
    "get_acoustic_challenges",
    "suggest_material",
]


class BoreType(Enum):
    CYLINDRICAL = "cylindrical"
    CONICAL = "conical"
    PARABOLIC = "parabolic"
    EXPONENTIAL = "exponential"
    BESSEL = "bessel"


class ExcitationType(Enum):
    SINGLE_REED = "single_reed"
    DOUBLE_REED = "double_reed"
    FIPPLE = "fipple"
    LIP_REED = "lip_reed"
    AIR_JET = "air_jet"


class MaterialType(Enum):
    PLASTIC = "plastic"
    BRASS = "brass"
    WOOD = "wood"
    SILVER = "silver"
    NICKEL = "nickel"
    GOLD = "gold"
    STAINLESS = "stainless"
    TITANIUM = "titanium"
    COPPER = "copper"
    ACRYLIC = "acrylic"
    RESIN = "resin"
    CERAMIC = "ceramic"


@dataclass(frozen=True)
class InstrumentFamily:
    name: str
    description: str
    bore_type: BoreType
    excitation: ExcitationType
    closed_top: bool
    typical_bore_radius_mm: tuple[float, float]
    typical_length_mm: tuple[float, float]
    typical_hole_count: tuple[int, int]
    typical_hole_diameter_mm: tuple[float, float]
    octave_range: tuple[int, int]
    key_acoustic_challenges: list[str]


@dataclass(frozen=True)
class HybridInstrument:
    name: str
    description: str
    mouthpiece_family: str
    body_family: str
    feasibility: str
    acoustic_challenges: list[str]


@dataclass(frozen=True)
class Scale:
    name: str
    description: str
    intervals_cents: list[float]
    n_notes_per_octave: int


@dataclass(frozen=True)
class Material:
    name: MaterialType
    density_kgm3: float
    speed_of_sound_ms: float
    thermal_conductivity: float
    notes: str


INSTRUMENT_FAMILIES: dict[str, InstrumentFamily] = {
    "clarinet": InstrumentFamily(
        name="clarinet",
        description="Standard B-flat soprano clarinet with cylindrical bore and single reed",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=True,
        typical_bore_radius_mm=(7.0, 7.5),
        typical_length_mm=(580.0, 620.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(6.5, 7.5),
        octave_range=(3, 7),
        key_acoustic_challenges=[
            "register_break_management",
            "overblow_at_twelfth",
            "reed_response_at_piano",
            "cross_fingering_intonation",
        ],
    ),
    "bass_clarinet": InstrumentFamily(
        name="bass_clarinet",
        description="Bass clarinet in B-flat with extended range and larger bore",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=True,
        typical_bore_radius_mm=(10.0, 12.0),
        typical_length_mm=(1300.0, 1400.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(8.0, 10.0),
        octave_range=(2, 6),
        key_acoustic_challenges=[
            "register_break_management",
            "overblow_at_twelfth",
            "large_bore_intonation",
            "key_noise_amplification",
        ],
    ),
    "soprano_sax": InstrumentFamily(
        name="soprano_sax",
        description="Soprano saxophone in B-flat with conical bore",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.5, 6.5),
        typical_length_mm=(640.0, 680.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(5.0, 7.0),
        octave_range=(3, 7),
        key_acoustic_challenges=[
            "overblow_at_octave",
            "conical_bore_tuning",
            "altissimo_register",
            "intonation_vs_dynamics",
        ],
    ),
    "alto_sax": InstrumentFamily(
        name="alto_sax",
        description="Alto saxophone in E-flat with conical bore",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(7.0, 8.5),
        typical_length_mm=(690.0, 730.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(6.0, 8.0),
        octave_range=(2, 7),
        key_acoustic_challenges=[
            "overblow_at_octave",
            "conical_bore_tuning",
            "altissimo_register",
            "intonation_vs_dynamics",
        ],
    ),
    "tenor_sax": InstrumentFamily(
        name="tenor_sax",
        description="Tenor saxophone in B-flat with conical bore",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(8.5, 10.0),
        typical_length_mm=(840.0, 880.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(7.0, 9.0),
        octave_range=(2, 6),
        key_acoustic_challenges=[
            "overblow_at_octave",
            "conical_bore_tuning",
            "altissimo_register",
            "intonation_vs_dynamics",
        ],
    ),
    "baritone_sax": InstrumentFamily(
        name="baritone_sax",
        description="Baritone saxophone in E-flat with conical bore",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(11.0, 13.0),
        typical_length_mm=(1350.0, 1420.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(9.0, 12.0),
        octave_range=(1, 5),
        key_acoustic_challenges=[
            "overblow_at_octave",
            "conical_bore_tuning",
            "large_bore_intonation",
            "low_register_response",
        ],
    ),
    "flute": InstrumentFamily(
        name="flute",
        description="Concert flute in C with cylindrical bore and air-jet excitation",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.AIR_JET,
        closed_top=False,
        typical_bore_radius_mm=(9.0, 10.0),
        typical_length_mm=(660.0, 700.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(10.0, 13.0),
        octave_range=(4, 7),
        key_acoustic_challenges=[
            "embouchure_angle_sensitivity",
            "overblow_at_octave",
            "harmonic_matching",
            "condensation_management",
        ],
    ),
    "alto_flute": InstrumentFamily(
        name="alto_flute",
        description="Alto flute in G with larger bore and lower range",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.AIR_JET,
        closed_top=False,
        typical_bore_radius_mm=(12.0, 13.5),
        typical_length_mm=(820.0, 860.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(12.0, 15.0),
        octave_range=(3, 6),
        key_acoustic_challenges=[
            "embouchure_angle_sensitivity",
            "overblow_at_octave",
            "harmonic_matching",
            "larger_bore_airflow",
        ],
    ),
    "bass_flute": InstrumentFamily(
        name="bass_flute",
        description="Bass flute in C with wide bore and lowest flute range",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.AIR_JET,
        closed_top=False,
        typical_bore_radius_mm=(15.0, 17.0),
        typical_length_mm=(1250.0, 1320.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(14.0, 18.0),
        octave_range=(2, 5),
        key_acoustic_challenges=[
            "embouchure_angle_sensitivity",
            "large_bore_airflow_demand",
            "low_register_projection",
            "key_noise_amplification",
        ],
    ),
    "recorder": InstrumentFamily(
        name="recorder",
        description="Soprano recorder with conical bore and fipple mouthpiece",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.FIPPLE,
        closed_top=False,
        typical_bore_radius_mm=(5.0, 6.0),
        typical_length_mm=(300.0, 340.0),
        typical_hole_count=(7, 8),
        typical_hole_diameter_mm=(4.0, 6.0),
        octave_range=(4, 7),
        key_acoustic_challenges=[
            "fipple_voicing",
            "overblow_at_octave",
            "breath_pressure_control",
            "cross_fingering_intonation",
        ],
    ),
    "tin_whistle": InstrumentFamily(
        name="tin_whistle",
        description="Six-hole tin whistle with cylindrical bore and fipple mouthpiece",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.FIPPLE,
        closed_top=False,
        typical_bore_radius_mm=(5.0, 6.0),
        typical_length_mm=(280.0, 320.0),
        typical_hole_count=(6, 6),
        typical_hole_diameter_mm=(4.0, 5.5),
        octave_range=(4, 7),
        key_acoustic_challenges=[
            "fipple_voicing",
            "overblow_at_octave",
            "breath_pressure_control",
            "limited_dynamic_range",
        ],
    ),
    "xaphoon": InstrumentFamily(
        name="xaphoon",
        description="Compact single-reed cylindrical-bore instrument resembling a pocket saxophone",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(6.5, 7.5),
        typical_length_mm=(320.0, 360.0),
        typical_hole_count=(6, 9),
        typical_hole_diameter_mm=(5.0, 7.0),
        octave_range=(3, 7),
        key_acoustic_challenges=[
            "overblow_at_twelfth",
            "compact_bore_tuning",
            "reed_response_consistency",
            "limited_low_fundamental",
        ],
    ),
    "chalumeau": InstrumentFamily(
        name="chalumeau",
        description="Historical single-reed ancestor of the clarinet with cylindrical bore",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=True,
        typical_bore_radius_mm=(7.0, 7.5),
        typical_length_mm=(310.0, 350.0),
        typical_hole_count=(5, 6),
        typical_hole_diameter_mm=(5.0, 7.0),
        octave_range=(3, 5),
        key_acoustic_challenges=[
            "limited_range",
            "register_break_management",
            "overblow_at_twelfth",
            "small_hole_intonation",
        ],
    ),
    "bass_chalumeau": InstrumentFamily(
        name="bass_chalumeau",
        description="Larger chalumeau with extended low range",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.SINGLE_REED,
        closed_top=True,
        typical_bore_radius_mm=(10.0, 11.0),
        typical_length_mm=(700.0, 750.0),
        typical_hole_count=(5, 6),
        typical_hole_diameter_mm=(6.0, 8.0),
        octave_range=(2, 4),
        key_acoustic_challenges=[
            "limited_range",
            "register_break_management",
            "large_bore_reed_matching",
            "low_register_response",
        ],
    ),
    "trumpet": InstrumentFamily(
        name="trumpet",
        description="B-flat trumpet with predominantly cylindrical bore and flared bell",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(6.0, 6.5),
        typical_length_mm=(1300.0, 1400.0),
        typical_hole_count=(3, 4),
        typical_hole_diameter_mm=(10.0, 12.0),
        octave_range=(3, 7),
        key_acoustic_challenges=[
            "lip_reed_feedback",
            "harmonic_series_matching",
            "bell_flare_design",
            "mouthpiece_coupling",
        ],
    ),
    "trombone": InstrumentFamily(
        name="trombone",
        description="Tenor trombone with slide mechanism and cylindrical bore",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(7.5, 8.5),
        typical_length_mm=(2200.0, 2400.0),
        typical_hole_count=(0, 0),
        typical_hole_diameter_mm=(0.0, 0.0),
        octave_range=(2, 6),
        key_acoustic_challenges=[
            "lip_reed_feedback",
            "slide_position_tuning",
            "bell_flare_design",
            "low_register_support",
        ],
    ),
    "french_horn": InstrumentFamily(
        name="french_horn",
        description="Double horn in F/B-flat with conical bore and flared bell",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.0, 6.0),
        typical_length_mm=(3600.0, 3900.0),
        typical_hole_count=(3, 4),
        typical_hole_diameter_mm=(10.0, 12.0),
        octave_range=(2, 6),
        key_acoustic_challenges=[
            "lip_reed_feedback",
            "conical_bore_harmonics",
            "hand_stop_intonation",
            "bell_throat_design",
        ],
    ),
    "oboe": InstrumentFamily(
        name="oboe",
        description="Conical-bore double-reed instrument with penetrating tone",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.DOUBLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(4.0, 5.0),
        typical_length_mm=(580.0, 620.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(3.0, 5.0),
        octave_range=(4, 7),
        key_acoustic_challenges=[
            "reed_scraping_voicing",
            "overblow_at_octave",
            "small_bore_airflow",
            "cross_fingering_intonation",
        ],
    ),
    "bassoon": InstrumentFamily(
        name="bassoon",
        description="Long conical-bore double-reed instrument with U-bend",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.DOUBLE_REED,
        closed_top=False,
        typical_bore_radius_mm=(4.0, 7.0),
        typical_length_mm=(2500.0, 2600.0),
        typical_hole_count=(6, 7),
        typical_hole_diameter_mm=(5.0, 9.0),
        octave_range=(2, 5),
        key_acoustic_challenges=[
            "reed_scraping_voicing",
            "long_bore_taper_design",
            "complex_keywork_coupling",
            "tone_hole_placement_compromise",
        ],
    ),
    "shakuhachi": InstrumentFamily(
        name="shakuhachi",
        description="Japanese end-blown flute with flared bore and five finger holes",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.AIR_JET,
        closed_top=False,
        typical_bore_radius_mm=(8.0, 12.0),
        typical_length_mm=(540.0, 580.0),
        typical_hole_count=(4, 5),
        typical_hole_diameter_mm=(6.0, 8.0),
        octave_range=(3, 7),
        key_acoustic_challenges=[
            "embouchure_angle_sensitivity",
            "flared_bore_harmonics",
            "partial_finger_intonation",
            "bamboo_variation",
        ],
    ),
    "didgeridoo": InstrumentFamily(
        name="didgeridoo",
        description="Long cylindrical drone instrument with lip-reed excitation",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(15.0, 25.0),
        typical_length_mm=(1200.0, 1800.0),
        typical_hole_count=(0, 0),
        typical_hole_diameter_mm=(0.0, 0.0),
        octave_range=(1, 3),
        key_acoustic_challenges=[
            "continuous_drone_stability",
            "circular_breathing_adaptation",
            "natural_taper_irregularity",
            "formant_modulation_technique",
        ],
    ),
}

HYBRID_INSTRUMENTS: list[HybridInstrument] = [
    HybridInstrument(
        name="clarinet_mouthpiece_saxophone_body",
        description="B-flat clarinet mouthpiece fitted to a saxophone body",
        mouthpiece_family="clarinet",
        body_family="alto_sax",
        feasibility="moderate",
        acoustic_challenges=[
            "cylindrical_reed_coupling_to_conical_bore",
            "impedance_match_mismatch",
            "tuning_shift_across_registers",
            "register_break_relocation",
        ],
    ),
    HybridInstrument(
        name="saxophone_mouthpiece_clarinet_body",
        description="Alto saxophone mouthpiece fitted to a clarinet body",
        mouthpiece_family="alto_sax",
        body_family="clarinet",
        feasibility="moderate",
        acoustic_challenges=[
            "conical_mouthpiece_to_cylindrical_bore",
            "impedance_match_mismatch",
            "overblow_behavior_change",
            "intonation_compensation",
        ],
    ),
    HybridInstrument(
        name="flute_head_joint_recorder_body",
        description="Flute embouchure head joint attached to a recorder body",
        mouthpiece_family="flute",
        body_family="recorder",
        feasibility="low",
        acoustic_challenges=[
            "air_jet_to_fipple_voicing_mismatch",
            "bore_taper_conflict",
            "harmonic_structure_disruption",
            "embouchure_response_mismatch",
        ],
    ),
    HybridInstrument(
        name="brass_mouthpiece_woodwind_body",
        description="Trumpet mouthpiece coupled to a woodwind body",
        mouthpiece_family="trumpet",
        body_family="soprano_sax",
        feasibility="low",
        acoustic_challenges=[
            "lip_reed_to_single_reed_geometry",
            "impedance_match_mismatch",
            "harmonic_series_vs_finger_holes",
            "cup_depth_and_backbore_effect",
        ],
    ),
    HybridInstrument(
        name="xaphoon_body_clarinet_mouthpiece",
        description="Xaphoon body paired with a standard clarinet mouthpiece",
        mouthpiece_family="clarinet",
        body_family="xaphoon",
        feasibility="high",
        acoustic_challenges=[
            "length_scaling_intonation",
            "hole_placement_adjustment",
            "reed_strength_matching",
        ],
    ),
    HybridInstrument(
        name="alto_flute_body_bass_flute_head",
        description="Bass flute head joint on an alto flute body",
        mouthpiece_family="bass_flute",
        body_family="alto_flute",
        feasibility="moderate",
        acoustic_challenges=[
            "head_cut_angle_mismatch",
            "embouchure_size_difference",
            "bore_discontinuity",
            "register_harmonic_shift",
        ],
    ),
    HybridInstrument(
        name="oboe_reed_bassoon_body",
        description="Oboe reed fitted to a bassoon body",
        mouthpiece_family="oboe",
        body_family="bassoon",
        feasibility="low",
        acoustic_challenges=[
            "reed_dimension_mismatch",
            "airflow_and_back_pressure",
            "bore_taper_mismatch",
            "harmonic_series_incompatibility",
        ],
    ),
    HybridInstrument(
        name="tin_whistle_head_recorder_body",
        description="Tin whistle fipple head on a recorder body",
        mouthpiece_family="tin_whistle",
        body_family="recorder",
        feasibility="high",
        acoustic_challenges=[
            "windway_dimension_matching",
            "voicing_adjustment",
            "tone_hole_alignment",
        ],
    ),
    HybridInstrument(
        name="chalumeau_body_clarinet_mouthpiece",
        description="Clarinet mouthpiece on a chalumeau body",
        mouthpiece_family="clarinet",
        body_family="chalumeau",
        feasibility="high",
        acoustic_challenges=[
            "bore_radius_match",
            "closed_top_consistency",
            "length_scaling_intonation",
        ],
    ),
    HybridInstrument(
        name="french_horn_mouthpiece_trumpet_body",
        description="French horn mouthpiece on a trumpet body",
        mouthpiece_family="french_horn",
        body_family="trumpet",
        feasibility="moderate",
        acoustic_challenges=[
            "mouthpiece_cup_depth_mismatch",
            "bore_profile_change",
            "harmonic_series_shift",
            "bell_flare_compensation",
        ],
    ),
    HybridInstrument(
        name="shakuhachi_embouchure_flute_body",
        description="Shakuhachi-style embouchure cut on a concert flute body",
        mouthpiece_family="shakuhachi",
        body_family="flute",
        feasibility="low",
        acoustic_challenges=[
            "cutting_edge_geometry",
            "bore_taper_vs_cylinder",
            "finger_hole_mapping",
            "harmonic_excitation_differences",
        ],
    ),
    HybridInstrument(
        name="bassoon_reed_oboe_body",
        description="Bassoon reed adapted to an oboe body",
        mouthpiece_family="bassoon",
        body_family="oboe",
        feasibility="moderate",
        acoustic_challenges=[
            "reed_scaling_and_voicing",
            "bore_taper_incompatibility",
            "airflow_demand_mismatch",
            "register_response_change",
        ],
    ),
]

SCALES: dict[str, Scale] = {
    "12_tet": Scale(
        name="12_tet",
        description="Twelve-tone equal temperament — standard Western chromatic scale",
        intervals_cents=[0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1100.0],
        n_notes_per_octave=12,
    ),
    "24_tet": Scale(
        name="24_tet",
        description="Twenty-four-tone equal temperament — quarter tones",
        intervals_cents=[0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0, 650.0, 700.0, 750.0, 800.0, 850.0, 900.0, 950.0, 1000.0, 1050.0, 1100.0, 1150.0],
        n_notes_per_octave=24,
    ),
    "maqam_rast": Scale(
        name="maqam_rast",
        description="Maqam Rast — Arabic scale with neutral seconds characteristic of the rast family",
        intervals_cents=[0.0, 200.0, 350.0, 500.0, 700.0, 850.0, 1000.0],
        n_notes_per_octave=7,
    ),
    "slendro": Scale(
        name="slendro",
        description="Slendro — Javanese five-tone gamelan scale with roughly equidistant intervals",
        intervals_cents=[0.0, 120.0, 240.0, 420.0, 720.0],
        n_notes_per_octave=5,
    ),
    "just_intonation": Scale(
        name="just_intonation",
        description="Five-limit just intonation based on pure frequency ratios derived from the harmonic series",
        intervals_cents=[0.0, 203.9, 386.3, 498.0, 702.0, 884.4, 1088.3],
        n_notes_per_octave=7,
    ),
}

MATERIALS: dict[str, Material] = {
    "plastic": Material(
        name=MaterialType.PLASTIC,
        density_kgm3=1050.0,
        speed_of_sound_ms=2200.0,
        thermal_conductivity=0.20,
        notes="ABS or similar thermoplastic; lightweight, moisture-resistant, common for student instruments",
    ),
    "brass": Material(
        name=MaterialType.BRASS,
        density_kgm3=8500.0,
        speed_of_sound_ms=3700.0,
        thermal_conductivity=120.0,
        notes="Yellow brass alloy; standard for metal wind instruments, good machinability and acoustic response",
    ),
    "wood": Material(
        name=MaterialType.WOOD,
        density_kgm3=1300.0,
        speed_of_sound_ms=4000.0,
        thermal_conductivity=0.18,
        notes="Grenadilla or equivalent hardwood; traditional clarinet/oboe body material with warm tone",
    ),
    "silver": Material(
        name=MaterialType.SILVER,
        density_kgm3=10500.0,
        speed_of_sound_ms=3650.0,
        thermal_conductivity=430.0,
        notes="Sterling silver; used for flute bodies and head joints, bright projection and high thermal conductivity",
    ),
    "nickel": Material(
        name=MaterialType.NICKEL,
        density_kgm3=8600.0,
        speed_of_sound_ms=3700.0,
        thermal_conductivity=30.0,
        notes="Nickel silver alloy; common for keywork and less expensive instrument bodies",
    ),
    "gold": Material(
        name=MaterialType.GOLD,
        density_kgm3=19300.0,
        speed_of_sound_ms=3240.0,
        thermal_conductivity=310.0,
        notes="Pure or plated gold; premium flute head joints, dense with warm dark tone",
    ),
    "stainless": Material(
        name=MaterialType.STAINLESS,
        density_kgm3=8000.0,
        speed_of_sound_ms=5000.0,
        thermal_conductivity=15.0,
        notes="Stainless steel; corrosion-resistant, high stiffness, used in specialty instruments",
    ),
    "titanium": Material(
        name=MaterialType.TITANIUM,
        density_kgm3=4500.0,
        speed_of_sound_ms=4950.0,
        thermal_conductivity=22.0,
        notes="Lightweight and strong with excellent corrosion resistance; experimental instrument bodies",
    ),
    "copper": Material(
        name=MaterialType.COPPER,
        density_kgm3=8960.0,
        speed_of_sound_ms=4660.0,
        thermal_conductivity=400.0,
        notes="High thermal and electrical conductivity; used in specialty wind instruments and mutes",
    ),
    "acrylic": Material(
        name=MaterialType.ACRYLIC,
        density_kgm3=1180.0,
        speed_of_sound_ms=2700.0,
        thermal_conductivity=0.20,
        notes="Transparent thermoplastic; modern visual design, similar acoustic properties to plastic",
    ),
    "resin": Material(
        name=MaterialType.RESIN,
        density_kgm3=1200.0,
        speed_of_sound_ms=2500.0,
        thermal_conductivity=0.30,
        notes="Synthetic resin; common for student recorders and experimental 3D-printed instruments",
    ),
    "ceramic": Material(
        name=MaterialType.CERAMIC,
        density_kgm3=2700.0,
        speed_of_sound_ms=5000.0,
        thermal_conductivity=2.0,
        notes="Alumina or similar ceramic; hard, inert, used for ocarinas and experimental wind instruments",
    ),
}


def get_acoustic_challenges(family: str) -> list[str]:
    if family not in INSTRUMENT_FAMILIES:
        raise KeyError(f"Unknown instrument family: {family!r}")
    return list(INSTRUMENT_FAMILIES[family].key_acoustic_challenges)


def suggest_material(family: str, purpose: str = "experimental") -> MaterialType:
    if family not in INSTRUMENT_FAMILIES:
        raise KeyError(f"Unknown instrument family: {family!r}")
    family_obj = INSTRUMENT_FAMILIES[family]
    if purpose == "traditional":
        if family_obj.bore_type in (BoreType.CONICAL, BoreType.CYLINDRICAL) and family_obj.excitation in (
            ExcitationType.SINGLE_REED,
            ExcitationType.DOUBLE_REED,
        ):
            return MaterialType.WOOD
        if family_obj.excitation == ExcitationType.LIP_REED:
            return MaterialType.BRASS
        if family_obj.excitation == ExcitationType.AIR_JET:
            return MaterialType.SILVER
    if purpose == "student":
        if family_obj.excitation in (ExcitationType.SINGLE_REED, ExcitationType.DOUBLE_REED, ExcitationType.FIPPLE):
            return MaterialType.PLASTIC
        if family_obj.excitation == ExcitationType.LIP_REED:
            return MaterialType.BRASS
        if family_obj.excitation == ExcitationType.AIR_JET:
            return MaterialType.NICKEL
    if purpose == "experimental":
        return MaterialType.ACRYLIC
    if purpose == "professional":
        if family_obj.excitation in (ExcitationType.SINGLE_REED, ExcitationType.DOUBLE_REED):
            return MaterialType.WOOD
        if family_obj.excitation == ExcitationType.LIP_REED:
            return MaterialType.BRASS
        if family_obj.excitation == ExcitationType.AIR_JET:
            return MaterialType.SILVER
    if purpose == "premium":
        return MaterialType.GOLD
    return MaterialType.PLASTIC
