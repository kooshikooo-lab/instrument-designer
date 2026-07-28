"""
Generative instrument design agent.

LLM-guided Pareto optimization for novel wind instrument designs.

Architecture:
  LLM (Ollama, optional) → suggests novel design specs based on acoustic physics
  → NSGA-II / JAX Pareto optimizer → refines for intonation vs timbre
  → Returns Pareto front with physics explanations

If LLM is unavailable, uses a deterministic physics-based suggestion engine
(instrument_knowledge.py) to generate candidate designs.

Usage:
    from backend.generative_agent import GenerativeAgent
    agent = GenerativeAgent()
    result = agent.design("quarter-tone bass clarinet with conical bore")
    result = agent.random_instrument()
    result = agent.hybrid("clarinet", "saxophone")
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from backend.tmm_acoustics import SPEED_OF_SOUND
from backend.pareto_optimizer import pareto_sweep, run_pareto, evaluate_bi_objective

c = SPEED_OF_SOUND

# Dask scheduler for parallel candidate optimization
DASK_SCHEDULER_URL = "tcp://100.69.113.41:9797"

# Try loading instrument knowledge base
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

# Try importing from benchmark_all for the instrument configs
try:
    from backend.benchmark_all import INSTRUMENTS as BENCHMARK_INSTRUMENTS
except ImportError:
    BENCHMARK_INSTRUMENTS = {}


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


# ============================================================================
# Bore shape generators
# ============================================================================

def _generate_cylindrical_radii(length_mm: float, radius_mm: float,
                                 flare_radius_mm: float | None = None,
                                 n_cp: int = 6) -> np.ndarray:
    return np.full(n_cp, radius_mm)


def _generate_conical_radii(length_mm: float, radius_start_mm: float,
                             radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    return np.linspace(radius_start_mm, radius_end_mm, n_cp)


def _generate_parabolic_radii(length_mm: float, radius_min_mm: float,
                               radius_max_mm: float, n_cp: int = 6) -> np.ndarray:
    t = np.linspace(0, 1, n_cp)
    r = radius_min_mm + (radius_max_mm - radius_min_mm) * t ** 2
    return r


def _generate_bessel_radii(length_mm: float, radius_start_mm: float,
                            radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    x = np.linspace(0.1, 1.0, n_cp)
    r = radius_start_mm + (radius_end_mm - radius_start_mm) * (1.0 - 1.0 / x) / (1.0 - 1.0)
    return np.clip(r, 1.0, 50.0)


def _generate_exponential_radii(length_mm: float, radius_start_mm: float,
                                 radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    x = np.linspace(0, 1, n_cp)
    growth = math.log(radius_end_mm / max(radius_start_mm, 0.1))
    r = radius_start_mm * np.exp(growth * x)
    return r


BORE_SHAPE_GENERATORS = {
    "cylindrical": _generate_cylindrical_radii,
    "conical": _generate_conical_radii,
    "parabolic": _generate_parabolic_radii,
    "bessel": _generate_bessel_radii,
    "exponential": _generate_exponential_radii,
}


# ============================================================================
# Standalone candidate optimizer (Dask-serializable)
# ============================================================================

def _optimize_candidate_standalone(spec_dict: dict, verbose: bool = False) -> dict:
    """Optimize a single design candidate. Module-level for Dask serialization.

    Parameters
    ----------
    spec_dict : dict
        DesignSpec fields serialized as a plain dict.
    verbose : bool
        If True, print progress messages.

    Returns
    -------
    dict
        CandidateResult fields serialized as a plain dict, plus a copy of
        the input spec.
    """
    import os
    import sys
    import time
    import traceback as _tb

    # Ensure repo is on path (Dask workers may not have it)
    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _repo not in sys.path:
        sys.path.insert(0, _repo)

    import numpy as np

    _c = SPEED_OF_SOUND
    t0 = time.time()
    result: dict = {"success": False, "error": "", "opt_time_s": 0.0}

    targets = spec_dict.get("targets", [])
    if not targets or len(targets) < 2:
        try:
            spec = DesignSpec(**{k: v for k, v in spec_dict.items()
                                 if k in DesignSpec.__dataclass_fields__})
            targets = _build_targets(spec)
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

    generator = BORE_SHAPE_GENERATORS.get(bore_type, _generate_cylindrical_radii)
    bore_radii = generator(bore_len, bore_r, bore_r * 1.2)

    pareto_front = []
    try:
        sweep = pareto_sweep(cfg, n_weights=5, maxiter=60, verbose=False)
        pareto_front = [
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
        pareto_front = [
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

    result["pareto_front"] = pareto_front
    result["opt_time_s"] = time.time() - t0
    return result


# ============================================================================
# Serialization helpers for Dask
# ============================================================================

def _spec_to_dict(spec: DesignSpec) -> dict:
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
    }


def _dict_to_candidate(res: dict, spec: DesignSpec) -> CandidateResult:
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
# Physics-based suggestion engine (LLM fallback)
# ============================================================================

def _suggest_from_knowledge(query: str) -> list[DesignSpec]:
    """Generate design specs from instrument_knowledge.py when LLM unavailable."""
    q = query.lower()
    suggestions = []

    # Hybrid instrument?
    for hybrid in HYBRID_INSTRUMENTS:
        words_in_q = [w for w in hybrid.name.lower().split() if len(w) > 3]
        if any(w in q for w in words_in_q):
            mp = INSTRUMENT_FAMILIES.get(hybrid.mouthpiece_family)
            body = INSTRUMENT_FAMILIES.get(hybrid.body_family)
            if mp and body:
                bore_r = (mp.typical_bore_radius_mm[0] + body.typical_bore_radius_mm[0]) / 2
                bore_l = (mp.typical_length_mm[1] + body.typical_length_mm[1]) / 2
                n_holes = max(mp.typical_hole_count[0], body.typical_hole_count[0])
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
            ))

    # Deduplicate by name
    seen = set()
    unique = []
    for s in suggestions:
        if s.name not in seen:
            seen.add(s.name)
            unique.append(s)
    return unique[:5]  # max 5 candidates


# ============================================================================
# LLM integration (Ollama)
# ============================================================================

OLLAMA_URLS = [
    "http://localhost:11434",
    "http://100.100.66.117:11434",
    "http://100.100.69.113:11434",
]


def _check_ollama() -> str | None:
    """Check if Ollama is available and return base URL."""
    import requests
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
    import requests

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
            specs.append(DesignSpec(
                name=d.get("name", "Unknown Design"),
                description=d.get("description", ""),
                family=d.get("family", ""),
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
            ))
        return specs
    except Exception:
        return []


# ============================================================================
# Target frequency generation
# ============================================================================

def _build_targets(spec: DesignSpec) -> list[float]:
    """Build target frequencies from scale definition."""
    scale = SCALES.get(spec.scale)
    if not scale:
        scale = SCALES.get("12_tet")

    if not scale:
        # Fallback: generate from 12-TET
        from backend.target_frequencies import _generate_targets
        closed_top = spec.closed_top
        n_reg = 1 if closed_top else 2
        try:
            return _generate_targets(spec.bore_length_mm / 1000, closed_top, n_reg, spec.hole_count + 1)
        except Exception:
            pass

    # Determine fundamental from bore length (c in mm/s)
    L_mm = spec.bore_length_mm
    if spec.closed_top:
        fundamental = c / (4.0 * L_mm)
    else:
        fundamental = c / (2.0 * L_mm)

    # Build frequencies from scale intervals
    targets = []
    for cents in scale.intervals_cents:
        f = fundamental * (2.0 ** (cents / 1200.0))
        targets.append(f)

    return targets


# ============================================================================
# Main Generative Agent
# ============================================================================

class GenerativeAgent:
    """Generative instrument design agent.

    Combines LLM-guided design suggestion with Pareto optimization.
    Falls back to physics-based suggestion when LLM unavailable.
    """

    def __init__(self, verbose: bool = True, dask_address: str | None = None):
        self.verbose = verbose
        self.ollama_url = None
        self.dask_client = None
        try:
            self.ollama_url = _check_ollama()
        except Exception:
            pass
        if self.verbose:
            if self.ollama_url:
                print(f"[GenerativeAgent] LLM available at {self.ollama_url}")
            else:
                print("[GenerativeAgent] LLM unavailable — using physics engine")

        # Dask connection for parallel candidate optimization
        addr = dask_address if dask_address else DASK_SCHEDULER_URL
        try:
            from distributed import Client
            self.dask_client = Client(addr, timeout=5)
            if self.verbose:
                info = self.dask_client.scheduler_info()
                n_w = len(info.get("workers", {}))
                print(f"[GenerativeAgent] Dask connected to {addr} ({n_w} workers)")
        except Exception as e:
            if self.verbose:
                print(f"[GenerativeAgent] Dask unavailable ({e}) — running sequentially")

    def design(self, query: str, n_candidates: int = 3) -> GenerativeResult:
        """Generate and optimize instrument designs from a text query.

        Parameters
        ----------
        query : str
            Design description (e.g., "quarter-tone bass clarinet with conical bore").
        n_candidates : int
            Maximum number of candidates to optimize.

        Returns
        -------
        GenerativeResult
            All candidates with optimization results.
        """
        t0 = time.time()
        result = GenerativeResult(query=query)

        # Step 1: Generate design specs
        if self.ollama_url:
            specs = _llm_suggest(self.ollama_url, query)
            result.llm_used = bool(specs)
            if specs:
                result.llm_response = specs[0].llm_reasoning if specs else ""

        if not getattr(result, 'llm_used', False) or not specs:
            specs = _suggest_from_knowledge(query)
            if not specs:
                result.errors.append("No designs could be generated for query.")
                result.total_time_s = time.time() - t0
                return result

        specs = specs[:n_candidates]

        # Step 2: Optimize each candidate (parallel via Dask or sequential)
        if self.dask_client is not None:
            spec_dicts = [_spec_to_dict(s) for s in specs]
            futures = {self.dask_client.submit(_optimize_candidate_standalone, sd, self.verbose): s
                       for sd, s in zip(spec_dicts, specs)}
            for future, spec in futures.items():
                res_dict = future.result()
                candidate = _dict_to_candidate(res_dict, spec)
                result.candidates.append(candidate)
        else:
            for spec in specs:
                candidate = self._optimize_candidate(spec)
                result.candidates.append(candidate)

        # Step 3: Select best
        valid = [c for c in result.candidates if c.success]
        if valid:
            result.best = min(valid, key=lambda c: c.intonation_rms)

        result.n_candidates = len(result.candidates)
        result.total_time_s = time.time() - t0
        return result

    def random_instrument(self) -> GenerativeResult:
        """Generate a completely novel random instrument design."""
        return self.design("random experimental instrument")

    def hybrid(self, mouthpiece_family: str, body_family: str) -> GenerativeResult:
        """Design a hybrid instrument combining two families.

        Parameters
        ----------
        mouthpiece_family : str
            Instrument family for the mouthpiece (e.g., "clarinet").
        body_family : str
            Instrument family for the body (e.g., "saxophone").

        Returns
        -------
        GenerativeResult
            Optimized hybrid instrument designs.
        """
        query = f"{mouthpiece_family} mouthpiece on {body_family} body"
        return self.design(query, n_candidates=2)

    def _optimize_candidate(self, spec: DesignSpec) -> CandidateResult:
        """Run Pareto optimization for a single design candidate."""
        import traceback as _tb
        t0 = time.time()
        candidate = CandidateResult(design=spec)

        targets = _build_targets(spec)
        if not targets or len(targets) < 2:
            candidate.error = "Insufficient target frequencies"
            return candidate

        n_holes = int(min(spec.hole_count, len(targets) - 1))

        cfg = {
            "desc": spec.name,
            "closed_top": spec.closed_top,
            "targets": targets,
            "bore_radius": spec.bore_radius_mm,
            "outer_diameter": spec.outer_diameter_mm,
            "hole_diameter": spec.hole_diameter_mm,
            "hole_length": spec.hole_length_mm,
        }

        # Generate initial bore radii based on bore type
        generator = BORE_SHAPE_GENERATORS.get(spec.bore_type, _generate_cylindrical_radii)
        bore_radii = generator(spec.bore_length_mm, spec.bore_radius_mm,
                                spec.bore_radius_mm * 1.2)

        # Run Pareto sweep
        try:
            sweep = pareto_sweep(cfg, n_weights=5, maxiter=60, verbose=False)
            candidate.pareto_front = [
                {"w_int": w, "intonation": intl, "timbre": timb}
                for w, intl, timb, L in sweep
            ]
        except Exception as e:
            if self.verbose:
                print(f"    Pareto sweep failed: {e}")

        # Run NSGA-II
        try:
            front, designs, elapsed = run_pareto(
                cfg, pop_size=20, n_gen=25, verbose=False,
            )
        except Exception:
            print("  NSGA-II failed:")
            _tb.print_exc()
            candidate.error = "NSGA-II optimization failed"
            candidate.opt_time_s = time.time() - t0
            return candidate

        candidate.opt_time_s = elapsed

        if front:
            candidate.pareto_front = [
                {"intonation": intl, "timbre": timb}
                for intl, timb in front
            ]
            # Extract best design
            best_idx = min(range(len(front)), key=lambda i: front[i][0])
            best_design = designs[best_idx]

            n_cp = 6
            candidate.bore_radii = best_design[:n_cp].tolist()
            hp = sorted(best_design[n_cp:n_cp + n_holes].tolist())
            candidate.hole_positions_mm = hp
            candidate.hole_diameters_mm = best_design[n_cp + n_holes:].tolist()
            candidate.intonation_rms = front[best_idx][0]
            candidate.timbre_cost = front[best_idx][1]
            candidate.bore_length_opt_mm = spec.bore_length_mm
            candidate.success = True
        else:
            candidate.error = "NSGA-II returned empty front"

        candidate.opt_time_s = time.time() - t0
        return candidate


# ============================================================================
# Module-level convenience functions
# ============================================================================

_agent: GenerativeAgent | None = None


def get_agent() -> GenerativeAgent:
    """Get or create the singleton generative agent."""
    global _agent
    if _agent is None:
        _agent = GenerativeAgent(verbose=False)
    return _agent


def generate(query: str, n_candidates: int = 3) -> dict:
    """Convenience: generate designs from query.

    Returns a JSON-serializable dict.
    """
    agent = get_agent()
    result = agent.design(query, n_candidates)
    return _result_to_dict(result)


def random_design() -> dict:
    """Convenience: generate a random instrument design."""
    agent = get_agent()
    result = agent.random_instrument()
    return _result_to_dict(result)


def hybrid_design(mouthpiece: str, body: str) -> dict:
    """Convenience: generate a hybrid instrument design."""
    agent = get_agent()
    result = agent.hybrid(mouthpiece, body)
    return _result_to_dict(result)


def _result_to_dict(result: GenerativeResult) -> dict:
    """Serialize GenerativeResult to a JSON-compatible dict."""
    return {
        "query": result.query,
        "total_time_s": result.total_time_s,
        "n_candidates": result.n_candidates,
        "llm_used": result.llm_used,
        "llm_response": result.llm_response,
        "errors": result.errors,
        "candidates": [
            {
                "name": c.design.name,
                "description": c.design.description,
                "family": c.design.family,
                "bore_type": c.design.bore_type,
                "closed_top": c.design.closed_top,
                "bore_radius_mm": c.design.bore_radius_mm,
                "material": c.design.material,
                "scale": c.design.scale,
                "quarter_tone_strategy": c.design.quarter_tone_strategy,
                "feasibility": c.design.feasibility,
                "llm_reasoning": c.design.llm_reasoning,
                "intonation_rms_cents": c.intonation_rms,
                "timbre_cost": c.timbre_cost,
                "bore_length_mm": c.bore_length_opt_mm,
                "hole_positions_mm": c.hole_positions_mm,
                "hole_diameters_mm": c.hole_diameters_mm,
                "bore_radii": c.bore_radii,
                "success": c.success,
                "opt_time_s": c.opt_time_s,
                "error": c.error,
                "pareto_front": c.pareto_front,
            }
            for c in result.candidates
        ],
        "best": (
            {
                "name": result.best.design.name,
                "description": result.best.design.description,
                "intonation_rms_cents": result.best.intonation_rms,
                "timbre_cost": result.best.timbre_cost,
            }
            if result.best else None
        ),
    }


if __name__ == "__main__":
    print("=" * 70)
    print("  GENERATIVE AGENT TEST")
    print("=" * 70)

    agent = GenerativeAgent(verbose=True)

    # Test 1: Known instrument
    print("\n--- Test 1: Design request ---")
    result = agent.design("quarter-tone recorder with parabolic bore", n_candidates=2)
    print(f"  Candidates: {len(result.candidates)}")
    for c in result.candidates:
        print(f"  {c.design.name}: success={c.success}, intonation={c.intonation_rms:.4f}c")

    # Test 2: Random instrument
    print("\n--- Test 2: Random instrument ---")
    result = agent.random_instrument()
    print(f"  Candidates: {len(result.candidates)}")

    # Test 3: Hybrid
    print("\n--- Test 3: Hybrid design ---")
    result = agent.hybrid("clarinet", "saxophone")
    print(f"  Candidates: {len(result.candidates)}")
    for c in result.candidates:
        print(f"  {c.design.name}: success={c.success}")
