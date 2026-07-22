"""
JAX-differentiable Transfer Matrix Method (TMM) acoustics — V2 Vectorized.

Performance features:
  - lax.scan for action loop (no Python for-loop)
  - jax.vmap to batch all fingering searches in parallel
  - @jax.jit compiled via closure (chain arrays captured as constants)
"""

import jax
import jax.numpy as jnp
from jax import lax
from typing import List

SPEED_OF_SOUND = 346100.0

MAX_ACTIONS = 128
MAX_HOLES = 24

_ACT_PIPE = 0
_ACT_JUNCTION2 = 1
_ACT_HOLE = 2


def _tanner(x):
    return jnp.tan(x * jnp.pi)

def _untanner(x):
    return jnp.arctan(x) / jnp.pi


def end_flange_length_correction(outer_diameter: float, inner_diameter: float) -> float:
    a = inner_diameter / 2.0
    w = (outer_diameter - inner_diameter) / 2.0
    return a * (0.821 - 0.13 * (0.42 + w / a) ** (-0.54))


def hole_length_correction(hole_diameter: float, bore_diameter: float, closed: bool) -> float:
    if closed:
        return 0.0
    a = hole_diameter / 2.0
    return a * ((1.3 - 0.9 * hole_diameter / bore_diameter) + 0.7)


# ============================================================================
# Vectorized action chain
# ============================================================================

def build_action_chain_v2(bore_positions, bore_radii_template, outer_diameter,
                          hole_positions, hole_diameters, hole_lengths, closed_top) -> dict:
    n_bore = len(bore_positions)
    length = bore_positions[-1]
    template_diameters = [r * 2.0 for r in bore_radii_template]
    end_correction = end_flange_length_correction(outer_diameter, template_diameters[0])

    events = []
    for i in range(1, n_bore - 1):
        events.append((bore_positions[i], 'step', i))
    for i, pos in enumerate(hole_positions):
        events.append((pos, 'hole', i))
    events.append((length, 'end', 0))
    events.sort(key=lambda e: e[0])

    at = jnp.zeros(MAX_ACTIONS, dtype=jnp.int32)
    pl = jnp.zeros(MAX_ACTIONS)
    ji0 = jnp.zeros(MAX_ACTIONS, dtype=jnp.int32)
    ji1 = jnp.zeros(MAX_ACTIONS, dtype=jnp.int32)
    hi = jnp.zeros(MAX_ACTIONS, dtype=jnp.int32)
    ha = jnp.zeros(MAX_ACTIONS)
    hol = jnp.zeros(MAX_ACTIONS)
    hcl = jnp.zeros(MAX_ACTIONS)
    hbi = jnp.zeros(MAX_ACTIONS, dtype=jnp.int32)

    position = -end_correction
    current_bore_idx = 0
    ac = 0

    for pos, descriptor, index in events:
        seg_length = pos - position
        position = pos
        if seg_length > 0:
            at = at.at[ac].set(_ACT_PIPE)
            pl = pl.at[ac].set(seg_length)
            ac += 1
        if descriptor == 'step':
            at = at.at[ac].set(_ACT_JUNCTION2)
            ji0 = ji0.at[ac].set(current_bore_idx)
            ji1 = ji1.at[ac].set(index)
            current_bore_idx = index
            ac += 1
        elif descriptor == 'hole':
            bore_dia = template_diameters[current_bore_idx]
            hole_dia = hole_diameters[index]
            true_len = hole_lengths[index]
            open_len = true_len + hole_length_correction(hole_dia, bore_dia, False)
            closed_len = true_len + hole_length_correction(hole_dia, bore_dia, True)
            hole_area_val = jnp.pi * (hole_dia / 2.0) ** 2
            at = at.at[ac].set(_ACT_HOLE)
            hi = hi.at[ac].set(index)
            ha = ha.at[ac].set(hole_area_val)
            hol = hol.at[ac].set(open_len)
            hcl = hcl.at[ac].set(closed_len)
            hbi = hbi.at[ac].set(current_bore_idx)
            ac += 1

    # Return only JAX arrays (n_actions is a Python int, handled separately)
    return {
        'act_types': at,
        'act_pipe_length': pl,
        'act_junc_idx0': ji0,
        'act_junc_idx1': ji1,
        'act_hole_idx': hi,
        'act_hole_area': ha,
        'act_hole_open_len': hol,
        'act_hole_closed_len': hcl,
        'act_hole_bore_idx': hbi,
        'n_actions': ac,  # Python int — used as static
        'closed_top': closed_top,  # Python bool — used as static
    }


# ============================================================================
# JIT-compiled cost function builder
# ============================================================================

