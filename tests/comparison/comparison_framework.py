"""
Comparison test framework for algorithm comparison testing.
"""
import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Optional, Any
from abc import ABC, abstractmethod
from pathlib import Path
import json


@dataclass
class AlgorithmResult:
    """Result of running an algorithm."""
    name: str
    success: bool
    runtime_seconds: float
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Result of comparing multiple algorithms."""
    test_name: str
    algorithms: Dict[str, AlgorithmResult] = field(default_factory=dict)
    best_by_metric: Dict[str, str] = field(default_factory=dict)
    summary: str = ""


class AlgorithmComparator:
    """Framework for comparing multiple algorithms on the same test cases."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.algorithms: Dict[str, Callable] = {}
        self.test_cases: List[Dict[str, Any]] = []
        self.results: List[ComparisonResult] = []
    
    def register_algorithm(self, name: str, func: Callable):
        """Register an algorithm for comparison."""
        self.algorithms[name] = func
    
    def add_test_case(self, name: str, inputs: Dict[str, Any], expected: Optional[Dict[str, float]] = None):
        """Add a test case for comparison."""
        self.test_cases.append({
            "name": name,
            "inputs": inputs,
            "expected": expected
        })
    
    def run_comparison(self, iterations: int = 3) -> List[ComparisonResult]:
        """Run all algorithms on all test cases."""
        results = []
        
        for test_case in self.test_cases:
            case_results = {}
            
            for alg_name, alg_func in self.algorithms.items():
                runtimes = []
                metrics_list = []
                success = True
                error = None
                
                for _ in range(iterations):
                    try:
                        start = time.perf_counter()
                        result = self._run_algorithm(alg_func, self.test_cases[0]["inputs"])
                        elapsed = time.perf_counter() - start
                        
                        runtimes.append(elapsed)
                        if isinstance(result, dict):
                            metrics_list.append(result)
                        else:
                            metrics_list.append({"output": result})
                    except Exception as e:
                        success = False
                        error = str(e)
                        break
                
                # Aggregate metrics
                metrics = {}
                if metrics_list:
                    all_keys = set().union(*[m.keys() for m in metrics_list])
                    for key in metrics_list[0].keys():
                        values = [m.get(key, 0) for m in metrics_list if key in m]
                        if values:
                            metrics[f"{key}_mean"] = statistics.mean(values)
                            metrics[f"{key}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0
                            metrics[f"{key}_min"] = min(values)
                            metrics[f"{key}_max"] = max(values)
                
                case_results[alg_name] = AlgorithmResult(
                    name=alg_name,
                    success=success,
                    runtime_seconds=statistics.mean(runtimes) if runtimes else 0,
                    metrics=metrics,
                    error=error
                )
            
            # Determine best by key metrics
            best_by_metric = {}
            for metric in ["runtime_seconds", "accuracy", "mean_error_cents"]:
                valid = [(name, r) for name, r in case_results.items() if r.success and metric in r.metrics]
                if valid:
                    best_by_metric[metric] = min(valid, key=lambda x: r.metrics.get(metric, float('inf')))[0]
            
            result = ComparisonResult(
                test_name=self.test_name,
                algorithms=case_results,
                best_by_metric=best_by_metric
            )
            self.results.append(result)
        
        return self.results
    
    def _run_algorithm(self, func: Callable, inputs: Dict[str, Any]) -> Any:
        """Run algorithm with inputs."""
        return func(**inputs)
    
    def generate_report(self) -> str:
        """Generate a comparison report."""
        lines = [f"Comparison Report: {self.test_name}", "=" * 50, ""]
        
        for result in self.results:
            lines.append(f"Test Case: {result.test_name}")
            lines.append("-" * 30)
            
            # Summary table
            lines.append(f"{'Algorithm':<20} {'Success':<8} {'Time (s)':>10} {'Metrics':<30}")
            lines.append("-" * 70)
            
            for name, result in result.algorithms.items():
                status = "✓" if result.success else "✗"
                metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in result.metrics.items())
                lines.append(f"{name:<20} {status:<8} {result.runtime_seconds:>10.4f} {metrics_str:<30}")
            
            lines.append("")
            lines.append("Best by metric:")
            for metric, best in result.best_by_metric.items():
                lines.append(f"  {metric}: {best}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_results(self, filepath: str):
        """Save results to JSON."""
        data = {
            "test_name": self.test_name,
            "results": [
                {
                    "test_name": r.test_name,
                    "algorithms": {
                        name: {
                            "name": r.name,
                            "success": r.success,
                            "runtime_seconds": r.runtime_seconds,
                            "metrics": r.metrics,
                            "error": r.error
                        } for name, r in result.algorithms.items()
                    },
                    "best_by_metric": result.best_by_metric
                }
                for result in self.results
            ]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


class AlgorithmTestCase:
    """Base class for algorithm comparison test cases."""
    
    def __init__(self, name: str):
        self.name = name
        self.comparator = AlgorithmComparator(name)
    
    def add_algorithm(self, name: str, func: Callable):
        """Add an algorithm to compare."""
        self.comparator.register_algorithm(name, func)
    
    def add_test_case(self, name: str, inputs: Dict[str, Any], expected: Optional[Dict[str, float]] = None):
        """Add a test case."""
        self.comparator.add_test_case(name, inputs, expected)
    
    def run(self, iterations: int = 3) -> List[ComparisonResult]:
        """Run the comparison."""
        return self.comparator.run_comparison(iterations)
    
    def assert_best(self, metric: str, expected_best: str):
        """Assert which algorithm is best for a metric."""
        results = self.comparator.results
        for result in results:
            best = result.best_by_metric.get(metric)
            assert best == expected_best, f"Expected {expected_best} to be best for {metric}, got {best}"


# Example usage and predefined comparisons
def create_optimizer_comparison():
    """Create a standard optimizer comparison suite."""
    comparator = AlgorithmComparator("Optimizer Comparison")
    
    # Register algorithms (these would be imported from actual modules)
    # comparator.register_algorithm("DE", run_de_optimizer)
    # comparator.register_algorithm("L-BFGS-B", run_lbfgsb_optimizer)
    # comparator.register_algorithm("TwoPhase", run_two_phase_optimizer)
    # comparator.register_algorithm("JAX", run_jax_optimizer)
    
    return comparator


def benchmark_tmm_solvers():
    """Benchmark different TMM solver implementations."""
    comparator = AlgorithmComparator("TMM Solver Comparison")
    
    # comparator.register_algorithm("Python TMM", run_python_tmm)
    # comparator.register_algorithm("JAX TMM", run_jax_tmm)
    # comparator.register_algorithm("OpenWInD", run_openwind)
    
    return comparator


# Example test case
class TestAlgorithmComparison:
    """Example test showing how to use the comparison framework."""
    
    def test_optimizer_comparison(self):
        """Compare optimizer algorithms on standard instruments."""
        # This would be implemented with actual algorithm functions
        pass
    
    def test_tmm_solver_comparison(self):
        """Compare TMM solver implementations."""
        pass


if __name__ == "__main__":
    # Demo usage
    comp = AlgorithmComparator("Demo Comparison")
    
    def algo_a(x):
        time.sleep(0.1)
        return {"output": x * 2, "accuracy": 0.99}
    
    def algo_b(x):
        time.sleep(0.05)
        return {"output": x * 2, "accuracy": 0.95}
    
    comp.register_algorithm("Algorithm A", algo_a)
    comp.register_algorithm("Algorithm B", algo_b)
    comp.add_test_case("test_1", {"x": 5})
    comp.add_test_case("test_2", {"x": 10})
    
    results = comp.run_comparison(iterations=3)
    print(comp.generate_report())
    comp.save_results("comparison_results.json")