"""
Simple unit test to verify test infrastructure.
"""
import pytest
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_import_backend():
    """Test that backend modules can be imported."""
    from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
    assert SPEED_OF_SOUND == 346100.0


def test_tmm_instrument_creation():
    """Test TMM instrument creation."""
    from backend.tmm_acoustics import tmm_instrument_from_radii
    
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
    assert len(inst.inner.pos) == 20


def test_fixture_registry():
    """Test fixture registry loading."""
    from backend.fixtures import FIXTURE_REGISTRY, load_all_fixtures
    
    registry = load_all_fixtures()
    assert len(registry.fixtures) > 0
    
    # Check a specific fixture exists
    cylinder = registry.get("Inria Cylinder 14mm Open-Open")
    assert cylinder is not None
    assert cylinder.family == "Flutes"
    assert cylinder.subcategory == "End-Blown Flutes"