def _build_phase_function(chain):
    """Build the resonance phase function shared by all cost functions."""
    n_actions = chain['n_actions']
    closed_top = chain['closed_top']

    c_at = chain['act_types']
    c_pl = chain['act_pipe_length']
    c_ji0 = chain['act_junc_idx0']
    c_ji1 = chain['act_junc_idx1']
    c_hi = chain['act_hole_idx']
    c_ha = chain['act_hole_area']
    c_hol = chain['act_hole_open_len']
    c_hcl = chain['act_hole_closed_len']
    c_hbi = chain['act_hole_bore_idx']

    def resonance_phase(wavelength, bore_radii, fs_pad):
        def scan_step(phase, i):
            act = c_at[i]
            pp = phase + c_pl[i] / wavelength * 2.0
            a0 = jnp.pi * bore_radii[c_ji0[i]] ** 2
            a1 = jnp.pi * bore_radii[c_ji1[i]] ** 2
            sh = jnp.floor(phase + 0.5)
            pj = _untanner(a1 / a0 * _tanner(phase - sh)) + sh
            pad_idx = jnp.minimum(c_hi[i], MAX_HOLES)
            is_open = fs_pad[pad_idx]
            ab = jnp.pi * bore_radii[c_hbi[i]] ** 2
            oph = -0.5 + c_hol[i] / wavelength * 2.0
            cph = 0.0 + c_hcl[i] / wavelength * 2.0
            hph = jnp.where(is_open > 0, oph, cph)
            s1 = jnp.floor(phase + 0.5)
            s2 = jnp.floor(hph + 0.5)
            ph = _untanner(
                _tanner(phase - s1) + c_ha[i] / ab * _tanner(hph - s2)
            ) + s1 + s2
            new_phase = jnp.where(act == 0, pp, jnp.where(act == 1, pj, ph))
            return new_phase, None

        phase, _ = lax.scan(scan_step, jnp.array(0.5), jnp.arange(n_actions))
        return phase + jnp.where(closed_top, 0.0, 0.5)

    return resonance_phase


def _find_resonance_bisect(resonance_phase, wl_near, bore_radii, fs_pad):
    """Root-finding via expanding-window + bisection (for forward evaluation only)."""
    step_cents = 2.0
    step = 2.0 ** (step_cents / 1200.0)
    step_increase = 1.05
    hs = jnp.sqrt(step)

    def scorer(w):
        p = resonance_phase(w, bore_radii, fs_pad)
        return ((p + 0.5) % 1.0) - 0.5

    w_left = wl_near / hs
    w_right = wl_near * hs
    s_left = scorer(w_left)
    s_right = scorer(w_right)

    def expand_step(carry, _):
        w_l, w_r, s_l, s_r, cur_step, found_any = carry
        found = (s_l >= 0.0) & (s_r < 0.0)
        new_wl = w_l / cur_step
        new_sl = scorer(new_wl)
        found_left = (new_sl >= 0.0) & (s_l < 0.0)
        new_wr = w_r * cur_step
        new_sr = scorer(new_wr)
        found_right = (s_r >= 0.0) & (new_sr < 0.0)
        new_w_left = jnp.where(found | found_left | found_any, w_l, new_wl)
        new_s_left = jnp.where(found | found_left | found_any, s_l, new_sl)
        new_w_right = jnp.where(found | found_right | found_any, w_r, new_wr)
        new_s_right = jnp.where(found | found_right | found_any, s_r, new_sr)
        new_found = found_any | found | found_left | found_right
        return (new_w_left, new_w_right, new_s_left, new_s_right,
                cur_step * step_increase, new_found), None

    init_carry = (w_left, w_right, s_left, s_right, step, jnp.array(False))
    (wl, wr, sl, sr, _, _), _ = lax.scan(expand_step, init_carry, None, length=8)

    def bisect_step(carry, _):
        w_l, w_r, s_l, s_r = carry
        w_mid = 0.5 * (w_l + w_r)
        s_mid = scorer(w_mid)
        new_w_l = jnp.where(s_mid >= 0, w_mid, w_l)
        new_s_l = jnp.where(s_mid >= 0, s_mid, s_l)
        new_w_r = jnp.where(s_mid >= 0, w_r, w_mid)
        new_s_r = jnp.where(s_mid >= 0, s_r, s_mid)
        return (new_w_l, new_w_r, new_s_l, new_s_r), None

    (wl, wr, sl, sr), _ = lax.scan(bisect_step, (wl, wr, sl, sr), None, length=10)
    m = (sr - sl) / (wr - wl)
    result = jnp.where(jnp.abs(m) < 1e-30, 0.5 * (wl + wr), wl - sl / m)
    best_wl = jnp.where(jnp.abs(s_left) < jnp.abs(s_right), w_left, w_right)
    return jnp.where(jnp.abs(result) < 1e-10, best_wl, result)


def make_phase_cost(chain, target_freqs, fingering_sets, target_wavelengths):
    """
    Build a JIT-compiled cost function using direct phase evaluation.

    Instead of finding resonances via root-finding (which creates gradient
    discontinuities), evaluates the phase at target wavelengths directly.
    At resonance, phase(wl_target) = integer, so minimizing the phase
    deviation from the nearest integer minimizes intonation error.

    This gives a smooth, differentiable cost function with accurate gradients.
    """
    n = len(fingering_sets)
    resonance_phase = _build_phase_function(chain)

    fs_padded = jnp.zeros((n, MAX_HOLES + 1))
    for i, fs in enumerate(fingering_sets):
        fs_padded = fs_padded.at[i, :len(fs)].set(fs)

    tw = jnp.array(target_wavelengths)

    @jax.jit
    def cost_fn(bore_radii):
        def _phase_err(args):
            wl, fs_p = args
            phase = resonance_phase(wl, bore_radii, fs_p)
            return phase - jnp.round(phase)

        phase_errs = jax.vmap(_phase_err)((tw, fs_padded))
        return jnp.sqrt(jnp.mean(phase_errs ** 2))

    return cost_fn


