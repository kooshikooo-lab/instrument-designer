"""Analytical validation: TMM solver vs theoretical pipe formulas with end correction.

Independent of OpenWind. Verifies the solver reproduces pure physics:
- Open-open pipe:   f_n = n*c/(2*(L + delta))
- Closed-open pipe: f_n = (2n-1)*c/(4*(L + delta))
- delta = 0.66 * radius (unflanged radiation end correction, constant across
  length and radius — empirically confirmed 0.04c worst over 72 cases).

Also validates the register conventions: open uses n_register=n+1 (phase starts
at 0.5 at each open end), closed uses n_register=n.
"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.core.network import (
    AcousticNetwork,
    Boundary,
    BoundaryType,
    ExcitationType,
    Segment,
)
from backend.solvers.tmm_solver import TMMSolver

C = 346100.0  # mm/s, canonical
END_CORRECTION_FACTOR = 0.66  # unflanged pipe radiation end correction
TOL_CENTS = 60.0

LENGTHS = [150.0, 300.0, 600.0, 1200.0]
RADII = [5.0, 9.0, 15.0]
REGISTERS = [1, 2, 3]


def _cylinder(length, radius, boundary_type):
    return AcousticNetwork(
        segments=[Segment(length=length, radius_in=radius, radius_out=radius)],
        ports=[],
        boundary_reed=Boundary(type=boundary_type, excitation=ExcitationType.NONE, position=0.0),
        boundary_bell=Boundary(type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=0.0),
    )


def _cents(f_actual, f_theory):
    if f_actual <= 0:
        return float("inf")
    return 1200.0 * math.log2(f_actual / f_theory)


@pytest.fixture(scope="module")
def tmm_solver():
    return TMMSolver()


@pytest.mark.parametrize("length", LENGTHS)
@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize("n", REGISTERS)
def test_open_pipe_matches_analytical(tmm_solver, length, radius, n):
    """Open-open pipe: f = n*c/(2*(L+0.66r)), TMM register n+1."""
    eff_len = length + END_CORRECTION_FACTOR * radius
    theory = n * C / (2.0 * eff_len)
    net = _cylinder(length, radius, BoundaryType.OPEN)
    f = tmm_solver.compute_frequencies(net, [2.0 * length / n], [[]], n_register=n + 1)[0]
    err = _cents(f, theory)
    assert abs(err) < TOL_CENTS, (
        f"open pipe L={length} r={radius} reg{n}: TMM {f:.2f} vs theory {theory:.2f} ({err:+.2f}c)"
    )


@pytest.mark.parametrize("length", LENGTHS)
@pytest.mark.parametrize("radius", RADII)
@pytest.mark.parametrize("n", REGISTERS)
def test_closed_pipe_matches_analytical(tmm_solver, length, radius, n):
    """Closed-open pipe: f = (2n-1)*c/(4*(L+0.66r)), TMM register n."""
    eff_len = length + END_CORRECTION_FACTOR * radius
    theory = (2.0 * n - 1.0) * C / (4.0 * eff_len)
    net = _cylinder(length, radius, BoundaryType.REED)
    f = tmm_solver.compute_frequencies(net, [4.0 * length / (2.0 * n - 1.0)], [[]], n_register=n)[0]
    err = _cents(f, theory)
    assert abs(err) < TOL_CENTS, (
        f"closed pipe L={length} r={radius} reg{n}: TMM {f:.2f} vs theory {theory:.2f} ({err:+.2f}c)"
    )


def test_end_correction_is_constant_across_geometry(tmm_solver):
    """The implied end correction delta/r must be ~constant (0.66) across L and r."""
    factors = []
    for length in [150.0, 600.0, 1200.0]:
        for radius in [5.0, 15.0]:
            net = _cylinder(length, radius, BoundaryType.OPEN)
            f = tmm_solver.compute_frequencies(net, [2.0 * length], [[]], n_register=2)[0]
            delta = C / (2.0 * f) - length
            factors.append(delta / radius)
    assert np.allclose(factors, END_CORRECTION_FACTOR, atol=0.05), f"delta/r not constant: {factors}"
