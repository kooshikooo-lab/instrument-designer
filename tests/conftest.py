"""
Shared pytest fixtures and configuration.
"""
import pytest
import os
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "woodwind_designer"))


@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def backend_root():
    """Backend directory."""
    return Path(__file__).parent.parent / "backend"


@pytest.fixture(scope="session")
def web_root():
    """Web frontend directory."""
    return Path(__file__).parent.parent / "web"


@pytest.fixture(scope="session")
def fixture_registry():
    """Fixture registry with built-in instruments."""
    from backend.fixtures import FIXTURE_REGISTRY, load_all_fixtures
    return load_all_fixtures()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for test artifacts."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# Markers for test categorization
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (multiple components)")
    config.addinivalue_line("markers", "benchmark: Performance/accuracy benchmarks")
    config.addinivalue_line("markers", "regression: Regression tests (V1/V2 validation)")
    config.addinivalue_line("markers", "comparison: Algorithm comparison tests")
    config.addinivalue_line("markers", "slow: Tests that take > 30s")
    config.addinivalue_line("markers", "requires_chalumier: Requires chalumier JAR built")
    config.addinivalue_line("markers", "requires_jax: Requires JAX installed")
    config.addinivalue_line("markers", "server: Requires design server running")