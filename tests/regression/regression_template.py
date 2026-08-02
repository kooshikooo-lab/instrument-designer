"""
Regression test template for V1/V2 validation.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class RegressionTestCase:
    """A single regression test case."""
    name: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    tolerance: Dict[str, float] = None
    description: str = ""
    
    def __post_init__(self):
        if self.tolerance is None:
            self.tolerance = {}


class RegressionTestSuite:
    """A suite of regression test cases."""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.test_cases: List[RegressionTestCase] = []
    
    def add_case(self, case: RegressionTestCase):
        self.test_cases.append(case)
    
    def load_from_json(self, filepath: str):
        """Load test cases from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for case_data in data.get("test_cases", []):
            self.add_case(RegressionTestCase(**case_data))
    
    def save_to_json(self, filepath: str):
        """Save test cases to JSON file."""
        data = {
            "name": self.name,
            "version": self.version,
            "test_cases": [
                {
                    "name": tc.name,
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "tolerance": tc.tolerance,
                    "description": tc.description
                }
                for tc in self.test_cases
            ]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def run(self, test_func: callable) -> Dict[str, Any]:
        """Run all test cases against a test function."""
        results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
        
        for case in self.test_cases:
            try:
                actual = test_func(case.input_data)
                passed = self._compare_outputs(case.expected_output, case.tolerance, actual)
                
                if passed:
                    results["passed"] += 1
                    status = "PASS"
                else:
                    results["failed"] += 1
                    status = "FAIL"
                
                results["details"].append({
                    "name": case.name,
                    "status": status,
                    "expected": case.expected_output,
                    "actual": actual
                })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "name": case.name,
                    "error": str(e)
                })
        
        return results
    
    def _compare_outputs(self, expected: Dict, tolerance: Dict, actual: Dict) -> bool:
        """Compare actual output to expected with tolerance."""
        for key, expected_value in expected.items():
            if key not in actual:
                return False
            
            actual_value = actual[key]
            tol = tolerance.get(key, 0.0)
            
            if isinstance(expected_value, (int, float)) and isinstance(actual[key], (int, float)):
                if abs(actual[key] - expected_value) > tolerance.get(key, 1e-6):
                    return False
            elif expected_value != actual[key]:
                return False
        
        return True


# Predefined regression test suites
V1_INRIA_BENCHMARK = [
    {
        "name": "cylinder_14mm_open_open",
        "input_data": {
            "length_mm": 180.0,
            "radii_mm": [7.0] * 20,
            "closed_top": False
        },
        "expected_output": {
            "frequencies": [480.0, 960.0, 1440.0, 1920.0, 2400.0, 2880.0, 3360.0, 3840.0, 4320.0, 4800.0],
            "mean_error_cents": 0.0,
            "max_error_cents": 0.0
        },
        "tolerance": {"mean_error_cents": 5.0, "max_error_cents": 10.0},
        "description": "Inria 2026 cylinder open-open"
    },
    {
        "name": "cylinder_14mm_open_closed",
        "input_data": {
            "length_mm": 180.0,
            "radii_mm": [7.0] * 20,
            "closed_top": True
        },
        "expected_output": {
            "frequencies": [240.0, 720.0, 1200.0, 1680.0, 2160.0, 2640.0, 3120.0, 3600.0, 4080.0, 4560.0],
            "mean_error_cents": 0.0,
            "max_error_cents": 0.0
        },
        "tolerance": {"mean_error_cents": 5.0, "max_error_cents": 10.0},
        "description": "Inria 2026 cylinder open-closed"
    }
]


def create_regression_suite(name: str, test_cases: List[Dict]) -> "RegressionTestSuite":
    """Create a regression test suite from test case definitions."""
    suite = RegressionTestSuite(name)
    for tc in test_cases:
        suite.add_case(RegressionTestCase(**tc))
    return suite


# Pytest fixtures
@pytest.fixture
def regression_suite():
    """Provide a regression test suite."""
    return RegressionTestSuite("default")


@pytest.fixture
def v1_inria_suite():
    """V1 Inria benchmark regression suite."""
    suite = RegressionTestSuite("V1 Inria Benchmark")
    for case_data in V1_INRIA_BENCHMARK:
        suite.add_case(RegressionTestCase(**case_data))
    return suite


# Example test
class TestRegressionExample:
    """Example regression test."""
    
    def test_v1_inria_cylinder_open_open(self, v1_inria_suite):
        """Test V1 Inria cylinder open-open regression."""
        from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
        
        for case in v1_inria_suite.test_cases:
            if case.name == "cylinder_14mm_open_open":
                inst = tmm_instrument_from_radii(
                    radii_mm=[7.0] * 20,
                    bore_length_mm=180.0,
                    hole_positions_mm=[],
                    hole_diameters_mm=[],
                    hole_lengths_mm=[],
                    outer_diameter_mm=22.0,
                    closed_top=False,
                    cone_step=0.5
                )
                
                # Compute resonances
                freqs = []
                for n in range(1, 11):
                    target_wl = 4.0 * 18.0 / (2 * n - 1) if False else 2.0 * 18.0 / n  # open-open
                    wl = tmm_instrument_from_radii(
                        radii_mm=[7.0] * 20,
                        bore_length_mm=180.0,
                        hole_positions_mm=[],
                        hole_diameters_mm=[],
                        hole_lengths_mm=[],
                        outer_diameter_mm=22.0,
                        closed_top=False,
                        cone_step=0.5
                    ).find_resonance(SPEED_OF_SOUND / case.expected_output["frequencies"][n-1], [], n_register=2)
                    freq = SPEED_OF_SOUND / wl
                    freqs.append(freq)
                
                # Compare
                for i, (expected, actual) in enumerate(zip(case.expected_output["frequencies"], freqs)):
                    error_cents = 1200 * abs(actual - expected) / expected
                    assert error_cents < 5.0, f"Mode {i+1}: expected {expected:.1f}Hz, got {actual:.1f}Hz ({error_cents:.1f}c)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])