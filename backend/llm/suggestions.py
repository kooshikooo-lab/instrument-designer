"""Physics-based suggestion engine — LLM fallback using instrument knowledge."""
from __future__ import annotations

import random
from typing import Any

from backend.llm.schema import DesignSpec

try:
    from backend.instrument_knowledge import (
        INSTRUMENT_FAMILIES,
        HYBRID_INSTRUMENTS,
        QUARTER_TONE_STRATEGIES,
        SCALES,
        MATERIALS,
        MaterialType,
        get_acoustic_challenges,
        suggest_material,
    )
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    INSTRUMENT_FAMILIES = {}
    HYBRID_INSTRUMENTS = []
    QUARTER_TONE_STRATEGIES = []
    SCALES = {}
    MATERIALS = {}
    MaterialType = str

    def get_acoustic_challenges(key: str) -> list[str]:
        return []

    def suggest_material(key: str, purpose: str = "experimental") -> Any:
        class M:
            value = "plastic"
        return M()


# Per-family lowest note mapping (A4 = 440 Hz)
FAMILY_LOWEST_NOTE: dict[str, tuple[float, int]] = {
    "clarinet":     (146.83, 3),   # D3
    "saxophone":    (174.61, 3),   # F3 (alto sax low Bb)
    "flute":        (261.63, 3),   # C4
    "recorder":     (523.25, 2),   # C5 (soprano)
    "folk_flute":   (392.00, 2),   # G4
    "shakuhachi":   (293.66, 2),   # D4
    "oboe":         (233.08, 3),   # Bb3
    "bassoon":      (58.27, 3),    # Bb1
    "trumpet":      (164.81, 3),   # E3
    "trombone":     (77.78, 3),    # D2
    "french_horn":  (87.31, 3),    # F2
    "tuba":         (43.65, 3),    # F1
    "didgeridoo":   (65.41, 1),    # C2
    "ocarina":      (392.00, 2),   # G4
    "kazoo":        (261.63, 1),   # C4 (voice driven)
}


def _family_lowest_note(family: str) -> tuple[float, int]:
    """Get the lowest note frequency and octave range for an instrument family."""
    from backend.tmm_acoustics import SPEED_OF_SOUND
    c = SPEED_OF_SOUND

    if family in FAMILY_LOWEST_NOTE:
        return FAMILY_LOWEST_NOTE[family]
    fam = INSTRUMENT_FAMILIES.get(family)
    if fam:
        bore_len = sum(fam.typical_length_mm) / 2
        closed = fam.closed_top
        fundamental = c / (4.0 * bore_len) if closed else c / (2.0 * bore_len)
        octaves = max(int(sum(fam.octave_range) / 2), 1)
        return (fundamental, octaves)
    return (261.63, 2)


def _build_targets(spec: DesignSpec) -> list[float]:
    """Build multi-octave target frequencies from scale definition."""
    scale = SCALES.get(spec.scale)
    if not scale:
        scale = SCALES.get("12_tet")
    if not scale:
        return []

    fundamental = spec.lowest_note_hz
    targets = []
    interval_count = len(scale.intervals_cents)
    for octave in range(max(spec.n_octaves, 1)):
        for cents in scale.intervals_cents:
            f = fundamental * (2.0 ** ((octave * 1200 + cents) / 1200.0))
            targets.append(f)
    max_targets = max(spec.hole_count + 3, 8)
    return targets[:max_targets]


