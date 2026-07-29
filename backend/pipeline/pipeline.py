"""Unified design pipeline — orchestrates Tier 1/2/3 with config-driven dispatch."""
from __future__ import annotations

import time
from typing import Any

import numpy as np

from backend.pipeline.config import PipelineConfig
from backend.pipeline.costs import COST_REGISTRY


# ── Tier 1: Sound analysis ───────────────────────────────────────────────────

def run_tier1(filepath: str) -> dict:
    """Analyse a WAV file and extract spectral features."""
    from backend.sound_analysis import analyze_wav
    try:
        analysis = analyze_wav(filepath)
        analysis["success"] = True
        return analysis
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Tier 2: Scale optimisation ───────────────────────────────────────────────

def run_tier2(input_data: str, cfg: PipelineConfig, fundamental: float | None = None) -> dict:
    """Optimise bore length + hole positions for a playable scale."""
    from backend.generative_agent import get_agent, _result_to_dict

    try:
        agent = get_agent()

        if cfg.input_type == "sound_file" and fundamental:
            result_obj = agent.design_from_sound(
                fundamental_hz=fundamental,
                label=f"Inverse: f0={fundamental:.0f}Hz",
                n_candidates=cfg.n_candidates,
            )
        elif cfg.input_type == "query":
            result_obj = agent.design(input_data, n_candidates=cfg.n_candidates)
        else:
            return {"success": False, "error": f"Unsupported input_type: {cfg.input_type}"}

        result_dict = _result_to_dict(result_obj)
        valid = [c for c in result_dict.get("candidates", []) if c.get("success")]
        result_dict["success"] = len(valid) > 0
        return result_dict

    except Exception as e:
        import traceback
        return {"success": False, "error": f"{e}\n{traceback.format_exc()}"}


# ── Tier 3: Timbre matching ──────────────────────────────────────────────────

def run_tier3(best_candidate: dict, cfg: PipelineConfig, tier1_analysis: dict | None = None) -> dict:
    """Match timbre by optimising bore radii."""
    from backend.design_from_wav import match_timbre
    from backend.pipeline.costs import cost_smoothness, cost_consistency, cost_timbre_proxy
    from scipy.optimize import minimize as sp_min
    import numpy as np

    if "magnitude_error" in cfg.tier3_costs and tier1_analysis:
        raw = match_timbre(best_candidate, tier1_analysis, n_gen=cfg.n_gen, pop_size=cfg.pop_size)
        return {
            "success": raw.get("tier3_success", False),
            "error": raw.get("tier3_error", ""),
            "cost_init": raw.get("tier3_cost_initial", 1e10),
            "cost_best": raw.get("tier3_cost_optimized", 1e10),
            "bore_radii": raw.get("bore_radii_optimized", best_candidate.get("bore_radii", [])),
            "target_envelope_frequencies": raw.get("target_envelope_frequencies", []),
            "target_envelope_magnitudes": raw.get("target_envelope_magnitudes", []),
            "estimated_envelope_initial": raw.get("estimated_envelope_initial", []),
            "estimated_envelope_optimized": raw.get("estimated_envelope_optimized", []),
        }

    bore_length = best_candidate.get("bore_length_mm", 500.0)
    bore_r = best_candidate.get("bore_radius_mm", 7.25)
    od = best_candidate.get("outer_diameter_mm", 22.0)
    closed_top = best_candidate.get("closed_top", False)
    hp = best_candidate.get("hole_positions_mm", [])
    hd = best_candidate.get("hole_diameters_mm", [])
    hl = best_candidate.get("hole_length_mm", 3.75)
    n_h = len(hp)
    init_radii = np.array(best_candidate.get("bore_radii", [bore_r] * 6))

    def cost_fn(radii: np.ndarray) -> float:
        total = 0.0
        for name in cfg.tier3_costs:
            if name == "smoothness":
                total += cost_smoothness(radii) * 1.0
            elif name == "consistency":
                total += cost_consistency(hd, bore_r) * 0.5
            elif name == "timbre_proxy":
                total += cost_timbre_proxy(radii, hd, bore_r)
        return total

    cost_init = cost_fn(init_radii)
    bounds = [(3.0, 15.0)] * len(init_radii)
    res = sp_min(cost_fn, init_radii, method="L-BFGS-B",
                 bounds=bounds, options={"maxiter": cfg.maxiter})

    cost_best = float(res.fun)
    radii_best = res.x.tolist() if res.success else init_radii.tolist()
    succeeded = cost_best <= cost_init + 1e-9

    return {
        "success": succeeded,
        "error": "" if succeeded else "Geometric cost did not improve",
        "cost_init": cost_init,
        "cost_best": cost_best,
        "bore_radii": radii_best,
    }


