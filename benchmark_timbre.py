#!/usr/bin/env python3
"""
Comprehensive Timbre Weight Benchmark Script

Sweeps weight_timbre values across multiple instrument types using
LBFGSBoreOptimizer with Dask parallelization.

Usage:
    python benchmark_timbre.py                    # Full benchmark
    python benchmark_timbre.py --quick            # Quick test (2 weights, 1 instrument)
    python benchmark_timbre.py --no-dask          # Run locally without Dask
    python benchmark_timbre.py --weights 0 0.1    # Custom weight list
    python benchmark_timbre.py --output-dir my_results  # Custom output dir

Outputs:
    benchmark_results/benchmark_<timestamp>.csv
    benchmark_results/benchmark_<timestamp>.json  (detailed results with bore profiles)
"""

import os
import sys
import json
import csv
import time
import argparse
import traceback
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Dask configuration
DASK_SCHEDULER = "tcp://100.69.113.41:8786"


# =============================================================================
# INSTRUMENT CONFIGURATIONS
# =============================================================================

@dataclass
class InstrumentConfig:
    """Configuration for a woodwind instrument type."""
    name: str
    target_frequencies: List[float]          # Target frequencies (Hz) for standard fingerings
    bore_length: float                       # Bore length in meters
    bore_type: str                           # "cylindrical" or "conical"
    end_type: str                            # "closed-open", "open-open"
    n_holes: int                             # Number of finger holes
    bore_diameter_range: Tuple[float, float] # (min, max) bore diameter in mm
    n_control_points: int = 12               # Control points for optimizer
    has_register_key: bool = False           # Has register key (clarinet)
    closed_top: bool = True                  # Closed at mouthpiece end
    temperature: float = 20.0                # Temperature in Celsius
    
    @property
    def min_radius(self) -> float:
        return self.bore_diameter_range[0] / 2000.0  # mm -> m radius
    
    @property
    def max_radius(self) -> float:
        return self.bore_diameter_range[1] / 2000.0  # mm -> m radius


# Standard instrument configurations matching the requirements
INSTRUMENT_CONFIGS = {
    "chalumeau": InstrumentConfig(
        name="chalumeau",
        target_frequencies=[
            130.81, 146.83, 164.81, 174.61, 196.00, 220.00,  # C3 to A3 (fundamental register)
            261.63, 293.66, 329.63, 349.23, 392.00, 440.00,  # C4 to A4 (1st overblow)
        ],
        bore_length=0.660,
        bore_type="cylindrical",
        end_type="closed-open",
        n_holes=6,
        bore_diameter_range=(10.0, 16.0),  # 10-16mm typical for chalumeau
        n_control_points=10,
        has_register_key=False,
        closed_top=True,
    ),
    "clarinet": InstrumentConfig(
        name="clarinet",
        target_frequencies=[
            146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65,  # D3 to G#3 (chalumeau register)
            220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13,  # A3 to Eb4
            311.13, 329.63, 349.23, 369.99, 392.00, 415.30,  # Eb4 to Ab4 (throat)
            415.30, 440.00, 466.16, 493.88, 523.25, 554.37,  # A4 to C#5 (clarion register)
            554.37, 587.33, 622.25, 659.26, 698.46, 739.99,  # C#5 to F#5 (altissimo)
        ],
        bore_length=0.660,
        bore_type="cylindrical",
        end_type="closed-open",
        n_holes=17,
        bore_diameter_range=(13.0, 16.0),  # 13-16mm typical for Bb clarinet
        n_control_points=14,
        has_register_key=True,
        closed_top=True,
    ),
    "flute": InstrumentConfig(
        name="flute",
        target_frequencies=[
            261.63, 277.18, 293.66, 311.13, 329.63, 349.23,  # C4 to F4
            369.99, 392.00, 415.30, 440.00, 466.16, 493.88,  # F#4 to B4
            523.25, 554.37, 587.33, 622.25, 659.26, 698.46,  # C5 to F5
        ],
        bore_length=0.660,
        bore_type="cylindrical",
        end_type="open-open",
        n_holes=14,
        bore_diameter_range=(17.0, 20.0),  # 17-20mm for concert flute
        n_control_points=12,
        has_register_key=False,
        closed_top=False,
    ),
    "soprano_sax": InstrumentConfig(
        name="soprano_sax",
        target_frequencies=[
            233.08, 246.94, 261.63, 277.18, 293.66, 311.13,  # G3 to Eb4
            311.13, 329.63, 349.23, 369.99, 392.00, 415.30,  # Eb4 to Ab4
            415.30, 440.00, 466.16, 493.88, 523.25, 554.37,  # A4 to C#5
            554.37, 587.33, 622.25, 659.26, 698.46, 739.99,  # C#5 to F#5
        ],
        bore_length=0.640,
        bore_type="conical",
        end_type="closed-open",
        n_holes=20,
        bore_diameter_range=(8.0, 45.0),  # Conical: narrow at mouthpiece, wide at bell
        n_control_points=16,
        has_register_key=True,
        closed_top=True,
    ),
}


