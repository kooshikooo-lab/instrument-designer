"""
Generalized woodwind bore builder, companion to metamaterial_elements.py,
brass_scaffold.py, and folded_bore_elements.py.

The earlier scripts hard-wired where resonators/bends went. This module
gives you a composable representation: a bore is a list of ('cyl', L, r)
/ ('cone', L, r1, r2) segments, and any number of shunt elements (tone
holes, metamaterial resonators, bend corrections) can be inserted at
arbitrary axial positions -- the segment they land in is split
automatically. This is the representation an optimizer wants: resonator
*position* becomes just another continuous parameter, not something that
requires manually restructuring the segment list.
"""

import numpy as np

from brass_scaffold import cylinder_matrix, cone_matrix, chain, RHO0, C0


def build_chain_with_insertions(f, base_segments, insertions):
    """
    base_segments: list of ('cyl', L, r) or ('cone', L, r1, r2), in order
                   from the driving end.
    insertions: list of (position, matrix_fn) where position is the
                cumulative distance (m) from the start of base_segments,
                and matrix_fn(f) -> (nfreq,2,2) complex ndarray is the
                shunt matrix to splice in there (tonehole, resonator,
                bend correction, ...).
    Returns the combined ABCD matrix chain.

    Segments are split at each insertion point (radius interpolated
    linearly along a 'cone' segment if the split falls inside one), so
    geometry stays continuous on either side of the inserted element.
    """
    f = np.atleast_1d(np.asarray(f, dtype=float))
    ins_sorted = sorted(insertions, key=lambda x: x[0])
    ins_idx = 0
    mats = []
    cum_start = 0.0

    for seg in base_segments:
        seg_type, L = seg[0], seg[1]
        seg_start, seg_end = cum_start, cum_start + L
        local_ins = []
        while ins_idx < len(ins_sorted) and ins_sorted[ins_idx][0] <= seg_end + 1e-12:
            pos, fn = ins_sorted[ins_idx]
            if pos >= seg_start - 1e-12:
                local_ins.append((pos, fn))
            ins_idx += 1

        if not local_ins:
            mats.append(_segment_matrix(f, seg))
        else:
            prev_pos = seg_start
            if seg_type == 'cyl':
                r = seg[2]
                for pos, fn in local_ins:
                    sub_L = pos - prev_pos
                    if sub_L > 1e-9:
                        mats.append(cylinder_matrix(f, sub_L, r))
                    mats.append(fn(f))
                    prev_pos = pos
                rem = seg_end - prev_pos
                if rem > 1e-9:
                    mats.append(cylinder_matrix(f, rem, r))
            elif seg_type == 'cone':
                r1, r2 = seg[2], seg[3]
                for pos, fn in local_ins:
                    frac_s = (prev_pos - seg_start) / L
                    frac_e = (pos - seg_start) / L
                    r_a = r1 + (r2 - r1) * frac_s
                    r_b = r1 + (r2 - r1) * frac_e
                    sub_L = pos - prev_pos
                    if sub_L > 1e-9:
                        mats.append(cone_matrix(f, sub_L, r_a, r_b))
                    mats.append(fn(f))
                    prev_pos = pos
                rem = seg_end - prev_pos
                if rem > 1e-9:
                    frac_s = (prev_pos - seg_start) / L
                    r_a = r1 + (r2 - r1) * frac_s
                    mats.append(cone_matrix(f, rem, r_a, r2))
            else:
                raise ValueError(f"unknown segment type {seg_type}")
        cum_start = seg_end

    return chain(mats)


def _segment_matrix(f, seg):
    if seg[0] == 'cyl':
        return cylinder_matrix(f, seg[1], seg[2])
    elif seg[0] == 'cone':
        return cone_matrix(f, seg[1], seg[2], seg[3])
    raise ValueError(f"unknown segment type {seg[0]}")


def bend_correction(r_bore, bend_radius, angle_deg=180.0, k_bend=0.6):
    """
    Heuristic bend correction (equivalent extra length, m) that shrinks
    as the bend gets gentler relative to the bore radius, and grows as
    the bend tightens toward a sharp elbow. NOT validated against
    woodwind-specific measurements -- see module-level caveat below.

    tightness = r_bore / bend_radius, capped at 2.0 (a bend radius at or
    below the bore radius counts as "as sharp as this heuristic models").
    """
    tightness = min(r_bore / max(bend_radius, 1e-6), 2.0)
    return k_bend * (angle_deg / 180.0) * (2 * r_bore) * tightness