class DesignPipeline:
    """Unified design pipeline — dispatches to the right solver/optimizer/cost.

    Usage:
        config = select_pipeline("copy_sound", "sound_file")
        pipeline = DesignPipeline(config)
        result = pipeline.run("my_instrument.wav")
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._tier1_analysis: dict[str, Any] | None = None

    # ── Convenience constructors ────────────────────────────────────────────

    @classmethod
    def copy_sound(cls, filepath: str, **overrides: Any) -> dict:
        """Convenience: copy a recorded sound's timbre and scale."""
        config = select_pipeline("copy_sound", "sound_file", **overrides)
        return cls(config).run(filepath)

    @classmethod
    def new_instrument(cls, query: str, **overrides: Any) -> dict:
        """Convenience: design a new instrument from a text description."""
        config = select_pipeline("new_instrument", "query", **overrides)
        return cls(config).run(query)

    @classmethod
    def explore(cls, query_or_lookup: str, **overrides: Any) -> dict:
        """Convenience: explore the Pareto frontier for a design concept."""
        config = select_pipeline("explore", "query", **overrides)
        return cls(config).run(query_or_lookup)

    # ── Core run method ────────────────────────────────────────────────────

    def run(self, input_data: str) -> dict:
        """Execute the pipeline.

        Parameters
        ----------
        input_data : str
            WAV file path, text query, or preset instrument name.

        Returns
        -------
        dict
            Pipeline result with all tier outputs.
        """
        cfg = self.config
        t_start = time.time()
        result: dict[str, Any] = {
            "config": {
                "goal": cfg.goal,
                "input_type": cfg.input_type,
                "solver": cfg.solver,
                "tier1": cfg.run_tier1,
                "tier2": cfg.run_tier2,
                "tier3": cfg.run_tier3,
                "tier2_costs": cfg.tier2_costs,
                "tier3_costs": cfg.tier3_costs,
                "tier2_optimizer": cfg.tier2_optimizer,
                "tier3_optimizer": cfg.tier3_optimizer,
                "hole_count": cfg.hole_count,
                "n_candidates": cfg.n_candidates,
            },
            "timing_s": {},
            "tier1": None,
            "tier2": None,
            "tier3": None,
            "final_geometry": None,
            "errors": [],
        }

        # ── Tier 1: Input processing ───────────────────────────────────────
        if cfg.input_type == "sound_file":
            t0 = time.time()
            tier1 = run_tier1(input_data)
            result["tier1"] = tier1
            result["timing_s"]["tier1"] = time.time() - t0

            if not tier1.get("success", False):
                result["errors"].append(
                    f"Tier 1 failed: {tier1.get('error', 'unknown')}"
                )
                result["total_time_s"] = time.time() - t_start
                return result

            self._tier1_analysis = tier1
            fundamental = tier1["fundamental_hz"]
        else:
            fundamental = None

        # ── Tier 2: Scale optimisation ─────────────────────────────────────
        if cfg.run_tier2:
            t0 = time.time()
            tier2 = run_tier2(input_data, cfg, fundamental)
            result["tier2"] = tier2
            result["timing_s"]["tier2"] = time.time() - t0

            if not tier2.get("success", False):
                result["errors"].append(
                    f"Tier 2 failed: {tier2.get('error', 'unknown')}"
                )
                result["total_time_s"] = time.time() - t_start
                return result

            # Extract best candidate geometry
            candidates = tier2.get("candidates", [])
            if candidates:
                c = candidates[0]
                best_candidate = {
                    "bore_length_mm": c.get("bore_length_mm", 500.0),
                    "bore_radii": c.get("bore_radii", [7.25] * 6),
                    "hole_positions_mm": c.get("hole_positions_mm", []),
                    "hole_diameters_mm": c.get("hole_diameters_mm", []),
                    "closed_top": c.get("closed_top", False),
                    "bore_radius_mm": c.get("bore_radius_mm", 7.25),
                    "outer_diameter_mm": c.get("outer_diameter_mm", 22.0),
                    "hole_length_mm": c.get("hole_length_mm", 3.75),
                    "intonation_rms_cents": c.get("intonation_rms_cents", 1e10),
                }
            else:
                best_candidate = None

            if fundamental:
                result["_fundamental_hz"] = fundamental
        else:
            best_candidate = None

        # ── Tier 3: Timbre matching ────────────────────────────────────────
        if cfg.run_tier3 and best_candidate:
            t0 = time.time()
            tier3 = run_tier3(best_candidate, cfg, self._tier1_analysis)
            result["tier3"] = tier3
            result["timing_s"]["tier3"] = time.time() - t0

            ok = tier3.get("success", False)
            result["final_geometry"] = {
                "bore_length_mm": best_candidate.get("bore_length_mm", 500.0),
                "bore_radii": tier3.get("bore_radii",
                                        best_candidate.get("bore_radii", [])),
                "hole_positions_mm": best_candidate.get("hole_positions_mm", []),
                "hole_diameters_mm": best_candidate.get("hole_diameters_mm", []),
                "intonation_rms_cents": best_candidate.get("intonation_rms_cents", 0.0),
                "timbre_match_cost": tier3.get("cost_best", None),
            }
            if not ok:
                result["errors"].append(
                    f"Tier 3 failed: {tier3.get('error', 'unknown')}"
                )
        elif best_candidate:
            result["final_geometry"] = {
                "bore_length_mm": best_candidate["bore_length_mm"],
                "bore_radii": best_candidate["bore_radii"],
                "hole_positions_mm": best_candidate["hole_positions_mm"],
                "hole_diameters_mm": best_candidate["hole_diameters_mm"],
                "intonation_rms_cents": best_candidate["intonation_rms_cents"],
                "timbre_match_cost": None,
            }

        result["total_time_s"] = time.time() - t_start
        return result