# =============================================================================
# BENCHMARK RESULT DATA CLASS
# =============================================================================

@dataclass
class BenchmarkResult:
    """Single benchmark result for one instrument/weight combination."""
    instrument: str
    weight_timbre: float
    rms_cents: float
    max_cents: float
    inharmonicity: float
    sharpness: float
    evenness: float
    projection: float
    wall_time: float
    evals: int
    bore_profile: List[Tuple[float, float]]  # List of (position_mm, radius_mm)
    success: bool = True
    error_message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['bore_profile'] = [(float(p), float(r)) for p, r in self.bore_profile]
        return d


# =============================================================================
# BENCHMARK WORKER FUNCTION (for Dask)
# =============================================================================

def run_single_benchmark(
    instrument_name: str,
    weight_timbre: float,
    config: InstrumentConfig,
    n_control_points: Optional[int] = None,
    seed: int = 42,
    maxiter_phase1: int = 200,
    maxiter_phase2: int = 300,
    n_freqs: int = 2000,  # Reduced from 5000 for speed
    freq_range: Optional[Tuple[float, float]] = None,
) -> BenchmarkResult:
    """
    Run a single benchmark for one instrument/weight combination.
    
    This function is designed to be serialized and run on Dask workers.
    """
    import sys
    # Ensure project root is in path BEFORE any backend imports
    if r"C:\instrument-designer" not in sys.path:
        sys.path.insert(0, r"C:\instrument-designer")
    
    start_time = time.time()
    
    try:
        # Use importlib to import at runtime (not deserialization time)
        import importlib
        bore_opt_module = importlib.import_module('backend.bore_optimizer_lbfgs')
        LBFGSBoreOptimizer = bore_opt_module.LBFGSBoreOptimizer
        
        # Use instrument config or override control points
        n_cp = n_control_points if n_control_points is not None else config.n_control_points
        
        # Determine frequency range
        if freq_range is None:
            min_freq = max(50, min(config.target_frequencies) * 0.25)
            max_freq = max(config.target_frequencies) * 3.5
            freq_range = (min_freq, max_freq)
        
        # Create optimizer
        opt = LBFGSBoreOptimizer(
            target_frequencies=config.target_frequencies,
            n_control_points=n_cp,
            bore_length=config.bore_length,
            min_radius=config.min_radius,
            max_radius=config.max_radius,
            temperature=config.temperature,
            seed=seed,
            weight_timbre=weight_timbre,
            weight_evenness=0.3,
            weight_projection=0.1,
            weight_smoothness=10.0,
            freq_range=freq_range,
            n_freqs=n_freqs,
        )
        
        # Run optimization (Phase 1 + Phase 2)
        result = opt.run(verbose=False, phase2=True)
        
        wall_time = time.time() - start_time
        
        # Extract metrics from optimization result
        rms_cents = result.get("rms_cents", float('inf'))
        bore_profile = result.get("bore_profile", [])
        evals = result.get("n_evaluations", 0)
        
        # Compute additional timbre metrics from final bore profile
        if bore_profile:
            from backend.timbre_objectives import (
                compute_inharmonicity,
                compute_phase_slope_sharpness,
                compute_harmonic_signature,
            )
            from backend.bore_optimizer_lbfgs import _compute_impedance
            
            # Recompute impedance on final bore
            peak_freqs, peak_mags = _compute_impedance(
                bore_profile,
                freq_range=(50, 3000),
                n_freqs=5000,
                temperature=config.temperature
            )
            
            fundamental = config.target_frequencies[0] if config.target_frequencies else 261.63
            
            # Inharmonicity
            inharmonicity = compute_inharmonicity(peak_freqs, peak_mags, fundamental)
            
            # Sharpness (even/odd ratio + spectral centroid)
            sharpness = compute_phase_slope_sharpness(peak_freqs, peak_mags, fundamental)
            
            # Evenness: std of peak magnitude differences
            matched = []
            for tf in config.target_frequencies:
                idx = np.argmin(np.abs(peak_freqs - tf))
                if idx < len(peak_mags):
                    matched.append((tf, peak_freqs[idx], peak_mags[idx]))
            
            if len(matched) > 1:
                mags = np.array([m[2] for m in matched])
                diffs = np.diff(mags)
                mean_diff = np.mean(diffs) if len(diffs) > 0 else 1e-6
                evenness = float(np.std(diffs / (abs(mean_diff) + 1e-6)))
            else:
                evenness = float('inf')
            
            # Projection: mean peak magnitude
            projection = float(-np.mean(peak_mags[:min(len(peak_mags), len(config.target_frequencies))]) / 1e6)
            
            # Max deviation cents
            cents_errors = []
            for tf, pf, _ in matched:
                err = 1200 * np.log2(pf / tf) if tf > 0 and pf > 0 else 0
                cents_errors.append(abs(err))
            max_cents = float(np.max(cents_errors)) if cents_errors else float('inf')
        else:
            inharmonicity = float('inf')
            sharpness = float('inf')
            evenness = float('inf')
            projection = float('inf')
            max_cents = float('inf')
        
        # Convert bore profile to mm
        bore_profile_mm = [(float(p) * 1000, float(r) * 1000) for p, r in bore_profile]
        
        return BenchmarkResult(
            instrument=instrument_name,
            weight_timbre=weight_timbre,
            rms_cents=rms_cents,
            max_cents=max_cents,
            inharmonicity=inharmonicity,
            sharpness=sharpness,
            evenness=evenness,
            projection=projection,
            wall_time=wall_time,
            evals=evals,
            bore_profile=bore_profile_mm,
            success=True,
            error_message="",
        )
        
    except Exception as e:
        wall_time = time.time() - start_time
        return BenchmarkResult(
            instrument=instrument_name,
            weight_timbre=weight_timbre,
            rms_cents=float('inf'),
            max_cents=float('inf'),
            inharmonicity=float('inf'),
            sharpness=float('inf'),
            evenness=float('inf'),
            projection=float('inf'),
            wall_time=wall_time,
            evals=0,
            bore_profile=[],
            success=False,
            error_message=str(e),
        )


