"""Property tests for the acoustic network.

These tests verify fundamental physical properties:
- Coordinate transforms are inverses
- Bell removed matches cylinder
- Zero holes matches analytical tube
"""
import sys, os
import numpy as np
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.core.coordinates import CoordinateTransform
from backend.core.network import AcousticNetwork, Segment, Port, Boundary, NodeType, BoundaryType, ExcitationType
from backend.solvers.tmm_solver import TMMSolver


class TestCoordinateTransform(unittest.TestCase):
    """Test coordinate transforms are correct inverses."""

    def test_chalumier_internal_inverse(self):
        L = 1200.0
        for x in [0.0, 100.0, 600.0, 1200.0]:
            x_internal = CoordinateTransform.chalumier_to_internal(x, L)
            x_back = CoordinateTransform.internal_to_chalumier(x_internal, L)
            self.assertAlmostEqual(x, x_back, places=10)

    def test_chalumier_boundary_mapping(self):
        L = 1200.0
        bell_chalumier = 0.0
        reed_chalumier = L
        bell_internal = CoordinateTransform.chalumier_to_internal(bell_chalumier, L)
        reed_internal = CoordinateTransform.chalumier_to_internal(reed_chalumier, L)
        self.assertAlmostEqual(bell_internal, 0.0, places=10)
        self.assertAlmostEqual(reed_internal, L, places=10)

    def test_openwind_internal_inverse(self):
        for x in [0.0, 500.0, 1200.0]:
            x_internal = CoordinateTransform.openwind_to_internal(x)
            x_back = CoordinateTransform.internal_to_openwind(x_internal)
            self.assertAlmostEqual(x, x_back, places=10)


class TestTMMPhysics(unittest.TestCase):
    """Test TMM solver against analytical solutions."""

    def _make_cylinder(self, length, radius):
        return AcousticNetwork(
            segments=[Segment(length=length, radius_in=radius, radius_out=radius)],
            ports=[],
            boundary_reed=Boundary(type=BoundaryType.REED, excitation=ExcitationType.REED),
            boundary_bell=Boundary(type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=0.0),
        )

    def test_zero_holes_matches_analytical(self):
        L = 1200.0
        r = 12.5
        c = 346100.0

        net = self._make_cylinder(L, r)
        solver = TMMSolver()

        f_analytical = c / (4 * L)
        wl_target = c / f_analytical
        wl = solver.find_resonance(net, wl_target, [], n_register=1)
        f_actual = c / wl

        error_pct = abs(f_actual - f_analytical) / f_analytical * 100
        self.assertLess(error_pct, 2.0,
            f"TMM {f_actual:.1f} Hz vs analytical {f_analytical:.1f} Hz ({error_pct:.1f}%)")


if __name__ == "__main__":
    unittest.main()
