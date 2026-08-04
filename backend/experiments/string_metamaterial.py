"""
String metamaterial dispersion calculator, companion to
metamaterial_elements.py and brass_scaffold.py.

Models a taut string (tension T, linear mass density mu) periodically
loaded with point masses, using the same transfer-matrix philosophy as
the bore elements: state vector (Y, F) where Y is transverse
displacement and F = T*dY/dx is the internal shear force -- this is
mechanically the exact analog of (pressure, volume velocity) for a
1D acoustic waveguide, so a free string segment has the same ABCD
form as a lossless cylinder, with Z0 = sqrt(T*mu) playing the role
of the acoustic characteristic impedance.

Two loading mechanisms are provided:
  - rigid point mass (classical Brillouin loaded-string problem --
    this is the mechanism behind Bader & Kontopidis's 1D metamaterial
    string demo)
  - spring-mass local resonator (the modern locally-resonant-metamaterial
    mechanism -- diverging effective mass near the resonator's own
    natural frequency opens a band gap there, not just at Bragg
    frequencies set by the lattice spacing)

Dispersion/band gaps are found via Bloch's theorem on the periodic
unit cell: propagating solutions exist only where |trace(T_cell)/2| <= 1;
outside that range the Bloch wavenumber is complex and waves decay --
that's the band gap.
"""

import numpy as np


def free_segment_matrix(f, L, T, mu, damping=0.0):
    """ABCD matrix for a free (unloaded) string segment of length L."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    c = np.sqrt(T / mu)
    omega = 2 * np.pi * f
    k = omega / c - 1j * damping  # damping: simple uniform loss, nepers/m if >0
    M = np.zeros((len(f), 2, 2), dtype=complex)
    M[:, 0, 0] = np.cos(k * L)
    M[:, 0, 1] = np.sin(k * L) / (T * k)
    M[:, 1, 0] = -T * k * np.sin(k * L)
    M[:, 1, 1] = np.cos(k * L)
    return M


def mass_jump_matrix(f, m, k_spring=None):
    """Shunt matrix for a point loading at the string.
    If k_spring is None: rigid point mass m (classical loaded string).
    If k_spring is given: mass m attached via a spring of that
    stiffness (locally-resonant attachment), resonant at
    f0 = sqrt(k_spring/m) / (2*pi)."""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    omega = 2 * np.pi * f
    if k_spring is None:
        C_jump = -m * omega**2
    else:
        C_jump = -m * omega**2 * k_spring / (k_spring - m * omega**2)
    M = np.zeros((len(f), 2, 2), dtype=complex)
    M[:, 0, 0] = 1.0
    M[:, 0, 1] = 0.0
    M[:, 1, 0] = C_jump
    M[:, 1, 1] = 1.0
    return M


def unit_cell_matrix(f, a, T, mu, m, k_spring=None, damping=0.0):
    """Symmetric unit cell: half-segment + mass/resonator + half-segment.
    a = lattice spacing (m), mass sits at the center of each cell."""
    half = free_segment_matrix(f, a / 2, T, mu, damping)
    jump = mass_jump_matrix(f, m, k_spring)
    return half @ jump @ half


def bloch_trace_half(f, a, T, mu, m, k_spring=None, damping=0.0):
    """Returns trace(T_cell)/2 vs frequency. Band gap where |value| > 1."""
    Tc = unit_cell_matrix(f, a, T, mu, m, k_spring, damping)
    return 0.5 * (Tc[:, 0, 0] + Tc[:, 1, 1])


def find_band_gaps(f, trace_half, threshold=1.0):
    """Return list of (f_start, f_end) bands where |trace_half| > threshold."""
    mag = np.abs(trace_half.real) if np.iscomplexobj(trace_half) else np.abs(trace_half)
    in_gap = mag > threshold
    gaps = []
    start = None
    for i, flag in enumerate(in_gap):
        if flag and start is None:
            start = f[i]
        elif not flag and start is not None:
            gaps.append((start, f[i - 1]))
            start = None
    if start is not None:
        gaps.append((start, f[-1]))
    return gaps


if __name__ == "__main__":
    # Illustrative guitar high-E-ish string, round numbers not measured
    T = 70.0          # N, tension
    mu = 0.00040       # kg/m, linear density
    L_speaking = 0.648  # m, standard scale length ballpark

    c = np.sqrt(T / mu)
    f1_open = c / (2 * L_speaking)
    print(f"Open-string fundamental for these illustrative params: {f1_open:.1f} Hz\n")

    f = np.linspace(50, 8000, 16000)

    # --- classical periodic rigid-mass loading (Bader/Brillouin mechanism) ---
    a = 0.05           # 5cm spacing between loading points
    m_rigid = 0.05e-3  # 50 mg point masses -- light, so the gap stays narrow
    th_rigid = bloch_trace_half(f, a, T, mu, m_rigid)
    gaps_rigid = find_band_gaps(f, th_rigid)
    print("Rigid periodic mass-loading (spacing 5cm, 50mg masses):")
    print("  Band gaps (Hz):", [(round(a_, 1), round(b_, 1)) for a_, b_ in gaps_rigid])
    print("  (first gap here is Bragg-scattering-driven: it sits near c/(2a),")
    print("   set by lattice spacing, not by the mass value)")

    # --- locally-resonant spring-mass attachment, tuned near 1.5 kHz ---
    f0_target = 1500.0
    m_res = 0.1e-3     # 100 mg resonant mass -- light coupling, narrower gap
    k_spring = (2 * np.pi * f0_target)**2 * m_res
    th_res = bloch_trace_half(f, a, T, mu, m_res, k_spring=k_spring)
    gaps_res = find_band_gaps(f, th_res)
    print(f"\nLocally-resonant attachment (100mg mass, spring tuned to {f0_target} Hz):")
    print("  Band gaps (Hz):", [(round(a_, 1), round(b_, 1)) for a_, b_ in gaps_res])
    print("  (this gap sits at/above f0 regardless of lattice spacing --")
    print("   that's the local-resonance signature vs. the Bragg gap above,")
    print("   which moves if you change 'a' instead of the resonator tuning)")