def suggest_from_knowledge(query: str) -> list[DesignSpec]:
    """Generate design specs from instrument_knowledge.py when LLM unavailable."""
    q = query.lower()
    suggestions = []

    # Hybrid instrument?
    found_known = bool([k for k in INSTRUMENT_FAMILIES if k in q])
    for hybrid in HYBRID_INSTRUMENTS:
        if found_known:
            break
        words_in_q = [w for w in hybrid.name.lower().split() if len(w) > 3]
        if any(w in q for w in words_in_q):
            mp = INSTRUMENT_FAMILIES.get(hybrid.mouthpiece_family)
            body = INSTRUMENT_FAMILIES.get(hybrid.body_family)
            if mp and body:
                bore_r = (mp.typical_bore_radius_mm[0] + body.typical_bore_radius_mm[0]) / 2
                bore_l = (mp.typical_length_mm[1] + body.typical_length_mm[1]) / 2
                n_holes = max(mp.typical_hole_count[0], body.typical_hole_count[0])
                lowest, octaves = _family_lowest_note(hybrid.body_family)
                suggestions.append(DesignSpec(
                    name=hybrid.name,
                    description=hybrid.description,
                    family=f"{hybrid.mouthpiece_family}_{hybrid.body_family}",
                    bore_type=body.bore_type.value,
                    closed_top=mp.closed_top,
                    bore_radius_mm=bore_r,
                    bore_length_mm=bore_l,
                    hole_count=n_holes,
                    scale="12_tet",
                    feasibility=hybrid.feasibility,
                    llm_reasoning="; ".join(hybrid.acoustic_challenges[:3]),
                    lowest_note_hz=lowest,
                    n_octaves=octaves,
                ))

    # Known instrument family?
    for key, fam in INSTRUMENT_FAMILIES.items():
        if key in q or fam.family.lower() in q:
            bore_r = sum(fam.typical_bore_radius_mm) / 2
            bore_l = sum(fam.typical_length_mm) / 2
            n_holes = max(fam.typical_hole_count)
            hole_d = sum(fam.typical_hole_diameter_mm) / 2 if fam.typical_hole_diameter_mm[1] > 0 else 7.0
            mat = suggest_material(key, purpose="experimental").value

            challenges = "; ".join(fam.key_acoustic_challenges[:2])

            # Quarter-tone variant?
            is_quarter_tone = "quarter" in q or "microtonal" in q or "24" in q
            qt_strategy = ""
            if is_quarter_tone and not fam.closed_top:
                qt_strategy = "additional side holes"
                n_holes = min(n_holes + 4, 14)
            elif is_quarter_tone:
                qt_strategy = "cross-fingering + half-holing"

            scale = "24_tet" if is_quarter_tone else "12_tet"
            use_closed_top = fam.closed_top and key not in ("clarinet", "oboe", "bassoon")

            lowest, octaves = _family_lowest_note(key)
            suggestions.append(DesignSpec(
                name=f"{'Quarter-Tone ' if is_quarter_tone else ''}{fam.family}",
                description=f"{fam.description} {'with quarter-tone capability' if is_quarter_tone else ''}",
                family=key,
                bore_type=fam.bore_type.value,
                closed_top=fam.closed_top,
                bore_radius_mm=bore_r,
                bore_length_mm=bore_l,
                hole_count=n_holes,
                hole_diameter_mm=hole_d,
                material=mat,
                scale=scale,
                quarter_tone_strategy=qt_strategy,
                n_register=1 if fam.closed_top else 2,
                feasibility="known",
                llm_reasoning=challenges,
                lowest_note_hz=lowest,
                n_octaves=octaves,
            ))

    # "Random instrument" case
    if "random" in q or not suggestions:
        family_keys = list(INSTRUMENT_FAMILIES.keys())
        for _ in range(3):
            key = random.choice(family_keys)
            fam = INSTRUMENT_FAMILIES[key]
            bore_r = random.uniform(*fam.typical_bore_radius_mm)
            bore_l = random.uniform(*fam.typical_length_mm)
            n_holes = random.randint(*fam.typical_hole_count)
            hole_d = random.uniform(*fam.typical_hole_diameter_mm) if fam.typical_hole_diameter_mm[1] > 0 else 7.0

            # Random bore shape variation
            bore_shapes = ["cylindrical", "conical", "parabolic", "exponential"]
            bore_type = random.choice(bore_shapes)

            lowest, octaves = _family_lowest_note(key)
            suggestions.append(DesignSpec(
                name=f"Random {fam.family} ({bore_type})",
                description=f"Randomly generated {fam.family} with {bore_type} bore profile.",
                family=key,
                bore_type=bore_type,
                closed_top=bool(random.choice([True, False])),
                bore_radius_mm=bore_r,
                bore_length_mm=bore_l,
                hole_count=n_holes,
                hole_diameter_mm=hole_d,
                scale=random.choice([s for s in SCALES.keys()]) if SCALES else "12_tet",
                feasibility="experimental",
                llm_reasoning=f"Random generation seeded from {fam.family} acoustic parameters.",
                lowest_note_hz=lowest,
                n_octaves=octaves,
            ))

    # Deduplicate by name
    seen = set()
    unique = []
    for s in suggestions:
        if s.name not in seen:
            seen.add(s.name)
            unique.append(s)
    return unique[:5]  # max 5 candidates