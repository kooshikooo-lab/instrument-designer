"""
Dask-parallelized generative instrument design agent.

Combines LLM-guided design suggestion (Ollama, optional),
physics-based fallback engine, Dask-parallelized Pareto optimization,
and inverse design from sound.

Usage:
    from backend.generative_agent import GenerativeAgent, generate

    agent = GenerativeAgent()
    result = agent.design("low clarinet in C with extra holes", n_candidates=4)
    print(result.best.design.name)

    # Convenience (JSON-serializable dict):
    data = generate("alto saxophone hybrid", n_candidates=3)
"""

from __future__ import annotations

import json
import math
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from urllib.request import Request, urlopen

import numpy as np

from backend.instrument_knowledge import (
    INSTRUMENT_FAMILIES,
    HYBRID_INSTRUMENTS,
    SCALES,
    MATERIALS,
    get_acoustic_challenges,
    suggest_material,
)
from backend.tmm_acoustics import SPEED_OF_SOUND
from backend.spline_bore import SplineBore, analytical_bore
from backend.inverse_design import analyze_wav

try:
    from distributed import Client
    _DASK_AVAILABLE = True
except ImportError:
    _DASK_AVAILABLE = False


__all__ = [
    "DesignSpec",
    "CandidateResult",
    "GenerativeResult",
    "GenerativeAgent",
    "get_agent",
    "generate",
    "generate_from_sound",
    "random_design",
    "hybrid_design",
]


# =============================================================================
# Data classes
# =============================================================================


@dataclass
class DesignSpec:
    name: str = ""
    description: str = ""
    family: str = ""
    bore_type: str = "cylindrical"
    closed_top: bool = False
    bore_radius_mm: float = 7.0
    bore_length_mm: float = 600.0
    hole_count: int = 6
    hole_diameter_mm: float = 7.0
    hole_length_mm: float = 3.75
    outer_diameter_mm: float = 22.0
    material: str = "plastic"
    scale: str = "12_tet"
    quarter_tone_strategy: str = "none"
    n_register: int = 1
    llm_reasoning: str = ""
    feasibility: str = "unknown"
    lowest_note_hz: float = 261.63
    n_octaves: int = 2
    targets: list[float] = field(default_factory=list)


@dataclass
class CandidateResult:
    design: DesignSpec = field(default_factory=DesignSpec)
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
    query: str = ""
    candidates: list[CandidateResult] = field(default_factory=list)
    best: CandidateResult | None = None
    total_time_s: float = 0.0
    n_candidates: int = 0
    llm_used: bool = False
    llm_response: str = ""
    errors: list[str] = field(default_factory=list)


# =============================================================================
# Bore shape generators (module-level for Dask serialization)
# =============================================================================


def _generate_cylindrical_radii(
    length_mm: float,
    radius_start_mm: float,
    radius_end_mm: float,
    n_cp: int = 6,
) -> np.ndarray:
    return np.full(n_cp, radius_start_mm)


def _generate_conical_radii(
    length_mm: float,
    radius_start_mm: float,
    radius_end_mm: float,
    n_cp: int = 6,
) -> np.ndarray:
    return np.linspace(radius_start_mm, radius_end_mm, n_cp)


def _generate_parabolic_radii(
    length_mm: float,
    radius_start_mm: float,
    radius_end_mm: float,
    n_cp: int = 6,
) -> np.ndarray:
    x = np.linspace(0.0, 1.0, n_cp)
    return radius_start_mm + (radius_end_mm - radius_start_mm) * x ** 2


def _generate_bessel_radii(
    length_mm: float,
    radius_start_mm: float,
    radius_end_mm: float,
    n_cp: int = 6,
) -> np.ndarray:
    x = np.linspace(0.0, 1.0, n_cp)
    flare = 0.5
    return radius_start_mm + (radius_end_mm - radius_start_mm) * x ** flare


