"""
design_desk.py — Automated instrument design agent.

Orchestrates the full design loop: optimize → analyze → iterate → store.
Follows the CrewAI multi-agent pattern from chat-logs/2026-07-18-crewai-pymoo-deep-dive.md

Agents:
- DesignAgent: sets up optimization parameters based on instrument type
- OptimizerAgent: runs the bore optimization (delegates to BoreOptimizer)
- EvaluatorAgent: analyzes results, checks quality, suggests improvements
- MemoryAgent: stores successful designs for future reference

Usage:
    from backend.design_desk import DesignDesk
    desk = DesignDesk()
    result = desk.auto_design("clarinet_Bb", max_iterations=3)
"""

import json
import os
import sys
import time
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class DesignIteration:
    iteration: int
    pop_size: int
    n_generations: int
    n_control_points: int
    frequency_accuracy: float
    scale_evenness: float
    n_evaluations: int
    suggestions: list = field(default_factory=list)
    bore_length: float = 0.0


@dataclass
class DesignDeskResult:
    instrument_type: str
    target_frequencies: list
    best_accuracy: float
    iterations: list
    total_evaluations: int
    final_bore_profile: list
    final_hole_positions: list
    final_hole_diameters: list
    final_bore_length: float
    log: list = field(default_factory=list)
    success: bool = False


# ── Instrument Presets ──────────────────────────────────────────────────

INSTRUMENT_CONFIGS = {
    "clarinet_Bb": {
        "description": "Bb Clarinet (odd harmonics, closed-open pipe)",
        "bore_length_range": (0.4, 0.7),  # meters
        "min_radius": 0.005,
        "max_radius": 0.010,
        "default_cp": 12,
        "default_pop": 30,
        "default_gen": 20,
        "pipe_type": "closed-open",
    },
    "folk_whistle": {
        "description": "D Penny Whistle (all harmonics, open-open pipe)",
        "bore_length_range": (0.15, 0.35),
        "min_radius": 0.004,
        "max_radius": 0.012,
        "default_cp": 10,
        "default_pop": 20,
        "default_gen": 15,
        "pipe_type": "open-open",
    },
    "folk_flute": {
        "description": "D Folk Flute (all harmonics, open-open pipe)",
        "bore_length_range": (0.3, 0.6),
        "min_radius": 0.006,
        "max_radius": 0.015,
        "default_cp": 12,
        "default_pop": 25,
        "default_gen": 15,
        "pipe_type": "open-open",
    },
    "recorder": {
        "description": "Soprano Recorder (all harmonics, fipple flute)",
        "bore_length_range": (0.2, 0.4),
        "min_radius": 0.005,
        "max_radius": 0.012,
        "default_cp": 10,
        "default_pop": 25,
        "default_gen": 15,
        "pipe_type": "open-open",
    },
    "reedpipe": {
        "description": "Reedpipe (odd harmonics, closed-open)",
        "bore_length_range": (0.2, 0.5),
        "min_radius": 0.004,
        "max_radius": 0.010,
        "default_cp": 10,
        "default_pop": 25,
        "default_gen": 15,
        "pipe_type": "closed-open",
    },
    "folk_shawm": {
        "description": "Folk Shawm (all harmonics, conical bore)",
        "bore_length_range": (0.2, 0.5),
        "min_radius": 0.004,
        "max_radius": 0.015,
        "default_cp": 12,
        "default_pop": 25,
        "default_gen": 15,
        "pipe_type": "open-open",
    },
    "soprano_sax": {
        "description": "Soprano Saxophone (all harmonics, conical bore, Bb)",
        "bore_length_range": (0.5, 0.8),
        "min_radius": 0.004,
        "max_radius": 0.012,
        "default_cp": 15,
        "default_pop": 30,
        "default_gen": 20,
        "pipe_type": "open-open",
    },
    "alto_sax": {
        "description": "Alto Saxophone (all harmonics, conical bore, Eb)",
        "bore_length_range": (0.9, 1.3),
        "min_radius": 0.005,
        "max_radius": 0.015,
        "default_cp": 15,
        "default_pop": 30,
        "default_gen": 20,
        "pipe_type": "open-open",
    },
    "tenor_sax": {
        "description": "Tenor Saxophone (all harmonics, conical bore, Bb)",
        "bore_length_range": (1.1, 1.5),
        "min_radius": 0.006,
        "max_radius": 0.018,
        "default_cp": 15,
        "default_pop": 30,
        "default_gen": 20,
        "pipe_type": "open-open",
    },
    "baritone_sax": {
        "description": "Baritone Saxophone (all harmonics, conical bore, Eb)",
        "bore_length_range": (1.5, 2.0),
        "min_radius": 0.008,
        "max_radius": 0.025,
        "default_cp": 18,
        "default_pop": 30,
        "default_gen": 25,
        "pipe_type": "open-open",
    },
    "trumpet_bb": {
        "description": "Bb Trumpet (all harmonics, closed-open with bell)",
        "bore_length_range": (1.0, 1.5),
        "min_radius": 0.003,
        "max_radius": 0.010,
        "default_cp": 15,
        "default_pop": 30,
        "default_gen": 20,
        "pipe_type": "closed-open",
    },
    "trombone": {
        "description": "Tenor Trombone (all harmonics, closed-open with bell)",
        "bore_length_range": (2.0, 3.0),
        "min_radius": 0.005,
        "max_radius": 0.012,
        "default_cp": 15,
        "default_pop": 30,
        "default_gen": 20,
        "pipe_type": "closed-open",
    },
    "french_horn": {
        "description": "French Horn in F (all harmonics, conical bore)",
        "bore_length_range": (3.0, 4.5),
        "min_radius": 0.004,
        "max_radius": 0.012,
        "default_cp": 18,
        "default_pop": 30,
        "default_gen": 25,
        "pipe_type": "open-open",
    },
    "tuba": {
        "description": "Tuba in Bb (all harmonics, conical bore)",
        "bore_length_range": (4.0, 6.0),
        "min_radius": 0.010,
        "max_radius": 0.030,
        "default_cp": 20,
        "default_pop": 30,
        "default_gen": 25,
        "pipe_type": "open-open",
    },
}


