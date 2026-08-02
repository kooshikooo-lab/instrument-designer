"""
Benchmark test template for TMM solver accuracy and performance.
"""
import pytest
import time
import statistics
from pathlib import Path
from typing import Dict, List, Any


class BenchmarkResult:
    """Container for benchmark results."""
    def __init__(self, name: str):
        self.name = name
        self.iterations: List[Dict[str, float]] = []
        self.success = True
        self.error: str = ""
    
    def add_iteration(self, metrics: Dict[str, float]):
        self.iterations.append(metrics)
    
    def get_summary(self) -> Dict[str, float]:
        if not self.iterations:
            return {}
        keys = self.iterations[0].keys()
        return {
            f"{key}_mean": statistics.mean([it[key] for it in self.iterations])
            for key in self.iterations[0].keys()
        }


class BenchmarkTestCase:
    """Base class for benchmark test cases."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.results = []
    
    def run_iteration(self, func: callable, *args, **kwargs) -> Dict[str, float]:
        """Run a single benchmark iteration."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        
        metrics = {"runtime_seconds": time.perf_counter() - start}
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, (int, float)):
                    metrics[k] = v
        metrics["runtime_seconds"] = time.perf_counter() - start
        return metrics
    
    def run_benchmark(self, func: callable, iterations: int = 5, *args, **kwargs) -> Dict[str, float]:
        """Run benchmark multiple times and return statistics."""
        metrics_list = []
        for _ in range(iterations):
            metrics = self.run_iteration(*args, **kwargs)
            metrics_list.append(metrics)
        
        # Compute statistics
        stats = {}
        keys = metrics_list[0].keys()
        for key in keys:
            values = [m[key] for m in metrics_list]
            metrics[key] = {
                "mean": statistics.mean(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values)
            }
        return metrics


@pytest.fixture
def benchmark_timer():
    """Fixture for timing operations."""
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start
    return Timer()


@pytest.fixture
def benchmark_result():
    """Fixture for collecting benchmark results."""
    results = []
    yield results
    # Could save to file here


class BenchmarkRunner:
    """Run a suite of benchmarks and generate report."""
    
    def __init__(self, name: str):
        self.name = name
        self.results: List[Dict[str, Any]] = []
    
    def add_benchmark(self, name: str, func: callable, iterations: int = 5, *args, **kwargs):
        """Add a benchmark to run."""
        self.results.append({
            "name": name,
            "func": func,
            "iterations": iterations,
            "args": args,
            "kwargs": kwargs
        })
    
    def run_all(self) -> List[Dict[str, Any]]:
        """Run all benchmarks and return results."""
        results = []
        for bench in self.results:
            metrics_list = []
            for _ in range(bench["iterations"]):
                start = time.perf_counter()
                result = bench["func"](*bench["args"], **bench["kwargs"])
                elapsed = time.perf_counter() - start
                
                metrics = {"runtime_seconds": elapsed}
                if isinstance(result, dict):
                    for k, v in result.items():
                        if isinstance(v, (int, float)):
                            metrics[k] = v
                metrics["runtime_seconds"] = elapsed
                metrics_list.append(metrics)
            
            # Aggregate
            stats = {}
            keys = metrics_list[0].keys()
            for key in keys:
                values = [m[key] for m in metrics_list]
                stats[key] = {
                    "mean": statistics.mean(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values)
                }
            
            self.results.append({
                "name": bench["name"],
                "stats": stats,
                "raw": metrics_list
            })
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a text report."""
        lines = [f"Benchmark Report", "=" * 50, ""]
        for result in self.results:
            lines.append(f"\n{result['name']}")
            lines.append("-" * 30)
            for key, stats in result["stats"].items():
                lines.append(f"  {key}: mean={stats['mean']:.4f}, stdev={stats['stdev']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")
        return "\n".join(lines)


# Pytest fixtures
@pytest.fixture
def benchmark_runner():
    """Provides a benchmark runner instance."""
    return BenchmarkRunner("Test Suite")


# Example test using the benchmark framework
class TestBenchmarkExample:
    """Example benchmark test."""
    
    def test_tmm_resonance_calculation(self):
        """Benchmark TMM resonance calculation."""
        import time
        import statistics
        from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
        
        def run_tmm():
            inst = tmm_instrument_from_radii(
                radii_mm=[10.0] * 20,
                bore_length_mm=300.0,
                hole_positions_mm=[],
                hole_diameters_mm=[],
                hole_lengths_mm=[],
                outer_diameter_mm=22.0,
                closed_top=False,
                cone_step=0.5
            )
            return inst.find_resonance(300.0, [], n_register=2)
        
        # Simple direct benchmark without framework
        iterations = 10
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            run_tmm()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        mean_time = statistics.mean(times)
        print(f"TMM Resonance Find: mean={mean_time:.4f}s, min={min(times):.4f}s, max={max(times):.4f}s")
        
        # Assert performance requirements
        assert statistics.mean(times) < 0.1, "TMM resonance finding too slow"
        
        print(f"TMM Resonance Find: mean={statistics.mean(times):.4f}s, min={min(times):.4f}s, max={max(times):.4f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])