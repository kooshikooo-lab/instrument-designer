"""Main generative agent class."""
from __future__ import annotations

import time
from typing import Any

from backend.llm.ollama import check_ollama, _llm_suggest
from backend.llm.schema import DesignSpec, CandidateResult, GenerativeResult
from backend.llm.optimizer import optimize_candidate
from backend.llm.serialization import spec_to_dict, dict_to_candidate
from backend.llm.suggestions import suggest_from_knowledge, _build_targets


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
            self.ollama_url = check_ollama()
        except Exception:
            pass

        if self.verbose:
            if self.ollama_url:
                print(f"[GenerativeAgent] LLM available at {self.ollama_url}")
            else:
                print("[GenerativeAgent] LLM unavailable — using physics engine")

        # Dask connection for parallel candidate optimization
        addr = dask_address if dask_address else "tcp://100.69.113.41:9797"
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
            specs = suggest_from_knowledge(query)
            if not specs:
                result.errors.append("No designs could be generated for query.")
                result.total_time_s = time.time() - t0
                return result

        specs = specs[:n_candidates]

        # Step 2: Optimize each candidate (parallel via Dask or sequential)
        if self.dask_client is not None:
            spec_dicts = [spec_to_dict(s) for s in specs]
            futures = {self.dask_client.submit(optimize_candidate, sd, self.verbose): s
                       for sd, s in zip(spec_dicts, specs)}
            for future, spec in futures.items():
                res_dict = future.result()
                candidate = dict_to_candidate(res_dict, spec)
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

    def _optimize_candidate(self, spec: DesignSpec) -> CandidateResult:
        """Optimize a single design candidate (sequential fallback)."""
        spec_dict = spec_to_dict(spec)
        # Add pre-computed targets if available
        if spec.targets:
            spec_dict["targets"] = spec.targets
        res_dict = optimize_candidate(spec_dict, self.verbose)
        return dict_to_candidate(res_dict, spec)

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

    def design_from_sound(self, filepath: str = "",
                          fundamental_hz: float = 0.0,
                          label: str = "",
                          n_candidates: int = 2) -> GenerativeResult:
        """Inverse design: design an instrument from a target sound spectrum.

        Analyzes a WAV file (or uses an explicit fundamental frequency) to
        determine the instrument's pitch, then optimizes a bore geometry that
        matches the target timbre.

        Parameters
        ----------
        filepath : str
            Path to WAV file for spectral analysis.
        fundamental_hz : float
            Explicit fundamental frequency (Hz) if no WAV provided.
        label : str
            Optional design label.
        n_candidates : int
            Number of candidates to optimize.

        Returns
        -------
        GenerativeResult
            Candidates with optimized bore geometry.
        """
        from backend.sound_analysis import analyze_wav

        t0 = time.time()
        result = GenerativeResult(query=label or "design_from_sound")

        # Analyze sound or use explicit fundamental
        if filepath:
            analysis = analyze_wav(filepath)
            if analysis.get("confidence", 0) < 0.1:
                result.errors.append(
                    f"Could not estimate fundamental "
                    f"(confidence={analysis['confidence']:.3f})"
                )
                result.total_time_s = time.time() - t0
                return result
            fundamental = analysis["fundamental_hz"]
            label = label or f"Inverse: {filepath.split('/')[-1]}"
        elif fundamental_hz > 0:
            fundamental = fundamental_hz
            label = label or f"Inverse: f0={fundamental_hz:.0f}Hz"
        else:
            result.errors.append("No sound file or fundamental frequency provided.")
            result.total_time_s = time.time() - t0
            return result

        result.query = label

        # Generate specs targeting this fundamental
        specs = []
        for _ in range(n_candidates):
            spec = DesignSpec(
                name=f"Inverse: {label}",
                description=f"Inverse design targeting {fundamental:.1f} Hz",
                family="inverse",
                bore_type="cylindrical",
                closed_top=False,
                bore_radius_mm=7.25,
                bore_length_mm=500.0,
                hole_count=6,
                hole_diameter_mm=7.0,
                scale="12_tet",
                feasibility="inverse",
                llm_reasoning="Optimized for timbre match to target spectrum.",
                lowest_note_hz=fundamental,
                n_octaves=2,
                targets=_build_targets(DesignSpec(
                    lowest_note_hz=fundamental, n_octaves=2, hole_count=6, scale="12_tet"
                )),
            )
            specs.append(spec)

        # Optimize
        if self.dask_client is not None:
            spec_dicts = [spec_to_dict(s) for s in specs]
            futures = {self.dask_client.submit(optimize_candidate, sd, self.verbose): s
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


# Convenience module-level functions
def get_agent(verbose: bool = True, dask_address: str | None = None) -> GenerativeAgent:
    """Get a shared GenerativeAgent instance."""
    return GenerativeAgent(verbose=verbose, dask_address=dask_address)


def _result_to_dict(result: GenerativeResult) -> dict:
    """Serialize GenerativeResult to plain dict."""
    return {
        "query": result.query,
        "candidates": [
            {
                "name": c.design.name,
                "description": c.design.description,
                "family": c.design.family,
                "bore_type": c.design.bore_type,
                "closed_top": c.design.closed_top,
                "bore_radius_mm": c.design.bore_radius_mm,
                "bore_length_mm": c.design.bore_length_mm,
                "hole_count": c.design.hole_count,
                "hole_diameter_mm": c.design.hole_diameter_mm,
                "material": c.design.material,
                "scale": c.design.scale,
                "feasibility": c.design.feasibility,
                "llm_reasoning": c.design.llm_reasoning,
                "success": c.success,
                "intonation_rms_cents": c.intonation_rms,
                "timbre_cost": c.timbre_cost,
                "bore_length_mm": c.bore_length_opt_mm,
                "bore_radii": c.bore_radii,
                "hole_positions_mm": c.hole_positions_mm,
                "hole_diameters_mm": c.hole_diameters_mm,
                "pareto_front": c.pareto_front,
                "opt_time_s": c.opt_time_s,
                "error": c.error,
            }
            for c in result.candidates
        ],
        "best": result.best.design.name if result.best else None,
        "total_time_s": result.total_time_s,
        "n_candidates": result.n_candidates,
        "llm_used": result.llm_used,
        "llm_response": result.llm_response,
        "errors": result.errors,
    }