def _generate_exponential_radii(
    length_mm: float,
    radius_start_mm: float,
    radius_end_mm: float,
    n_cp: int = 6,
) -> np.ndarray:
    x = np.linspace(0.0, 1.0, n_cp)
    r_start = max(radius_start_mm, 1e-6)
    r_end = max(radius_end_mm, 1e-6)
    return r_start * np.exp(x * np.log(r_end / r_start))


BORE_SHAPE_GENERATORS = {
    "cylindrical": _generate_cylindrical_radii,
    "conical": _generate_conical_radii,
    "parabolic": _generate_parabolic_radii,
    "bessel": _generate_bessel_radii,
    "exponential": _generate_exponential_radii,
}


# =============================================================================
# Standalone candidate optimizer (module-level for Dask)
# =============================================================================


def _optimize_candidate_standalone(spec_dict: dict, verbose: bool = False) -> dict:
    from backend.pareto_optimizer import run_pareto
    from backend.benchmark_all import sequential_refined

    name = spec_dict.get("name", "unknown")
    closed_top = spec_dict.get("closed_top", False)
    bore_radius_mm = spec_dict.get("bore_radius_mm", 7.0)
    bore_length_mm = spec_dict.get("bore_length_mm", 600.0)
    hole_count = spec_dict.get("hole_count", 6)
    hole_diameter_mm = spec_dict.get("hole_diameter_mm", 7.0)
    hole_length_mm = spec_dict.get("hole_length_mm", 3.75)
    outer_diameter_mm = spec_dict.get("outer_diameter_mm", 22.0)
    scale = spec_dict.get("scale", "12_tet")
    targets = spec_dict.get("targets", [])
    lowest_note_hz = spec_dict.get("lowest_note_hz", 261.63)
    n_octaves = spec_dict.get("n_octaves", 2)

    if not targets:
        scale_obj = SCALES.get(scale, SCALES["12_tet"])
        cents = scale_obj.intervals_cents
        target_list = []
        for octave in range(n_octaves):
            for cent in cents:
                freq = lowest_note_hz * 2.0 ** ((octave * 1200.0 + cent) / 1200.0)
                target_list.append(freq)
        max_targets = max(hole_count + 3, 8)
        targets = target_list[:max_targets]

    from backend.pareto_optimizer import build_fingerings

    fingerings = build_fingerings(hole_count, closed_top)
    n_register = 1 if closed_top else 2
    cfg = {
        "closed_top": closed_top,
        "targets": targets,
        "bore_radius": bore_radius_mm,
        "outer_diameter": outer_diameter_mm,
        "hole_diameter": hole_diameter_mm,
        "hole_length": hole_length_mm,
        "fingerings": fingerings,
        "n_register": n_register,
    }

    try:
        pareto_points, pareto_designs, elapsed = run_pareto(cfg, verbose=verbose)
    except Exception:
        try:
            baseline = sequential_refined(cfg)
            rms = float(baseline[0])
            L_base = float(baseline[1])
            hp_seq = baseline[2]
            hd_seq = baseline[3]
            return {
                "success": True,
                "intonation_rms": rms,
                "timbre_cost": 0.0,
                "bore_length_opt_mm": L_base,
                "bore_radii": [bore_radius_mm] * 6,
                "hole_positions_mm": hp_seq,
                "hole_diameters_mm": hd_seq,
                "pareto_front": [],
                "elapsed": 0.0,
                "error": "",
            }
        except Exception as exc:
            return {
                "success": False,
                "intonation_rms": 1e10,
                "timbre_cost": 1e10,
                "bore_length_opt_mm": bore_length_mm,
                "bore_radii": [],
                "hole_positions_mm": [],
                "hole_diameters_mm": [],
                "pareto_front": [],
                "elapsed": 0.0,
                "error": str(exc),
            }

    if not pareto_points or not pareto_designs:
        return {
            "success": False,
            "intonation_rms": 1e10,
            "timbre_cost": 1e10,
            "bore_length_opt_mm": bore_length_mm,
            "bore_radii": [],
            "hole_positions_mm": [],
            "hole_diameters_mm": [],
            "pareto_front": [],
            "elapsed": elapsed,
            "error": "empty pareto front",
        }

    best_idx = min(range(len(pareto_points)), key=lambda i: pareto_points[i][0])
    intonation_rms = float(pareto_points[best_idx][0])
    timbre_cost = float(pareto_points[best_idx][1])
    x_best = pareto_designs[best_idx]

    try:
        baseline = sequential_refined(cfg)
        L_base = float(baseline[1])
        hp_seq = baseline[2]
        n_h = len(hp_seq)
    except Exception:
        L_base = bore_length_mm
        n_h = hole_count

    n_cp = 6
    # run_pareto design vector: [bore_length, radii (n_cp), hp (n_h), hd (n_h)]
    n_h = (len(x_best) - 1 - n_cp) // 2
    L_opt = float(x_best[0])
    radii = x_best[1:n_cp + 1].tolist()
    hp = x_best[n_cp + 1:n_cp + 1 + n_h].tolist()
    hd = x_best[n_cp + 1 + n_h:].tolist()

    return {
        "success": True,
        "intonation_rms": intonation_rms,
        "timbre_cost": timbre_cost,
        "bore_length_opt_mm": L_opt,
        "bore_radii": radii,
        "hole_positions_mm": hp,
        "hole_diameters_mm": hd,
        "pareto_front": [(float(p[0]), float(p[1])) for p in pareto_points],
        "elapsed": elapsed,
        "error": "",
    }


