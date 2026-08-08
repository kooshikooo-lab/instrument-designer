"""FEM cross-check of the single-HR stopband dip.

Builds a 3D duct + Helmholtz-resonator side-branch geometry with gmsh,
solves the complex Helmholtz equation with scikit-fem, sweeps frequency
to find the transmission dip, and compares the dip frequency against the
TMM L1 prediction (MetamaterialSideBranch.helmholtz_frequency()).

Target: <5% relative error on the resonance frequency f0.

Usage:
    python scripts/benchmark_metamaterial_fem_crosscheck.py         # full sweep
    python scripts/benchmark_metamaterial_fem_crosscheck.py --quick  # fast smoke test
"""

import argparse
import math
import os
import time

import gmsh
import meshio
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from backend.tmm_acoustics import SPEED_OF_SOUND, MetamaterialSideBranch
from skfem import (
    BilinearForm,
    ElementTetP1,
    FacetBasis,
    LinearForm,
    Basis,
    asm,
)
from skfem.helpers import dot
from skfem.io import from_meshio

NECK_R = 3.0
NECK_L = 8.0
CAVITY_V = 4000.0
FEM_MESH_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "test_output", "fem_hr_mesh.msh"
)


def _build_gmsh_mesh():
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("hr_fem")

    R_DUCT = 0.0095
    L_DUCT = 0.200
    z_hr = L_DUCT / 2.0
    r_n = NECK_R / 1000.0
    l_n = NECK_L / 1000.0
    V = CAVITY_V * 1e-9

    duct = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, L_DUCT, R_DUCT)
    neck = gmsh.model.occ.addCylinder(R_DUCT, 0, z_hr, l_n, 0, 0, r_n)
    r_cav = (3.0 * V / (4.0 * math.pi)) ** (1.0 / 3.0)
    cav = gmsh.model.occ.addSphere(R_DUCT + l_n, 0, z_hr, r_cav)

    gmsh.model.occ.fragment([(3, duct), (3, neck), (3, cav)], [])
    gmsh.model.occ.synchronize()

    vols = gmsh.model.getEntities(3)
    gmsh.model.addPhysicalGroup(3, [v[1] for v in vols], tag=1)
    gmsh.model.setPhysicalName(3, 1, "air")

    inlet_tags, outlet_tags = [], []
    for s in gmsh.model.getEntities(2):
        bb = gmsh.model.getBoundingBox(2, s[1])
        zmin, zmax = bb[2], bb[5]
        if abs(zmin) < 1e-4 and abs(zmax) < 1e-4:
            inlet_tags.append(s[1])
        elif abs(zmin - L_DUCT) < 1e-4 and abs(zmax - L_DUCT) < 1e-4:
            outlet_tags.append(s[1])

    if inlet_tags:
        gmsh.model.addPhysicalGroup(2, inlet_tags, tag=10)
        gmsh.model.setPhysicalName(2, 10, "inlet")
    if outlet_tags:
        gmsh.model.addPhysicalGroup(2, outlet_tags, tag=11)
        gmsh.model.setPhysicalName(2, 11, "outlet")

    f = gmsh.model.mesh.field.add("Box")
    gmsh.model.mesh.field.setNumber(f, "XMin", 0.008)
    gmsh.model.mesh.field.setNumber(f, "XMax", 0.032)
    gmsh.model.mesh.field.setNumber(f, "YMin", -0.015)
    gmsh.model.mesh.field.setNumber(f, "YMax", 0.015)
    gmsh.model.mesh.field.setNumber(f, "ZMin", z_hr - 0.015)
    gmsh.model.mesh.field.setNumber(f, "ZMax", z_hr + 0.015)
    gmsh.model.mesh.field.setNumber(f, "VIn", 0.001)
    gmsh.model.mesh.field.setNumber(f, "VOut", 0.004)
    gmsh.model.mesh.field.setAsBackgroundMesh(f)

    gmsh.model.mesh.generate(3)
    os.makedirs(os.path.dirname(FEM_MESH_PATH), exist_ok=True)
    gmsh.write(FEM_MESH_PATH)
    gmsh.finalize()
    return FEM_MESH_PATH


def _load_mesh():
    if not os.path.exists(FEM_MESH_PATH):
        _build_gmsh_mesh()
    msh = meshio.read(FEM_MESH_PATH)
    return from_meshio(msh)