class DesignAgent:
    """Sets up initial optimization parameters based on instrument type."""

    def __init__(self, instrument_type: str, custom_targets: Optional[list] = None):
        self.instrument_type = instrument_type
        self.config = INSTRUMENT_CONFIGS.get(instrument_type, INSTRUMENT_CONFIGS["folk_whistle"])
        self.custom_targets = custom_targets

    def get_targets(self) -> list[float]:
        """Get target frequencies for this instrument."""
        if self.custom_targets:
            return self.custom_targets
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from backend.target_frequencies import get_targets
            instrument_type = self.instrument_type
            if instrument_type in ("clarinet_Bb", "reedpipe", "reed_drone", "chalumeau"):
                return get_targets(instrument_type, fundamental=233.1, n_notes=6)
            elif instrument_type == "folk_whistle":
                return get_targets(instrument_type, fundamental=293.7, n_notes=6)
            elif instrument_type == "folk_flute":
                return get_targets(instrument_type, fundamental=293.7, n_notes=6)
            elif instrument_type == "recorder":
                return get_targets(instrument_type, fundamental=261.6, n_notes=6)
            else:
                return get_targets(instrument_type, fundamental=261.6, n_notes=6)
        except ImportError:
            pass
        return []

    def get_initial_params(self) -> dict:
        """Get initial optimization parameters."""
        return {
            "n_control_points": self.config["default_cp"],
            "pop_size": self.config["default_pop"],
            "n_generations": self.config["default_gen"],
            "min_radius": self.config["min_radius"],
            "max_radius": self.config["max_radius"],
        }


