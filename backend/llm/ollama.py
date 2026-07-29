"""LLM integration via Ollama."""
from __future__ import annotations

import json
from typing import Any

import requests

from backend.llm.suggestions import KNOWLEDGE_AVAILABLE, INSTRUMENT_FAMILIES, SCALES, _family_lowest_note
from backend.llm.schema import DesignSpec


OLLAMA_URLS = [
    "http://localhost:11434",
    "http://100.100.66.117:11434",
    "http://100.100.69.113:11434",
]


def check_ollama() -> str | None:
    """Check if Ollama is available and return base URL."""
    for url in OLLAMA_URLS:
        try:
            r = requests.get(f"{url}/api/tags", timeout=3)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return None


def _llm_suggest(base_url: str, query: str) -> list[DesignSpec]:
    """Use Ollama LLM to suggest instrument designs based on query."""
    # Prepare the physics context for the LLM
    family_descriptions = []
    for key, fam in list(INSTRUMENT_FAMILIES.items())[:8]:
        family_descriptions.append(
            f"- {fam.family}: {fam.bore_type.value} bore, {fam.excitation.value} excitation, "
            f"closed_top={fam.closed_top}, {fam.typical_hole_count[0]}-{fam.typical_hole_count[1]} holes, "
            f"{fam.typical_bore_radius_mm[0]}-{fam.typical_bore_radius_mm[1]}mm bore radius"
        )

    scale_list = list(SCALES.keys())[:10]

    system_prompt = """You are an acoustic physics expert who designs novel wind instruments.
Given a user request, suggest 1-3 instrument designs with physical justification.

For each design, output a JSON object with these fields:
{
  "name": "Design name",
  "description": "Design description",
  "family": "clarinet|saxophone|flute|recorder|trumpet|trombone|oboe|bassoon|hybrid",
  "bore_type": "cylindrical|conical|parabolic|exponential|bessel",
  "closed_top": true/false,
  "bore_radius_mm": float,
  "bore_length_mm": float,
  "hole_count": int,
  "hole_diameter_mm": float,
  "scale": "12_tet | 24_tet | maqam_rast | slendro | etc",
  "quarter_tone_strategy": "additional holes | half-holing | cross-fingering | side keys | slide",
  "feasibility": "easy|moderate|hard|experimental",
  "reasoning": "Physical explanation of why this design works"
}

Output ONLY a JSON array of designs, no other text.
"""

    user_prompt = f"""Available instrument families:
{chr(10).join(family_descriptions)}

Available scales: {', '.join(scale_list)}

Request: {query}

Output a JSON array of 1-3 instrument designs with full acoustic justification."""

    try:
        r = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": "llama3.1",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "temperature": 0.8,
                "max_tokens": 2048,
            },
            timeout=60,
        )
        if r.status_code != 200:
            return []

        text = r.json().get("response", "")
        # Extract JSON array from response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                designs = json.loads(text[start:end])
            except json.JSONDecodeError:
                return []
        else:
            # Try single object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    designs = json.loads(text[start:end])
                    if isinstance(designs, dict):
                        designs = [designs]
                except json.JSONDecodeError:
                    return []
            else:
                return []

        specs = []
        for d in designs:
            family_key = d.get("family", "")
            lowest, octaves = _family_lowest_note(family_key)
            specs.append(DesignSpec(
                name=d.get("name", "Unknown Design"),
                description=d.get("description", ""),
                family=family_key,
                bore_type=d.get("bore_type", "cylindrical"),
                closed_top=d.get("closed_top", False),
                bore_radius_mm=d.get("bore_radius_mm", 7.25),
                bore_length_mm=d.get("bore_length_mm", 500.0),
                hole_count=d.get("hole_count", 6),
                hole_diameter_mm=d.get("hole_diameter_mm", 7.0),
                scale=d.get("scale", "12_tet"),
                quarter_tone_strategy=d.get("quarter_tone_strategy", ""),
                feasibility=d.get("feasibility", "unknown"),
                llm_reasoning=d.get("reasoning", ""),
                lowest_note_hz=lowest,
                n_octaves=octaves,
            ))
        return specs
    except Exception:
        return []