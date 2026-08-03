"""
Minimal brass-instrument TMM scaffold, companion to metamaterial_elements.py.

Provides: cylindrical bore segments, conical bore segments (via the
psi = r*p Webster-horn substitution), a bell flare built by chaining
conical frustums, an open-end radiation load, and input-impedance /
peak-finding helpers.

Demo at the bottom reproduces the classic "1-3 valve combination plays
sharp" problem on a simplified, illustrative geometry (round numbers,
NOT a calibrated real trumpet -- use this to check methodology, not
absolute pitch), and shows a Helmholtz side-branch (imported from
metamaterial_elements.py) inserted into the valve slide correcting it.
"""

import numpy as np
from scipy.signal import find_peaks

from metamaterial_elements import helmholtz_shunt_matrix, resonance_frequency

RHO0 = 1.2039
C0 = 343.26


def _lossy_wavenumber(f, r):
    """Rough first-order viscothermal loss (Benade-style approximation).
    Same fidelity level as the neck-loss term in metamaterial_elements.py --
    replace with your real bore-loss model when wiring this into the
    actual pipeline."""
    omega = 2 * np.pi * f
    alpha = 3e-5 * np.sqrt(np.maximum(f, 1e-9)) / r  # nepers/m
    return omega / C0 - 1j * alpha


def cylinder_matrix(f, L, r):
    """ABCD matrix for a cylindrical bore segment, length L, radius r."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    k = _lossy_wavenumber(f, r)
    S = np.pi * r**2
    Z0 = RHO0 * C0 / S
    T = np.zeros((len(f), 2, 2), dtype=complex)
    T[:, 0, 0] = np.cos(k * L)
    T[:, 0, 1] = 1j * Z0 * np.sin(k * L)
    T[:, 1, 0] = 1j * np.sin(k * L) / Z0
    T[:, 1, 1] = np.cos(k * L)
    return T


def cone_matrix(f, L, r1, r2, cyl_tol=1e-6):
    """ABCD matrix for a conical frustum, length L, end radii r1 -> r2.
    Falls back to cylinder_matrix if r1 ~= r2 (avoids the apex-distance
    singularity for near-cylindrical segments)."""
    if abs(r2 - r1) < cyl_tol:
        return cylinder_matrix(f, L, 0.5 * (r1 + r2))

    f = np.atleast_1d(np.asarray(f, dtype=float))
    x1 = r1 * L / (r2 - r1)   # distance from virtual apex to input
    x2 = x1 + L
    S1, S2 = np.pi * r1**2, np.pi * r2**2

    T = np.zeros((len(f), 2, 2), dtype=complex)
    for i, fi in enumerate(f):
        k = complex(_lossy_wavenumber(np.array([fi]), 0.5 * (r1 + r2))[0])
        omega = 2 * np.pi * fi

        # (p,U) -> (psi, psi') at x1
        Min = np.array([[x1, 0.0],
                         [1.0, -1j * omega * RHO0 * x1 / S1]], dtype=complex)
        # propagate psi ODE (psi'' + k^2 psi = 0) over length L
        Rpsi = np.array([[np.cos(k * L), np.sin(k * L) / k],
                          [-k * np.sin(k * L), np.cos(k * L)]], dtype=complex)
        # (psi, psi') -> (p,U) at x2
        Mout = np.array([[1.0 / x2, 0.0],
                          [S2 / (1j * omega * RHO0 * x2), -S2 / (1j * omega * RHO0 * x2)]],
                         dtype=complex)
        T[i] = Mout @ Rpsi @ Min
    return T


def bell_flare_matrix(f, profile, n_segments=None):
    """Chain conical frustums through a bell profile.
    profile: list of (x, r) points along the bore axis (m), increasing x.
    Returns the combined ABCD matrix chain (frequency-batched)."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    T_total = np.tile(np.eye(2, dtype=complex), (len(f), 1, 1))
    for (x0, r0), (x1, r1) in zip(profile[:-1], profile[1:]):
        seg = cone_matrix(f, x1 - x0, r0, r1)
        T_total = seg @ T_total
    return T_total