# =============================================================================
# Helper functions
# =============================================================================


def _spec_to_dict(spec: DesignSpec) -> dict:
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


def _dict_to_candidate(res: dict, spec: DesignSpec) -> CandidateResult:
    return CandidateResult(
        design=spec,
        intonation_rms=float(res.get("intonation_rms", 1e10)),
        timbre_cost=float(res.get("timbre_cost", 1e10)),
        bore_length_opt_mm=float(res.get("bore_length_opt_mm", 0.0)),
        hole_positions_mm=list(res.get("hole_positions_mm", [])),
        hole_diameters_mm=list(res.get("hole_diameters_mm", [])),
        bore_radii=list(res.get("bore_radii", [])),
        pareto_front=list(res.get("pareto_front", [])),
        success=bool(res.get("success", False)),
        opt_time_s=float(res.get("elapsed", 0.0)),
        error=str(res.get("error", "")),
    )


def _build_targets(spec: DesignSpec) -> list[float]:
    scale = SCALES.get(spec.scale, SCALES["12_tet"])
    cents = scale.intervals_cents
    fundamental = spec.lowest_note_hz
    targets = []
    for octave in range(spec.n_octaves):
        for cent in cents:
            freq = fundamental * 2.0 ** ((octave * 1200.0 + cent) / 1200.0)
            targets.append(freq)
    max_targets = max(spec.hole_count + 3, 8)
    return targets[:max_targets]


def _family_lowest_note(family: str) -> tuple[float, int]:
    fam = INSTRUMENT_FAMILIES[family]
    typical_length = (fam.typical_length_mm[0] + fam.typical_length_mm[1]) / 2.0
    if fam.closed_top:
        lowest = SPEED_OF_SOUND / (4.0 * typical_length)
    else:
        lowest = SPEED_OF_SOUND / (2.0 * typical_length)
    n_octaves = fam.octave_range[1] - fam.octave_range[0] + 1
    return (lowest, n_octaves)


