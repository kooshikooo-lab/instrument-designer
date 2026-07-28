"""
Unified design pipeline: dispatcher that selects optimizer/solver/cost by goal.

Integrates all existing methods (generative agent, inverse design, Pareto
optimizer, TMM solver) behind a single configurable pipeline with mode switching.

Usage:
    from backend.design_pipeline import DesignPipeline, select_pipeline

    # Auto-select pipeline by goal
    config = select_pipeline("new_instrument", "query")
    pipeline = DesignPipeline(config)
    result = pipeline.run("quarter-tone bass clarinet")

    # Or configure manually
    config = PipelineConfig(goal="copy_sound", run_tier1=True, tier3_costs=["magnitude_error"])
    pipeline = DesignPipeline(config)
    result = pipeline.run("recording.wav")

    # Direct convenience:
    result = DesignPipeline.copy_sound("recording.wav")
    result = DesignPipeline.new_instrument("bass flute with conical bore")
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from backend.tmm_acoustics import SPEED_OF_SOUND, TMMInstrument, tmm_instrument_from_radii

c = SPEED_OF_SOUND


# =============================================================================
# Pipeline configuration
# =============================================================================

@dataclass
class PipelineConfig:
    """Configuration for a single design pipeline run.

    Parameters
    ----------
    goal : str
        Design goal: ``"copy_sound"``, ``"new_instrument"``, ``"explore"``,
        ``"precision"``.
    input_type : str
        Type of input: ``"sound_file"``, ``"query"``, ``"preset"``.
    solver : str
        Forward solver: ``"tmm_phase"`` (fast, phase-based),
        ``"tmm_cascade"`` (transfer-matrix, medium), ``"openwind"`` (slow,
        accurate).  Default ``"tmm_phase"``.
    run_tier1 : bool
        Run sound analysis (Tier 1).  Default False.
    run_tier2 : bool
        Run scale optimisation (Tier 2).  Default True.
    run_tier3 : bool
        Run timbre matching (Tier 3).  Default False.
    tier2_costs : list of str
        Cost components for Tier 2.  Default ``["intonation"]``.
    tier3_costs : list of str
        Cost components for Tier 3.  Default ``["smoothness", "consistency"]``.
    tier2_optimizer : str
        Optimizer for Tier 2: ``"nsga2"``, ``"de"``, ``"lbfgsb"``.
        Default ``"nsga2"``.
    tier3_optimizer : str
        Optimizer for Tier 3.  Default ``"nsga2"``.
    hole_count : int
        Number of tone holes.  Default 6.
    n_candidates : int
        Number of candidate designs per pipeline run.  Default 2.
    pop_size : int
        Population size for population-based optimizers.  Default 30.
    n_gen : int
        Number of generations for population-based optimizers.  Default 25.
    maxiter : int
        Max iterations for gradient-based optimizers.  Default 100.
    verbose : bool
        Print progress.  Default False.
    """
    goal: str = "new_instrument"
    input_type: str = "query"
    solver: str = "tmm_phase"
    run_tier1: bool = False
    run_tier2: bool = True
    run_tier3: bool = False
    tier2_costs: list[str] = field(default_factory=lambda: ["intonation"])
    tier3_costs: list[str] = field(default_factory=lambda: ["smoothness", "consistency"])
    tier2_optimizer: str = "nsga2"
    tier3_optimizer: str = "nsga2"
    hole_count: int = 6
    n_candidates: int = 2
    pop_size: int = 30
    n_gen: int = 25
    maxiter: int = 100
    verbose: bool = False


# =============================================================================
# Cost function registry
# =============================================================================

def _cost_intonation(inst: TMMInstrument, fingerings: list[list[str]],
                     targets: list[float], n_register: int = 1) -> float:
    """RMS cents intonation cost."""
    from backend.pareto_optimizer import compute_intonation_cost
    return compute_intonation_cost(inst, fingerings, targets, n_register)


def _cost_smoothness(bore_radii: np.ndarray, **kwargs) -> float:
    """Bore smoothness cost (second-difference std)."""
    from backend.pareto_optimizer import _bore_smoothness
    return _bore_smoothness(bore_radii)


def _cost_consistency(hole_diameters: list[float], bore_radius: float, **kwargs) -> float:
    """Hole radiation consistency cost."""
    from backend.pareto_optimizer import _hole_radiation_consistency
    return _hole_radiation_consistency(hole_diameters, bore_radius)


def _cost_timbre_proxy(radii: np.ndarray, hole_diameters: list[float],
                       bore_radius: float, **kwargs) -> float:
    """Combined timbre proxy: smoothness + consistency."""
    from backend.pareto_optimizer import compute_timbre_cost
    return compute_timbre_cost(radii, hole_diameters, bore_radius)


def _cost_magnitude_error(inst: TMMInstrument, target_mags: np.ndarray,
                          n_harmonics: int = 8, **kwargs) -> float:
    """RMS error between estimated and target harmonic magnitudes."""
    from backend.inverse_design import estimate_harmonic_magnitudes
    from backend.physics.losses import KeefeLoss
    estimated = estimate_harmonic_magnitudes(inst, n_harmonics,
                                              loss_model=KeefeLoss())
    n = min(len(estimated), len(target_mags))
    if n < 2:
        return 1e10
    return float(np.sqrt(np.mean((estimated[:n] - target_mags[:n]) ** 2)))


def _cost_evenness(**kwargs) -> float:
    """Impedance peak evenness — stub (needs full spectrum)."""
    return 0.0


def _cost_projection(**kwargs) -> float:
    """Impedance peak projection — stub (needs full spectrum)."""
    return 0.0


def _cost_inharmonicity(**kwargs) -> float:
    """Inharmonicity — stub (needs full spectrum)."""
    return 0.0


# Registry: cost_name → (callable, requires_full_spectrum)
COST_REGISTRY: dict[str, tuple[Callable, bool]] = {
    "intonation":      (_cost_intonation, False),
    "smoothness":      (_cost_smoothness, False),
    "consistency":     (_cost_consistency, False),
    "timbre_proxy":    (_cost_timbre_proxy, False),
    "magnitude_error": (_cost_magnitude_error, False),
    "evenness":        (_cost_evenness, True),
    "projection":      (_cost_projection, True),
    "inharmonicity":   (_cost_inharmonicity, True),
}


# =============================================================================
# Pipeline dispatcher
# =============================================================================

def select_pipeline(goal: str, input_type: str,
                    **overrides: Any) -> PipelineConfig:
    """Select pipeline configuration based on goal and input type.

    Parameters
    ----------
    goal : str
        ``"copy_sound"``, ``"new_instrument"``, ``"explore"``, ``"precision"``.
    input_type : str
        ``"sound_file"``, ``"query"``, ``"preset"``.
    **overrides
        Override any ``PipelineConfig`` field.

    Returns
    -------
    PipelineConfig
    """
    configs: dict[tuple[str, str], PipelineConfig] = {
        # ── Copy a recorded sound exactly ──────────────────────────────────
        ("copy_sound", "sound_file"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=True,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["magnitude_error"],
        ),
        # ── Design a new instrument from a text description ───────────────
        ("new_instrument", "query"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=False,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["smoothness", "consistency"],
        ),
        # ── Design from a preset instrument config ────────────────────────
        ("new_instrument", "preset"): PipelineConfig(
            goal=goal, input_type=input_type,
            run_tier1=False,
            run_tier2=True,
            run_tier3=False,
            tier2_costs=["intonation"],
        ),
        # ── Scientific exploration of the design space ────────────────────
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
        # ── High-precision optimisation (OpenWInD-level accuracy) ─────────
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
        # Fallback to a reasonable default
        config = PipelineConfig(goal=goal, input_type=input_type)
    else:
        config = configs[key]

    # Apply overrides
    for k, v in overrides.items():
        if hasattr(config, k):
            setattr(config, k, v)
    return config


# =============================================================================
# Design pipeline
# =============================================================================

class DesignPipeline:
    """Unified design pipeline — dispatches to the right solver/optimizer/cost.

    Usage:
        config = select_pipeline("copy_sound", "sound_file")
        pipeline = DesignPipeline(config)
        result = pipeline.run("my_instrument.wav")
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.result: dict[str, Any] = {}

    # ── Convenience constructors ──────────────────────────────────────────

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

    # ── Core run method ──────────────────────────────────────────────────

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

        # Pass the full Tier 1 analysis dict through to Tier 3
        self._tier1_analysis: dict[str, Any] | None = None

        # ── Tier 1: Input processing ─────────────────────────────────────
        if cfg.input_type == "sound_file":
            t0 = time.time()
            tier1 = self._run_tier1(input_data)
            result["tier1"] = tier1
            result["timing_s"]["tier1"] = time.time() - t0

            if not tier1.get("success", False):
                result["errors"].append(
                    f"Tier 1 failed: {tier1.get('error', 'unknown')}"
                )
                result["total_time_s"] = time.time() - t_start
                return result

            # Pass full Tier 1 analysis to downstream tiers
            self._tier1_analysis = tier1
            fundamental = tier1["fundamental_hz"]
        else:
            fundamental = None

        # ── Tier 2: Scale optimisation ───────────────────────────────────
        if cfg.run_tier2:
            t0 = time.time()
            tier2 = self._run_tier2(input_data, cfg, fundamental)
            result["tier2"] = tier2
            result["timing_s"]["tier2"] = time.time() - t0

            if not tier2.get("success", False):
                result["errors"].append(
                    f"Tier 2 failed: {tier2.get('error', 'unknown')}"
                )
                result["total_time_s"] = time.time() - t_start
                return result

            # Extract best candidate geometry (use first candidate — "best" key
            # only has name/intonation/timbre, not full geometry)
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

            # Pre-compute targets (needed by Tier 3 if using geometric costs)
            if fundamental:
                result["_fundamental_hz"] = fundamental
        else:
            best_candidate = None

        # ── Tier 3: Timbre matching ──────────────────────────────────────
        if cfg.run_tier3 and best_candidate:
            t0 = time.time()
            tier3 = self._run_tier3(best_candidate, cfg)
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

    # ── Tier 1: Sound analysis ───────────────────────────────────────────

    def _run_tier1(self, filepath: str) -> dict:
        """Analyse a WAV file and extract spectral features."""
        from backend.inverse_design import analyze_wav
        try:
            analysis = analyze_wav(filepath)
            analysis["success"] = True
            return analysis
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Tier 2: Scale optimisation ───────────────────────────────────────

    def _run_tier2(self, input_data: str, cfg: PipelineConfig,
                    fundamental: float | None = None) -> dict:
        """Optimise bore length + hole positions for a playable scale."""
        from backend.generative_agent import get_agent, _result_to_dict

        try:
            agent = get_agent()

            if cfg.input_type == "sound_file" and fundamental:
                # Use the inverse design path via the agent
                result_obj = agent.design_from_sound(
                    fundamental_hz=fundamental,
                    label=f"Inverse: f0={fundamental:.0f}Hz",
                    n_candidates=cfg.n_candidates,
                )
            elif cfg.input_type == "query":
                # Standard LLM-guided or knowledge-base design
                result_obj = agent.design(
                    input_data,
                    n_candidates=cfg.n_candidates,
                )
            else:
                return {"success": False, "error": f"Unsupported input_type: {cfg.input_type}"}

            result_dict = _result_to_dict(result_obj)

            # Determine success from candidates
            valid = [c for c in result_dict.get("candidates", [])
                     if c.get("success")]
            result_dict["success"] = len(valid) > 0
            return result_dict

        except Exception as e:
            import traceback
            return {"success": False, "error": f"{e}\n{traceback.format_exc()}"}

    # ── Tier 3: Timbre matching ──────────────────────────────────────────

    def _run_tier3(self, best_candidate: dict, cfg: PipelineConfig) -> dict:
        """Match timbre by optimising bore radii.

        Dispatches to the appropriate optimiser based on the cost
        components selected.
        """
        from backend.inverse_design import match_timbre

        # If magnitude_error cost is requested, use the full Tier 3 pipeline
        if "magnitude_error" in cfg.tier3_costs and self._tier1_analysis:
            raw = match_timbre(
                best_candidate, self._tier1_analysis,
                n_gen=cfg.n_gen, pop_size=cfg.pop_size,
            )
            # Normalise match_timbre result keys to pipeline convention
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

        # Otherwise use geometric timbre proxy (smoothness + consistency)
        # Build a simple optimisation around the candidate
        from backend.pareto_optimizer import evaluate_bi_objective
        from scipy.optimize import minimize as sp_min

        bore_length = best_candidate.get("bore_length_mm", 500.0)
        bore_r = best_candidate.get("bore_radius_mm", 7.25)
        od = best_candidate.get("outer_diameter_mm", 22.0)
        closed_top = best_candidate.get("closed_top", False)
        hp = best_candidate.get("hole_positions_mm", [])
        hd = best_candidate.get("hole_diameters_mm", [])
        hl = best_candidate.get("hole_length_mm", 3.75)
        n_h = len(hp)

        # Targets (needed for intonation evaluation)
        targets = best_candidate.get("_targets", [])

        # Initial radii (from Tier 2 or defaults)
        init_radii = np.array(best_candidate.get("bore_radii", [bore_r] * 6))

        # Build combined cost: sum of selected cost components
        def cost_fn(radii: np.ndarray) -> float:
            total = 0.0
            for name in cfg.tier3_costs:
                if name == "smoothness":
                    total += _cost_smoothness(radii) * 1.0
                elif name == "consistency":
                    total += _cost_consistency(hd, bore_r) * 0.5
                elif name == "timbre_proxy":
                    total += _cost_timbre_proxy(radii, hd, bore_r)
            return total

        # Initial cost
        cost_init = cost_fn(init_radii)

        # Run a quick L-BFGS-B refinement
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


# =============================================================================
# Module-level convenience
# =============================================================================

def design(**kwargs: Any) -> dict:
    """Top-level convenience: run a design pipeline.

    Accepts any ``PipelineConfig`` field as a keyword argument.
    The ``goal`` and ``input_type`` fields determine the pipeline; all
    other fields override the defaults.

    Examples
    --------
    >>> design(goal="copy_sound", input_type="sound_file",
    ...        filepath="recording.wav")

    >>> design(goal="new_instrument", input_type="query",
    ...        query="quarter-tone bass clarinet")
    """
    # Extract special fields
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
    from backend.inverse_design import synthesize_harmonic, save_synthetic_wav
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
