"""Generative instrument design LLM agent."""
from backend.llm.schema import DesignSpec, CandidateResult, GenerativeResult
from backend.llm.agent import GenerativeAgent, get_agent
from backend.llm.bore_shapes import BORE_SHAPE_GENERATORS, generate_cylindrical_radii, generate_conical_radii
from backend.llm.suggestions import suggest_from_knowledge, FAMILY_LOWEST_NOTE
from backend.llm.ollama import check_ollama
from backend.llm.optimizer import optimize_candidate
from backend.llm.serialization import spec_to_dict, dict_to_candidate

__all__ = [
    "DesignSpec",
    "CandidateResult", 
    "GenerativeResult",
    "GenerativeAgent",
    "get_agent",
    "BORE_SHAPE_GENERATORS",
    "generate_cylindrical_radii",
    "generate_conical_radii",
    "suggest_from_knowledge",
    "FAMILY_LOWEST_NOTE",
    "check_ollama",
    "optimize_candidate",
    "spec_to_dict",
    "dict_to_candidate",
]