def _suggest_from_knowledge(query: str) -> list[DesignSpec]:
    query_lower = query.lower()
    specs: list[DesignSpec] = []

    matched_families = []
    for name, fam in INSTRUMENT_FAMILIES.items():
        if name in query_lower or fam.name in query_lower:
            matched_families.append((name, fam))

    if not matched_families:
        for name, fam in INSTRUMENT_FAMILIES.items():
            for word in query_lower.split():
                if word in name or word in fam.description.lower():
                    matched_families.append((name, fam))
                    break

    if not matched_families:
        matched_families = [("clarinet", INSTRUMENT_FAMILIES["clarinet"])]

    for name, fam in matched_families:
        bore_radius = (fam.typical_bore_radius_mm[0] + fam.typical_bore_radius_mm[1]) / 2.0
        bore_length = (fam.typical_length_mm[0] + fam.typical_length_mm[1]) / 2.0
        hole_diameter = (fam.typical_hole_diameter_mm[0] + fam.typical_hole_diameter_mm[1]) / 2.0
        hole_count = (fam.typical_hole_count[0] + fam.typical_hole_count[1]) // 2
        lowest, n_oct = _family_lowest_note(name)
        material = str(suggest_material(name, "experimental").value)
        spec = DesignSpec(
            name=name,
            description=fam.description,
            family=name,
            bore_type=fam.bore_type.value,
            closed_top=fam.closed_top,
            bore_radius_mm=float(bore_radius),
            bore_length_mm=float(bore_length),
            hole_count=int(hole_count),
            hole_diameter_mm=float(hole_diameter),
            hole_length_mm=3.75,
            outer_diameter_mm=float(bore_radius * 2.0 + 6.0),
            material=material,
            scale="12_tet",
            n_register=1 if fam.closed_top else 2,
            lowest_note_hz=float(lowest),
            n_octaves=int(n_oct),
        )
        spec.targets = _build_targets(spec)
        specs.append(spec)

    return specs


# =============================================================================
# GenerativeAgent
# =============================================================================