def radiation_impedance(f, r, flanged=True):
    """Low-ka open-end radiation impedance (Levine-Schwinger style approx)."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    S = np.pi * r**2
    Z0 = RHO0 * C0 / S
    k = 2 * np.pi * f / C0
    ka = k * r
    if flanged:
        R = Z0 * (ka**2) / 2.0
        X = Z0 * 0.8488 * ka
    else:
        R = Z0 * (ka**2) / 4.0
        X = Z0 * 0.6133 * ka
    return R + 1j * X


def chain(matrices_list):
    """Multiply a list of (n_freq,2,2) matrices in series, input to output."""
    T = matrices_list[0]
    for M in matrices_list[1:]:
        T = M @ T
    return T


def input_impedance(T_chain, Z_load):
    """Zin given the ABCD chain and a load impedance at the output end."""
    A, B = T_chain[:, 0, 0], T_chain[:, 0, 1]
    C, D = T_chain[:, 1, 0], T_chain[:, 1, 1]
    return (A * Z_load + B) / (C * Z_load + D)


def find_impedance_peaks(f, Zin, band=None):
    mag = np.abs(Zin)
    idx, _ = find_peaks(mag)
    if band is not None:
        idx = [i for i in idx if band[0] <= f[i] <= band[1]]
    return [(f[i], mag[i]) for i in idx]


def cents(f_actual, f_target):
    return 1200 * np.log2(f_actual / f_target)


if __name__ == "__main__":
    # --- sanity check: cone_matrix should match cylinder_matrix when r1==r2 ---
    f_test = np.array([300.0])
    Tc = cylinder_matrix(f_test, 0.3, 0.006)
    Tk = cone_matrix(f_test, 0.3, 0.006, 0.006)
    assert np.allclose(Tc, Tk, atol=1e-8), "cone/cylinder mismatch at r1=r2"
    print("cone_matrix sanity check OK (matches cylinder at r1=r2)\n")

    # --- illustrative geometry, round numbers, NOT a calibrated trumpet ---
    r_bore = 0.006          # 6mm main tubing radius
    leadpipe = [(0.0, 0.0045), (0.15, r_bore)]        # short conical leadpipe
    bell = [(0.0, r_bore), (0.08, 0.010), (0.14, 0.022), (0.18, 0.062)]  # coarse flare

    L_main_open = 1.20      # open (no valves) main tubing length, illustrative
    L_valve1 = 0.065        # illustrative valve-1 slide added length
    L_valve3 = 0.145        # illustrative valve-3 slide added length (bigger loop)

    f = np.linspace(150, 900, 4000)

    def build_zin(extra_L, resonator_at_extra=None):
        mats = [bell_flare_matrix(f, leadpipe)]
        if extra_L > 0:
            if resonator_at_extra is None:
                mats.append(cylinder_matrix(f, extra_L, r_bore))
            else:
                half = extra_L / 2
                mats.append(cylinder_matrix(f, half, r_bore))
                mats.append(resonator_at_extra)
                mats.append(cylinder_matrix(f, half, r_bore))
        mats.append(cylinder_matrix(f, L_main_open, r_bore))
        mats.append(bell_flare_matrix(f, bell))
        Zload = radiation_impedance(f, bell[-1][1], flanged=False)
        return input_impedance(chain(mats), Zload)

    Zin_open = build_zin(extra_L=0.0)
    Zin_13 = build_zin(extra_L=L_valve1 + L_valve3)

    peaks_open = find_impedance_peaks(f, Zin_open, band=(150, 900))
    peaks_13 = find_impedance_peaks(f, Zin_13, band=(150, 900))

    print("Open fingering impedance peaks (Hz):", [round(p[0], 1) for p in peaks_open])
    print("1-3 combination peaks (Hz):        ", [round(p[0], 1) for p in peaks_13])

    # Compare the partial nearest a nominal 'in-tune' target: naive theory
    # says 1-3 should land near the same partial as the open series
    # transposed down -- take the open series' 3rd found peak as the
    # naive target and compare against the actual 1-3 peak nearest it.
    if len(peaks_open) >= 3 and len(peaks_13) >= 3:
        target = peaks_open[2][0]
        actual = min(peaks_13, key=lambda p: abs(p[0] - target))[0]
        dev = cents(actual, target)
        print(f"\n1-3 combination peak nearest target {target:.1f} Hz "
              f"is at {actual:.1f} Hz ({dev:+.1f} cents)")

        # --- correct it with an embedded Helmholtz resonator in the slide ---
        V = 4e-6
        r_neck = 0.003
        L_neck = None
        from scipy.optimize import brentq
        # tune resonator so its own f0 sits near the sharp peak, to pull it down
        g = lambda L: resonance_frequency(V, L, r_neck) - actual
        L_neck = brentq(g, 1e-4, 0.05)
        resonator = helmholtz_shunt_matrix(f, V, L_neck, r_neck, bore_radius=r_bore)

        Zin_13_corrected = build_zin(extra_L=L_valve1 + L_valve3,
                                      resonator_at_extra=resonator)
        peaks_13_corr = find_impedance_peaks(f, Zin_13_corrected, band=(150, 900))
        actual_corr = min(peaks_13_corr, key=lambda p: abs(p[0] - target))[0]
        dev_corr = cents(actual_corr, target)
        print(f"After adding a {V*1e6:.1f}cm3 / {L_neck*1000:.1f}mm-neck resonator "
              f"in the slide: {actual_corr:.1f} Hz ({dev_corr:+.1f} cents)")
