"""
JAX-autodiff version of the Helmholtz shunt element, for use in the
project's existing JAX optimizer branch.

STATUS: UNTESTED IN THIS SANDBOX. jax isn't installed here and this
sandbox has no network access to install it. This mirrors
metamaterial_elements.helmholtz_shunt_matrix line-for-line (same
formulas, same variable names), which HAS been tested -- so translation
risk is low, but run this yourself before trusting it.

Why this matters for your project specifically: your JAX branch's known
limitation is that it can't differentiate with respect to hole positions/
diameters because they're baked into a static action chain at trace
time. A resonator defined purely algebraically like this (no Python-level
branching on the frequency array, no scipy calls) traces cleanly and
IS differentiable end-to-end with respect to every geometric parameter
passed in -- V, neck_length, neck_radius all become ordinary JAX
tracers. Use jax.grad / jax.value_and_grad directly instead of finite
differences, which should sidestep the PAVA-plateau and slow-serial-
finite-difference issues from your two_phase_optimizer work.
"""

import jax.numpy as jnp
from jax import grad, jit, value_and_grad

RHO0 = 1.2039
C0 = 343.26
MU = 1.8e-5


def helmholtz_shunt_matrix_jax(f, V, neck_length, neck_radius, flanged=True):
    """Same physics as metamaterial_elements.helmholtz_shunt_matrix, but
    written for jax.numpy so it's traceable/differentiable. f is expected
    to be a jnp array; V, neck_length, neck_radius can be jnp scalars
    (the parameters you'll want gradients with respect to)."""
    omega = 2 * jnp.pi * f
    S_neck = jnp.pi * neck_radius**2

    corr = jnp.where(flanged, 0.85 * neck_radius, 0.61 * neck_radius)
    l_eff = neck_length + 2 * corr

    M_a = RHO0 * l_eff / S_neck
    C_a = V / (RHO0 * C0**2)

    k = omega / C0
    R_rad = RHO0 * C0 * (k * neck_radius)**2 / 2.0
    R_visc = neck_length / S_neck * jnp.sqrt(2 * MU * omega * RHO0) / neck_radius
    R = R_rad + R_visc

    Z_shunt = R + 1j * omega * M_a - 1j / (omega * C_a)

    A = jnp.ones_like(f, dtype=complex)
    B = jnp.zeros_like(f, dtype=complex)
    C = 1.0 / Z_shunt
    D = jnp.ones_like(f, dtype=complex)
    return jnp.stack([jnp.stack([A, B], axis=-1),
                       jnp.stack([C, D], axis=-1)], axis=-2)


def reactance_at_target(V, neck_length, neck_radius, f_target):
    """Loss target: reactance (imag part of shunt impedance) should cross
    zero at f_target -- the standard smooth-and-differentiable stand-in
    for 'the resonance peak sits at f_target', avoiding a non-
    differentiable argmax/peak-search inside the loss."""
    f = jnp.array([f_target])
    omega = 2 * jnp.pi * f
    S_neck = jnp.pi * neck_radius**2
    l_eff = neck_length + 2 * 0.85 * neck_radius
    M_a = RHO0 * l_eff / S_neck
    C_a = V / (RHO0 * C0**2)
    X = omega * M_a - 1.0 / (omega * C_a)
    return jnp.sum(X**2)


# Example usage (run in an environment with jax installed):
#
#   from jax import value_and_grad
#   import jax.numpy as jnp
#
#   loss_fn = lambda params: reactance_at_target(params[0], params[1], params[2], 1000.0)
#   params = jnp.array([3e-6, 0.015, 0.0025])  # V, neck_length, neck_radius
#   loss, grads = value_and_grad(loss_fn)(params)
#   # grads is now the analytic gradient of the resonance-matching loss
#   # w.r.t. (V, neck_length, neck_radius) -- feed straight into your
#   # existing L-BFGS-B / scipy.optimize.minimize call with jac=True,
#   # or use optax for a pure-JAX training loop.
#
# For a multi-element chain (several resonators + bore segments), the
# same pattern extends: write the whole chain multiplication in
# jax.numpy (jnp.matmul / the @ operator both trace fine), and jax.grad
# will differentiate through the ENTIRE chain automatically -- true
# adjoint-equivalent gradients, no finite differences, no PAVA plateau.