class GenerativeAgent:
    def __init__(self, verbose: bool = True, dask_address: str | None = None):
        self.verbose = verbose
        self.dask_address = dask_address or os.environ.get("DASK_SCHEDULER", "tcp://127.0.0.1:8786")
        self._client: Client | None = None
        self._ollama_available = False
        self._connect_dask()
        self._check_ollama()

    def _connect_dask(self) -> None:
        if not _DASK_AVAILABLE:
            if self.verbose:
                print("  Dask not installed; running candidates sequentially")
            return
        try:
            self._client = Client(self.dask_address, timeout=5)
            if self.verbose:
                print(f"  Connected to Dask scheduler at {self.dask_address}")
            scheduler_info = self._client.scheduler_info()
            workers = scheduler_info.get("workers", {})
            if not workers:
                if self.verbose:
                    print("  No Dask workers available; falling back to sequential")
                self._client.close()
                self._client = None
        except Exception:
            if self.verbose:
                print("  Could not connect to Dask scheduler; running sequentially")
            self._client = None

    def _check_ollama(self) -> None:
        try:
            req = Request("http://100.69.113.41:11434/api/tags", method="GET")
            req.add_header("Content-Type", "application/json")
            with urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                self._ollama_available = len(data.get("models", [])) > 0
            if self.verbose:
                print(f"  Ollama {'available' if self._ollama_available else 'no models found'}")
        except Exception:
            self._ollama_available = False
            if self.verbose:
                print("  Ollama not available")

    def _query_llm(self, prompt: str) -> str:
        if not self._ollama_available:
            return ""
        try:
            payload = json.dumps({
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 512},
            }).encode()
            req = Request(
                "http://100.69.113.41:11434/api/generate",
                data=payload,
                method="POST",
            )
            req.add_header("Content-Type", "application/json")
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data.get("response", "")
        except Exception:
            return ""

    def _generate_specs_via_llm(self, query: str, n_candidates: int) -> list[DesignSpec]:
        prompt = (
            f"You are a wind instrument designer. Given the request '{query}', "
            f"suggest {n_candidates} distinct instrument designs. "
            f"For each, provide: name, family, bore_type (cylindrical/conical/parabolic/exponential/bessel), "
            f"closed_top (true/false), bore_radius_mm, bore_length_mm, hole_count, "
            f"hole_diameter_mm, material, scale (12_tet/24_tet/maqam_rast/slendro/just_intonation), "
            f"and a brief feasibility assessment. "
            f"Return valid JSON as a list of objects."
        )
        response = self._query_llm(prompt)
        specs = []
        if response:
            try:
                data = json.loads(response)
                if isinstance(data, list):
                    for item in data:
                        spec = DesignSpec(
                            name=item.get("name", ""),
                            description=item.get("description", ""),
                            family=item.get("family", ""),
                            bore_type=item.get("bore_type", "cylindrical"),
                            closed_top=bool(item.get("closed_top", False)),
                            bore_radius_mm=float(item.get("bore_radius_mm", 7.0)),
                            bore_length_mm=float(item.get("bore_length_mm", 600.0)),
                            hole_count=int(item.get("hole_count", 6)),
                            hole_diameter_mm=float(item.get("hole_diameter_mm", 7.0)),
                            material=item.get("material", "plastic"),
                            scale=item.get("scale", "12_tet"),
                            llm_reasoning=item.get("feasibility", ""),
                            feasibility=item.get("feasibility", "unknown"),
                        )
                        try:
                            spec.lowest_note_hz, spec.n_octaves = _family_lowest_note(spec.family)
                        except KeyError:
                            spec.lowest_note_hz = 261.63
                            spec.n_octaves = 2
                        spec.targets = _build_targets(spec)
                        specs.append(spec)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return specs

    def _optimize_candidate(self, spec: DesignSpec) -> CandidateResult:
        spec_dict = _spec_to_dict(spec)
        if not spec.targets:
            spec.targets = _build_targets(spec)
            spec_dict["targets"] = spec.targets
        result = _optimize_candidate_standalone(spec_dict, verbose=self.verbose)
        return _dict_to_candidate(result, spec)

    def design(self, query: str, n_candidates: int = 3, **kwargs: Any) -> GenerativeResult:
        t0 = time.time()
        result = GenerativeResult(query=query, n_candidates=n_candidates)

        specs = self._generate_specs_via_llm(query, n_candidates)
        if not specs:
            specs = _suggest_from_knowledge(query)
            if len(specs) > n_candidates:
                specs = specs[:n_candidates]
            while len(specs) < n_candidates and specs:
                specs.append(specs[-1])
        if len(specs) > n_candidates:
            specs = specs[:n_candidates]

        result.llm_used = self._ollama_available and bool(specs[0].llm_reasoning) if specs else False
        result.llm_response = specs[0].llm_reasoning if specs else ""

        if self._client is not None:
            futures = []
            for spec in specs:
                spec_dict = _spec_to_dict(spec)
                if not spec.targets:
                    spec.targets = _build_targets(spec)
                    spec_dict["targets"] = spec.targets
                future = self._client.submit(_optimize_candidate_standalone, spec_dict)
                futures.append((future, spec))
            all_failed = False
            for future, spec in futures:
                try:
                    res = future.result(timeout=600)
                    candidate = _dict_to_candidate(res, spec)
                    result.candidates.append(candidate)
                except Exception as exc:
                    result.errors.append(str(exc))
                    candidate = CandidateResult(design=spec, error=str(exc), success=False)
                    result.candidates.append(candidate)
            if result.candidates and not any(c.success for c in result.candidates):
                all_failed = True
            if all_failed:
                result.candidates.clear()
                result.errors.append("Dask workers failed -- falling back to sequential")
                for spec in specs:
                    candidate = self._optimize_candidate(spec)
                    result.candidates.append(candidate)
        else:
            for spec in specs:
                candidate = self._optimize_candidate(spec)
                result.candidates.append(candidate)

        if result.candidates:
            succeeded = [c for c in result.candidates if c.success]
            if succeeded:
                result.best = min(succeeded, key=lambda c: c.intonation_rms)
            else:
                result.best = min(result.candidates, key=lambda c: c.intonation_rms)

        result.total_time_s = time.time() - t0
        return result

    def random_instrument(self) -> GenerativeResult:
        import random as _random
        rng = _random.Random()
        family_names = list(INSTRUMENT_FAMILIES.keys())
        family_name = rng.choice(family_names)
        fam = INSTRUMENT_FAMILIES[family_name]
        bore_radius = rng.uniform(fam.typical_bore_radius_mm[0], fam.typical_bore_radius_mm[1])
        bore_length = rng.uniform(fam.typical_length_mm[0], fam.typical_length_mm[1])
        hole_count = rng.randint(fam.typical_hole_count[0], fam.typical_hole_count[1])
        hole_diameter = rng.uniform(fam.typical_hole_diameter_mm[0], fam.typical_hole_diameter_mm[1])
        scale_names = list(SCALES.keys())
        scale_name = rng.choice(scale_names)
        material_keys = list(MATERIALS.keys())
        material = rng.choice(material_keys)
        bore_types = ["cylindrical", "conical", "parabolic", "exponential", "bessel"]
        bore_type = rng.choice(bore_types)
        lowest, n_oct = _family_lowest_note(family_name)

        spec = DesignSpec(
            name=f"random_{family_name}_{uuid.uuid4().hex[:6]}",
            description=f"Randomized {family_name}",
            family=family_name,
            bore_type=bore_type,
            closed_top=fam.closed_top,
            bore_radius_mm=float(bore_radius),
            bore_length_mm=float(bore_length),
            hole_count=int(hole_count),
            hole_diameter_mm=float(hole_diameter),
            hole_length_mm=3.75,
            outer_diameter_mm=float(bore_radius * 2.0 + 6.0),
            material=material,
            scale=scale_name,
            n_register=1 if fam.closed_top else 2,
            lowest_note_hz=float(lowest),
            n_octaves=int(n_oct),
        )
        spec.targets = _build_targets(spec)
        return self.design(spec.description, n_candidates=1)

    def hybrid(self, mouthpiece_family: str, body_family: str) -> GenerativeResult:
        match_name = None
        for h in HYBRID_INSTRUMENTS:
            if mouthpiece_family in h.mouthpiece_family and body_family in h.body_family:
                match_name = h.name
                break
            if h.mouthpiece_family == mouthpiece_family and h.body_family == body_family:
                match_name = h.name
                break

        if match_name is None:
            fallback = HYBRID_INSTRUMENTS[0]
            mouthpiece_family = fallback.mouthpiece_family
            body_family = fallback.body_family

        body_fam = INSTRUMENT_FAMILIES.get(body_family, INSTRUMENT_FAMILIES["clarinet"])
        bore_radius = (body_fam.typical_bore_radius_mm[0] + body_fam.typical_bore_radius_mm[1]) / 2.0
        bore_length = (body_fam.typical_length_mm[0] + body_fam.typical_length_mm[1]) / 2.0
        hole_count = (body_fam.typical_hole_count[0] + body_fam.typical_hole_count[1]) // 2
        hole_diameter = (body_fam.typical_hole_diameter_mm[0] + body_fam.typical_hole_diameter_mm[1]) / 2.0
        lowest, n_oct = _family_lowest_note(body_family)

        spec = DesignSpec(
            name=f"hybrid_{mouthpiece_family}_{body_family}",
            description=f"Hybrid: {mouthpiece_family} mouthpiece on {body_family} body",
            family=body_family,
            bore_type=body_fam.bore_type.value,
            closed_top=body_fam.closed_top,
            bore_radius_mm=float(bore_radius),
            bore_length_mm=float(bore_length),
            hole_count=int(hole_count),
            hole_diameter_mm=float(hole_diameter),
            hole_length_mm=3.75,
            outer_diameter_mm=float(bore_radius * 2.0 + 6.0),
            material="plastic",
            scale="12_tet",
            n_register=1 if body_fam.closed_top else 2,
            lowest_note_hz=float(lowest),
            n_octaves=int(n_oct),
        )
        spec.targets = _build_targets(spec)
        return self.design(spec.description, n_candidates=2)

    def design_from_sound(
        self,
        filepath: str = "",
        fundamental_hz: float = 0.0,
        label: str = "",
        n_candidates: int = 2,
    ) -> GenerativeResult:
        from backend.pareto_optimizer import run_pareto
        from backend.benchmark_all import sequential_refined

        t0 = time.time()
        result = GenerativeResult(query=f"design_from_sound:{label or filepath}")

        if filepath:
            try:
                analysis = analyze_wav(filepath)
                f0 = analysis.get("fundamental_hz", fundamental_hz)
            except Exception:
                f0 = fundamental_hz
        else:
            f0 = fundamental_hz

        if f0 <= 0.0:
            f0 = 261.63

        target_freqs = [f0 * (i + 1) for i in range(6)]

        length_guess = SPEED_OF_SOUND / (2.0 * f0) if f0 > 0 else 600.0

        spec = DesignSpec(
            name=label or f"sound_design_{uuid.uuid4().hex[:6]}",
            description=f"Inverse design from {'WAV' if filepath else 'fundamental'}",
            family="clarinet",
            bore_type="cylindrical",
            closed_top=True,
            bore_radius_mm=7.0,
            bore_length_mm=float(length_guess),
            hole_count=6,
            hole_diameter_mm=7.0,
            hole_length_mm=3.75,
            outer_diameter_mm=20.0,
            material="plastic",
            scale="12_tet",
            n_register=1,
            lowest_note_hz=float(f0),
            n_octaves=2,
            targets=[float(t) for t in target_freqs],
        )

        candidate = self._optimize_candidate(spec)
        result.candidates = [candidate]
        if candidate.success:
            result.best = candidate
        else:
            result.best = candidate

        result.total_time_s = time.time() - t0
        result.n_candidates = 1
        return result


