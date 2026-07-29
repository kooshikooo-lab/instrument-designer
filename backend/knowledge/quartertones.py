"""Quarter-tone and microtonal implementation strategies for wind instruments."""
from __future__ import annotations

from dataclasses import dataclass


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
        applicable_families=["clarinet", "saxophone", "recorder", "folk_flute", "oboe", "flute"],
    ),
    QuarterToneStrategy(
        name="Half-Holing",
        mechanism="Partially covering a tone hole to produce intermediate pitches",
        description="Player slides finger to partially cover a hole, shifting pitch by up to 50 cents.",
        advantages=["No additional hardware", "Traditional technique (Middle Eastern, Baroque)", "Flexible pitch control"],
        disadvantages=["Difficult to achieve consistent pitch", "Requires skilled player", "Not repeatable across players"],
        applicable_families=["clarinet", "saxophone", "flute", "recorder", "folk_flute", "oboe", "bassoon"],
    ),
    QuarterToneStrategy(
        name="Cross-Fingering",
        mechanism="Specific combinations of open/closed holes that produce microtonal inflections",
        description="Certain fingering combinations produce pitches between chromatic notes due to venting effects.",
        advantages=["No additional hardware", "Can produce multiple quarter-tones", "Uses existing hole pattern"],
        disadvantages=["Timbre changes significantly", "Intonation varies by instrument", "Limited pitch accuracy"],
        applicable_families=["clarinet", "recorder", "folk_flute", "oboe", "bassoon"],
    ),
    QuarterToneStrategy(
        name="Side Keys / Trill Keys",
        mechanism="Small auxiliary keys that open specific holes for quarter-tone access",
        description="Dedicated keys for specific quarter-tone intervals, similar to saxophone altissimo keys.",
        advantages=["Precise pitch", "Easy to activate", "Doesn't disrupt normal fingering"],
        disadvantages=["Adds mechanical complexity", "Limited to specific intervals", "Weight increase"],
        applicable_families=["clarinet", "saxophone", "flute", "oboe", "bassoon"],
    ),
    QuarterToneStrategy(
        name="Slide Mechanism",
        mechanism="Trombone-style slide or adjustable tuning tube for continuous pitch",
        description="A short slide or telescoping tube that changes effective bore length by ~50 cents.",
        advantages=["Continuous pitch control", "Precise tuning", "No holes needed for microtones"],
        disadvantages=["Adds weight and bulk", "Slower than key mechanism", "Limited pitch range"],
        applicable_families=["trumpet", "french_horn", "trombone", "flute", "shakuhachi"],
    ),
    QuarterToneStrategy(
        name="Pitch Bend / Lip Control",
        mechanism="Player embouchure or voicing adjustment to bend pitch by 50 cents",
        description="Exploiting the instrument's natural pitch flexibility for quarter-tone access.",
        advantages=["No hardware changes", "Expressive control", "Traditional technique"],
        disadvantages=["Player skill dependent", "Limited pitch accuracy", "Affects timbre"],
        applicable_families=["trumpet", "french_horn", "flute", "shakuhachi", "saxophone", "clarinet"],
    ),
    QuarterToneStrategy(
        name="Quarter-Tone Valve",
        mechanism="Additional valve that shortens/lengthens bore by exactly 50 cents",
        description="Third valve on trumpet or extra valve on horn specifically tuned to quarter-tone interval.",
        advantages=["Precise pitch", "Fast activation", "Integrates with existing valve technique"],
        disadvantages=["Adds valve complexity", "Requires precise bore compensation", "Only works for specific notes"],
        applicable_families=["trumpet", "french_horn", "tuba"],
    ),
    QuarterToneStrategy(
        name="Finger Hole on Slide",
        mechanism="Small hole on trombone slide for quarter-tone access in specific positions",
        description="A small vent hole on the slide tube that can be covered/uncovered for pitch adjustment.",
        advantages=["Minimal mechanical change", "Uses existing slide technique", "Precise when calibrated"],
        disadvantages=["Only works at specific slide positions", "Requires slide position adjustment", "May affect slide smoothness"],
        applicable_families=["trombone"],
    ),
]