"""
SymPy validation harness for the numeric TMM acoustic kernels.

What this does
--------------
The project's TMM engine (``backend/tmm_acoustics.py`` and its JAX port
``backend/tmm_acoustics_jax.py``) is a *phase-based* transfer-matrix method
ported from chalumier/demakein: instead of multiplying 2x2 matrices it walks
a scalar "reflection phase" through the bore (open end = 0.5, closed end = 0,
resonance when the phase is an integer).  The acoustic building blocks are:

  * the cylindrical-section propagation advance ``phase + 2*L/wavelength``
    (a round trip), with the Keefe visco-thermal complex propagation constant
    ``gamma`` entering as ``-Im(exp(-gamma*L))`` per segment;
  * the two-pipe (bore step) junction ``junction2_reply_phase``;
  * the three-pipe (tone-hole) junction ``junction3_reply_phase`` plus the
    hole length corrections;
  * the Keefe visco-thermal loss factor ``exp(-gamma*L)`` from
    ``backend/physics/losses.py`` (the complex-wavenumber building block).

There is no bend/corner kernel in the codebase (a Keefe-1984 BendLoss was
searched for and does not exist), so no bend test is included here.

Each kernel below is transcribed *symbolically* with SymPy from the exact
formula in the code (same constants, same unit conversions — mm and mm/s),
evaluated over a frequency sweep, and compared to the numeric implementation.
Kernels implemented with float64 (numpy/Python math) are checked at rel
~1e-9; the JAX port defaults to float32 and is checked at rel ~1e-3.

We also validate two invariants of the standard 2x2 TMM formalism that the
phase-domain kernels must be consistent with:

  * reciprocity: ``det(ABCD) == 1`` for a cylindrical section, both lossless
    (symbolically: ``cos^2 + sin^2 = 1``) and with the actual Keefe loss
    factor (numerically over the sweep);
  * the phase advance ``p + 2L/wavelength`` equals ``-arg(Gamma_L *
    e^{-2 i k L}) / (2 pi)`` of the 2x2 propagation matrix (pinning the
    ``Gamma = e^{-i 2 pi p}`` phase convention used by the code).

NOTE on the Keefe loss phase term: ``losses.py`` documents the loss factor as
``exp(-gamma*L)`` and the TMM loop adds ``-Im(exp(-gamma*L))`` as a "phase
shift".  That is NOT the phase ``arg(exp(-gamma*L)) = -Im(gamma*L)`` — the
harness validates exactly what the code computes (``-Im(exp(-gamma*L))``),
which matches the transcription to machine precision.  This is worth keeping
in mind: the implemented term is bounded in [-1, 1] and oscillates with
frequency, whereas the documented intent was the unbounded phase ``-Im(gamma*L)``.

How to extend
-------------
1. Add a new symbolic transcription helper in the "Symbolic transcriptions"
   section, mirroring the code formula line by line (constants, units, and
   order of operations included).
2. Write a test that evaluates the numeric implementation and the SymPy
   expression over :func:`_frequencies` and asserts agreement with
   :func:`_assert_close` (rel ~1e-9 for float64, ~1e-3 for float32/JAX).
3. For an end-to-end check of a new instrument topology, build a
   ``TMMInstrument`` and compare ``resonance_phase`` against
   :func:`_sym_resonance_phase`, which transcribes the whole action chain.

The module is skipped cleanly when SymPy is not installed.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

# Make the project importable even when the file is run standalone
# (pytest normally gets the paths from tests/conftest.py).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import sympy as sp
except ImportError:  # pragma: no cover
    sp = None

from backend.tmm_acoustics import (  # noqa: E402
    SPEED_OF_SOUND,
    Hole,
    TMMInstrument,
    end_flange_length_correction,
    hole_length_correction,
    junction2_reply_phase,
    junction3_reply_phase,
    pipe_reply_phase,
    pipe_reply_phase_with_loss,
)
from backend.physics.losses import KeefeLoss  # noqa: E402

pytestmark = pytest.mark.skipif(sp is None, reason="sympy is required")

# ---------------------------------------------------------------------------
# Constants transcribed from the code (units: mm, mm/s)
# ---------------------------------------------------------------------------

# backend/tmm_acoustics.py
# _C_MM_S = SPEED_OF_SOUND  (346100.0 mm/s)

# backend/physics/losses.py -- KeefeLoss at 20 degC (default temperature,
# where the Sutherland/temperature corrections are exactly identity).
RHO = 1.204          # kg/m^3
ETA = 1.846e-5       # Pa*s
KAPPA = 0.02624      # W/(m*K)
CP = 1005.0          # J/(kg*K)
GAMMA = 1.4          # ratio of specific heats
C_BOUNDARY_MM_S = 346100.0  # c used inside KeefeLoss._boundary_layers (matches global SPEED_OF_SOUND)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _frequencies(n=40, fmin=50.0, fmax=4000.0):
    """Frequency sweep used by every kernel test (Hz)."""
    return np.linspace(fmin, fmax, n)


def _assert_close(numeric, symbolic, rtol=1e-9, atol=1e-12, label=""):
    """Assert a numeric value matches its symbolic transcription.

    Uses numpy (handles complex scalars); both float64 and SymPy are ~1e-15
    precise for identical formulas, so the tolerances are deliberately loose.
    """
    np.testing.assert_allclose(
        numeric, symbolic, rtol=rtol, atol=atol,
        err_msg=f"{label} numeric={numeric!r} symbolic={symbolic!r}",
    )


def _wrap_phase(p):
    """Map a phase onto (-0.5, 0.5] (phase-domain equivalent of wrapping)."""
    return ((p + 0.5) % 1.0) - 0.5


# ---------------------------------------------------------------------------
# Symbolic transcriptions (same formulas, constants and units as the code)
# ---------------------------------------------------------------------------

_lam = sp.Symbol("lambda", positive=True) if sp is not None else None
_r = sp.Symbol("r", positive=True) if sp is not None else None
_L = sp.Symbol("L", positive=True) if sp is not None else None


def _keefe_gamma_expr():
    """Complex propagation constant gamma from KeefeLoss (units: 1/mm).

    Transcribed from backend/physics/losses.py `_boundary_layers` +
    `bore_loss`::

        lam_m   = wavelength * 1e-3            # mm -> m
        f       = 346100.0 / lam_m             # Hz (c = 346.1 m/s, matches global SPEED_OF_SOUND)
        omega   = 2*pi*f
        delta_v = sqrt(2*ETA/(RHO*omega))*1000 # m -> mm
        delta_t = sqrt(2*KAPPA/(RHO*CP*omega))*1000
        eps_v   = delta_v / r
        eps_t   = delta_t / r
        gamma   = (2*pi/lambda)*(1 + (1+I)/sqrt(2)*((GAMMA-1)*eps_t + eps_v))
    """
    lam_m = _lam * 1e-3
    f_boundary = C_BOUNDARY_MM_S / lam_m
    omega = 2 * sp.pi * f_boundary
    delta_v = sp.sqrt(2 * ETA / (RHO * omega)) * 1000.0
    delta_t = sp.sqrt(2 * KAPPA / (RHO * CP * omega)) * 1000.0
    eps_v = delta_v / _r
    eps_t = delta_t / _r
    omega_over_c = 2 * sp.pi / _lam
    factor = (1 + sp.I) / sp.sqrt(2) * ((GAMMA - 1) * eps_t + eps_v)
    return omega_over_c * (1 + factor)


def _keefe_loss_factor(wavelength, radius, length):
    """Complex loss factor exp(-gamma*L) evaluated at (wl, r, L)."""
    expr = sp.exp(-_keefe_gamma_expr() * _L)
    return complex(expr.evalf(subs={_lam: wavelength, _r: radius, _L: length}))


def _sym_pipe_phase(phase, length, wavelength):
    """Phase advance of a cylindrical section: phase + 2*L/wavelength."""
    return sp.N(phase + 2.0 * length / wavelength)


def _sym_pipe_loss_phase_shift(length, radius, wavelength):
    """-Im(exp(-gamma*L)) -- the phase term the TMM loop actually adds."""
    lf = _keefe_loss_factor(wavelength, radius, length)
    return -lf.imag


def _sym_tanpi(x):
    """tan(pi*x) as in the code's `tanner()`, evaluated symbolically.

    SymPy returns the exact symbolic ``zoo`` at a pole (e.g. x = 1/2) where
    the float64 implementation returns a large finite float; mirror float64
    in that measure-zero case so numeric and symbolic always agree.
    """
    val = sp.N(sp.tan(sp.pi * x))
    if val.is_finite:
        return val
    return sp.Float(math.tan(math.pi * float(x)))


def _sym_junction2(a0, a1, p1):
    """junction2_reply_phase transcribed:
    atan(a1/a0*tan(pi*(p1-shift)))/pi + shift, shift = floor(p1 + 0.5).
    """
    p1 = sp.Float(p1)
    shift = sp.floor(p1 + sp.Rational(1, 2))
    return sp.N(sp.atan(a1 / a0 * _sym_tanpi(p1 - shift)) / sp.pi + shift)


def _sym_junction3(a0, a1, a2, p1, p2):
    """junction3_reply_phase (tone-hole 3-pipe junction) transcribed."""
    p1 = sp.Float(p1)
    p2 = sp.Float(p2)
    s1 = sp.floor(p1 + sp.Rational(1, 2))
    s2 = sp.floor(p2 + sp.Rational(1, 2))
    combo = a1 / a0 * _sym_tanpi(p1 - s1) + a2 / a0 * _sym_tanpi(p2 - s2)
    return sp.N(sp.atan(combo) / sp.pi + s1 + s2)


def _sym_resonance_phase(actions, wavelength, fingerings, closed_top, with_loss=False):
    """Transcribe TMMInstrument.resonance_phase over its whole action chain."""
    phase = sp.Rational(1, 2)  # open-end reflection phase
    for action in actions:
        if action[0] == "pipe":
            _, seg_length, seg_diameter = action
            phase = _sym_pipe_phase(phase, seg_length, wavelength)
            if with_loss:
                phase = sp.N(phase + _sym_pipe_loss_phase_shift(
                    seg_length, seg_diameter / 2.0, wavelength))
        elif action[0] == "junction2":
            _, area_a, area_b = action
            phase = _sym_junction2(area_a, area_b, phase)
        elif action[0] == "hole":
            _, hole_idx, area_bore, hole_area, open_length, closed_length = action
            if fingerings[hole_idx] == Hole.OPEN:
                hole_phase = _sym_pipe_phase(sp.Rational(-1, 2), open_length, wavelength)
            else:
                hole_phase = _sym_pipe_phase(sp.Integer(0), closed_length, wavelength)
            phase = _sym_junction3(area_bore, area_bore, hole_area, phase, hole_phase)
    if not closed_top:
        phase = sp.N(phase + sp.Rational(1, 2))
    return float(phase)


def _uniform_instrument(length, diameter, holes=(), closed_top=False, loss_model=None):
    """A uniform cylindrical TMMInstrument with optional tone holes."""
    hole_positions, hole_diameters, hole_lengths = holes or ([], [], [])
    return TMMInstrument(
        inner_positions=[0.0, length],
        inner_diameters=[diameter, diameter],
        outer_diameters=[22.0, 22.0],
        hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        hole_lengths=hole_lengths,
        closed_top=closed_top,
        loss_model=loss_model,
    )


# ---------------------------------------------------------------------------
# Kernel 1: Keefe visco-thermal loss factor exp(-gamma*L)
# ---------------------------------------------------------------------------

def test_keefe_bore_loss_factor_matches_symbolic():
    loss = KeefeLoss()
    length, radius = 150.0, 7.5
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        _assert_close(
            loss.bore_loss(length, radius, wl),
            _keefe_loss_factor(wl, radius, length),
            label=f"bore_loss f={f:.1f}",
        )


def test_keefe_hole_loss_factor_matches_symbolic():
    loss = KeefeLoss()
    hole_length, hole_radius = 3.0, 3.5
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        _assert_close(
            loss.hole_loss(hole_radius, hole_length, wl),
            _keefe_loss_factor(wl, hole_radius, hole_length),
            label=f"hole_loss f={f:.1f}",
        )


# ---------------------------------------------------------------------------
# Kernel 2: cylindrical-section propagation (phase advance)
# ---------------------------------------------------------------------------

def test_pipe_propagation_phase_advance_lossless():
    for length in (50.0, 150.0, 300.0):
        for f in _frequencies():
            wl = SPEED_OF_SOUND / f
            numeric = pipe_reply_phase(0.5, length / wl)
            symbolic = float(_sym_pipe_phase(sp.Rational(1, 2), length, wl))
            _assert_close(numeric, symbolic, label=f"pipe L={length} f={f:.1f}")


def test_pipe_propagation_phase_with_keefe_loss():
    loss = KeefeLoss()
    phase0, length, radius = 0.5, 150.0, 7.5
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        numeric = pipe_reply_phase_with_loss(phase0, length, radius, wl, loss)
        symbolic = (float(_sym_pipe_phase(sp.Rational(1, 2), length, wl))
                    + _sym_pipe_loss_phase_shift(length, radius, wl))
        _assert_close(numeric, symbolic, label=f"pipe+loss f={f:.1f}")


def test_lossless_pipe_consistent_with_2x2_propagation_matrix():
    """The phase advance must equal the round-trip reflection phase of the
    standard 2x2 propagation matrix [[cos, i sin], [i sin, cos]].

    With the code's convention Gamma = e^{-i 2 pi p} (open end p=0.5 -> -1),
    the input reflection is Gamma_in = Gamma_L * e^{-2 i k L} and the phase
    advance p + 2L/wavelength must equal -arg(Gamma_in)/(2 pi).
    """
    length = 150.0
    p_load = 0.5
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        k = 2 * np.pi / wl
        gamma_load = np.exp(-1j * 2 * np.pi * p_load)
        gamma_in = gamma_load * np.exp(-2j * k * length)
        p_from_matrix = -np.angle(gamma_in) / (2 * np.pi)
        p_from_code = _wrap_phase(pipe_reply_phase(p_load, length / wl))
        _assert_close(p_from_code, p_from_matrix, rtol=1e-12, atol=1e-12,
                      label=f"2x2 pipe f={f:.1f}")


# ---------------------------------------------------------------------------
# Kernel 3: two-pipe junction (bore step)
# ---------------------------------------------------------------------------

def test_junction2_matches_symbolic():
    a0 = 283.0  # mm^2
    for a1 in (50.0, 141.5, 283.0, 500.0):
        for p1 in np.linspace(-1.4, 1.4, 25):
            _assert_close(
                junction2_reply_phase(a0, a1, float(p1)),
                float(_sym_junction2(a0, a1, float(p1))),
                rtol=1e-12, atol=1e-12,
                label=f"junction2 a1={a1} p1={p1:.4f}",
            )


# ---------------------------------------------------------------------------
# Kernel 4: tone-hole shunt (three-pipe junction)
# ---------------------------------------------------------------------------

def test_junction3_tonehole_shunt_matches_symbolic():
    a_bore = 283.0
    for a_hole in (5.0, 50.0, 200.0):
        for p1 in np.linspace(-0.9, 0.9, 13):
            for p2 in np.linspace(-0.5, 0.5, 7):
                _assert_close(
                    junction3_reply_phase(a_bore, a_bore, a_hole, float(p1), float(p2)),
                    float(_sym_junction3(a_bore, a_bore, a_hole, float(p1), float(p2))),
                    rtol=1e-12, atol=1e-12,
                    label=f"junction3 ah={a_hole} p1={p1:.4f} p2={p2:.4f}",
                )


def test_tonehole_length_correction_matches_symbolic():
    for hole_dia in (5.0, 7.0, 9.0):
        for bore_dia in (14.5, 19.0):
            a = hole_dia / 2.0
            symbolic_open = a * ((1.3 - 0.9 * hole_dia / bore_dia) + 0.7)
            _assert_close(hole_length_correction(hole_dia, bore_dia, False),
                          symbolic_open, label=f"hole corr hd={hole_dia}")
            assert hole_length_correction(hole_dia, bore_dia, True) == 0.0


def test_end_flange_length_correction_matches_symbolic():
    for outer, inner in ((22.0, 19.0), (22.0, 14.5), (24.0, 8.0)):
        a = inner / 2.0
        w = (outer - inner) / 2.0
        symbolic = a * (0.821 - 0.13 * (0.42 + w / a) ** (-0.54))
        _assert_close(end_flange_length_correction(outer, inner), symbolic,
                      label=f"end flange od={outer} id={inner}")


# ---------------------------------------------------------------------------
# End-to-end: full action chain vs symbolic transcription
# ---------------------------------------------------------------------------

def test_resonance_phase_chain_open_pipe():
    inst = _uniform_instrument(500.0, 19.0)
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        _assert_close(
            inst.resonance_phase(wl, []),
            _sym_resonance_phase(inst.actions, wl, [], inst.closed_top),
            rtol=1e-12, atol=1e-12, label=f"open pipe f={f:.1f}",
        )


def test_resonance_phase_chain_closed_pipe():
    inst = _uniform_instrument(500.0, 19.0, closed_top=True)
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        _assert_close(
            inst.resonance_phase(wl, []),
            _sym_resonance_phase(inst.actions, wl, [], inst.closed_top),
            rtol=1e-12, atol=1e-12, label=f"closed pipe f={f:.1f}",
        )


def test_resonance_phase_chain_tonehole():
    inst = _uniform_instrument(500.0, 19.0, holes=([250.0], [8.0], [3.0]))
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        for fingering in ([Hole.OPEN], [Hole.CLOSED]):
            _assert_close(
                inst.resonance_phase(wl, fingering),
                _sym_resonance_phase(inst.actions, wl, fingering, inst.closed_top),
                rtol=1e-12, atol=1e-12,
                label=f"tonehole {fingering} f={f:.1f}",
            )


def test_resonance_phase_chain_stepped_bore():
    # A 0.4 mm diameter step is below cone_step so the stepped profile keeps a
    # single junction2 action in the chain.
    inst = TMMInstrument(
        inner_positions=[0.0, 250.0, 500.0],
        inner_diameters=[19.0, 19.0, 18.6],
        outer_diameters=[22.0, 22.0, 22.0],
        hole_positions=[], hole_diameters=[], hole_lengths=[],
        closed_top=False,
    )
    assert any(a[0] == "junction2" for a in inst.actions)
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        _assert_close(
            inst.resonance_phase(wl, []),
            _sym_resonance_phase(inst.actions, wl, [], inst.closed_top),
            rtol=1e-12, atol=1e-12, label=f"stepped bore f={f:.1f}",
        )


def test_resonance_phase_chain_with_keefe_loss():
    inst = _uniform_instrument(
        500.0, 19.0, holes=([250.0], [8.0], [3.0]), loss_model=KeefeLoss())
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        _assert_close(
            inst.resonance_phase(wl, [Hole.OPEN]),
            _sym_resonance_phase(inst.actions, wl, [Hole.OPEN], inst.closed_top,
                                 with_loss=True),
            rtol=1e-9, atol=1e-12, label=f"keefe chain f={f:.1f}",
        )


# ---------------------------------------------------------------------------
# Reciprocity invariants of the 2x2 propagation matrix
# ---------------------------------------------------------------------------

def test_lossless_section_reciprocity_symbolic():
    """det(ABCD) == 1 for a lossless cylindrical section (cos^2 + sin^2 = 1)."""
    theta = sp.symbols("theta", real=True)
    M = sp.Matrix([
        [sp.cos(theta), sp.I * sp.sin(theta)],
        [sp.I * sp.sin(theta), sp.cos(theta)],
    ])
    assert sp.simplify(M.det() - 1) == 0


def test_lossy_section_reciprocity_symbolic():
    """det(ABCD) == 1 for a reciprocal two-port with propagation constant
    Gamma and characteristic impedance Zc (cosh^2 - sinh^2 = 1)."""
    Gamma = sp.Symbol("Gamma")
    Zc = sp.Symbol("Zc", positive=True)
    length = sp.Symbol("length", positive=True)
    M = sp.Matrix([
        [sp.cosh(Gamma * length), Zc * sp.sinh(Gamma * length)],
        [sp.sinh(Gamma * length) / Zc, sp.cosh(Gamma * length)],
    ])
    assert sp.simplify(M.det() - 1) == 0


def test_keefe_lossy_section_reciprocity_numeric():
    """det(ABCD) ~= 1 built from the actual Keefe propagation constant."""
    loss = KeefeLoss()
    length, radius = 150.0, 7.5
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        lf = loss.bore_loss(length, radius, wl)
        gamma = -np.log(lf) / length  # complex propagation constant (1/mm)
        M = np.array([
            [np.cosh(gamma * length), np.sinh(gamma * length)],
            [np.sinh(gamma * length), np.cosh(gamma * length)],
        ], dtype=complex)
        det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
        _assert_close(det, 1.0, rtol=0.0, atol=1e-6, label=f"det-1 f={f:.1f}")


# ---------------------------------------------------------------------------
# JAX port (float32 -> looser tolerance)
# ---------------------------------------------------------------------------

def test_jax_pipe_propagation_matches_symbolic():
    jax = pytest.importorskip("jax")
    import jax.numpy as jnp  # noqa: F401

    from backend.tmm_acoustics_jax import (  # noqa: E402
        _build_phase_function,
        build_action_chain_v2,
        end_flange_length_correction,
    )

    length, diameter, outer = 500.0, 19.0, 22.0
    radius = diameter / 2.0
    chain = build_action_chain_v2(
        jnp.array([0.0, length]), jnp.array([radius, radius]), outer,
        jnp.array([]), jnp.array([]), jnp.array([]), False)
    resonance_phase = _build_phase_function(chain)
    bore_radii = jnp.array([radius, radius])
    fs_pad = jnp.zeros(25)

    # Chain for a hole-less open pipe: init phase 0.5, one pipe segment of
    # length L + end_correction, final +0.5 for the open far end.
    end_corr = float(end_flange_length_correction(outer, diameter))
    for f in _frequencies():
        wl = SPEED_OF_SOUND / f
        jax_val = float(resonance_phase(jnp.float32(wl), bore_radii, fs_pad))
        expected = 1.0 + 2.0 * (length + end_corr) / wl
        _assert_close(jax_val, expected, rtol=1e-3, atol=1e-3,
                      label=f"jax pipe f={f:.1f}")
