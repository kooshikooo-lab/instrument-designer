"""Regression tests: OpenWind wrapper vs TMM reference solver.

Catches the register/boundary-convention mismatch documented in
docs/AI_FAILURE_PATTERNS.md #9. Key physics:

- A reed (closed) input sounds at the impedance *resonances*.
- An open input (flute-like) sounds at the impedance *antiresonances*; a pipe
  open at both ends has impedance peaks only at its odd modes, so scanning
  peaks alone returns 3x/5x/9x the fundamental.
- Open geometry uses TMM register n+1 for the n-th played note (phase starts
  at 0.5 at each open end); TMM register 1 is a spurious near-zero mode.
- The register vent is OPEN for register >= 2 and CLOSED otherwise.

TMM and OpenWind are complementary (ADR-006): TMM drives optimization, OpenWind
FEM validates. These tests keep the two locked to the same convention.
"""

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
    NodeType,
    Port,
    Segment,
)
from backend.solvers.openwind_solver import OpenWindSolver
from backend.solvers.tmm_solver import TMMSolver

pytest.importorskip("openwind")

CENTS_TOL = 60.0
SPEED_OF_SOUND = 346100.0  # mm/s, chalumier value


def _cylinder(length, radius, boundary_type):
    """A single cylindrical segment, no holes."""
    return AcousticNetwork(
        segments=[Segment(length=length, radius_in=radius, radius_out=radius)],
        ports=[],
        boundary_reed=Boundary(
            type=boundary_type, excitation=ExcitationType.NONE, position=0.0
        ),
        boundary_bell=Boundary(
            type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=0.0
        ),
    )


def _cents(f_openwind, f_tmm):
    return 1200.0 * np.log2(f_openwind / f_tmm)


@pytest.fixture(scope="module")
def ow_solver():
    return OpenWindSolver()


@pytest.fixture(scope="module")
def tmm_solver():
    return TMMSolver()


def _assert_close(f_ow, f_tmm, label):
    assert np.isfinite(f_ow), f"{label}: OpenWind returned NaN"
    cents = _cents(f_ow, f_tmm)
    assert abs(cents) < CENTS_TOL, (
        f"{label}: OpenWind {f_ow:.1f} Hz vs TMM {f_tmm:.1f} Hz "
        f"({cents:.1f} cents)"
    )


def test_open_pipe_openwind_register_matches_tmm_register_plus_one(ow_solver, tmm_solver):
    """Open-open pipe: OpenWind register n equals TMM register n+1.

    Regression for the original bug: the old window (f_min = c/(2*max_wl))
    started exactly on the first antiresonance, so register 1 silently returned
    the *next* peak (+1417 cents) and register >= 2 returned NaN.
    """
    length = 300.0
    radius = 9.0
    net = _cylinder(length, radius, BoundaryType.OPEN)

    for reg in [1, 3]:
        target_wl = 2.0 * length / reg  # open-open harmonic
        f_ow = ow_solver.compute_frequencies(
            net, [target_wl], [[]], n_register=reg
        )[0]
        f_tmm = tmm_solver.compute_frequencies(
            net, [target_wl], [[]], n_register=reg + 1
        )[0]
        _assert_close(f_ow, f_tmm, f"open pipe register {reg}")


def test_reed_pipe_openwind_matches_tmm(ow_solver, tmm_solver):
    """Closed-open (reed) pipe: OpenWind register n equals TMM register n."""
    length = 300.0
    radius = 9.0
    net = _cylinder(length, radius, BoundaryType.REED)

    for reg in [1, 2]:
        target_wl = 4.0 * length / (2.0 * reg - 1.0)  # odd quarter-wave mode
        f_ow = ow_solver.compute_frequencies(
            net, [target_wl], [[]], n_register=reg
        )[0]
        f_tmm = tmm_solver.compute_frequencies(
            net, [target_wl], [[]], n_register=reg
        )[0]
        _assert_close(f_ow, f_tmm, f"reed pipe register {reg}")


def test_register_vent_open_for_register_two(ow_solver, tmm_solver):
    """Register vent (Port.is_register_vent) is OPEN for register >= 2 in both solvers.

    Verifies the Port.is_register_vent interface fix (the property was missing,
    so any TMMSolver call on a network with ports raised AttributeError) and
    that the two solvers agree once the vent is opened.
    """
    length = 300.0
    radius = 9.0
    net = AcousticNetwork(
        segments=[Segment(length=length, radius_in=radius, radius_out=radius)],
        ports=[
            Port(
                position=length - 10.0,  # near the reed end (0 = bell)
                radius=1.25,
                length=3.0,
                is_open=False,
                node_type=NodeType.REGISTER_VENT,
            )
        ],
        boundary_reed=Boundary(
            type=BoundaryType.REED, excitation=ExcitationType.NONE, position=0.0
        ),
        boundary_bell=Boundary(
            type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=0.0
        ),
    )

    target_wl = 4.0 * length / 3.0  # register 2 odd quarter-wave mode
    f_ow = ow_solver.compute_frequencies(
        net, [target_wl], [[]], n_register=2
    )[0]
    f_tmm = tmm_solver.compute_frequencies(
        net, [target_wl], [[]], n_register=2
    )[0]
    _assert_close(f_ow, f_tmm, "reed pipe register 2 with register vent")
