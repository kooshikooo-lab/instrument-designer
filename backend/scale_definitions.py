"""
Scale definitions for all world tuning systems.

Re-exports from instrument_knowledge.py for convenience and backwards
compatibility. Contains scale data for:

- Western: 12-TET, major, minor modes, blues, pentatonic
- Indian: bilawal, khamaj, marwa, purvi, todi, 22 shrutis
- Arabic: maqam rast, hijaz, saba, kurd, nahawand
- Microtonal: 24-TET, 19-TET, 31-TET, 53-TET
- Experimental: slendro, pelog, Bohlen-Pierce, Partch 43-tone

Also includes quarter-tone fingering strategies for wind instruments.
"""

from backend.instrument_knowledge import (
    ScaleDefinition,
    QuarterToneStrategy,
    SCALES,
    QUARTER_TONE_STRATEGIES,
    get_acoustic_challenges,
    suggest_material,
)

__all__ = [
    "ScaleDefinition",
    "QuarterToneStrategy",
    "SCALES",
    "QUARTER_TONE_STRATEGIES",
    "get_acoustic_challenges",
    "suggest_material",
]