# =============================================================================
# DASK DISTRIBUTED EXECUTION
# =============================================================================

def run_with_dask(
    tasks: List[Tuple[str, float, InstrumentConfig, Dict]],
    scheduler_address: str = DASK_SCHEDULER,
) -> List[BenchmarkResult]:
    """
    Run benchmark tasks using Dask distributed.
    
    Args:
        tasks: List of (instrument_name, weight_timbre, config, kwargs) tuples
        scheduler_address: Dask scheduler address
        
    Returns:
        List of BenchmarkResult objects
    """
    try:
        from dask.distributed import Client, as_completed
    except ImportError:
        print("Dask not available, falling back to local execution")
        return run_locally(tasks)
    
    print(f"Connecting to Dask scheduler at {scheduler_address}...")
    client = Client(scheduler_address, timeout="30s", connection_limit=512)
    
    try:
        # Submit all tasks
        futures = []
        for instrument_name, weight_timbre, config, kwargs in tasks:
            future = client.submit(
                run_single_benchmark,
                instrument_name,
                weight_timbre,
                config,
                **kwargs
            )
            futures.append(future)
        
        print(f"Submitted {len(futures)} tasks to Dask cluster")
        print(f"Dashboard: {client.dashboard_link}")
        
        # Collect results as they complete
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                status = "OK" if result.success else f"FAILED: {result.error_message}"
                print(f"  [{result.instrument}, w={result.weight_timbre:.3f}] {status} "
                      f"({result.wall_time:.1f}s, {result.evals} evals)")
            except Exception as e:
                print(f"  Task failed with exception: {e}")
                traceback.print_exc()
        
        return results
        
    finally:
        client.close()


def run_locally(tasks: List[Tuple[str, float, InstrumentConfig, Dict]]) -> List[BenchmarkResult]:
    """Run benchmark tasks locally without Dask."""
    print("Running locally (no Dask)...")
    results = []
    for i, (instrument_name, weight_timbre, config, kwargs) in enumerate(tasks):
        print(f"  [{i+1}/{len(tasks)}] {instrument_name}, weight_timbre={weight_timbre:.3f}...", end=" ", flush=True)
        result = run_single_benchmark(instrument_name, weight_timbre, config, **kwargs)
        results.append(result)
        status = "OK" if result.success else f"FAILED: {result.error_message}"
        print(f"{status} ({result.wall_time:.1f}s, {result.evals} evals)")
    return results


