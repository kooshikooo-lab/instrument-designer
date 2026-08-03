"""
Folded-bore woodwind scaffold, companion to metamaterial_elements.py and
brass_scaffold.py. Aimed at low clarinets (bass, contra-alto, contrabass)
where the bore is folded into U-turns to keep the physical instrument a
manageable height.

Reuses cylinder_matrix / cone_matrix / chain / input_impedance /
find_impedance_peaks from brass_scaffold.py (those elements are generic
1D waveguide acoustics, not brass-specific) and helmholtz_shunt_matrix
from metamaterial_elements.py.

Adds:
  - open/closed tonehole shunt elements (needed for anything beyond a
    single fundamental, and useful context even though the demo below
    only drives the all-closed "lowest note" configuration)
  - an explicitly-approximate bend correction for U-turns
  - a folded-bore builder
  - a reed-end (near-closed) input impedance driver, matching clarinet
    acoustics where playing frequencies sit near impedance MAXIMA,
    unlike an open/flute-type driver

IMPORTANT CAVEAT: the bend correction below is a first-order engineering
placeholder (borrowed from general duct-acoustics minor-loss practice),
NOT a validated woodwind-specific bend model. Treat its output as "which
direction and roughly how much," not a number to trust for final design.
If you want a trustworthy number, compare against an OpenWInD FEM run of
the actual folded geometry, or an impedance-tube measurement of a real
folded joint.
"""

import numpy as np
from scipy.optimize import brentq

from brass_scaffold import (cylinder_matrix, cone_matrix, chain,
                             input_impedance, find_impedance_peaks,
                             radiation_impedance, cents, RHO0, C0)
from metamaterial_elements import helmholtz_shunt_matrix, resonance_frequency


def tonehole_open_matrix(f, hole_radius, chimney_height, unflanged=True):
    """Open tonehole: inertance + radiation shunt to atmosphere (no cavity
    compliance term -- atmosphere is effectively infinite compliance)."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    omega = 2 * np.pi * f
    S_h = np.pi * hole_radius**2
    corr = (0.61 if unflanged else 0.85) * hole_radius
    l_eff = chimney_height + 2 * corr
    M_a = RHO0 * l_eff / S_h
    k = omega / C0
    R = RHO0 * C0 * (k * hole_radius)**2 / 2.0
    Z = R + 1j * omega * M_a
    T = np.zeros((len(f), 2, 2), dtype=complex)
    T[:, 0, 0] = 1.0
    T[:, 1, 0] = 1.0 / Z
    T[:, 1, 1] = 1.0
    return T


def tonehole_closed_matrix(f, hole_radius, chimney_height):
    """Closed (padded/keyed) tonehole: small residual shunt from the
    trapped air in the chimney, modeled as pure compliance (leading-order
    Keefe-style closed-hole correction; ignoring the small mass/resistive
    terms). chimney_height<=0 collapses to no effect."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    if chimney_height <= 0:
        T = np.zeros((len(f), 2, 2), dtype=complex)
        T[:, 0, 0] = 1.0
        T[:, 1, 1] = 1.0
        return T
    omega = 2 * np.pi * f
    S_h = np.pi * hole_radius**2
    V = S_h * chimney_height
    C_a = V / (RHO0 * C0**2)
    Z = -1j / (omega * C_a)
    T = np.zeros((len(f), 2, 2), dtype=complex)
    T[:, 0, 0] = 1.0
    T[:, 1, 0] = 1.0 / Z
    T[:, 1, 1] = 1.0
    return T


def bend_added_length(r_bore, angle_deg=180.0, k_bend=0.6):
    """Rough placeholder equivalent-length correction for a bend -- see
    module docstring caveat. Returns extra length (m) to fold into the
    adjacent straight segment."""
    return k_bend * (angle_deg / 180.0) * (2 * r_bore)


def build_folded_bore(f, total_length, r_bore, n_bends, bell_profile=None,
                       k_bend=0.6):
    """
    Build a folded cylindrical bore as a chain of straight segments with
    bend corrections folded into the segment lengths at n_bends evenly
    spaced points. bell_profile, if given, is appended as a conical flare
    (list of (x,r) points starting at x=0 with r=r_bore).
    Returns the combined ABCD matrix chain.
    """
    # total_length is the physical centerline length (how clarinet bore
    # length is normally specified/measured, following the bends). The
    # bend correction is a small EXTRA acoustic length added at each
    # fold on top of that -- it does not shorten the straight runs.
    bend_len = bend_added_length(r_bore, 180.0, k_bend)
    seg_len = total_length / (n_bends + 1)

    mats = []
    for i in range(n_bends + 1):
        mats.append(cylinder_matrix(f, seg_len, r_bore))
        if i < n_bends:
            # fold the bend's added length in as its own tiny segment,
            # kept separate so a resonator could later be inserted here
            mats.append(cylinder_matrix(f, bend_len, r_bore))
    if bell_profile is not None:
        full_profile = [(0.0, r_bore)] + list(bell_profile)
        for (x0, r0), (x1, r1) in zip(full_profile[:-1], full_profile[1:]):
            mats.append(cone_matrix(f, x1 - x0, r0, r1))
        r_end = bell_profile[-1][1]
    else:
        r_end = r_bore
    return chain(mats), r_end


