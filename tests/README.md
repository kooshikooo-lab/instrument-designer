# Test Infrastructure

## Directory Structure

```
tests/
├── unit/           # Unit tests (fast, isolated)
├── integration/    # Integration tests (multiple components)
├── benchmark/      # Performance/accuracy benchmarks
├── regression/     # Regression tests (V1/V2 validation)
├── comparison/     # Algorithm comparison tests
├── conftest.py     # Shared pytest fixtures
├── run_tests.py    # Test runner script
└── README.md       # This file
```

## Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py unit
python tests/run_tests.py integration
python tests/run_tests.py benchmark
python tests/run_tests.py regression
python tests/run_tests.py comparison

# With coverage
python tests/run_tests.py --coverage

# Verbose output
python tests/run_tests.py unit -v

# Generate reports
python tests/run_tests.py --output reports

# List available tests
python tests/run_tests.py --list
```

## Test Categories

| Category | Marker | Description | Speed |
|----------|--------|-------------|-------|
| Unit | `unit` | Fast, isolated tests | Fast |
| Integration | `integration` | Multi-component tests | Medium |
| Benchmark | `benchmark` | Performance/accuracy | Slow |
| Regression | `regression` | V1/V2 validation | Medium |
| Comparison | `comparison` | Algorithm comparisons | Medium |

## Writing Tests

### Unit Test Example
```python
# tests/unit/test_tmm_acoustics.py
import pytest
from backend.tmm_acoustics import tmm_instrument_from_radii

def test_tmm_instrument_creation():
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
    assert inst is not None
    assert inst.length == 300.0
```

### Benchmark Test Example
```python
# tests/benchmark/test_tmm_performance.py
import pytest
from tests.benchmark.benchmark_template import BenchmarkRunner

def test_tmm_resonance_performance():
    runner = BenchmarkRunner("TMM Performance")
    runner.add_benchmark("find_resonance", run_tmm_resonance, iterations=10)
    results = runner.run_all()
    
    for result in runner.results:
        assert result["stats"]["runtime_seconds"]["mean"] < 0.1
```

### Comparison Test Example
```python
# tests/comparison/test_optimizer_comparison.py
from tests.comparison.comparison_framework import AlgorithmComparator

def test_optimizer_comparison():
    comp = AlgorithmComparator("Optimizer Comparison")
    
    comp.register_algorithm("DE", run_de_optimizer)
    comp.register_algorithm("L-BFGS-B", run_lbfgsb_optimizer)
    comp.register_algorithm("TwoPhase", run_two_phase)
    
    comp.add_test_case("folk_flute", {"targets": [...], "fingerings": [...]})
    
    results = comp.run_comparison(iterations=3)
    comp.save_results("optimizer_comparison.json")
    
    # Assert TwoPhase is best for accuracy
    for result in comp.results:
        assert result.best_by_metric.get("mean_error_cents") == "TwoPhase"
```

## Running Tests

```bash
# From project root
cd tests
python run_tests.py                    # All tests
python tests/run_tests.py unit         # Unit tests only
python tests/run_tests.py benchmark    # Benchmarks
python tests/run_tests.py --coverage   # With coverage
python tests/run_tests.py --output reports  # Generate reports
```

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: python tests/run_tests.py --coverage --output reports
      - uses: codecov/codecov-action@v3
```