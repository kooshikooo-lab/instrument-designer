"""
Metamaterial-style acoustic elements for woodwind bore TMM chains.

Both functions return a 2x2 complex ABCD (transfer) matrix relating
(p, U) -- acoustic pressure and volume velocity -- across the element,
in the same convention used for cylindrical/conical bore segments and
tonehole shunts:

    [p_out]   [A B] [p_in]
    [U_out] = [C D] [U_in]

A shunt element (side branch, closed off, not fingered) has the form
    [[1, 0], [1/Z_shunt, 1]]
and can be inserted into a chain by matrix-multiplying it at the
junction position, exactly like a tonehole matrix.

Units: SI throughout (m, s, kg, Pa). Frequencies in Hz.
"""

import numpy as np

RHO0 = 1.2039       # kg/m^3, air density at ~20C, 1 atm
C0 = 343.26         # m/s, speed of sound at ~20C
MU = 1.8e-5         # Pa*s, dynamic viscosity of air
KAPPA_OVER_CP = 2.6e-5  # thermal diffusivity-ish term, rough constant for correction


def helmholtz_shunt_matrix(f, V, neck_length, neck_radius, bore_radius,
                            flanged=True, wall_loss=True):
    """
    ABCD matrix for a closed Helmholtz-resonator side branch (a 'phantom
    tonehole' with no fingering, i.e. permanently closed to the player
    but open into the bore).

    f            : frequency (Hz), scalar or array
    V            : cavity volume (m^3)
    neck_length  : physical neck length (m) -- the hole wall thickness
                   plus any added chimney
    neck_radius  : neck (hole) radius (m)
    bore_radius  : main bore radius at the junction (m), used for the
                   flanged end-correction on the inner opening
    flanged      : apply Ingard's flanged end correction on both neck ends
    wall_loss    : include a simple viscothermal series resistance

    Returns: complex ndarray, shape (2,2,) broadcast over f if f is array
    """
    f = np.asarray(f, dtype=float)
    omega = 2 * np.pi * f
    S_neck = np.pi * neck_radius**2

    # End corrections (Ingard-style), one for the outer (flanged) end,
    # one for the inner end opening into the bore (also roughly flanged
    # if bore_radius >> neck_radius; unflanged correction is ~0.6*r if not)
    if flanged:
        delta_outer = 0.85 * neck_radius
        delta_inner = 0.85 * neck_radius
    else:
        delta_outer = 0.61 * neck_radius
        delta_inner = 0.61 * neck_radius

    l_eff = neck_length + delta_outer + delta_inner

    # Acoustic mass and compliance
    M_a = RHO0 * l_eff / S_neck
    C_a = V / (RHO0 * C0**2)

    # Simple resistive loss: radiation resistance at outer opening +
    # viscothermal loss in the neck (boundary-layer approx, good enough
    # for a first pass -- replace with Keefe/Zwikker-Kosten model if you
    # want this to match your bore-loss treatment elsewhere in the pipeline)
    if wall_loss:
        k = omega / C0
        R_rad = RHO0 * C0 * (k * neck_radius)**2 / 2.0  # small-hole radiation R
        # viscothermal series resistance in neck, rough boundary-layer scaling
        R_visc = neck_length / S_neck * np.sqrt(2 * MU * omega * RHO0) / neck_radius
        R = R_rad + R_visc
    else:
        R = 0.0

    Z_shunt = R + 1j * omega * M_a - 1j / (omega * C_a)

    T = np.zeros(omega.shape + (2, 2), dtype=complex) if omega.shape else np.zeros((2, 2), dtype=complex)
    ones = np.ones_like(omega, dtype=complex) if omega.shape else 1.0
    if omega.shape:
        T[..., 0, 0] = 1.0
        T[..., 0, 1] = 0.0
        T[..., 1, 0] = 1.0 / Z_shunt
        T[..., 1, 1] = 1.0
    else:
        T[0, 0], T[0, 1] = 1.0, 0.0
        T[1, 0], T[1, 1] = 1.0 / Z_shunt, 1.0
    return T


def resonance_frequency(V, neck_length, neck_radius, flanged=True):
    """Quick sanity-check f0 for the shunt above (undamped, lumped-element)."""
    S_neck = np.pi * neck_radius**2
    corr = (0.85 if flanged else 0.61) * neck_radius
    l_eff = neck_length + 2 * corr
    return (C0 / (2 * np.pi)) * np.sqrt(S_neck / (V * l_eff))


def effective_density_locally_resonant(f, rho_matrix, phi, rho_core, f0, zeta=0.02):
    """
    Effective (complex, frequency-dependent) density of a locally-resonant
    metamaterial section: a soft matrix (e.g. rubber liner) with embedded
    resonant masses at volume fraction phi, tuned to resonance f0.

    This is the mechanism from Liu et al.'s locally-resonant sonic
    materials: near f0 the effective density goes negative, giving a
    band gap even though the unit cell is far smaller than the
    wavelength -- unlike Helmholtz/Bragg approaches, which need cell
    sizes comparable to a fraction of a wavelength.

    Use this if you want to model a *soft-wall lined bore section*
    rather than a rigid side-branch: it changes the wall admittance
    boundary condition of the bore segment rather than adding a shunt.
    Wiring it into your TMM properly means switching that section from
    a rigid-wall bore matrix to a lined-duct matrix (Zwikker-Kosten /
    locally-reacting or bulk-reacting liner formulation) using this
    rho_eff in place of RHO0 in the wave-number calculation.

    f          : frequency (Hz), array
    rho_matrix : density of surrounding soft matrix (kg/m^3), e.g. rubber
    phi        : volume fraction of embedded resonant mass inclusions
    rho_core   : density of embedded mass inclusions (kg/m^3)
    f0         : target local-resonance frequency (Hz)
    zeta       : damping ratio of the local resonance (matrix compliance loss)
    """
    f = np.asarray(f, dtype=float)
    omega = 2 * np.pi * f
    omega0 = 2 * np.pi * f0
    denom = omega0**2 - omega**2 - 1j * 2 * zeta * omega0 * omega
    rho_eff = rho_matrix + phi * rho_core * omega0**2 / denom
    return rho_eff


if __name__ == "__main__":
    # sanity check: a small side-branch tuned near 1kHz
    f0_target = 1000.0
    V = 3e-6       # 3 cm^3 cavity
    r_neck = 0.0025  # 2.5 mm radius neck
    # solve neck length for target f0 (simple 1D search)
    from scipy.optimize import brentq
    g = lambda L: resonance_frequency(V, L, r_neck) - f0_target
    L_solution = brentq(g, 1e-4, 0.05)
    print(f"Neck length for f0={f0_target} Hz: {L_solution*1000:.2f} mm")

    T = helmholtz_shunt_matrix(np.array([f0_target]), V, L_solution, r_neck, bore_radius=0.0075)
    print("ABCD at f0:\n", T[0])
