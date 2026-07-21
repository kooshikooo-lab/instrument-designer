"""
Staged bore optimizer — Noreland approach.

Optimizes in stages:
  Stage 1: Fundamental only (fast convergence to rough shape)
  Stage 2: Add next harmonic(s) (refine with more targets)
  Stage 3: Full target set (final refinement)

Each stage uses the previous stage's best design as initial guess.
This dramatically reduces total evaluations compared to full optimization from scratch.

Run: python -m backend.staged_optimizer
"""
import numpy as np
from backend.bore_optimizer import BoreOptimizer, _compute_impedance_from_bore, _match_peaks_to_targets


def staged_optimize(
    target_frequencies,
    n_control_points=12,
    pop_size=30,
    n_generations_per_stage=15,
    temperature=20.0,
    seed=None,
    n_workers=None,
    verbose=True,
):
    """
    Run staged optimization following Noreland's 3-step strategy.
    
    Stage 1: Fundamental + 2nd harmonic (2 targets) — find rough bore shape
    Stage 2: Add harmonics up to 5 (5 targets) — refine
    Stage 3: Full target set — final accuracy
    
    Returns combined result dict with stage-by-stage history.
    """
    targets = sorted(target_frequencies)
    stages = []
    
    # Build stage target sets
    if len(targets) <= 2:
        stages = [targets]
    elif len(targets) <= 4:
        stages = [targets[:2], targets]
    else:
        # Stage 1: first 2 targets
        # Stage 2: first half
        # Stage 3: all targets
        half = len(targets) // 2
        stages = [targets[:2], targets[:half], targets]
    
    if verbose:
        print(f"Staged optimization: {len(stages)} stages")
        for i, s in enumerate(stages):
            print(f"  Stage {i+1}: {len(s)} targets — {[f'{f:.0f}' for f in s]}")
    
    best_variables = None
    stage_results = []
    total_evals = 0
    
    for stage_idx, stage_targets in enumerate(stages):
        if verbose:
            print(f"\n--- Stage {stage_idx + 1}/{len(stages)}: {len(stage_targets)} targets ---")
        
        # Adjust pop_size for early stages (smaller is fine)
        if stage_idx == 0:
            stage_pop = min(pop_size, 20)
            stage_gen = max(n_generations_per_stage, 10)
        elif stage_idx == len(stages) - 1:
            stage_pop = pop_size
            stage_gen = n_generations_per_stage * 2  # More gens for final stage
        else:
            stage_pop = min(pop_size, 30)
            stage_gen = n_generations_per_stage
        
        # Use initial sampling seeded with previous best if available
        optimizer = BoreOptimizer(
            target_frequencies=stage_targets,
            n_control_points=n_control_points,
            temperature=temperature,
            pop_size=stage_pop,
            n_generations=stage_gen,
            seed=seed + stage_idx if seed else None,
            n_workers=n_workers,
        )
        
        # If we have a previous best, seed the initial population
        if best_variables is not None:
            from backend.bore_optimizer import MonotonicSampling
            # Override the algorithm's sampling to include our best guess
            optimizer._algorithm.sampling = _SeedSampling(best_variables)
        
        result = optimizer.run(verbose=verbose)
        
        total_evals += result.get("n_evaluations", 0)
        best = result["best_candidates"][0] if result["best_candidates"] else None
        
        if best and "variables" in best:
            best_variables = np.array(best["variables"])
        
        stage_results.append({
            "stage": stage_idx + 1,
            "n_targets": len(stage_targets),
            "targets": stage_targets,
            "best_fitness": best["objectives"]["frequency_accuracy"] if best else None,
            "n_evaluations": result.get("n_evaluations", 0),
            "matched_frequencies": best.get("matched_frequencies", []) if best else [],
        })
        
        if verbose and best:
            print(f"  Stage {stage_idx+1} result: {best['objectives']['frequency_accuracy']:.4f} cents")
    
    # Final evaluation with all targets
    final_optimizer = BoreOptimizer(
        target_frequencies=targets,
        n_control_points=n_control_points,
        temperature=temperature,
        pop_size=1,
        n_generations=1,
        seed=seed,
        n_workers=1,
    )
    
    if best_variables is not None:
        final_result = final_optimizer.evaluate_single(best_variables)
    else:
        final_result = None
    
    return {
        "stages": stage_results,
        "total_evaluations": total_evals,
        "final_targets": targets,
        "final_result": final_result,
        "best_variables": best_variables.tolist() if best_variables is not None else None,
    }


class _SeedSampling:
    """Custom sampling that seeds population with a known good design."""
    
    def __init__(self, seed_variables):
        self.seed = np.array(seed_variables)
    
    def __call__(self, problem, n_samples, **kwargs):
        xl = np.asarray(problem.xl)
        xu = np.asarray(problem.xu)
        n_var = problem.n_var
        
        X = np.empty((n_samples, n_var))
        # First individual is the seed
        X[0] = np.clip(self.seed, xl, xu)
        # Rest are random + PAVA repair
        from backend.bore_optimizer import _pava_isotonic
        for i in range(1, n_samples):
            raw = np.random.uniform(xl, xu, n_var)
            X[i] = _pava_isotonic(raw)
        return X


if __name__ == "__main__":
    from backend.target_frequencies import get_targets
    
    print("=== Staged Optimizer Test ===\n")
    
    # Clarinet Bb: 6 odd harmonics
    targets = get_targets("clarinet_Bb", fundamental=233.1, n_notes=6)
    print(f"Targets: {[f'{f:.1f}' for f in targets]}")
    
    result = staged_optimize(
        target_frequencies=targets,
        n_control_points=12,
        pop_size=20,
        n_generations_per_stage=10,
        seed=42,
        verbose=True,
    )
    
    print(f"\n=== RESULTS ===")
    print(f"Total evaluations: {result['total_evaluations']}")
    if result["final_result"]:
        matched = result["final_result"]["matched_frequencies"]
        for m in matched:
            print(f"  {m['target']:.1f} Hz -> {m['actual']:.1f} Hz ({m['error_cents']:.1f} cents)")
    
    print(f"\nStage history:")
    for s in result["stages"]:
        print(f"  Stage {s['stage']}: {s['n_targets']} targets, {s['n_evaluations']} evals, {s['best_fitness']:.4f} cents")
