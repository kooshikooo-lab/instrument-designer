"""
Instrument physics knowledge base — backward-compatible re-export layer.

All implementation has moved to the `backend.knowledge` subpackage:

- ``backend.knowledge.materials``     — MaterialType, MaterialProperties, MATERIALS
- ``backend.knowledge.families``      — BoreType, ExcitationType, FamilyConstraints, INSTRUMENT_FAMILIES
- ``backend.knowledge.scales``        — ScaleDefinition, SCALES
- ``backend.knowledge.hybrids``       — HybridInstrumentSpec, HYBRID_INSTRUMENTS
- ``backend.knowledge.quartertones``  — QuarterToneStrategy, QUARTER_TONE_STRATEGIES

Helper functions:
- ``backend.knowledge.families.get_acoustic_challenges``
- ``backend.knowledge.families.suggest_material``
- ``backend.knowledge.families._family_lowest_note``
"""
from backend.knowledge.materials import (  # noqa: F401
    BoreType,
    ExcitationType,
    MaterialType,
    MaterialProperties,
    MATERIALS,
)
from backend.knowledge.families import (  # noqa: F401
    FamilyConstraints,
    INSTRUMENT_FAMILIES,
    get_acoustic_challenges,
    suggest_material,
)
from backend.knowledge.scales import (  # noqa: F401
    ScaleDefinition,
    SCALES,
)
from backend.knowledge.hybrids import (  # noqa: F401
    HybridInstrumentSpec,
    HYBRID_INSTRUMENTS,
)
from backend.knowledge.quartertones import (  # noqa: F401
    QuarterToneStrategy,
    QUARTER_TONE_STRATEGIES,
)