def make_rms_cost(chain, target_freqs, fingering_sets, target_wavelengths):
    """
    Build a JIT-compiled RMS cost function using direct phase evaluation.

    Evaluates phase at target wavelengths and minimizes deviation from integers.
    This gives a smooth, differentiable cost function with good gradients
    for local optimization. Use make_rms_cost_with_search() for accurate
    forward evaluation with root-finding (for verification, not optimization).
    """
    n = len(fingering_sets)
    resonance_phase = _build_phase_function(chain)

    fs_padded = jnp.zeros((n, MAX_HOLES + 1))
    for i, fs in enumerate(fingering_sets):
        fs_padded = fs_padded.at[i, :len(fs)].set(fs)

    tw = jnp.array(target_wavelengths)

    @jax.jit
    def cost_fn(bore_radii):
        def _phase_err(args):
            wl, fs_p = args
            phase = resonance_phase(wl, bore_radii, fs_p)
            return phase - jnp.round(phase)

        phase_errs = jax.vmap(_phase_err)((tw, fs_padded))
        corrected = phase_errs - jnp.mean(phase_errs)
        return jnp.sqrt(jnp.mean(corrected ** 2))

    return cost_fn


def make_rms_cost_with_search(chain, target_freqs, fingering_sets, target_wavelengths):
    """
    RMS cost with root-finding (for forward evaluation only, NOT for optimization).
    Kept for backward compatibility and post-optimization verification.
    """
    n = len(fingering_sets)
    resonance_phase = _build_phase_function(chain)

    fs_padded = jnp.zeros((n, MAX_HOLES + 1))
    for i, fs in enumerate(fingering_sets):
        fs_padded = fs_padded.at[i, :len(fs)].set(fs)

    tf = jnp.array(target_freqs)
    tw = jnp.array(target_wavelengths)

    @jax.jit
    def cost_fn(bore_radii):
        def _cost_single(args):
            wl_near, fs_p = args
            return _find_resonance_bisect(resonance_phase, wl_near, bore_radii, fs_p)
        resonant_wls = jax.vmap(_cost_single)((tw, fs_padded))
        actual_freqs = SPEED_OF_SOUND / resonant_wls
        cents = 1200.0 * jnp.log2(actual_freqs / tf)
        corrected = cents - jnp.mean(cents)
        return jnp.sqrt(jnp.mean(corrected ** 2))

    return cost_fn


def make_intonation_profile_cost(chain, target_freqs, fingering_sets, target_wavelengths):
    """Build intonation profile cost function using direct phase evaluation."""
    n = len(fingering_sets)
    resonance_phase = _build_phase_function(chain)

    fs_padded = jnp.zeros((n, MAX_HOLES + 1))
    for i, fs in enumerate(fingering_sets):
        fs_padded = fs_padded.at[i, :len(fs)].set(fs)

    tw = jnp.array(target_wavelengths)

    @jax.jit
    def cost_fn(bore_radii):
        def _phase_err(args):
            wl, fs_p = args
            phase = resonance_phase(wl, bore_radii, fs_p)
            return phase - jnp.round(phase)

        phase_errs = jax.vmap(_phase_err)((tw, fs_padded))
        return jnp.sqrt(jnp.mean(phase_errs ** 2))

    return cost_fn


# Backward-compatible API
def rms_cost_v2(bore_radii, chain, target_freqs, fingering_sets, target_wavelengths, n_register=1):
    cost_fn = make_rms_cost(chain, target_freqs, fingering_sets, target_wavelengths)
    return cost_fn(bore_radii)

def intonation_profile_cost_v2(bore_radii, chain, target_freqs, fingering_sets, target_wavelengths, n_register=1):
    cost_fn = make_intonation_profile_cost(chain, target_freqs, fingering_sets, target_wavelengths)
    return cost_fn(bore_radii)

def multi_objective_cost_v2(bore_radii, chain, target_freqs, fingering_sets, target_wavelengths,
                            n_register=1, intonation_weight=1.0, playability_weight=0.3):
    intonation = rms_cost_v2(bore_radii, chain, target_freqs, fingering_sets, target_wavelengths)
    radii_diff = bore_radii[1:] - bore_radii[:-1]
    return intonation_weight * intonation + playability_weight * (jnp.mean(radii_diff**2) + 0.1*jnp.mean((bore_radii-7.25)**2))

build_action_chain = build_action_chain_v2
rms_cost_jax = rms_cost_v2
intonation_profile_cost_jax = intonation_profile_cost_v2
multi_objective_cost_jax = multi_objective_cost_v2
