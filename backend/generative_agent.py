"""
Generative instrument design agent.

LLM-guided Pareto optimization for novel wind instrument designs.

Architecture:
  LLM (Ollama, optional) suggests novel design specs based on acoustic physics
  NSGA-II / JAX Pareto optimizer refines for intonation vs timbre
  Returns Pareto front with physics explanations

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
import os
import time

from backend.physics.pipeline_utils import (
    BORE_SHAPE_GENERATORS,
    CandidateResult,
    DesignSpec,
    GenerativeResult,
    build_targets,
    dict_to_candidate,
    family_lowest_note,
    generate_cylindrical_radii,
    optimize_candidate_standalone,
    spec_to_dict,
    suggest_from_knowledge,
)
from backend.tmm_acoustics import SPEED_OF_SOUND

# Dask scheduler — override via DASK_SCHEDULER_URL env var
DASK_SCHEDULER_URL = os.environ.get("DASK_SCHEDULER_URL", "tcp://localhost:9797")

# Ollama hosts — override via OLLAMA_HOSTS env var (comma-separated)
OLLAMA_URLS = [h.strip() for h in os.environ.get("OLLAMA_HOSTS", "http://localhost:11434").split(",")]

INSTRUMENT_FAMILIES = {}
HYBRID_INSTRUMENTS = []
QUARTER_TONE_STRATEGIES = []
SCALES = {}
MATERIALS = {}
MaterialType = None
get_acoustic_challenges = None
suggest_material = None
KNOWLEDGE_AVAILABLE = False

try:
    from backend.instrument_knowledge import (
        HYBRID_INSTRUMENTS,
        INSTRUMENT_FAMILIES,
        MATERIALS,
        QUARTER_TONE_STRATEGIES,
        SCALES,
        MaterialType,
        get_acoustic_challenges,
        suggest_material,
    )
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    pass

try:
    from backend.benchmark_all import INSTRUMENTS as BENCHMARK_INSTRUMENTS
except ImportError:
    BENCHMARK_INSTRUMENTS = {}


def _check_ollama() -> str | None:
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
    import requests

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
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                designs = json.loads(text[start:end])
            except json.JSONDecodeError:
                return []
        else:
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
            lowest, octaves = family_lowest_note(family_key)
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

        addr = dask_address if dask_address else DASK_SCHEDULER_URL
        try:
            from distributed import Client
            self.dask_client = Client(addr, timeout=5)
            if self.verbose:
                info = self.dask_client.scheduler_info()
                n_w = len(info.get("workers", {}))
                print(f"[GenerativeAgent] Dask connected to {addr} ({n_w} workers)")
            if not info.get("workers"):
                if self.verbose:
                    print("[GenerativeAgent] No Dask workers — falling back to sequential")
                self.dask_client = None
        except Exception as e:
            self.dask_client = None
            if self.verbose:
                print(f"[GenerativeAgent] Dask unavailable ({e}) — running sequentially")

    def design(self, query: str, n_candidates: int = 3) -> GenerativeResult:
        t0 = time.time()
        result = GenerativeResult(query=query)

        if self.ollama_url:
            specs = _llm_suggest(self.ollama_url, query)
            result.llm_used = bool(specs)
            if specs:
                result.llm_response = specs[0].llm_reasoning if specs else ""

        if not getattr(result, 'llm_used', False) or not specs:
            specs = suggest_from_knowledge(query)
            if not specs:
                result.errors.append("No designs could be generated for query.")
                result.total_time_s = time.time() - t0
                return result

        specs = specs[:n_candidates]

        if self.dask_client is not None:
            spec_dicts = [spec_to_dict(s) for s in specs]
            futures = {self.dask_client.submit(optimize_candidate_standalone, sd, self.verbose): s
                       for sd, s in zip(spec_dicts, specs)}
            for future, spec in futures.items():
                res_dict = future.result()
                candidate = dict_to_candidate(res_dict, spec)
                result.candidates.append(candidate)
        else:
            for spec in specs:
                candidate = self._optimize_candidate(spec)
                result.candidates.append(candidate)

        valid = [c for c in result.candidates if c.success]
        if valid:
            result.best = min(valid, key=lambda c: c.intonation_rms)

        result.n_candidates = len(result.candidates)
        result.total_time_s = time.time() - t0
        return result

    def random_instrument(self) -> GenerativeResult:
        return self.design("random experimental instrument")

    def hybrid(self, mouthpiece_family: str, body_family: str) -> GenerativeResult:
        query = f"{mouthpiece_family} mouthpiece on {body_family} body"
        return self.design(query, n_candidates=2)

    def design_from_sound(self, filepath: str = "",
                          fundamental_hz: float = 0.0,
                          label: str = "",
                          n_candidates: int = 2) -> GenerativeResult:
        from backend import inverse_design

        if filepath:
            analysis = inverse_design.analyze_wav(filepath)
            if analysis["confidence"] < 0.1:
                result = GenerativeResult(query=label or filepath)
                result.errors.append(
                    f"Could not estimate fundamental "
                    f"(confidence={analysis['confidence']:.3f})"
                )
                result.total_time_s = 0.0
                return result
            fundamental = analysis["fundamental_hz"]
            label = label or f"Inverse: {filepath.split('/')[-1]}"
        elif fundamental_hz > 0:
            fundamental = fundamental_hz
            label = label or f"Inverse: f0={fundamental_hz:.0f}Hz"
        else:
            result = GenerativeResult(query="design_from_sound")
            result.errors.append("Provide filepath or fundamental_hz")
            result.total_time_s = 0.0
            return result

        c_sped = SPEED_OF_SOUND
        L_open = c_sped / (2.0 * fundamental)
        is_closed = False
        bore_length = L_open

        spec = DesignSpec(
            name=label,
            description=f"Inverse-designed from sound (f0={fundamental:.1f} Hz)",
            bore_type="cylindrical",
            closed_top=is_closed,
            bore_radius_mm=7.25,
            bore_length_mm=min(bore_length, 5000.0),
            hole_count=6,
            scale="12_tet",
            lowest_note_hz=fundamental,
            n_octaves=2,
        )

        t0 = time.time()
        result = GenerativeResult(query=label)

        if self.dask_client is not None:
            spec_dict = spec_to_dict(spec)
            future = self.dask_client.submit(optimize_candidate_standalone,
                                              spec_dict, self.verbose)
            res_dict = future.result()
            candidate = dict_to_candidate(res_dict, spec)
            result.candidates.append(candidate)
        else:
            candidate = self._optimize_candidate(spec)
            result.candidates.append(candidate)

        valid_c = [c for c in result.candidates if c.success]
        if valid_c:
            result.best = min(valid_c, key=lambda c: c.intonation_rms)

        result.n_candidates = len(result.candidates)
        result.total_time_s = time.time() - t0
        return result

    def _optimize_candidate(self, spec: DesignSpec) -> CandidateResult:
        import traceback as _tb
        t0 = time.time()
        candidate = CandidateResult(design=spec)

        targets = spec.targets if spec.targets else build_targets(spec)
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

        generator = BORE_SHAPE_GENERATORS.get(spec.bore_type, generate_cylindrical_radii)
        bore_radii = generator(spec.bore_length_mm, spec.bore_radius_mm,
                                spec.bore_radius_mm * 1.2)

        try:
            from backend.pareto_optimizer import pareto_sweep
            sweep = pareto_sweep(cfg, n_weights=5, maxiter=60, verbose=False)
            candidate.pareto_front = [
                {"w_int": w, "intonation": intl, "timbre": timb}
                for w, intl, timb, L in sweep
            ]
        except Exception as e:
            if self.verbose:
                print(f"    Pareto sweep failed: {e}")

        try:
            from backend.pareto_optimizer import run_pareto
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


def get_agent() -> GenerativeAgent:
    if not hasattr(get_agent, '_cache'):
        get_agent._cache = GenerativeAgent(verbose=False)
    return get_agent._cache


def generate(query: str, n_candidates: int = 3) -> dict:
    agent = get_agent()
    result = agent.design(query, n_candidates)
    return _result_to_dict(result)


def generate_from_sound(filepath: str = "",
                        fundamental_hz: float = 0.0,
                        label: str = "",
                        n_candidates: int = 2) -> dict:
    agent = get_agent()
    result = agent.design_from_sound(
        filepath=filepath,
        fundamental_hz=fundamental_hz,
        label=label,
        n_candidates=n_candidates,
    )
    return _result_to_dict(result)


def random_design() -> dict:
    agent = get_agent()
    result = agent.random_instrument()
    return _result_to_dict(result)


def hybrid_design(mouthpiece: str, body: str) -> dict:
    agent = get_agent()
    result = agent.hybrid(mouthpiece, body)
    return _result_to_dict(result)


def _result_to_dict(result: GenerativeResult) -> dict:
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