def _solve_complex_helmholtz(m, k):
    basis = Basis(m, ElementTetP1())
    fb_in = FacetBasis(m, ElementTetP1(), facets=m.boundaries["inlet"])
    fb_out = FacetBasis(m, ElementTetP1(), facets=m.boundaries["outlet"])

    @BilinearForm
    def stiffness(u, v, w):
        return dot(u.grad, v.grad)

    @BilinearForm
    def mass(u, v, w):
        return u * v

    @BilinearForm
    def robin(u, v, w):
        return u * v

    @LinearForm
    def source(v, w):
        return v

    A = asm(stiffness, basis)
    M = asm(mass, basis)
    C_in = asm(robin, fb_in)
    C_out = asm(robin, fb_out)
    f = asm(source, fb_in)

    K = A - (k ** 2) * M + (1j * k) * (C_in + C_out)
    rhs = (2j * k) * f
    p = spla.spsolve(sp.csc_matrix(K), rhs)
    return p, basis


def _transmission(p, basis, m):
    dofs = basis.get_dofs(facets=m.boundaries["outlet"])
    nodes = dofs.flatten()
    return float(np.mean(np.abs(p[nodes])))


def _find_dip(m, f_center, f_span=200.0, n_coarse=40, n_refine=15):
    freqs = np.linspace(f_center - f_span, f_center + f_span, n_coarse)
    pouts = np.empty(len(freqs))
    for i, f_hz in enumerate(freqs):
        k = 2.0 * math.pi * f_hz / (SPEED_OF_SOUND / 1000.0)
        p, basis = _solve_complex_helmholtz(m, k)
        pouts[i] = _transmission(p, basis, m)

    idx = int(np.argmin(pouts))
    f_coarse = freqs[idx]

    f_lo = freqs[max(0, idx - 2)]
    f_hi = freqs[min(len(freqs) - 1, idx + 2)]
    phi = (1.0 + 5.0 ** 0.5) / 2.0
    for _ in range(n_refine):
        f1 = f_hi - (f_hi - f_lo) / phi
        f2 = f_lo + (f_hi - f_lo) / phi
        k1 = 2.0 * math.pi * f1 / (SPEED_OF_SOUND / 1000.0)
        p1, b1 = _solve_complex_helmholtz(m, k1)
        v1 = _transmission(p1, b1, m)
        k2 = 2.0 * math.pi * f2 / (SPEED_OF_SOUND / 1000.0)
        p2, b2 = _solve_complex_helmholtz(m, k2)
        v2 = _transmission(p2, b2, m)
        if v1 < v2:
            f_hi = f2
        else:
            f_lo = f1

    f_fine = 0.5 * (f_lo + f_hi)
    k_fine = 2.0 * math.pi * f_fine / (SPEED_OF_SOUND / 1000.0)
    p_fine, b_fine = _solve_complex_helmholtz(m, k_fine)
    v_fine = _transmission(p_fine, b_fine, m)
    return f_fine, v_fine


def run_fem_crosscheck(quick=False):
    """Run the FEM cross-check and return (f_fem, f_tmm, rel_error_pct)."""
    m = _load_mesh()
    mb = MetamaterialSideBranch(
        position_mm=100.0,
        neck_radius_mm=NECK_R,
        neck_length_mm=NECK_L,
        cavity_volume_mm3=CAVITY_V,
    )
    f_tmm = mb.helmholtz_frequency()

    if quick:
        f_fem, v_fem = _find_dip(m, f_tmm, f_span=300.0, n_coarse=10, n_refine=3)
    else:
        t0 = time.time()
        f_fem, v_fem = _find_dip(m, f_tmm)
        print(f"  solve elapsed: {time.time() - t0:.0f}s")

    rel_err = abs(f_fem - f_tmm) / f_tmm * 100.0
    print(f"FEM dip: {f_fem:.1f} Hz  |p_out|={v_fem:.4f}")
    print(f"TMM  f0: {f_tmm:.1f} Hz")
    print(f"Relative error: {rel_err:.2f}%")
    return f_fem, f_tmm, rel_err


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FEM cross-check of single-HR stopband dip")
    parser.add_argument("--quick", action="store_true", help="fast smoke-test mode")
    args = parser.parse_args()
    run_fem_crosscheck(quick=args.quick)