class EvaluatorAgent:
    """Analyzes optimization results and suggests parameter changes."""

    def __init__(self):
        try:
            from backend.ai_advisor import analyze_optimization_result
            self._analyze = analyze_optimization_result
        except ImportError:
            self._analyze = None

    def evaluate(self, result: dict, targets: list[float]) -> dict:
        """Evaluate results and return analysis + suggested params for next iteration."""
        if not self._analyze:
            return {"score": 0, "grade": "N/A", "suggestions": []}

        analysis = self._analyze(result, targets)

        suggested_params = {}
        for s in analysis.suggestions:
            if s.category == "strategy" and "pop=" in s.action:
                import re
                pop_match = re.search(r'pop=(\d+)', s.action)
                gen_match = re.search(r'gen=(\d+)', s.action)
                if pop_match:
                    suggested_params["pop_size"] = int(pop_match.group(1))
                if gen_match:
                    suggested_params["n_generations"] = int(gen_match.group(1))

        return {
            "score": analysis.score,
            "grade": analysis.grade,
            "suggestions": [{"title": s.title, "action": s.action, "priority": s.priority} for s in analysis.suggestions],
            "suggested_params": suggested_params,
            "analysis": analysis.analysis,
        }


class MemoryAgent:
    """Stores successful designs for future reference."""

    def store(self, result: DesignDeskResult):
        """Store the design in the advisor memory."""
        try:
            from backend.ai_advisor import store_design
            store_design({
                "instrument_type": result.instrument_type,
                "target_frequencies": result.target_frequencies,
                "bore_profile": result.final_bore_profile,
                "n_control_points": result.iterations[-1].n_control_points if result.iterations else 0,
                "pop_size": result.iterations[-1].pop_size if result.iterations else 0,
                "n_generations": result.iterations[-1].n_generations if result.iterations else 0,
                "frequency_accuracy": result.best_accuracy,
                "scale_evenness": result.iterations[-1].scale_evenness if result.iterations else 0,
                "n_evaluations": result.total_evaluations,
                "bore_length": result.final_bore_length,
                "notes": f"Auto-designed in {len(result.iterations)} iterations",
            })
        except ImportError:
            pass


