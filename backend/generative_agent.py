"""
Generative agent — backward-compatible re-export layer.

All implementation moved to backend.llm subpackage:

- backend.llm.schema     — DesignSpec, CandidateResult, GenerativeResult
- backend.llm.agent      — GenerativeAgent, get_agent
- backend.llm.bore_shapes — Bore profile generators
- backend.llm.suggestions — Physics-based suggestion engine
- backend.llm.ollama      — Ollama LLM integration
- backend.llm.optimizer   — Standalone Dask-serializable optimizer
- backend.llm.serialization — Dask transport helpers
"""
from backend.llm.schema import (  # noqa: F401
    DesignSpec,
    CandidateResult,
    GenerativeResult,
)
from backend.llm.agent import (  # noqa: F401
    GenerativeAgent,
    get_agent,
)
from backend.llm.bore_shapes import (  # noqa: F401
    BORE_SHAPE_GENERATORS,
    generate_cylindrical_radii,
    generate_conical_radii,
)
from backend.llm.suggestions import (  # noqa: F401
    suggest_from_knowledge,
    FAMILY_LOWEST_NOTE,
)
from backend.llm.ollama import (  # noqa: F401
    check_ollama,
)
from backend.llm.optimizer import (  # noqa: F401
    optimize_candidate,
)
from backend.llm.serialization import (  # noqa: F401
    spec_to_dict,
    dict_to_candidate,
)