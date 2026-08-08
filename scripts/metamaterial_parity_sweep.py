"""
L2-vs-L1 parity sweep: compare the homogenized effective-medium segment
(Level 2) against the explicit Helmholtz-resonator side-branch array
(Level 1) in the phase-based TMM across spacings and resonator densities.

Also includes an independent complex-impedance TMM reference solver
(standard 2x2 [P, U] transfer matrices) used to validate the stopband
location and the L1/L2 resonance shifts with a different formalism.

Run: python scripts/metamaterial_parity_sweep.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from backend.tmm_acoustics import (
    TMMInstrument,
    SPEED_OF_SOUND,
    MetamaterialSideBranch,
    MetamaterialSegment,
)

RHO = 1.2  # kg/m^3 (SI for the complex reference solver)
C = SPEED_OF_SOUND / 1000.0  # m/s


# ============================================================================
# Independent reference: complex-impedance 2x2 transfer-matrix TMM (SI units)
# ============================================================================

def hr_shunt_admittance(omega, neck_r, neck_l, cavity_v, neck_end_corr_frac=1.45):
    """Shunt admittance of a Helmholtz resonator (SI: neck r/l in m, V in m^3)."""
    s_n = math.pi * neck_r ** 2
    l_eff = neck_l + neck_end_corr_frac * neck_r
    m_ac = RHO * l_eff / s_n
    c_ac = cavity_v / (RHO * C * C)
    denom = omega * m_ac - 1.0 / (omega * c_ac)
    r_res = 0.02 * (RHO * C / s_n)  # finite-Q neck resistance
    z = r_res + 1j * denom
    return 1.0 / z


def pipe_matrix(length, radius, omega):
    """2x2 transfer matrix for a lossless cylindrical tube (SI)."""
    k = omega / C
    yc = math.pi * radius ** 2 / (RHO * C)  # characteristic admittance
    a = math.cos(k * length)
    b = 1j * math.sin(k * length) / yc
    c_ = 1j * yc * math.sin(k * length)
    d = a
    return np.array([[a, b], [c_, d]], dtype=complex)


def shunt_matrix(y_shunt):
    """Matrix for a shunt admittance in the main duct: [[1,0],[Y,1]]."""
    return np.array([[1.0, 0.0], [y_shunt, 1.0]], dtype=complex)


def matmul(*ms):
    out = np.eye(2, dtype=complex)
    for m in ms:
        out = m @ out
    return out


def tube_with_hr_array(bore_r, bore_l, n_res, spacing, neck_r, neck_l, cavity_v, f):
    """
    Input admittance of a rigid-terminated tube with N HR side branches
    spaced `spacing` apart (complex TMM, SI units). Returns Y_in at f (Hz).
    """
    omega = 2.0 * math.pi * f
    y_in = 0.0  # rigid end (infinite impedance)
    # Walk from the rigid end (bell in our convention) back to the input.
    total = bore_l
    for i in range(n_res):
        seg = spacing if i < n_res - 1 else max(total - (n_res - 1) * spacing, 0.0)
        m = pipe_matrix(seg, bore_r, omega)
        yc = math.pi * bore_r ** 2 / (RHO * C)
        # Convert y_in (input admittance seen looking toward termination)
        # through segment, then add shunt at the branch.
        # State vector [P, U]; admittance = U/P.
        z_in = 1.0 / y_in if y_in != 0 else 1e9
        p_out, u_out = 1.0, z_in
        # apply pipe
        p_in = m[0, 0] * p_out + m[0, 1] * u_out
        u_in = m[1, 0] * p_out + m[1, 1] * u_out
        y = u_in / p_in
        # add HR shunt at this junction
        y = y + hr_shunt_admittance(omega, neck_r, neck_l, cavity_v)
        y_in = y
    return y_in


def input_impedance_magnitude_db(bore_r, bore_l, n_res, spacing, neck_r, neck_l, cavity_v, freqs):
    """|Z_in| in dB for the complex-TMM reference across a frequency grid."""
    out = []
    for f in freqs:
        y = tube_with_hr_array(bore_r, bore_l, n_res, spacing, neck_r, neck_l, cavity_v, f)
        z = 1.0 / y if y != 0 else 1e12
        out.append(20.0 * math.log10(abs(z)))
    return np.array(out)


# ============================================================================
# L1 / L2 phase-TMM comparison
# ============================================================================

def bore_resonances(inst, n_registers=4):
    """Resonant frequencies (Hz) for registers 1..n, no holes."""
    out = []
    for n in range(1, n_registers + 1):
        wl = inst.find_resonance(2.0 * 600.0 / n, [], n_register=n + 1)
        out.append(inst.frequency_from_wavelength(wl))
    return out


def make_base(bore_r_mm=9.5, bore_l_mm=600.0):
    return TMMInstrument(
        inner_positions=[0, bore_l_mm],
        inner_diameters=[2 * bore_r_mm, 2 * bore_r_mm],
        outer_diameters=[22.0, 22.0],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=False,
    )


def sweep():
    print("=" * 70)
    print("L2-vs-L1 parity sweep (phase TMM, 600mm x 19mm open-open pipe)")
    print("=" * 70)
    bore_r = 9.5
    bore_l = 600.0
    neck_r = 3.0
    neck_l = 8.0

    base = make_base(bore_r, bore_l)
    base_freqs = bore_resonances(base)
    print(f"baseline resonances: {[round(f, 1) for f in base_freqs]} Hz")

    print(f"\n{'spacing':>8} {'n_res':>5} {'f0':>9} | "
          f"{'L1 shift %':>10} {'L2 shift %':>10} {'L1-f0 dev':>9} {'L2-f0 dev':>9}")
    print("-" * 70)

    results = []
    for spacing in (100.0, 50.0, 25.0, 12.5):
        n_res = max(2, int(bore_l // spacing))
        cavity_v = 4000.0
        mb = MetamaterialSideBranch(
            position_mm=spacing / 2.0, neck_radius_mm=neck_r,
            neck_length_mm=neck_l, cavity_volume_mm3=cavity_v,
        )
        f0 = mb.helmholtz_frequency()

        # L1: explicit array
        inst1 = make_base(bore_r, bore_l)
        inst1.meta_slots = [MetamaterialSideBranch(
            position_mm=i * spacing + spacing / 2.0, neck_radius_mm=neck_r,
            neck_length_mm=neck_l, cavity_volume_mm3=cavity_v,
        ) for i in range(n_res)]
        inst1._prepare_phase()
        f1 = bore_resonances(inst1)

        # L2: homogenized segment covering the array region
        seg = MetamaterialSegment(
            start_mm=0.0, end_mm=n_res * spacing,
            resonator=MetamaterialSideBranch(
                position_mm=0.0, neck_radius_mm=neck_r,
                neck_length_mm=neck_l, cavity_volume_mm3=cavity_v),
            spacing_mm=spacing,
        )
        inst2 = make_base(bore_r, bore_l)
        inst2.metamaterial_segments = [seg]
        inst2._prepare_phase()
        f2 = bore_resonances(inst2)

        # Shift of the nearest resonance to f0 (quantitative parity metric)
        shift1 = min(abs((fi - f0) / f0) for fi in f1)
        shift2 = min(abs((fi - f0) / f0) for fi in f2)
        # deviation of nearest L1/L2 resonance from f0 vs baseline's
        base_nearest = min(abs((fi - f0) / f0) for fi in base_freqs)

        results.append((spacing, n_res, f0, f1, f2, shift1, shift2, base_nearest))
        print(f"{spacing:>8.1f} {n_res:>5d} {f0:>9.1f} | "
              f"{shift1 * 100:>9.2f}% {shift2 * 100:>9.2f}% "
              f"{base_nearest * 100:>8.2f}% {shift2 / max(shift1, 1e-12):>8.2f}x")

    return results


def reference_check():
    print("\n" + "=" * 70)
    print("Independent complex-TMM reference: stopband dip at f0 (20 dB+ expected)")
    print("=" * 70)
    bore_r = 0.0095
    bore_l = 0.6
    neck_r = 0.003
    neck_l = 0.008
    cavity_v = 4000e-9
    mb = MetamaterialSideBranch(0, neck_r * 1000, neck_l * 1000, cavity_v * 1e9)
    f0 = mb.helmholtz_frequency()
    print(f"HR f0 = {f0:.1f} Hz (SI resonator: r={neck_r}m l={neck_l}m V={cavity_v*1e9:.0f}mm3)")

    for n_res in (1, 4):
        spacing = 0.1
        freqs = np.linspace(300, 2500, 220)
        zmag = input_impedance_magnitude_db(bore_r, bore_l, n_res, spacing,
                                            neck_r, neck_l, cavity_v, freqs)
        idx = int(np.argmin(np.abs(freqs - f0)))
        dip = zmag[idx]
        # deepest 20 dB below the off-resonance average
        off = np.mean(np.concatenate([zmag[:idx - 15], zmag[idx + 15:]]))
        print(f"  n_res={n_res}: |Z_in| at f0 = {dip:6.2f} dB vs off-resonance "
              f"{off:6.2f} dB -> dip {dip - off:6.2f} dB "
              f"({'PASS: >15dB stopband' if (dip - off) < -15 else 'WEAK'})")


if __name__ == "__main__":
    sweep()
    reference_check()