class DesignDesk:
    """Orchestrates the full instrument design loop."""

    def __init__(self, on_progress: Optional[Callable[[str], None]] = None):
        self.on_progress = on_progress or (lambda msg: None)

    def _log(self, msg: str, result: Optional[DesignDeskResult] = None):
        self.on_progress(msg)
        if result is not None:
            result.log.append(msg)

    def auto_design(self, instrument_type: str, max_iterations: int = 3,
                    target_accuracy: float = 3.0,
                    custom_targets: Optional[list] = None,
                    max_total_evals: int = 2000) -> DesignDeskResult:
        """
        Run an automated multi-iteration design loop.

        Args:
            instrument_type: Key from INSTRUMENT_CONFIGS
            max_iterations: Maximum number of optimization runs
            target_accuracy: Stop if RMS accuracy reaches this (cents)
            custom_targets: Override target frequencies
            max_total_evals: Stop if total evaluations exceed this
        """
        self._log(f"Starting automated design for {instrument_type}")
        self._log(f"Target: {target_accuracy} cents RMS, max {max_iterations} iterations")

        design_agent = DesignAgent(instrument_type, custom_targets)
        evaluator = EvaluatorAgent()
        memory = MemoryAgent()

        targets = design_agent.get_targets()
        if not targets:
            return DesignDeskResult(
                instrument_type=instrument_type,
                target_frequencies=[],
                best_accuracy=float("inf"),
                iterations=[],
                total_evaluations=0,
                final_bore_profile=[],
                final_hole_positions=[],
                final_hole_diameters=[],
                final_bore_length=0.0,
                log=["No target frequencies found"],
                success=False,
            )

        self._log(f"Target frequencies: {targets}")
        params = design_agent.get_initial_params()
        result = DesignDeskResult(
            instrument_type=instrument_type,
            target_frequencies=targets,
            best_accuracy=float("inf"),
            iterations=[],
            total_evaluations=0,
            final_bore_profile=[],
            final_hole_positions=[],
            final_hole_diameters=[],
            final_bore_length=0.0,
        )

        for iteration in range(1, max_iterations + 1):
            self._log(f"\n=== Iteration {iteration}/{max_iterations} ===", result)
            self._log(f"Params: pop={params['pop_size']}, gen={params['n_generations']}, cp={params['n_control_points']}", result)

            if result.total_evaluations >= max_total_evals:
                self._log(f"Reached max total evaluations ({max_total_evals}). Stopping.", result)
                break

            try:
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from backend.bore_optimizer import BoreOptimizer

                optimizer = BoreOptimizer(
                    target_frequencies=targets,
                    n_control_points=params["n_control_points"],
                    bore_length=None,
                    min_radius=params["min_radius"],
                    max_radius=params["max_radius"],
                    pop_size=params["pop_size"],
                    n_generations=params["n_generations"],
                )

                opt_result = optimizer.run(verbose=False)
                result.total_evaluations += opt_result.get("n_evaluations", 0)

                evaluation = evaluator.evaluate(opt_result, targets)
                accuracy = evaluation["score"]

                self._log(f"Accuracy: {evaluation['grade']} ({accuracy:.2f}/100)", result)
                self._log(f"Analysis: {evaluation['analysis']}", result)

                best_design = opt_result.get("best_candidates", [{}])[0] if opt_result.get("best_candidates") else {}
                bore = best_design.get("bore_profile", [])
                matched = best_design.get("matched_frequencies", [])

                iteration_data = DesignIteration(
                    iteration=iteration,
                    pop_size=params["pop_size"],
                    n_generations=params["n_generations"],
                    n_control_points=params["n_control_points"],
                    frequency_accuracy=opt_result.get("best_candidates", [{}])[0].get("objectives", {}).get("frequency_accuracy", 999) if opt_result.get("best_candidates") else 999,
                    scale_evenness=opt_result.get("best_candidates", [{}])[0].get("objectives", {}).get("scale_evenness", 0) if opt_result.get("best_candidates") else 0,
                    n_evaluations=opt_result.get("n_evaluations", 0),
                    suggestions=[s["title"] for s in evaluation["suggestions"]],
                    bore_length=opt_result.get("bore_length", 0),
                )
                result.iterations.append(iteration_data)

                acc = iteration_data.frequency_accuracy
                if acc < result.best_accuracy:
                    result.best_accuracy = acc
                    result.final_bore_profile = bore
                    result.final_bore_length = iteration_data.bore_length
                    self._log(f"New best: {acc:.2f} cents RMS", result)

                if acc <= target_accuracy:
                    self._log(f"Target reached! {acc:.2f} <= {target_accuracy} cents", result)
                    result.success = True
                    break

                if evaluation["suggested_params"]:
                    for k, v in evaluation["suggested_params"].items():
                        if k in params:
                            self._log(f"Adjusting {k}: {params[k]} -> {v}", result)
                            params[k] = v

            except Exception as e:
                self._log(f"Error in iteration {iteration}: {e}", result)
                break

        memory.store(result)
        self._log(f"\nDesign complete. Best accuracy: {result.best_accuracy:.2f} cents RMS", result)
        self._log(f"Total evaluations: {result.total_evaluations}", result)

        return result


def run_auto_design(instrument_type: str, max_iterations: int = 3,
                    on_progress: Optional[Callable] = None) -> dict:
    """Convenience function to run auto design and return a dict."""
    desk = DesignDesk(on_progress)
    result = desk.auto_design(instrument_type, max_iterations)
    return {
        "instrument_type": result.instrument_type,
        "target_frequencies": result.target_frequencies,
        "best_accuracy": result.best_accuracy,
        "iterations": [
            {
                "iteration": it.iteration,
                "pop_size": it.pop_size,
                "n_generations": it.n_generations,
                "n_control_points": it.n_control_points,
                "frequency_accuracy": it.frequency_accuracy,
                "n_evaluations": it.n_evaluations,
                "bore_length": it.bore_length,
                "suggestions": it.suggestions,
            }
            for it in result.iterations
        ],
        "total_evaluations": result.total_evaluations,
        "final_bore_profile": result.final_bore_profile,
        "final_bore_length": result.final_bore_length,
        "success": result.success,
        "log": result.log,
    }