def select_pipeline(goal: str, input_type: str,
                    **overrides: Any) -> PipelineConfig:
    """Select pipeline configuration based on goal and input type."""
    configs: dict[tuple[str, str], PipelineConfig] = {
        ("copy_sound", "sound_file"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=True,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["magnitude_error"],
        ),
        ("new_instrument", "query"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=False,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["smoothness", "consistency"],
        ),
        ("new_instrument", "preset"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=False,
            run_tier2=True,
            run_tier3=False,
            tier2_costs=["intonation"],
        ),
        ("explore", "query"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=False,
            run_tier2=True,
            run_tier3=False,
            tier2_costs=["intonation", "smoothness"],
            tier2_optimizer="nsga2",
        ),
        ("explore", "preset"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=False,
            run_tier2=True,
            run_tier3=False,
            tier2_costs=["intonation", "smoothness"],
            tier2_optimizer="nsga2",
        ),
        ("precision", "preset"): PipelineConfig(
            goal=goal, input_type=input_type,
            solver="openwind",
            run_tier1=False,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["evenness", "projection"],
            tier3_optimizer="lbfgsb",
        ),
    }

    key = (goal, input_type)
    if key not in configs:
        config = PipelineConfig(goal=goal, input_type=input_type)
    else:
        config = configs[key]

    # Apply overrides
    for k, v in overrides.items():
        if hasattr(config, k):
            setattr(config, k, v)
    return config


def design(**kwargs: Any) -> dict:
    """Top-level convenience: run a design pipeline.

    Accepts any PipelineConfig field as a keyword argument.
    The goal and input_type fields determine the pipeline; all
    other fields override the defaults.

    Examples
    --------
    >>> design(goal="copy_sound", input_type="sound_file",
    ...        filepath="recording.wav")

    >>> design(goal="new_instrument", input_type="query",
    ...        query="quarter-tone bass clarinet")
    """
    goal = kwargs.pop("goal", "new_instrument")
    input_type = kwargs.pop("input_type", "query")
    input_data = kwargs.pop("input_data", kwargs.pop("filepath",
                           kwargs.pop("query", "")))

    config = select_pipeline(goal, input_type, **kwargs)
    pipeline = DesignPipeline(config)
    return pipeline.run(input_data)


if __name__ == "__main__":
    print("=" * 70)
    print("  DESIGN PIPELINE — Mode-switching test")
    print("=" * 70)

    # Test 1: Copy sound from synthetic WAV
    print("\n--- Test 1: copy_sound (synthetic 440Hz) ---")
    from backend.sound_analysis import synthesize_harmonic, save_synthetic_wav
    import tempfile, os
    samples = synthesize_harmonic(fundamental_hz=440.0, duration_s=0.5)
    tmp = tempfile.gettempdir()
    wav_path = os.path.join(tmp, "test_440.wav")
    save_synthetic_wav(wav_path, samples)
    r1 = DesignPipeline.copy_sound(wav_path)
    print(f"  Tiers: {r1['config']['tier1']}/{r1['config']['tier2']}/{r1['config']['tier3']}")
    print(f"  Errors: {r1['errors']}")
    print(f"  Time: {r1['total_time_s']:.1f}s")
    if r1.get("tier1"):
        print(f"  Fundamental: {r1['tier1'].get('fundamental_hz', 'N/A'):.1f} Hz")

    # Test 2: New instrument from query
    print("\n--- Test 2: new_instrument (query) ---")
    r2 = DesignPipeline.new_instrument("recorder", verbose=False)
    print(f"  Errors: {r2['errors']}")
    if r2.get("final_geometry"):
        g = r2["final_geometry"]
        print(f"  Length: {g.get('bore_length_mm', 'N/A'):.0f} mm, "
              f"Intonation: {g.get('intonation_rms_cents', 'N/A'):.1f}c")