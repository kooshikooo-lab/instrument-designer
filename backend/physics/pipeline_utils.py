"""Pipeline utility functions extracted from generative_agent.py.

Bore shape generators, frequency mappings, target computation, and
Dask-serializable candidate optimizer.  Separated per Law 4 (geometry/acoustics
separation) and Law 5 (thin orchestrators).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from backend.tmm_acoustics import SPEED_OF_SOUND
from backend.pareto_optimizer import pareto_sweep, run_pareto

_c = SPEED_OF_SOUND


# ============================================================================
# Shared data types
# ============================================================================


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
    llm_reasoning: str = ""
    feasibility: str = "unknown"
    lowest_note_hz: float = 261.63
    n_octaves: int = 2
    targets: list = field(default_factory=list)


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
    """Top-level result from the generative agent."""
    query: str = ""
    total_time_s: float = 0.0
    n_candidates: int = 0
    llm_used: bool = False
    llm_response: str = ""
    errors: list[str] = field(default_factory=list)
    candidates: list[CandidateResult] = field(default_factory=list)
    best: CandidateResult | None = None


# ============================================================================
# Bore shape generators
# ============================================================================

def generate_cylindrical_radii(length_mm: float, radius_mm: float,
                                flare_radius_mm: float | None = None,
                                n_cp: int = 6) -> np.ndarray:
    return np.full(int(n_cp), radius_mm)


def generate_conical_radii(length_mm: float, radius_start_mm: float,
                            radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    return np.linspace(radius_start_mm, radius_end_mm, int(n_cp))


def generate_parabolic_radii(length_mm: float, radius_min_mm: float,
                              radius_max_mm: float, n_cp: int = 6) -> np.ndarray:
    t = np.linspace(0, 1, int(n_cp))
    r = radius_min_mm + (radius_max_mm - radius_min_mm) * t ** 2
    return r


def generate_bessel_radii(length_mm: float, radius_start_mm: float,
                           radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    x = np.linspace(0.1, 1.0, int(n_cp))
    eps = math.log(radius_start_mm / max(radius_end_mm, 0.1)) / math.log(10.0)
    r = radius_start_mm * (x / 0.1) ** (-eps)
    return np.clip(r, 1.0, 50.0)


def generate_exponential_radii(length_mm: float, radius_start_mm: float,
                                radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    x = np.linspace(0, 1, int(n_cp))
    growth = math.log(radius_end_mm / max(radius_start_mm, 0.1))
    r = radius_start_mm * np.exp(growth * x)
    return r


BORE_SHAPE_GENERATORS: dict[str, callable] = {
    "cylindrical": generate_cylindrical_radii,
    "conical": generate_conical_radii,
    "parabolic": generate_parabolic_radii,
    "bessel": generate_bessel_radii,
    "exponential": generate_exponential_radii,
}


# ============================================================================
# Per-family lowest note mapping (A4 = 440 Hz)
# ============================================================================

FAMILY_LOWEST_NOTE: dict[str, tuple[float, int]] = {
    "clarinet":     (146.83, 3),   # D3
    "saxophone":    (174.61, 3),   # F3
    "flute":        (261.63, 3),   # C4
    "recorder":     (523.25, 2),   # C5
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
    "kazoo":        (261.63, 1),   # C4
}


def family_lowest_note(family: str) -> tuple[float, int]:
    if family in FAMILY_LOWEST_NOTE:
        return FAMILY_LOWEST_NOTE[family]
    try:
        from backend.instrument_knowledge import INSTRUMENT_FAMILIES
        fam = INSTRUMENT_FAMILIES.get(family)
        if fam:
            bore_len = sum(fam.typical_length_mm) / 2
            closed = fam.closed_top
            fundamental = _c / (4.0 * bore_len) if closed else _c / (2.0 * bore_len)
            octaves = max(int(sum(fam.octave_range) / 2), 1)
            return (fundamental, octaves)
    except ImportError:
        pass
    return (261.63, 2)


# ============================================================================
# Target frequency generation
# ============================================================================


def build_targets(spec: DesignSpec) -> list[float]:
    """Build multi-octave target frequencies from scale definition."""
    try:
        from backend.instrument_knowledge import SCALES
    except ImportError:
        return []
    scale = SCALES.get(spec.scale)
    if not scale:
        scale = SCALES.get("12_tet")
    if not scale:
        return []

    fundamental = spec.lowest_note_hz
    targets = []
    for octave in range(max(spec.n_octaves, 1)):
        for cents in scale.intervals_cents:
            f = fundamental * (2.0 ** ((octave * 1200 + cents) / 1200.0))
            targets.append(f)
    max_targets = max(spec.hole_count + 3, 8)
    return targets[:max_targets]


# ============================================================================
# Physics-based suggestion engine (LLM fallback)
# ============================================================================


def suggest_from_knowledge(query: str) -> list[DesignSpec]:
    """Generate design specs from instrument_knowledge.py when LLM unavailable."""
    import random

    from backend.instrument_knowledge import (
        HYBRID_INSTRUMENTS,
        INSTRUMENT_FAMILIES,
        SCALES,
        suggest_material,
    )

    q = query.lower()
    suggestions = []

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
                lowest, octaves = family_lowest_note(hybrid.body_family)
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

    for key, fam in INSTRUMENT_FAMILIES.items():
        if key in q or fam.family.lower() in q:
            bore_r = sum(fam.typical_bore_radius_mm) / 2
            bore_l = sum(fam.typical_length_mm) / 2
            n_holes = max(fam.typical_hole_count)
            hole_d = sum(fam.typical_hole_diameter_mm) / 2 if fam.typical_hole_diameter_mm[1] > 0 else 7.0
            mat = suggest_material(key, purpose="experimental").value

            is_quarter_tone = "quarter" in q or "microtonal" in q or "24" in q
            qt_strategy = ""
            if is_quarter_tone and not fam.closed_top:
                qt_strategy = "additional side holes"
                n_holes = min(n_holes + 4, 14)
            elif is_quarter_tone:
                qt_strategy = "cross-fingering + half-holing"

            scale = "24_tet" if is_quarter_tone else "12_tet"
            lowest, octaves = family_lowest_note(key)
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
                llm_reasoning="; ".join(fam.key_acoustic_challenges[:2]),
                lowest_note_hz=lowest,
                n_octaves=octaves,
            ))

    if "random" in q or not suggestions:
        family_keys = list(INSTRUMENT_FAMILIES.keys())
        for _ in range(3):
            key = random.choice(family_keys)
            fam = INSTRUMENT_FAMILIES[key]
            bore_r = random.uniform(*fam.typical_bore_radius_mm)
            bore_l = random.uniform(*fam.typical_length_mm)
            n_holes = random.randint(*fam.typical_hole_count)
            hole_d = random.uniform(*fam.typical_hole_diameter_mm) if fam.typical_hole_diameter_mm[1] > 0 else 7.0

            bore_shapes = ["cylindrical", "conical", "parabolic", "exponential"]
            bore_type = random.choice(bore_shapes)

            lowest, octaves = family_lowest_note(key)
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

    seen = set()
    unique = []
    for s in suggestions:
        if s.name not in seen:
            seen.add(s.name)
            unique.append(s)
    return unique[:5]


# ============================================================================
# Serialization helpers for Dask
# ============================================================================


def spec_to_dict(spec: DesignSpec) -> dict:
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


# ============================================================================
# Standalone candidate optimizer (Dask-serializable)
# ============================================================================


def optimize_candidate_standalone(spec_dict: dict, verbose: bool = False) -> dict:
    """Optimize a single design candidate. Module-level for Dask serialization."""
    import os
    import sys
    import traceback as _tb

    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _repo not in sys.path:
        sys.path.insert(0, _repo)

    t0 = time.time()
    result: dict = {"success": False, "error": "", "opt_time_s": 0.0}

    targets = spec_dict.get("targets", [])
    if not targets or len(targets) < 2:
        try:
            spec = DesignSpec(**{k: v for k, v in spec_dict.items()
                                 if k in DesignSpec.__dataclass_fields__})
            targets = build_targets(spec)
        except Exception:
            pass
        if not targets or len(targets) < 2:
            result["error"] = "Insufficient target frequencies"
            result["opt_time_s"] = time.time() - t0
            return result

    closed_top = spec_dict.get("closed_top", False)
    bore_r = spec_dict.get("bore_radius_mm", 7.25)
    outer_d = spec_dict.get("outer_diameter_mm", 22.0)
    hole_d = spec_dict.get("hole_diameter_mm", 7.0)
    hole_l = spec_dict.get("hole_length_mm", 3.75)
    bore_len = spec_dict.get("bore_length_mm", 500.0)
    hole_cnt = spec_dict.get("hole_count", 6)
    bore_type = spec_dict.get("bore_type", "cylindrical")
    name = spec_dict.get("name", "Unknown")

    n_holes = int(min(hole_cnt, len(targets) - 1))

    cfg = {
        "desc": name,
        "closed_top": closed_top,
        "targets": targets,
        "bore_radius": bore_r,
        "outer_diameter": outer_d,
        "hole_diameter": hole_d,
        "hole_length": hole_l,
    }

    generator = BORE_SHAPE_GENERATORS.get(bore_type, generate_cylindrical_radii)
    bore_radii = generator(bore_len, bore_r, bore_r * 1.2)

    try:
        sweep = pareto_sweep(cfg, n_weights=5, maxiter=60, verbose=False)
        result["pareto_front"] = [
            {"w_int": w, "intonation": intl, "timbre": timb}
            for w, intl, timb, L in sweep
        ]
    except Exception as e:
        if verbose:
            print(f"    Pareto sweep failed: {e}")

    front, designs, elapsed = [], [], 0.0
    try:
        front, designs, elapsed = run_pareto(
            cfg, pop_size=20, n_gen=25, verbose=False,
        )
    except Exception:
        if verbose:
            print("  NSGA-II failed:")
            _tb.print_exc()
        result["error"] = "NSGA-II optimization failed"
        result["opt_time_s"] = time.time() - t0
        return result

    if front:
        result["pareto_front"] = [
            {"intonation": intl, "timbre": timb}
            for intl, timb in front
        ]
        best_idx = min(range(len(front)), key=lambda i: front[i][0])
        best_design = designs[best_idx]

        n_cp = 6
        result["bore_radii"] = best_design[:n_cp].tolist()
        hp = sorted(best_design[n_cp:n_cp + n_holes].tolist())
        result["hole_positions_mm"] = hp
        result["hole_diameters_mm"] = best_design[n_cp + n_holes:].tolist()
        result["intonation_rms"] = float(front[best_idx][0])
        result["timbre_cost"] = float(front[best_idx][1])
        result["bore_length_opt_mm"] = bore_len
        result["success"] = True
    else:
        result["error"] = "NSGA-II returned empty front"

    result["opt_time_s"] = time.time() - t0
    return result