# =============================================================================
# OUTPUT HANDLING
# =============================================================================

def save_results(
    results: List[BenchmarkResult],
    output_dir: str,
    timestamp: str,
) -> Tuple[str, str]:
    """
    Save benchmark results to CSV and JSON.
    
    Returns:
        Tuple of (csv_path, json_path)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # CSV: one row per result with key metrics
    csv_path = os.path.join(output_dir, f"benchmark_{timestamp}.csv")
    rows = []
    for r in results:
        bore_str = json.dumps([list(p) for p in r.bore_profile]) if r.bore_profile else "[]"
        rows.append({
            "instrument": r.instrument,
            "weight_timbre": r.weight_timbre,
            "rms_cents": r.rms_cents,
            "max_cents": r.max_cents,
            "inharmonicity": r.inharmonicity,
            "sharpness": r.sharpness,
            "evenness": r.evenness,
            "projection": r.projection,
            "wall_time": r.wall_time,
            "evals": r.evals,
            "bore_profile": bore_str,
            "success": r.success,
            "error_message": r.error_message,
            "timestamp": r.timestamp,
        })
    
    fieldnames = list(rows[0].keys()) if rows else [
        "instrument", "weight_timbre", "rms_cents", "max_cents", "inharmonicity",
        "sharpness", "evenness", "projection", "wall_time", "evals",
        "bore_profile", "success", "error_message", "timestamp"
    ]
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # JSON: full detailed results including bore profiles
    json_path = os.path.join(output_dir, f"benchmark_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    
    return csv_path, json_path


def print_summary(results: List[BenchmarkResult]):
    """Print a summary table of results."""
    print("\n" + "=" * 120)
    print("BENCHMARK SUMMARY")
    print("=" * 120)
    print(f"{'Instrument':<15} {'w_timbre':>8} | {'RMS¢':>8} {'Max¢':>8} {'Inharm':>10} "
          f"{'Sharp':>10} {'Even':>10} {'Proj':>10} | {'Time':>6} {'Evals':>6} {'Status'}")
    print("-" * 120)
    
    for r in results:
        if r.success:
            print(f"{r.instrument:<15} {r.weight_timbre:>8.3f} | "
                  f"{r.rms_cents:>8.3f} {r.max_cents:>8.3f} "
                  f"{r.inharmonicity:>10.6f} {r.sharpness:>10.6f} "
                  f"{r.evenness:>10.4f} {r.projection:>10.4f} | "
                  f"{r.wall_time:>6.1f} {r.evals:>6} OK")
        else:
            print(f"{r.instrument:<15} {r.weight_timbre:>8.3f} | "
                  f"{'FAILED':>8} {'FAILED':>8} {'FAILED':>10} {'FAILED':>10} "
                  f"{'FAILED':>10} {'FAILED':>10} | "
                  f"{r.wall_time:>6.1f} {'0':>6} {r.error_message[:40]}")
    
    print("=" * 120)
    
    # Summary by instrument
    print("\nSUMMARY BY INSTRUMENT:")
    for inst_name in sorted(set(r.instrument for r in results)):
        inst_results = [r for r in results if r.instrument == inst_name and r.success]
        if inst_results:
            best = min(inst_results, key=lambda x: x.rms_cents)
            print(f"  {inst_name:15s}: best RMS={best.rms_cents:.3f}¢ at w_timbre={best.weight_timbre:.3f}")
    
    # Summary by weight_timbre
    print("\nSUMMARY BY WEIGHT_TIMBRE:")
    for w in sorted(set(r.weight_timbre for r in results)):
        w_results = [r for r in results if r.weight_timbre == w and r.success]
        if w_results:
            avg_rms = np.mean([r.rms_cents for r in w_results])
            avg_time = np.mean([r.wall_time for r in w_results])
            print(f"  weight_timbre={w:.3f}: avg RMS={avg_rms:.3f}¢, avg time={avg_time:.1f}s")


# =============================================================================
# MAIN BENCHMARK ORCHESTRATION
# =============================================================================

def create_benchmark_tasks(
    instrument_names: List[str],
    weight_timbre_values: List[float],
    instrument_configs: Dict[str, InstrumentConfig],
    n_control_points: Optional[int] = None,
    seed: int = 42,
    maxiter_phase1: int = 200,
    maxiter_phase2: int = 300,
    n_freqs: int = 2000,
) -> List[Tuple[str, float, InstrumentConfig, Dict]]:
    """Create list of benchmark tasks."""
    tasks = []
    for inst_name in instrument_names:
        config = instrument_configs[inst_name]
        for weight in weight_timbre_values:
            kwargs = {
                'n_control_points': n_control_points,
                'seed': seed,
                'maxiter_phase1': maxiter_phase1,
                'maxiter_phase2': maxiter_phase2,
                'n_freqs': n_freqs,
            }
            tasks.append((inst_name, weight, config, kwargs))
    return tasks


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive timbre weight benchmark for woodwind bore optimization",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Weight sweep
    parser.add_argument(
        '--weights',
        type=float,
        nargs='+',
        default=[0.0, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2],
        help='Weight_timbre values to sweep',
    )
    
    # Instrument selection
    parser.add_argument(
        '--instruments',
        type=str,
        nargs='+',
        default=list(INSTRUMENT_CONFIGS.keys()),
        choices=list(INSTRUMENT_CONFIGS.keys()),
        help='Instrument types to test',
    )
    
    # Execution mode
    parser.add_argument(
        '--no-dask',
        action='store_true',
        help='Run locally without Dask distributed',
    )
    parser.add_argument(
        '--scheduler',
        type=str,
        default=DASK_SCHEDULER,
        help='Dask scheduler address',
    )
    
    # Optimization parameters
    parser.add_argument(
        '--n-cp',
        type=int,
        default=None,
        help='Number of control points (overrides instrument default)',
    )
    parser.add_argument(
        '--n-freqs',
        type=int,
        default=2000,
        help='Number of frequency points for impedance computation (lower = faster)',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility',
    )
    parser.add_argument(
        '--maxiter1',
        type=int,
        default=200,
        help='Max iterations for Phase 1',
    )
    parser.add_argument(
        '--maxiter2',
        type=int,
        default=300,
        help='Max iterations for Phase 2',
    )
    
    # Output
    parser.add_argument(
        '--output-dir',
        type=str,
        default='benchmark_results',
        help='Output directory for results',
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test: 2 weights x 1 instrument',
    )
    
    args = parser.parse_args()
    
    # Quick mode overrides
    if args.quick:
        args.weights = [0.0, 0.1]
        args.instruments = ['chalumeau']
        args.maxiter1 = 10
        args.maxiter2 = 15
        print("QUICK MODE: weights=[0.0, 0.1], instruments=['chalumeau'], maxiter1=10, maxiter2=15")
    
    # Print configuration
    print("=" * 70)
    print("TIMBRE WEIGHT BENCHMARK")
    print("=" * 70)
    print(f"Instruments: {args.instruments}")
    print(f"Weight_timbre values: {args.weights}")
    print(f"Total combinations: {len(args.instruments) * len(args.weights)}")
    print(f"Dask: {'disabled' if args.no_dask else f'enabled ({args.scheduler})'}")
    print(f"Output dir: {args.output_dir}")
    print(f"Seed: {args.seed}")
    print(f"Phase 1 maxiter: {args.maxiter1}")
    print(f"Phase 2 maxiter: {args.maxiter2}")
    if args.n_cp:
        print(f"Control points: {args.n_cp} (override)")
    print("=" * 70)
    
    # Create tasks
    tasks = create_benchmark_tasks(
        instrument_names=args.instruments,
        weight_timbre_values=args.weights,
        instrument_configs=INSTRUMENT_CONFIGS,
        n_control_points=args.n_cp,
        seed=args.seed,
        maxiter_phase1=args.maxiter1,
        maxiter_phase2=args.maxiter2,
        n_freqs=args.n_freqs,
    )
    
    # Run benchmarks
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.no_dask:
        results = run_locally(tasks)
    else:
        results = run_with_dask(tasks, args.scheduler)
    
    # Save results
    csv_path, json_path = save_results(results, args.output_dir, timestamp)
    
    # Print summary
    print_summary(results)
    
    print(f"\nResults saved to:")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    
    # Return non-zero if any failures
    failures = [r for r in results if not r.success]
    if failures:
        print(f"\nWARNING: {len(failures)} task(s) failed")
        for f in failures:
            print(f"  {f.instrument}, w={f.weight_timbre:.3f}: {f.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()