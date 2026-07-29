"""Pipeline configuration dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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