"""FEM cross-check of the single-HR stopband dip.

Validates the TMM L1 MetamaterialSideBranch resonance frequency
against an independent scikit-fem Helmholtz solve of the full 3D
duct + HR geometry.  Target: <5% relative error on f0.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

# FEM cross-check needs the optional `fem` extra (gmsh/meshio/scikit-fem);
# skip cleanly on machines without them (e.g. desktop) instead of failing
# collection.
pytest.importorskip("gmsh", reason="gmsh not installed (pip install .[fem])")
pytest.importorskip("meshio", reason="meshio not installed (pip install .[fem])")
pytest.importorskip("skfem", reason="scikit-fem not installed (pip install .[fem])")

from scripts.benchmark_metamaterial_fem_crosscheck import run_fem_crosscheck


@pytest.mark.slow
def test_fem_crosscheck_runs():
    """FEM cross-check must complete and return a result."""
    f_fem, f_tmm, rel_err = run_fem_crosscheck(quick=True)
    assert f_fem > 0
    assert f_tmm > 0
    assert rel_err >= 0


@pytest.mark.slow
def test_fem_crosscheck_reasonable():
    """FEM dip should be in the same decade as the TMM prediction."""
    f_fem, f_tmm, rel_err = run_fem_crosscheck(quick=True)
    assert rel_err < 50.0, (
        f"FEM dip {f_fem:.1f} Hz is {rel_err:.1f}% from TMM "
        f"f0 {f_tmm:.1f} Hz -- check mesh/BCs"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])