def reed_end_lowest_note_peak(f, T_chain, r_end, flanged=True):
    """For a clarinet-family (near-closed reed) driver, playing
    frequencies sit near impedance MAGNITUDE MAXIMA (opposite convention
    from an open/flute-type driver). Returns the impedance peaks."""
    Zload = radiation_impedance(f, r_end, flanged=flanged)
    Zin = input_impedance(T_chain, Zload)
    return find_impedance_peaks(f, Zin, band=(f[0], f[-1])), Zin


if __name__ == "__main__":
    # Illustrative geometries, round numbers -- NOT catalog-accurate.
    # Bore-length figures are ballpark placeholders for the family, not
    # measurements of a specific instrument.
    instruments = {
        "bass clarinet (illustrative)":      dict(L=1.35, r=0.0085, n_bends=1),
        "contra-alto clarinet (illustrative)": dict(L=1.95, r=0.0110, n_bends=2),
        "contrabass clarinet (illustrative)":  dict(L=2.65, r=0.0130, n_bends=3),
    }

    f = np.linspace(30, 400, 8000)
    bell = [(0.10, 0.030), (0.16, 0.055)]  # coarse illustrative bell flare

    results = {}
    for name, spec in instruments.items():
        T_folded, r_end = build_folded_bore(f, spec["L"], spec["r"],
                                             spec["n_bends"], bell_profile=bell)
        peaks_folded, _ = reed_end_lowest_note_peak(f, T_folded, r_end)

        T_straight, _ = build_folded_bore(f, spec["L"], spec["r"], 0,
                                           bell_profile=bell)
        peaks_straight, _ = reed_end_lowest_note_peak(f, T_straight, r_end)

        f0_folded = peaks_folded[0][0] if peaks_folded else float("nan")
        f0_straight = peaks_straight[0][0] if peaks_straight else float("nan")
        shift = cents(f0_folded, f0_straight) if peaks_folded and peaks_straight else float("nan")
        results[name] = (f0_straight, f0_folded, shift)
        print(f"{name}:")
        print(f"  straight-bore fundamental: {f0_straight:.2f} Hz")
        print(f"  folded ({spec['n_bends']} bend(s)) fundamental: {f0_folded:.2f} Hz"
              f"  ({shift:+.1f} cents vs straight)")

    # --- feasibility check: how big does a RIGID Helmholtz resonator's
    #     neck have to be to reach these fundamentals? This matters more
    #     than a single demo correction -- it tells you which mechanism
    #     (rigid cavity vs. locally-resonant liner) is actually usable at
    #     each register. ---
    print("\nRigid-cavity resonator feasibility (neck length needed to tune")
    print("to each instrument's folded fundamental, r_neck=10mm):")
    for name, (f0_straight, f0_folded, shift) in results.items():
        for V in (10e-6, 30e-6, 100e-6):
            r_neck = 0.010
            g = lambda L: resonance_frequency(V, L, r_neck) - f0_folded
            try:
                L_neck = brentq(g, 1e-4, 3.0)
                print(f"  {name:38s} V={V*1e6:4.0f}cm3 -> neck {L_neck*100:6.1f}cm")
            except ValueError:
                print(f"  {name:38s} V={V*1e6:4.0f}cm3 -> unreachable within a 3m neck")
    print("\n  Takeaway: correcting a fundamental this low with a rigid air")
    print("  column needs neck lengths of tens of cm to several meters --")
    print("  not embeddable in a fold joint. The rigid Helmholtz mechanism")
    print("  stays practical for shaping upper partials/formants (where the")
    print("  neck-length math looks like the ~1kHz soprano-clarinet case")
    print("  earlier in this project), but NOT for pulling a low fundamental")
    print("  into tune. For that, the locally-resonant liner mechanism")
    print("  (effective_density_locally_resonant, in metamaterial_elements.py)")
    print("  is the better-fitted tool: its tuning knob is spring stiffness,")
    print("  not a physically long air column, so it doesn't hit this wall.")
