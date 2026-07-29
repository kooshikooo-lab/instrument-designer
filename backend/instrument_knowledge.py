"""
Acoustic physics knowledge base for all wind instrument families.

Encodes the physical principles that constrain instrument design:
- Bore geometry → pitch range, timbre, intonation
- Hole placement → fingering mechanics, cross-fingering behavior
- Material properties → loss characteristics, radiation efficiency
- Family-specific constraints → what works, what doesn't

This module is used by the generative agent to:
1. Validate that proposed instrument designs are physically plausible
2. Suggest appropriate bore profiles, hole counts, and material choices
3. Explain acoustic challenges for hybrid instruments
4. Guide the LLM with physics-grounded reasoning

References:
- Benade (1990): Fundamentals of Musical Acoustics
- Wolfe (2009): The Physics of Musical Instruments (UNSW)
- Fletcher & Rossing (1998): The Physics of Musical Instruments
- Campbell & Greated: The Musician's Guide to Acoustics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BoreType(Enum):
    CYLINDRICAL = "cylindrical"
    CONICAL = "conical"
    PARABOLIC = "parabolic"
    EXPONENTIAL = "exponential"
    BESSEL = "bessel"
    COMPOUND = "compound"  # multiple sections


class ExcitationType(Enum):
    REED = "reed"           # single reed (clarinet, sax)
    DOUBLE_REED = "double_reed"  # double reed (oboe, bassoon)
    FLUTE_LIP = "flute_lip"     # edge tone (flute, recorder)
    LIP_REED = "lip_reed"       # lip buzz (brass)
    AIR_REED = "air_reed"       # no reed (whistle, ocarina)


class MaterialType(Enum):
    BRASS = "brass"
    WOOD = "wood"
    PLASTIC = "plastic"
    PVC = "pvc"
    BAMBOO = "bamboo"
    CARBON_FIBER = "carbon_fiber"
    ALUMINUM = "aluminum"
    SILVER = "silver"
    BELL_METAL = "bell_metal"


@dataclass
class MaterialProperties:
    """Acoustic properties of construction materials."""
    name: str
    density_kg_m3: float           # material density
    speed_of_sound_m_s: float      # sound speed in material (for loss)
    surface_roughness_um: float    # internal surface roughness
    loss_factor: float             # internal damping (higher = more loss)
    radiation_efficiency: float    # how well it radiates sound (0-1)
    thermal_conductivity: float    # W/(m·K) — affects viscothermal losses
    description: str = ""

    @property
    def loss_quality(self) -> str:
        if self.loss_factor < 0.01:
            return "low_loss"
        elif self.loss_factor < 0.05:
            return "medium_loss"
        return "high_loss"


MATERIALS = {
    MaterialType.BRASS: MaterialProperties(
        name="Brass",
        density_kg_m3=8500,
        speed_of_sound_m_s=3480,
        surface_roughness_um=2.0,
        loss_factor=0.001,
        radiation_efficiency=0.95,
        thermal_conductivity=120.0,
        description="Standard brass instrument material. High radiation efficiency, low loss.",
    ),
    MaterialType.WOOD: MaterialProperties(
        name="Wood (grenadilla)",
        density_kg_m3=1200,
        speed_of_sound_m_s=4500,
        surface_roughness_um=10.0,
        loss_factor=0.02,
        radiation_efficiency=0.7,
        thermal_conductivity=0.2,
        description="Traditional clarinet/oboe material. Higher surface roughness adds warmth.",
    ),
    MaterialType.PLASTIC: MaterialProperties(
        name="Plastic (ABS/PLA)",
        density_kg_m3=1050,
        speed_of_sound_m_s=2100,
        surface_roughness_um=5.0,
        loss_factor=0.03,
        radiation_efficiency=0.75,
        thermal_conductivity=0.15,
        description="3D-printable material. Affordable, consistent, moderate losses.",
    ),
    MaterialType.PVC: MaterialProperties(
        name="PVC",
        density_kg_m3=1400,
        speed_of_sound_m_s=2300,
        surface_roughness_um=3.0,
        loss_factor=0.02,
        radiation_efficiency=0.72,
        thermal_conductivity=0.16,
        description="Common DIY instrument material. Smooth bore, easy to work.",
    ),
    MaterialType.BAMBOO: MaterialProperties(
        name="Bamboo",
        density_kg_m3=700,
        speed_of_sound_m_s=5000,
        surface_roughness_um=20.0,
        loss_factor=0.04,
        radiation_efficiency=0.6,
        thermal_conductivity=0.16,
        description="Traditional material for flutes, shakuhachi, bansuri. High roughness.",
    ),
    MaterialType.CARBON_FIBER: MaterialProperties(
        name="Carbon Fiber",
        density_kg_m3=1600,
        speed_of_sound_m_s=1300,
        surface_roughness_um=1.0,
        loss_factor=0.005,
        radiation_efficiency=0.9,
        thermal_conductivity=7.0,
        description="Modern high-performance material. Very smooth, low loss, lightweight.",
    ),
    MaterialType.ALUMINUM: MaterialProperties(
        name="Aluminum",
        density_kg_m3=2700,
        speed_of_sound_m_s=6300,
        surface_roughness_um=1.5,
        loss_factor=0.002,
        radiation_efficiency=0.92,
        thermal_conductivity=237.0,
        description="Lightweight metal. Used in marching band instruments.",
    ),
    MaterialType.SILVER: MaterialProperties(
        name="Silver",
        density_kg_m3=10500,
        speed_of_sound_m_s=3650,
        surface_roughness_um=1.0,
        loss_factor=0.0008,
        radiation_efficiency=0.96,
        thermal_conductivity=429.0,
        description="Premium brass material. Excellent radiation, very low loss.",
    ),
    MaterialType.BELL_METAL: MaterialProperties(
        name="Bell Metal",
        density_kg_m3=8800,
        speed_of_sound_m_s=3400,
        surface_roughness_um=2.5,
        loss_factor=0.0005,
        radiation_efficiency=0.98,
        thermal_conductivity=110.0,
        description="High-copper brass alloy. Maximum radiation, used for bells.",
    ),
}


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
    harmonic_series: str  # "odd" or "all"
    description: str
    key_acoustic_challenges: list[str] = field(default_factory=list)
    materials: list[MaterialType] = field(default_factory=list)
    fingering_complexity: str = "simple"  # simple, moderate, complex
    octave_range: tuple[float, float] = (0, 0)  # in octaves above fundamental


INSTRUMENT_FAMILIES: dict[str, FamilyConstraints] = {
    # ── CLARINET FAMILY ──────────────────────────────────────────────
    "clarinet": FamilyConstraints(
        family="Clarinet",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.REED,
        closed_top=True,
        typical_bore_radius_mm=(6.5, 9.0),
        typical_length_mm=(450, 650),
        typical_hole_count=(5, 8),
        typical_hole_diameter_mm=(6.0, 10.0),
        harmonic_series="odd",
        description="Cylindrical closed-open bore, single reed. Odd harmonics dominant gives hollow timbre.",
        key_acoustic_challenges=[
            "Register key mechanism required (overblowing at 12th)",
            "Tone hole chimney height affects intonation in upper register",
            "Cross-fingerings for chromatic notes",
        ],
        materials=[MaterialType.BRASS, MaterialType.WOOD, MaterialType.PLASTIC],
        fingering_complexity="complex",
        octave_range=(3.5, 4.0),
    ),
    "saxophone": FamilyConstraints(
        family="Saxophone",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.REED,
        closed_top=False,
        typical_bore_radius_mm=(8.0, 25.0),
        typical_length_mm=(400, 2000),
        typical_hole_count=(20, 25),
        typical_hole_diameter_mm=(8.0, 16.0),
        harmonic_series="all",
        description="Conical open-open bore, single reed. All harmonics give full, rich timbre.",
        key_acoustic_challenges=[
            "Octave key required (overblowing at octave)",
            "Large bore instruments have more intonation variation across range",
            "Key mechanism complexity scales with hole count",
        ],
        materials=[MaterialType.BRASS],
        fingering_complexity="moderate",
        octave_range=(2.5, 3.5),
    ),

    # ── FLUTE FAMILY ─────────────────────────────────────────────────
    "flute": FamilyConstraints(
        family="Flute",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(9.5, 13.0),
        typical_length_mm=(400, 700),
        typical_hole_count=(14, 18),
        typical_hole_diameter_mm=(10.0, 14.0),
        harmonic_series="all",
        description="Cylindrical open-open bore, edge-tone excitation. All harmonics, bright timbre.",
        key_acoustic_challenges=[
            "Embourchure affects pitch stability",
            "Tone hole size affects low register response",
            "Headjoint geometry critical for projection",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER, MaterialType.PLASTIC],
        fingering_complexity="moderate",
        octave_range=(2.0, 3.0),
    ),
    "recorder": FamilyConstraints(
        family="Recorder",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(5.5, 8.0),
        typical_length_mm=(250, 500),
        typical_hole_count=(6, 8),
        typical_hole_diameter_mm=(5.0, 9.0),
        harmonic_series="all",
        description="Mildly conical open-open bore, fipple mouthpiece. Simple fingering, bright timbre.",
        key_acoustic_challenges=[
            "Fipple (whistle) mouthpiece limits dynamic range",
            "Low register can be breathy with large holes",
            "Cross-fingerings for chromatic notes",
        ],
        materials=[MaterialType.WOOD, MaterialType.PLASTIC],
        fingering_complexity="simple",
        octave_range=(1.5, 2.5),
    ),
    "folk_flute": FamilyConstraints(
        family="Folk Flute",
        bore_type=BoreType.CYLINDRICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(8.0, 12.0),
        typical_length_mm=(300, 600),
        typical_hole_count=(4, 7),
        typical_hole_diameter_mm=(6.0, 10.0),
        harmonic_series="all",
        description="Simple cylindrical flute. Few holes limit chromatic capability.",
        key_acoustic_challenges=[
            "Limited chromatic options with few holes",
            "Hole spacing constrained by finger reach",
            "Bore length determines fundamental pitch",
        ],
        materials=[MaterialType.BAMBOO, MaterialType.WOOD, MaterialType.PVC],
        fingering_complexity="simple",
        octave_range=(1.5, 2.0),
    ),
    "shakuhachi": FamilyConstraints(
        family="Shakuhachi",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.FLUTE_LIP,
        closed_top=False,
        typical_bore_radius_mm=(18.0, 22.0),
        typical_length_mm=(500, 800),
        typical_hole_count=(5, 7),
        typical_hole_diameter_mm=(10.0, 14.0),
        harmonic_series="all",
        description="Large-bore end-blown flute. Extensive pitch bending via embouchure.",
        key_acoustic_challenges=[
            "Large bore requires strong breath support",
            "Pitch bending is primary technique (not just hole covering)",
            "Material (bamboo) has high internal losses",
        ],
        materials=[MaterialType.BAMBOO],
        fingering_complexity="complex",
        octave_range=(1.5, 2.5),
    ),

    # ── DOUBLE REED FAMILY ───────────────────────────────────────────
    "oboe": FamilyConstraints(
        family="Oboe",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.DOUBLE_REED,
        closed_top=True,
        typical_bore_radius_mm=(3.5, 7.0),
        typical_length_mm=(450, 600),
        typical_hole_count=(18, 23),
        typical_hole_diameter_mm=(3.0, 6.0),
        harmonic_series="odd",
        description="Narrow conical closed-open bore, double reed. Bright, penetrating timbre.",
        key_acoustic_challenges=[
            "Very narrow bore makes intonation sensitive to hole placement",
            "Double reed is highly player-dependent",
            "Key mechanism complexity with many small holes",
        ],
        materials=[MaterialType.WOOD],
        fingering_complexity="complex",
        octave_range=(3.0, 4.0),
    ),
    "bassoon": FamilyConstraints(
        family="Bassoon",
        bore_type=BoreType.CONICAL,
        excitation=ExcitationType.DOUBLE_REED,
        closed_top=True,
        typical_bore_radius_mm=(6.0, 18.0),
        typical_length_mm=(1200, 2000),
        typical_hole_count=(18, 23),
        typical_hole_diameter_mm=(4.0, 12.0),
        harmonic_series="odd",
        description="Large conical closed-open bore, double reed. Rich, warm low register.",
        key_acoustic_challenges=[
            "Very long bore requires folded construction",
            "Register breaks are challenging",
            "Large holes need key mechanisms (fingers too small)",
        ],
        materials=[MaterialType.WOOD],
        fingering_complexity="complex",
        octave_range=(2.5, 3.5),
    ),

    # ── BRASS FAMILY ─────────────────────────────────────────────────
    "trumpet": FamilyConstraints(
        family="Trumpet",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.5, 7.0),
        typical_length_mm=(1200, 1400),
        typical_hole_count=(3, 3),  # valves
        typical_hole_diameter_mm=(0, 0),  # valves, not holes
        harmonic_series="all",
        description="Cylindrical bore with conical leadpipe and bell. 3 piston valves.",
        key_acoustic_challenges=[
            "Valve combinations produce discrete pitch set",
            "Tuning slides needed for each valve combination",
            "Bell flare critical for projection and intonation",
        ],
        materials=[MaterialType.BRASS, MaterialType.SILVER],
        fingering_complexity="moderate",
        octave_range=(2.0, 3.0),
    ),
    "trombone": FamilyConstraints(
        family="Trombone",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(6.0, 7.5),
        typical_length_mm=(2000, 2700),
        typical_hole_count=(0, 0),  # slide, no valves/holes
        typical_hole_diameter_mm=(0, 0),
        harmonic_series="all",
        description="Mostly cylindrical bore with bell. Slide provides continuous pitch.",
        key_acoustic_challenges=[
            "Slide positions are approximate (player adjusts)",
            "Continuous pitch requires precise embouchure",
            "Bore length is very long (folded in U-shape)",
        ],
        materials=[MaterialType.BRASS],
        fingering_complexity="simple",
        octave_range=(1.5, 3.0),
    ),
    "french_horn": FamilyConstraints(
        family="French Horn",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(5.0, 6.5),
        typical_length_mm=(3000, 4000),
        typical_hole_count=(4, 4),  # rotary valves
        typical_hole_diameter_mm=(0, 0),
        harmonic_series="all",
        description="Conical bore with rotary valves and large bell. Very long tubing.",
        key_acoustic_challenges=[
            "Extremely long bore (4+ meters coiled)",
            "Hand-in-bell technique for pitch/timbre control",
            "Close harmonic spacing in low register",
        ],
        materials=[MaterialType.BRASS],
        fingering_complexity="complex",
        octave_range=(1.5, 3.0),
    ),
    "tuba": FamilyConstraints(
        family="Tuba",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(7.0, 38.0),
        typical_length_mm=(2500, 5000),
        typical_hole_count=(4, 6),  # piston/rotary valves
        typical_hole_diameter_mm=(0, 0),
        harmonic_series="all",
        description="Largest brass instrument. Wide conical bore, deep range.",
        key_acoustic_challenges=[
            "Very large bore requires significant air volume",
            "Low register response is slow",
            "Intonation very sensitive to bore proportions",
        ],
        materials=[MaterialType.BRASS],
        fingering_complexity="moderate",
        octave_range=(0.5, 2.0),
    ),

    # ── EXOTIC/SPECIALTY ─────────────────────────────────────────────
    "didgeridoo": FamilyConstraints(
        family="Didgeridoo",
        bore_type=BoreType.COMPOUND,
        excitation=ExcitationType.LIP_REED,
        closed_top=False,
        typical_bore_radius_mm=(30.0, 60.0),
        typical_length_mm=(1000, 2000),
        typical_hole_count=(0, 0),
        typical_hole_diameter_mm=(0, 0),
        harmonic_series="all",
        description="Large bore drone instrument. Circular breathing enables continuous sound.",
        key_acoustic_challenges=[
            "Drone only (no holes for melody)",
            "Timbral variation via tongue/vocal tract shape",
            "Bore irregularities create characteristic sound",
        ],
        materials=[MaterialType.BAMBOO, MaterialType.WOOD],
        fingering_complexity="simple",
        octave_range=(0, 0.5),
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
        ],
        materials=[MaterialType.PLASTIC],
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


@dataclass
class HybridInstrumentSpec:
    """Specification for a cross-family hybrid instrument."""
    name: str
    mouthpiece_family: str
    body_family: str
    description: str
    acoustic_challenges: list[str]
    feasibility: str  # "easy", "moderate", "hard", "experimental"
    key_considerations: list[str]

    @property
    def combined_challenges(self) -> list[str]:
        mouthpiece = INSTRUMENT_FAMILIES.get(self.mouthpiece_family)
        body = INSTRUMENT_FAMILIES.get(self.body_family)
        challenges = list(self.acoustic_challenges)
        if mouthpiece:
            challenges.extend([f"[mouthpiece] {c}" for c in mouthpiece.key_acoustic_challenges[:1]])
        if body:
            challenges.extend([f"[body] {c}" for c in body.key_acoustic_challenges[:1]])
        return challenges


HYBRID_INSTRUMENTS: list[HybridInstrumentSpec] = [
    HybridInstrumentSpec(
        name="Bass Clarinet Mouthpiece + Trombone Body",
        mouthpiece_family="clarinet",
        body_family="trombone",
        description="Single reed on cylindrical→conical bore. Combines reed warmth with brass projection.",
        acoustic_challenges=[
            "Impedance mismatch between reed and large bore",
            "Register breaks will be dramatic",
            "Exciter (reed) may not couple well to large-bore standing waves",
        ],
        feasibility="experimental",
        key_considerations=[
            "Bore taper must transition smoothly from reed to bell",
            "Valve/slide mechanism needed for chromatic play",
            "Reed may need to be larger for large bore",
        ],
    ),
    HybridInstrumentSpec(
        name="Saxophone Mouthpiece + Flute Body",
        mouthpiece_family="saxophone",
        body_family="flute",
        description="Single reed on cylindrical open bore. Reed articulation on flute body.",
        acoustic_challenges=[
            "Sax reed is designed for closed-top excitation",
            "Open bore changes harmonic content (all vs odd harmonics)",
            "Reed coupling to flute bore is untested territory",
        ],
        feasibility="experimental",
        key_considerations=[
            "Open bore means reed vibrates differently",
            "May need modified reed or mouthpiece facing",
            "Key mechanism from flute body preserved",
        ],
    ),
    HybridInstrumentSpec(
        name="Clarinet Mouthpiece + Saxophone Body",
        mouthpiece_family="clarinet",
        body_family="saxophone",
        description="Cylindrical reed on conical bore. Hybrid timbre between clarinet and sax.",
        acoustic_challenges=[
            "Bore taper mismatch (cylindrical mouthpiece → conical body)",
            "Harmonic content shifts from odd-only to all harmonics",
            "Register mechanism must accommodate both families",
        ],
        feasibility="moderate",
        key_considerations=[
            "Soprano sax body is closest in size to Bb clarinet",
            "Taper transition must be gradual to avoid reflections",
            "Fingering system can use sax layout",
        ],
    ),
    HybridInstrumentSpec(
        name="Flute Headjoint + Trombone Slide",
        mouthpiece_family="flute",
        body_family="trombone",
        description="Edge-tone excitation on trombone bore. Continuous pitch via slide.",
        acoustic_challenges=[
            "Flute embouchure requires very different air speed than trombone",
            "Trombone bore is too large for flute excitation efficiency",
            "Slide positions will be very far apart (long wavelengths)",
        ],
        feasibility="hard",
        key_considerations=[
            "Reducing bore diameter would help coupling",
            "Embouchure plate needs redesign for larger air column",
            "Could work as a novelty/experimental instrument",
        ],
    ),
    HybridInstrumentSpec(
        name="Recorder Fipple + Clarinet Body",
        mouthpiece_family="recorder",
        body_family="clarinet",
        description="Fipple mouthpiece on closed cylindrical bore. Simplicity of recorder on clarinet range.",
        acoustic_challenges=[
            "Fipple excites all harmonics, but closed bore reinforces odd only",
            "Register breaks will be unpredictable",
            "Fipple may not couple efficiently to larger bore",
        ],
        feasibility="moderate",
        key_considerations=[
            "Fipple geometry must be scaled for bore size",
            "Closed top creates odd-harmonic series (different from recorder)",
            "Could produce unique timbre — flute-like attack, clarinet-like sustain",
        ],
    ),
    HybridInstrumentSpec(
        name="Bassoon Reed + Trumpet Body",
        mouthpiece_family="bassoon",
        body_family="trumpet",
        description="Double reed on trumpet bore. Combines reed articulation with brass brightness.",
        acoustic_challenges=[
            "Double reed impedance must match trumpet bore impedance",
            "Trumpet bore is much wider than bassoon — coupling is critical",
            "Valve mechanism must handle reed vibration without damping it",
        ],
        feasibility="experimental",
        key_considerations=[
            "Bassoon reed could work if bore diameter is reduced",
            "Leadpipe geometry becomes critical coupling element",
            "May produce oboe-like timbre with brass projection",
        ],
    ),
]


@dataclass
class QuarterToneStrategy:
    """Strategy for achieving quarter-tone intervals on a wind instrument."""
    name: str
    mechanism: str
    description: str
    advantages: list[str]
    disadvantages: list[str]
    applicable_families: list[str]
    pitch_range_semitones: float = 0.5  # pitch shift achievable


QUARTER_TONE_STRATEGIES: list[QuarterToneStrategy] = [
    QuarterToneStrategy(
        name="Additional Side Holes",
        mechanism="Extra tone holes between standard holes, operated by thumb or side keys",
        description="Add holes between the standard chromatic positions, each lowering pitch by ~50 cents when opened.",
        advantages=["Simple concept", "Consistent pitch accuracy", "Can be added to existing designs"],
        disadvantages=["Increases key mechanism complexity", "Holes may be too close together", "Cross-fingering interactions"],
        applicable_families=["clarinet", "saxophone", "recorder", "folk_flute"],
    ),
    QuarterToneStrategy(
        name="Half-Holing",
        mechanism="Partially covering a tone hole to produce intermediate pitches",
        description="Player slides finger to partially cover a hole, shifting pitch by up to 50 cents.",
        advantages=["No additional hardware", "Traditional technique (used in Middle Eastern music)", "Flexible pitch control"],
        disadvantages=["Difficult to achieve consistent pitch", "Requires skilled player", "Not repeatable across players"],
        applicable_families=["clarinet", "saxophone", "flute", "recorder"],
    ),
    QuarterToneStrategy(
        name="Cross-Fingering",
        mechanism="Specific combinations of open/closed holes that produce microtonal inflections",
        description="Certain fingering combinations produce pitches between chromatic notes due to venting effects.",
        advantages=["No additional hardware", "Can produce multiple quarter-tones", "Uses existing hole pattern"],
        disadvantages=["Timbre changes significantly", "Intonation varies by instrument", "Limited pitch accuracy"],
        applicable_families=["clarinet", "recorder", "folk_flute"],
    ),
    QuarterToneStrategy(
        name="Side Keys / Trill Keys",
        mechanism="Small auxiliary keys that open specific holes for quarter-tone access",
        description="Dedicated keys for specific quarter-tone intervals, similar to saxophone altissimo keys.",
        advantages=["Precise pitch", "Easy to activate", "Doesn't disrupt normal fingering"],
        disadvantages=["Adds mechanical complexity", "Limited to specific intervals", "Weight increase"],
        applicable_families=["clarinet", "saxophone"],
    ),
    QuarterToneStrategy(
        name="Slide Mechanism",
        mechanism="Trombone-style slide or adjustable tuning tube for continuous pitch",
        description="A short slide or telescoping tube that changes effective bore length by ~50 cents.",
        advantages=["Continuous pitch control", "Precise tuning", "No holes needed for microtones"],
        disadvantages=["Adds weight and bulk", "Slower than key mechanism", "Limited pitch range"],
        applicable_families=["trumpet", "french_horn", "trombone", "flute"],
    ),
    QuarterToneStrategy(
        name="Pitch Bend / Lip Control",
        mechanism="Player embouchure or voicing adjustment to bend pitch by 50 cents",
        description="Exploiting the instrument's natural pitch flexibility for quarter-tone access.",
        advantages=["No hardware changes", "Expressive control", "Traditional technique"],
        disadvantages=["Player skill dependent", "Limited pitch accuracy", "Affects timbre"],
        applicable_families=["trumpet", "french_horn", "flute", "shakuhachi"],
    ),
]


# ============================================================================
# Scale definitions (quarter-tone, microtonal, non-Western)
# ============================================================================

@dataclass
class ScaleDefinition:
    """A musical scale with interval structure and origin."""
    name: str
    family: str  # western, indian, arabic, experimental, etc.
    intervals_cents: list[float]  # intervals from root in cents
    description: str
    n_notes: int = 0

    def __post_init__(self):
        if not self.n_notes:
            self.n_notes = len(self.intervals_cents)


SCALES: dict[str, ScaleDefinition] = {
    # ── WESTERN ──────────────────────────────────────────────────────
    "12_tet": ScaleDefinition(
        name="12-TET (Equal Temperament)",
        family="western",
        intervals_cents=[0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100],
        description="Standard Western tuning. 12 equal semitones per octave.",
    ),
    "major": ScaleDefinition(
        name="Major (Ionian)",
        family="western",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1100],
        description="Major scale: W-W-H-W-W-W-H.",
    ),
    "natural_minor": ScaleDefinition(
        name="Natural Minor (Aeolian)",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 800, 1000],
        description="Natural minor: W-H-W-W-H-W-W.",
    ),
    "harmonic_minor": ScaleDefinition(
        name="Harmonic Minor",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 800, 1100],
        description="Minor with raised 7th. Augmented 2nd between 6th and 7th.",
    ),
    "melodic_minor": ScaleDefinition(
        name="Melodic Minor (ascending)",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 900, 1100],
        description="Minor with raised 6th and 7th ascending. Descending = natural minor.",
    ),
    "dorian": ScaleDefinition(
        name="Dorian",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 900, 1000],
        description="Minor with raised 6th. Common in jazz and folk music.",
    ),
    "mixolydian": ScaleDefinition(
        name="Mixolydian",
        family="western",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1000],
        description="Major with lowered 7th. Dominant scale.",
    ),
    "phrygian": ScaleDefinition(
        name="Phrygian",
        family="western",
        intervals_cents=[0, 100, 300, 500, 700, 800, 1000],
        description="Minor with lowered 2nd. Spanish/Flamenco flavor.",
    ),
    "lydian": ScaleDefinition(
        name="Lydian",
        family="western",
        intervals_cents=[0, 200, 400, 600, 700, 900, 1100],
        description="Major with raised 4th. Bright, dreamy quality.",
    ),
    "locrian": ScaleDefinition(
        name="Locrian",
        family="western",
        intervals_cents=[0, 100, 300, 500, 600, 800, 1000],
        description="Diminished scale. Rarely used as tonal center.",
    ),
    "whole_tone": ScaleDefinition(
        name="Whole Tone",
        family="western",
        intervals_cents=[0, 200, 400, 600, 800, 1000],
        description="All whole steps. Symmetric, dreamy, impressionistic.",
    ),
    "blues": ScaleDefinition(
        name="Blues",
        family="western",
        intervals_cents=[0, 300, 500, 600, 700, 1000],
        description="Minor pentatonic with added b5. Foundation of blues music.",
    ),
    "pentatonic_major": ScaleDefinition(
        name="Pentatonic Major",
        family="western",
        intervals_cents=[0, 200, 400, 700, 900],
        description="5-note major scale. Universal across cultures.",
    ),
    "pentatonic_minor": ScaleDefinition(
        name="Pentatonic Minor",
        family="western",
        intervals_cents=[0, 300, 500, 700, 1000],
        description="5-note minor scale. Foundation of many folk traditions.",
    ),

    # ── INDIAN (Hindustani/Carnatic) ─────────────────────────────────
    "bilawal": ScaleDefinition(
        name="Bilawal Thaat (Natural Major)",
        family="indian",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1100],
        description="Hindustani thaat equivalent to Ionian/major. Foundation of raga Bilawal.",
    ),
    "khamaj": ScaleDefinition(
        name="Khamaj Thaat",
        family="indian",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1000],
        description="Hindustani thaat with lowered 7th ascending, natural 7th descending. Versatile.",
    ),
    "marwa": ScaleDefinition(
        name="Marwa Thaat",
        family="indian",
        intervals_cents=[0, 100, 400, 500, 700, 900, 1100],
        description="Hindustani thaat with flattened 2nd. Tension-filled, meditative quality.",
    ),
    "purvi": ScaleDefinition(
        name="Purvi Thaat",
        family="indian",
        intervals_cents=[0, 100, 400, 500, 700, 800, 1100],
        description="Hindustani thaat with flattened 2nd and 6th. Evening raga mood.",
    ),
    "todi": ScaleDefinition(
        name="Todi Thaat",
        family="indian",
        intervals_cents=[0, 100, 300, 500, 700, 800, 1100],
        description="Hindustani thaat with flattened 2nd, 3rd, and 6th. Morning meditation.",
    ),
    "shrutis_22": ScaleDefinition(
        name="22 Shrutis (Microtonal)",
        family="indian",
        intervals_cents=[0, 90, 180, 200, 300, 390, 400, 500, 590, 600, 700, 790, 800, 900, 990, 1000, 1100, 1190, 1200],
        description="22 microtonal intervals per octave in Indian classical music. Shruti = smallest interval.",
    ),

    # ── ARABIC (Maqam) ───────────────────────────────────────────────
    "maqam_rast": ScaleDefinition(
        name="Maqam Rast",
        family="arabic",
        intervals_cents=[0, 150, 300, 500, 700, 850, 1000, 1200],
        description="Foundation maqam. Quarter-tones (3/4 tones) in positions 2 and 6.",
    ),
    "maqam_hijaz": ScaleDefinition(
        name="Maqam Hijaz",
        family="arabic",
        intervals_cents=[0, 150, 300, 500, 700, 850, 1000, 1200],
        description="Augmented 2nd between notes 1-2. Distinctive Middle Eastern sound.",
    ),
    "maqam_saba": ScaleDefinition(
        name="Maqam Saba",
        family="arabic",
        intervals_cents=[0, 150, 300, 450, 700, 850, 1000],
        description="Unique maqam with three quarter-tone steps. Melancholic character.",
    ),
    "maqam_kurd": ScaleDefinition(
        name="Maqam Kurd",
        family="arabic",
        intervals_cents=[0, 150, 300, 500, 700, 850, 1000],
        description="Similar to Phrygian but with quarter-tone inflections. Kurdish origin.",
    ),
    "maqam_nahawand": ScaleDefinition(
        name="Maqam Nahawand",
        family="arabic",
        intervals_cents=[0, 200, 350, 500, 700, 850, 1000],
        description="Similar to natural minor but with quarter-tone variations.",
    ),

    # ── MICROTONAL / QUARTER-TONE ────────────────────────────────────
    "24_tet": ScaleDefinition(
        name="24-TET (Quarter-tone)",
        family="microtonal",
        intervals_cents=[i * 50 for i in range(24)],
        description="24 equal quarter-tones per octave. Equal-tempered microtonal system.",
    ),
    "19_tet": ScaleDefinition(
        name="19-TET",
        family="microtonal",
        intervals_cents=[i * (1200 / 19) for i in range(19)],
        description="19 equal divisions. Good approximation of meantone temperament.",
    ),
    "31_tet": ScaleDefinition(
        name="31-TET",
        family="microtonal",
        intervals_cents=[i * (1200 / 31) for i in range(31)],
        description="31 equal divisions. Excellent approximation of quarter-comma meantone.",
    ),
    "53_tet": ScaleDefinition(
        name="53-TET",
        family="microtonal",
        intervals_cents=[i * (1200 / 53) for i in range(53)],
        description="53 equal divisions. Near-just intonation for 5-limit intervals.",
    ),

    # ── EXPERIMENTAL / NON-WESTERN ───────────────────────────────────
    "slendro": ScaleDefinition(
        name="Slendro (Javanese)",
        family="experimental",
        intervals_cents=[0, 240, 480, 720, 960],
        description="5-note Javanese scale. Approximate equal spacing, not tempered.",
    ),
    "pelog": ScaleDefinition(
        name="Pelog (Javanese)",
        family="experimental",
        intervals_cents=[0, 120, 300, 420, 720, 840, 1020],
        description="7-note Javanese scale with unequal intervals. Distinctive gap.",
    ),
    "bohlen_pierce": ScaleDefinition(
        name="Bohlen-Pierce",
        family="experimental",
        intervals_cents=[0, 147, 294, 441, 588, 735, 882, 1029, 1176],
        description="Tritave-based scale (3:1 ratio). Uses 13 equal steps per tritave.",
    ),
    "partch_43": ScaleDefinition(
        name="Partch 43-tone",
        family="experimental",
        intervals_cents=[
            0, 22, 71, 112, 183, 204, 267, 294, 316, 351, 386, 408,
            435, 478, 498, 520, 563, 583, 617, 680, 702, 737, 765, 782,
            814, 841, 884, 925, 955, 977, 1018, 1049, 1088, 1116, 1129,
            1159, 1178, 1200,
        ],
        description="Harry Partch's 43-tone just intonation scale. 11-limit intervals.",
    ),
}


def get_acoustic_challenges(
    mouthpiece_family: str,
    body_family: str,
) -> list[str]:
    """Get acoustic challenges for a hybrid instrument combination.

    Parameters
    ----------
    mouthpiece_family : str
        Key in INSTRUMENT_FAMILIES for the mouthpiece (e.g., "clarinet").
    body_family : str
        Key in INSTRUMENT_FAMILIES for the body (e.g., "saxophone").

    Returns
    -------
    list of str
        Combined acoustic challenges.
    """
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
    """Suggest appropriate material based on instrument family and constraints.

    Parameters
    ----------
    family : str
        Key in INSTRUMENT_FAMILIES.
    budget : str
        "low", "medium", or "high".
    purpose : str
        "performance", "practice", "experimental", or "education".

    Returns
    -------
    MaterialType
        Suggested material.
    """
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


if __name__ == "__main__":
    print("=== Instrument Families ===")
    for name, fc in INSTRUMENT_FAMILIES.items():
        print(f"\n{fc.family}:")
        print(f"  Bore: {fc.bore_type.value}, Excitation: {fc.excitation.value}")
        print(f"  Harmonics: {fc.harmonic_series}, Closed top: {fc.closed_top}")
        print(f"  Length: {fc.typical_length_mm[0]}-{fc.typical_length_mm[1]}mm")
        print(f"  Holes: {fc.typical_hole_count[0]}-{fc.typical_hole_count[1]}")
        print(f"  Challenges: {fc.key_acoustic_challenges}")

    print("\n\n=== Hybrid Instruments ===")
    for h in HYBRID_INSTRUMENTS:
        print(f"\n{h.name} ({h.feasibility}):")
        print(f"  {h.description}")
        for c in h.acoustic_challenges:
            print(f"  - {c}")

    print("\n\n=== Quarter-Tone Strategies ===")
    for s in QUARTER_TONE_STRATEGIES:
        print(f"\n{s.name}: {s.mechanism}")
        print(f"  Families: {', '.join(s.applicable_families)}")