# =============================================================================
# Serialization helpers for module-level access
# =============================================================================

_AGENT: GenerativeAgent | None = None


def get_agent() -> GenerativeAgent:
    global _AGENT
    if _AGENT is None:
        _AGENT = GenerativeAgent(verbose=False)
    return _AGENT


def _result_to_dict(r: GenerativeResult) -> dict:
    def _candidate_dict(c: CandidateResult) -> dict:
        return {
            "design": _spec_to_dict(c.design),
            "intonation_rms": c.intonation_rms,
            "timbre_cost": c.timbre_cost,
            "bore_length_opt_mm": c.bore_length_opt_mm,
            "hole_positions_mm": c.hole_positions_mm,
            "hole_diameters_mm": c.hole_diameters_mm,
            "bore_radii": c.bore_radii,
            "pareto_front": c.pareto_front,
            "success": c.success,
            "opt_time_s": c.opt_time_s,
            "error": c.error,
        }

    return {
        "query": r.query,
        "candidates": [_candidate_dict(c) for c in r.candidates],
        "best": _candidate_dict(r.best) if r.best else None,
        "total_time_s": r.total_time_s,
        "n_candidates": r.n_candidates,
        "llm_used": r.llm_used,
        "llm_response": r.llm_response,
        "errors": r.errors,
    }


def generate(query: str, n_candidates: int = 3) -> dict:
    agent = get_agent()
    return _result_to_dict(agent.design(query, n_candidates))


def generate_from_sound(
    filepath: str = "",
    fundamental_hz: float = 0.0,
    label: str = "",
    n_candidates: int = 2,
) -> dict:
    agent = get_agent()
    return _result_to_dict(
        agent.design_from_sound(filepath, fundamental_hz, label, n_candidates)
    )


def random_design() -> dict:
    agent = get_agent()
    return _result_to_dict(agent.random_instrument())


def hybrid_design(mouthpiece: str, body: str) -> dict:
    agent = get_agent()
    return _result_to_dict(agent.hybrid(mouthpiece, body))
