"""Data schemas for generative design."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DesignSpec:
    """Specification for a candidate instrument design."""
    name: str
    description: str
    family: str = ""
    bore_type: str = "cylindrical"
    closed_top: bool = False
    bore_radius_mm: float = 7.25
    bore_length_mm: float = 500.0
    hole_count: int = 6
    hole_diameter_mm: float = 7.0
    hole_length_mm: float = 3.75
    outer_diameter_mm: float = 22.0
    material: str = "plastic"
    scale: str = "12_tet"
    quarter_tone_strategy: str = ""
    n_register: int = 2
    feasibility: str = "unknown"
    llm_reasoning: str = ""
    lowest_note_hz: float = 261.63  # default C4
    n_octaves: int = 2
    targets: list[float] = field(default_factory=list)  # pre-computed target freqs


@dataclass
class CandidateResult:
    """Optimization result for a single design candidate."""
    design: DesignSpec
    intonation_rms: float = 1e10
    timbre_cost: float = 1e10
    bore_length_opt_mm: float = 0.0
    hole_positions_mm: list[float] = field(default_factory=list)
    hole_diameters_mm: list[float] = field(default_factory=list)
    bore_radii: list[float] = field(default_factory=list)
    pareto_front: list = field(default_factory=list)
    success: bool = False
    opt_time_s: float = 0.0
    error: str = ""


@dataclass
class GenerativeResult:
    """Full result from the generative agent."""
    query: str
    candidates: list[CandidateResult] = field(default_factory=list)
    best: CandidateResult | None = None
    total_time_s: float = 0.0
    n_candidates: int = 0
    llm_used: bool = False
    llm_response: str = ""
    errors: list[str] = field(default_factory=list)


__all__ = ["DesignSpec", "CandidateResult", "GenerativeResult"]