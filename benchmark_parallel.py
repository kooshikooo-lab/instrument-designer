"""
Benchmark: StarmapParallelization (current) vs ProcessPoolExecutor (alternative).

ProcessPoolExecutor may perform better on Windows because:
- Uses `concurrent.futures` which has a cleaner pickling path
- Can use `initializer` for shared state setup
- Better cancellation/timeout support

Run: python benchmark_parallel.py
"""
import os
import time
import numpy as np
from multiprocessing import cpu_count


# ── Shared evaluation function (must be at module level for pickling) ────

def _evaluate_single(args):
    """Evaluate one bore profile. Designed for ProcessPoolExecutor."""
    bore_radii, target_freqs, bore_length, freq_range, n_freqs, temperature = args
    # Import inside worker to avoid issues with spawn
    import sys, os, tempfile, hashlib
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from backend.bore_optimizer import _compute_impedance_from_bore, _match_peaks_to_targets
    
    n_cp = len(bore_radii)
    positions = np.linspace(0, bore_length, n_cp)
    bore = list(zip(positions.tolist(), [float(r) for r in bore_radii]))
    
    result = _compute_impedance_from_bore(bore, freq_range=freq_range, n_freqs=n_freqs, temperature=temperature)
    peak_freqs = result["peak_frequencies"]
    
    if len(peak_freqs) < 2:
        return 1e10
    
    matched = _match_peaks_to_targets(peak_freqs, target_freqs)
    raw_cents = np.array([m[3] for m in matched])
    global_offset = np.median(raw_cents)
    corrected = np.abs(raw_cents - global_offset)
    return float(np.sqrt(np.mean(corrected ** 2)))


def benchmark_serial(pop_size, n_gen, target_freqs, bore_length, freq_range, n_freqs, temperature, seed=42):
    """Run optimization serially."""
    np.random.seed(seed)
    n_cp = 12
    xl = np.full(n_cp, 0.003)
    xu = np.full(n_cp, 0.025)
    
    # Generate population
    from backend.bore_optimizer import _pava_isotonic
    population = []
    for _ in range(pop_size):
        raw = np.random.uniform(xl, xu, n_cp)
        population.append(_pava_isotonic(raw))
    
    best_fitness = 1e10
    t0 = time.time()
    
    for gen in range(n_gen):
        fitnesses = []
        for ind in population:
            f = _evaluate_single((ind, target_freqs, bore_length, freq_range, n_freqs, temperature))
            fitnesses.append(f)
        
        fitnesses = np.array(fitnesses)
        gen_best = fitnesses.min()
        if gen_best < best_fitness:
            best_fitness = gen_best
        
        # Simple ES-style selection + mutation
        sorted_idx = np.argsort(fitnesses)[:pop_size // 2]
        parents = [population[i] for i in sorted_idx]
        
        new_pop = list(parents)
        while len(new_pop) < pop_size:
            p1, p2 = np.random.choice(len(parents), 2, replace=False)
            # Crossover
            alpha = np.random.uniform(0, 1, n_cp)
            child = alpha * parents[p1] + (1 - alpha) * parents[p2]
            # Mutation
            child += np.random.normal(0, 0.001, n_cp)
            child = np.clip(child, xl, xu)
            child = _pava_isotonic(child)
            new_pop.append(child)
        
        population = new_pop[:pop_size]
        print(f"  Gen {gen+1}/{n_gen}: best={best_fitness:.4f} cents")
    
    elapsed = time.time() - t0
    return best_fitness, elapsed


def benchmark_processpoolexecutor(pop_size, n_gen, target_freqs, bore_length, freq_range, n_freqs, temperature, n_workers, seed=42):
    """Run optimization with ProcessPoolExecutor."""
    from concurrent.futures import ProcessPoolExecutor
    
    np.random.seed(seed)
    n_cp = 12
    xl = np.full(n_cp, 0.003)
    xu = np.full(n_cp, 0.025)
    
    from backend.bore_optimizer import _pava_isotonic
    population = []
    for _ in range(pop_size):
        raw = np.random.uniform(xl, xu, n_cp)
        population.append(_pava_isotonic(raw))
    
    best_fitness = 1e10
    t0 = time.time()
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        for gen in range(n_gen):
            # Submit all evaluations
            futures = [
                executor.submit(_evaluate_single, (ind, target_freqs, bore_length, freq_range, n_freqs, temperature))
                for ind in population
            ]
            fitnesses = np.array([f.result() for f in futures])
            
            gen_best = fitnesses.min()
            if gen_best < best_fitness:
                best_fitness = gen_best
            
            sorted_idx = np.argsort(fitnesses)[:pop_size // 2]
            parents = [population[i] for i in sorted_idx]
            
            new_pop = list(parents)
            while len(new_pop) < pop_size:
                p1, p2 = np.random.choice(len(parents), 2, replace=False)
                alpha = np.random.uniform(0, 1, n_cp)
                child = alpha * parents[p1] + (1 - alpha) * parents[p2]
                child += np.random.normal(0, 0.001, n_cp)
                child = np.clip(child, xl, xu)
                child = _pava_isotonic(child)
                new_pop.append(child)
            
            population = new_pop[:pop_size]
            print(f"  Gen {gen+1}/{n_gen}: best={best_fitness:.4f} cents")
    
    elapsed = time.time() - t0
    return best_fitness, elapsed


if __name__ == "__main__":
    from backend.target_frequencies import get_targets
    
    # Clarinet Bb: odd harmonics
    target_freqs = get_targets("clarinet_Bb", fundamental=233.1, n_notes=6)
    print(f"Targets: {[f'{f:.1f}' for f in target_freqs]}")
    
    bore_length = 331.3 / (4 * 233.1)  # quarter-wave for Bb3
    freq_range = (50, 3000)
    n_freqs = 5000
    temperature = 20.0
    n_workers = min(cpu_count() or 4, 8)
    
    pop_size = 15
    n_gen = 5
    
    print(f"\nConfig: pop={pop_size}, gen={n_gen}, workers={n_workers}")
    print(f"Bore length: {bore_length*1000:.0f}mm")
    
    # Serial benchmark
    print("\n=== SERIAL ===")
    serial_fitness, serial_time = benchmark_serial(pop_size, n_gen, target_freqs, bore_length, freq_range, n_freqs, temperature)
    print(f"Result: {serial_fitness:.4f} cents in {serial_time:.1f}s")
    
    # ProcessPoolExecutor benchmark
    print(f"\n=== ProcessPoolExecutor ({n_workers} workers) ===")
    par_fitness, par_time = benchmark_processpoolexecutor(pop_size, n_gen, target_freqs, bore_length, freq_range, n_freqs, temperature, n_workers)
    print(f"Result: {par_fitness:.4f} cents in {par_time:.1f}s")
    
    speedup = serial_time / par_time if par_time > 0 else 0
    print(f"\n=== SUMMARY ===")
    print(f"Serial:    {serial_time:.1f}s ({serial_fitness:.4f} cents)")
    print(f"Parallel:  {par_time:.1f}s ({par_fitness:.4f} cents)")
    print(f"Speedup:   {speedup:.2f}x")
