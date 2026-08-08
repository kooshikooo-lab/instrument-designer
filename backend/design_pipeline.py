"""Unified design pipeline dispatcher for unconventional wind instrument design.

Modes:
  - copy_sound   : Copy a recorded sound's timbre and scale (Tiers 1+2+3)
  - new_instrument: Design from text description (Tiers 2+3)
  - explore      : Scientific exploration of design space (Pareto front)
  - precision    : High-precision with OpenWind-level accuracy (future)

Usage:
    from backend.design_pipeline import DesignPipeline, design

    result = DesignPipeline.copy_sound("recording.wav", hole_count=8)
    result = DesignPipeline.new_instrument("A baroque flute", verbose=True)
    result = DesignPipeline.explore("6-hole flute pareto front")

    from backend.design_pipeline import select_pipeline, PipelineConfig
    config = select_pipeline("precision", "preset", solver="openwind")
    pipeline = DesignPipeline(config)
    result = pipeline.run("baroque_flute_v3")

    result = design(goal="copy_sound", input_type="sound_file", filepath="recording.wav")
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

import numpy as np
from scipy.optimize import minimize

from backend.generative_agent import get_agent, _result_to_dict
from backend.inverse_design import analyze_wav, match_timbre
from backend.pareto_optimizer import (
    build_fingerings,
    compute_intonation_cost,
    compute_timbre_cost,
)
from backend.tmm_acoustics import SPEED_OF_SOUND, tmm_instrument_from_radii


@dataclass
class PipelineConfig:
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


# ---------------------------------------------------------------------------
# Cost functions
# ---------------------------------------------------------------------------


def _cost_intonation(candidate: dict) -> float:
    bore_length = candidate.get("bore_length", candidate.get("bore_length_mm", 600.0))
    hole_positions = candidate.get("hole_positions", candidate.get("hole_positions_mm", []))
    hole_diameters = candidate.get("hole_diameters", candidate.get("hole_diameters_mm", []))
    hole_lengths = candidate.get("hole_lengths", candidate.get("hole_lengths_mm", []))
    closed_top = candidate.get("closed_top", False)
    bore_radii = candidate.get("bore_radii", candidate.get("bore_radii_mm", []))
    targets = candidate.get("target_frequencies", [])

    if not targets or not hole_positions or len(bore_radii) == 0:
        return 0.0

    try:
        inst = tmm_instrument_from_radii(
            np.array(bore_radii, dtype=float),
            bore_length,
            hole_positions,
            hole_diameters,
            hole_lengths,
            closed_top=closed_top,
        )
        fingerings = build_fingerings(len(hole_positions), closed_top)
        return compute_intonation_cost(inst, fingerings, targets)
    except Exception:
        return 1e10


def _bore_smoothness(radii: np.ndarray) -> float:
    if len(radii) < 3:
        return 0.0
    dd = np.diff(radii, n=2)
    return float(np.std(dd))


def _hole_radiation_consistency(hole_diameters: list[float], bore_radius: float) -> float:
    if not hole_diameters or bore_radius <= 0:
        return 0.0
    ratios = [(d / (2.0 * bore_radius)) ** 2 for d in hole_diameters]
    return float(np.std(ratios))


def _cost_smoothness(candidate: dict) -> float:
    radii = np.array(candidate.get("bore_radii", candidate.get("bore_radii_mm", [])), dtype=float)
    return _bore_smoothness(radii)


def _cost_consistency(candidate: dict) -> float:
    hole_diameters = candidate.get("hole_diameters", candidate.get("hole_diameters_mm", []))
    bore_radii = candidate.get("bore_radii", candidate.get("bore_radii_mm", []))
    bore_radius = candidate.get("bore_radius", np.mean(bore_radii) if bore_radii else 7.0)
    return _hole_radiation_consistency(hole_diameters, bore_radius)


def _cost_timbre_proxy(candidate: dict) -> float:
    radii = np.array(candidate.get("bore_radii", candidate.get("bore_radii_mm", [])), dtype=float)
    if len(radii) < 3:
        return 0.0
    smoothness = _bore_smoothness(radii)
    hole_diameters = candidate.get("hole_diameters", candidate.get("hole_diameters_mm", []))
    bore_radii = candidate.get("bore_radii", candidate.get("bore_radii_mm", []))
    bore_radius = candidate.get("bore_radius", np.mean(bore_radii) if bore_radii else 7.0)
    consistency = _hole_radiation_consistency(hole_diameters, bore_radius)
    return smoothness + 0.5 * consistency


def _cost_magnitude_error(candidate: dict) -> float:
    target = np.array(candidate.get("target_envelope", []), dtype=float)
    actual = np.array(candidate.get("estimated_envelope", []), dtype=float)
    if len(target) == 0 or len(actual) == 0:
        return 0.0
    n = min(len(target), len(actual))
    return float(np.mean((target[:n] - actual[:n]) ** 2))


def _cost_evenness(candidate: dict) -> float:
    hp = candidate.get("hole_positions", [])
    if len(hp) < 2:
        return 0.0
    gaps = np.diff(sorted(hp))
    mean_gap = np.mean(gaps)
    if mean_gap == 0:
        return 0.0
    return float(np.sqrt(np.mean((gaps - mean_gap) ** 2)) / mean_gap)


def _cost_projection(candidate: dict) -> float:
    bore_radii = candidate.get("bore_radii", [])
    if not bore_radii:
        return 0.0
    bell_radius = bore_radii[-1]
    mouth_radius = bore_radii[0]
    ratio = bell_radius / max(mouth_radius, 1.0)
    if ratio < 1.0:
        return 1.0 - ratio
    return max(0.0, min(1.0, (ratio - 2.0) * 0.5))


def _cost_inharmonicity(candidate: dict) -> float:
    try:
        from backend.timbre_objectives import compute_inharmonicity
        bore_length = candidate.get("bore_length", 600.0)
        bore_radii = candidate.get("bore_radii", [])
        if not bore_radii or bore_length <= 0:
            return 0.0
        return compute_inharmonicity(bore_radii, bore_length)
    except (ImportError, Exception):
        return 0.0


CostFn = Callable[[dict], float]

COST_REGISTRY: dict[str, tuple[CostFn, bool]] = {
    "intonation": (_cost_intonation, False),
    "smoothness": (_cost_smoothness, False),
    "consistency": (_cost_consistency, False),
    "timbre_proxy": (_cost_timbre_proxy, False),
    "magnitude_error": (_cost_magnitude_error, False),
    "evenness": (_cost_evenness, False),
    "projection": (_cost_projection, False),
    "inharmonicity": (_cost_inharmonicity, False),
}


# ---------------------------------------------------------------------------
# Mode selector
# ---------------------------------------------------------------------------


def select_pipeline(goal: str, input_type: str, **overrides: Any) -> PipelineConfig:
    config: PipelineConfig

    if goal == "copy_sound" and input_type == "sound_file":
        config = PipelineConfig(
            goal="copy_sound",
            input_type="sound_file",
            run_tier1=True,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["magnitude_error"],
        )
    elif goal == "new_instrument" and input_type == "query":
        config = PipelineConfig(
            goal="new_instrument",
            input_type="query",
            run_tier1=False,
            run_tier2=True,
            run_tier3=True,
            tier2_costs=["intonation"],
            tier3_costs=["smoothness", "consistency"],
        )
    elif goal == "explore" and input_type == "query":
        config = PipelineConfig(
            goal="explore",
            input_type="query",
            run_tier2=True,
            tier2_costs=["intonation", "smoothness"],
            tier2_optimizer="nsga2",
        )
    elif goal == "precision" and input_type == "preset":
        config = PipelineConfig(
            goal="precision",
            input_type="preset",
            solver="openwind",
            run_tier2=True,
            run_tier3=True,
            tier3_costs=["evenness", "projection"],
        )
    else:
        config = PipelineConfig(goal=goal, input_type=input_type)

    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config


# ---------------------------------------------------------------------------
# DesignPipeline
# ---------------------------------------------------------------------------


class DesignPipeline:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    @classmethod
    def copy_sound(cls, filepath: str, **overrides: Any) -> dict:
        config = select_pipeline("copy_sound", "sound_file", **overrides)
        return cls(config).run(filepath)

    @classmethod
    def new_instrument(cls, query: str, **overrides: Any) -> dict:
        config = select_pipeline("new_instrument", "query", **overrides)
        return cls(config).run(query)

    @classmethod
    def explore(cls, query_or_lookup: str, **overrides: Any) -> dict:
        config = select_pipeline("explore", "query", **overrides)
        return cls(config).run(query_or_lookup)

    def run(self, input_data: str) -> dict:
        t_start = time.time()
        cfg = self.config
        errors: list[str] = []
        tier1: dict[str, Any] | None = None
        tier2: dict[str, Any] | None = None
        tier3: dict[str, Any] | None = None
        final_geometry: dict[str, Any] | None = None

        try:
            if cfg.run_tier1:
                t1 = time.time()
                if cfg.input_type == "sound_file":
                    tier1 = analyze_wav(input_data)
                else:
                    tier1 = {}
            else:
                tier1 = {}

            if cfg.run_tier2:
                t2 = time.time()
                agent = get_agent()

                if cfg.goal == "copy_sound" and cfg.input_type == "sound_file":
                    fundamental = tier1.get("fundamental_hz", 0.0) if tier1 else 0.0
                    tier2_raw = agent.design_from_sound(
                        fundamental=fundamental,
                        hole_count=cfg.hole_count,
                        n_candidates=cfg.n_candidates,
                    )
                else:
                    tier2_raw = agent.design(
                        query=input_data,
                        hole_count=cfg.hole_count,
                        n_candidates=cfg.n_candidates,
                    )

                tier2 = _result_to_dict(tier2_raw) if tier2_raw is not None else {}
                tier2["_time_s"] = time.time() - t2
            else:
                tier2 = {}

            if cfg.run_tier3 and tier2:
                t3 = time.time()
                tier3_candidates = tier2.get("candidates", tier2.get("designs", []))
                if tier3_candidates:
                    best = tier3_candidates[0] if isinstance(tier3_candidates[0], dict) else tier3_candidates[0]

                    if "magnitude_error" in cfg.tier3_costs and tier1:
                        tier3 = match_timbre(
                            best,
                            tier1,
                            pop_size=cfg.pop_size,
                            n_gen=cfg.n_gen,
                        )
                    else:
                        tier3 = self._run_geometric_timbre(best)

                    tier3["_time_s"] = time.time() - t3

                    bore_radii_opt = tier3.get("bore_radii_optimized", tier3.get("bore_radii", []))
                    if bore_radii_opt:
                        final_geometry = {
                            "bore_length": best.get("bore_length", best.get("bore_length_mm", 600.0)),
                            "hole_positions": best.get("hole_positions", best.get("hole_positions_mm", [])),
                            "hole_diameters": best.get("hole_diameters", best.get("hole_diameters_mm", [])),
                            "hole_lengths": best.get("hole_lengths", best.get("hole_lengths_mm", [])),
                            "closed_top": best.get("closed_top", False),
                            "bore_radii": bore_radii_opt,
                        }
                    else:
                        final_geometry = _extract_geometry(best)
                else:
                    tier3 = {}
                    candidate_list = tier2.get("candidates", tier2.get("designs", []))
                    if candidate_list:
                        final_geometry = _extract_geometry(candidate_list[0] if isinstance(candidate_list[0], dict) else candidate_list[0])
                    else:
                        final_geometry = tier2.get("geometry", None)
            else:
                if tier3 is None:
                    tier3 = {}
                if cfg.run_tier2 and tier2:
                    candidate_list = tier2.get("candidates", tier2.get("designs", []))
                    if candidate_list:
                        best = candidate_list[0] if isinstance(candidate_list[0], dict) else candidate_list[0]
                        final_geometry = _extract_geometry(best)
                    else:
                        final_geometry = tier2.get("geometry", None)

        except Exception as exc:
            errors.append(str(exc))

        total_time = time.time() - t_start

        t1_time = 0.0
        t2_time = 0.0
        t3_time = 0.0
        if tier1 is not None:
            t1_time = tier1.get("_time_s", 0.0)
        if tier2 is not None:
            t2_time = tier2.get("_time_s", 0.0)
        if tier3 is not None:
            t3_time = tier3.get("_time_s", 0.0)

        stl_path_val = None
        stl_error_val = None
        if final_geometry is not None:
            try:
                from backend.stl_export import export_optimizer_result
                output_dir_val = getattr(cfg, 'output_dir', None) or "output"
                stl_input = {
                    "bore_length_mm": final_geometry.get("bore_length", 600.0),
                    "bore_radii": final_geometry.get("bore_radii", []),
                    "hole_positions": final_geometry.get("hole_positions", []),
                    "hole_diameters": final_geometry.get("hole_diameters", []),
                }
                stl_path_val = export_optimizer_result(
                    stl_input,
                    output_path=os.path.join(output_dir_val, "instrument.stl"),
                )
            except ImportError:
                pass
            except Exception as e:
                stl_error_val = str(e)

        return {
            "config": asdict(cfg),
            "success": len(errors) == 0,
            "tier1": tier1,
            "tier2": tier2,
            "tier3": tier3,
            "final_geometry": final_geometry,
            "stl_path": stl_path_val,
            "stl_error": stl_error_val,
            "errors": errors,
            "timing_s": {
                "tier1": t1_time,
                "tier2": t2_time,
                "tier3": t3_time,
            },
            "total_time_s": total_time,
        }

    def _run_geometric_timbre(self, candidate: dict) -> dict:
        bore_length = candidate.get("bore_length", candidate.get("bore_length_mm", 600.0))
        hole_positions = candidate.get("hole_positions", candidate.get("hole_positions_mm", []))
        hole_diameters = candidate.get("hole_diameters", candidate.get("hole_diameters_mm", []))
        hole_lengths = candidate.get("hole_lengths", candidate.get("hole_lengths_mm", []))
        closed_top = candidate.get("closed_top", False)

        n_cp = 6
        r_min = 3.0
        r_max = 15.0

        raw_radii = candidate.get("bore_radii", candidate.get("bore_radii_mm", np.linspace(7.0, 9.0, n_cp)))
        initial_radii = np.array(raw_radii, dtype=float)
        if len(initial_radii) != n_cp:
            initial_radii = np.linspace(7.0, 9.0, n_cp)

        cost_fns: list[CostFn] = []
        for name in self.config.tier3_costs:
            entry = COST_REGISTRY.get(name)
            if entry is not None:
                fn, _ = entry
                cost_fns.append(fn)

        def _objective(radii: np.ndarray) -> float:
            modified = dict(candidate)
            modified["bore_radii"] = radii.tolist()
            total = 0.0
            for fn in cost_fns:
                total += fn(modified)
            return total

        res = minimize(
            _objective,
            initial_radii,
            method="L-BFGS-B",
            bounds=[(r_min, r_max)] * n_cp,
            options={"maxiter": self.config.maxiter, "ftol": 1e-8},
        )

        radii_opt = np.clip(res.x, r_min, r_max)
        cost_initial = float(_objective(initial_radii))
        cost_optimized = float(_objective(radii_opt))

        return {
            "bore_radii_initial": initial_radii.tolist(),
            "bore_radii_optimized": radii_opt.tolist(),
            "cost_initial": cost_initial,
            "cost_optimized": cost_optimized,
            "optimizer_success": bool(res.success),
        }


def _extract_geometry(data: dict) -> dict:
    return {
        "bore_length": data.get("bore_length", data.get("bore_length_mm", 600.0)),
        "hole_positions": data.get("hole_positions", data.get("hole_positions_mm", [])),
        "hole_diameters": data.get("hole_diameters", data.get("hole_diameters_mm", [])),
        "hole_lengths": data.get("hole_lengths", data.get("hole_lengths_mm", [])),
        "closed_top": data.get("closed_top", False),
        "bore_radii": data.get("bore_radii", data.get("bore_radii_mm", [])),
    }


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def design(**kwargs: Any) -> dict:
    goal = kwargs.pop("goal", "new_instrument")
    input_type = kwargs.pop("input_type", "query")

    if input_type == "sound_file":
        input_data = kwargs.pop("filepath", "")
    elif input_type == "preset":
        input_data = kwargs.pop("preset", kwargs.pop("input_data", ""))
    else:
        input_data = kwargs.pop("query", kwargs.pop("input_data", ""))

    config = select_pipeline(goal, input_type, **kwargs)
    pipeline = DesignPipeline(config)
    return pipeline.run(input_data)