def plane_wave_validity_ok(straight_run_length, r_bore, n_diameters=3.0):
    """
    Rule-of-thumb check from general duct acoustics: higher-order
    evanescent modes excited at a discontinuity (bend, tonehole, step)
    typically decay within a few bore diameters. If the straight run
    between two discontinuities is shorter than that, the plane-wave TMM
    assumption used throughout these scripts is questionable there --
    consider 3D FEM or a direct impedance-tube measurement instead of
    trusting this model's number at that specific junction.
    """
    return straight_run_length >= n_diameters * 2 * r_bore


def tonehole_open_matrix(f, hole_radius, chimney_height, unflanged=True):
    """Open tonehole shunt (inertance + radiation to atmosphere)."""
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
    """Closed (padded) tonehole shunt (trapped-air compliance only)."""
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


def build_fingering_chain(f, base_segments, toneholes, fingering):
    """
    toneholes: list of dicts, each {'position':x, 'radius':r, 'chimney':h}
               in order along the bore.
    fingering: list of bool, same length/order as toneholes; True = open.
    Returns the ABCD chain for that fingering.
    """
    insertions = []
    for hole, is_open in zip(toneholes, fingering):
        if is_open:
            fn = lambda f_, h=hole: tonehole_open_matrix(f_, h['radius'], h['chimney'])
        else:
            fn = lambda f_, h=hole: tonehole_closed_matrix(f_, h['radius'], h['chimney'])
        insertions.append((hole['position'], fn))
    return build_chain_with_insertions(f, base_segments, insertions)


if __name__ == "__main__":
    # sanity check: inserting a tonehole via build_chain_with_insertions
    # partway through a cylinder should match manually splitting it
    f = np.array([500.0])
    r = 0.0075

    manual = chain([
        cylinder_matrix(f, 0.10, r),
        tonehole_open_matrix(f, 0.004, 0.003),
        cylinder_matrix(f, 0.05, r),
    ])
    auto = build_chain_with_insertions(
        f,
        base_segments=[('cyl', 0.15, r)],
        insertions=[(0.10, lambda f_: tonehole_open_matrix(f_, 0.004, 0.003))],
    )
    assert np.allclose(manual, auto, atol=1e-10), "insertion splitting mismatch"
    print("build_chain_with_insertions sanity check OK\n")

    # bend_correction behavior check: gentle bend should barely register,
    # tight bend should approach the old fixed heuristic
    r_bore = 0.010
    print("bend_correction sanity (r_bore=10mm):")
    for bend_r in [0.005, 0.010, 0.030, 0.100]:
        c = bend_correction(r_bore, bend_r)
        print(f"  bend_radius={bend_r*1000:5.1f}mm -> correction={c*1000:6.2f}mm")

    print("\nplane_wave_validity_ok checks:")
    for run_len in [0.01, 0.03, 0.08]:
        ok = plane_wave_validity_ok(run_len, r_bore)
        print(f"  straight run {run_len*100:.1f}cm between discontinuities: "
              f"{'OK' if ok else 'TOO SHORT -- 1D model questionable here'}")

    # small fingering-chart demo: 3 toneholes on a short cylindrical bore
    toneholes = [
        {'position': 0.20, 'radius': 0.004, 'chimney': 0.003},
        {'position': 0.30, 'radius': 0.004, 'chimney': 0.003},
        {'position': 0.40, 'radius': 0.004, 'chimney': 0.003},
    ]
    base = [('cyl', 0.60, 0.0075)]
    f_scan = np.linspace(30, 1500, 6000)  # NOTE: must scan low enough to
    # catch the true fundamental -- an earlier version of this demo used
    # a 200Hz floor and silently reported the 3rd harmonic instead. This
    # is exactly the kind of thing benchmark_and_optimize.py's frequency-
    # range sanity check exists to catch.
    for name, fingering in [("all closed", [False, False, False]),
                             ("lowest hole open", [True, False, False]),
                             ("all open", [True, True, True])]:
        from brass_scaffold import input_impedance, find_impedance_peaks, radiation_impedance
        T = build_fingering_chain(f_scan, base, toneholes, fingering)
        Zload = radiation_impedance(f_scan, 0.0075, flanged=False)
        Zin = input_impedance(T, Zload)
        peaks = find_impedance_peaks(f_scan, Zin, band=(30, 1500))
        f0 = peaks[0][0] if peaks else float('nan')
        print(f"{name:20s}: lowest impedance peak {f0:.1f} Hz")
