"""Serialization helpers for Dask transport."""
from __future__ import annotations

from typing import Any

from backend.llm.schema import DesignSpec, CandidateResult


def spec_to_dict(spec: DesignSpec) -> dict[str, Any]:
    """Serialize a DesignSpec to a plain dict for Dask transport."""
    return {
        "name": spec.name,
        "description": spec.description,
        "family": spec.family,
        "bore_type": spec.bore_type,
        "closed_top": spec.closed_top,
        "bore_radius_mm": spec.bore_radius_mm,
        "bore_length_mm": spec.bore_length_mm,
        "hole_count": spec.hole_count,
        "hole_diameter_mm": spec.hole_diameter_mm,
        "hole_length_mm": spec.hole_length_mm,
        "outer_diameter_mm": spec.outer_diameter_mm,
        "material": spec.material,
        "scale": spec.scale,
        "quarter_tone_strategy": spec.quarter_tone_strategy,
        "n_register": spec.n_register,
        "llm_reasoning": spec.llm_reasoning,
        "feasibility": spec.feasibility,
        "lowest_note_hz": spec.lowest_note_hz,
        "n_octaves": spec.n_octaves,
        "targets": spec.targets,
    }


def dict_to_candidate(res: dict, spec: DesignSpec) -> CandidateResult:
    """Reconstruct a CandidateResult from a standalone optimizer dict."""
    return CandidateResult(
        design=spec,
        intonation_rms=res.get("intonation_rms", 1e10),
        timbre_cost=res.get("timbre_cost", 1e10),
        bore_length_opt_mm=res.get("bore_length_opt_mm", 0.0),
        hole_positions_mm=res.get("hole_positions_mm", []),
        hole_diameters_mm=res.get("hole_diameters_mm", []),
        bore_radii=res.get("bore_radii", []),
        pareto_front=res.get("pareto_front", []),
        success=res.get("success", False),
        opt_time_s=res.get("opt_time_s", 0.0),
        error=res.get("error", ""),
    )