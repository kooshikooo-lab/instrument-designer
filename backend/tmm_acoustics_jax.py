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

def make_rms_cost(chain, target_freqs, fingering_sets, target_wavelengths):
    """
    Build a JIT-compiled RMS cost function.

    Returns a function `cost_fn(bore_radii) -> scalar` that is
    fully compiled and batches all fingerings via vmap.
    """
    n = len(fingering_sets)
    n_actions = chain['n_actions']
    closed_top = chain['closed_top']

    # Extract chain arrays (all JAX arrays, captured as constants)
    c_at = chain['act_types']
    c_pl = chain['act_pipe_length']
    c_ji0 = chain['act_junc_idx0']
    c_ji1 = chain['act_junc_idx1']
    c_hi = chain['act_hole_idx']
    c_ha = chain['act_hole_area']
    c_hol = chain['act_hole_open_len']
    c_hcl = chain['act_hole_closed_len']
    c_hbi = chain['act_hole_bore_idx']

    # Pad fingering sets to (n, MAX_HOLES+1)
    fs_padded = jnp.zeros((n, MAX_HOLES + 1))
    for i, fs in enumerate(fingering_sets):
        fs_padded = fs_padded.at[i, :len(fs)].set(fs)

    tf = jnp.array(target_freqs)
    tw = jnp.array(target_wavelengths)

    def _resonance_phase(wavelength, bore_radii, fs_pad):
        def scan_step(phase, i):
            act = c_at[i]
            # PIPE
            pp = phase + c_pl[i] / wavelength * 2.0
            # JUNCTION2
            a0 = jnp.pi * bore_radii[c_ji0[i]] ** 2
            a1 = jnp.pi * bore_radii[c_ji1[i]] ** 2
            sh = jnp.floor(phase + 0.5)
            pj = _untanner(a1 / a0 * _tanner(phase - sh)) + sh
            # HOLE
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
            # Select
            new_phase = jnp.where(act == 0, pp, jnp.where(act == 1, pj, ph))
            return new_phase, None

        phase, _ = lax.scan(scan_step, jnp.array(0.5), jnp.arange(n_actions))
        return phase + jnp.where(closed_top, 0.0, 0.5)

    def _find_resonance(wl_near, bore_radii, fs_pad):
        """Expanding-window search matching baseline wavelength_near()."""
        step_cents = 2.0
        step = 2.0 ** (step_cents / 1200.0)
        step_increase = 1.05
        hs = jnp.sqrt(step)
        max_iter = 20

        def scorer(w):
            p = _resonance_phase(w, bore_radii, fs_pad)
            return ((p + 0.5) % 1.0) - 0.5

        # Initialize probes around the guess
        w_left = wl_near / hs
        w_right = wl_near * hs
        s_left = scorer(w_left)
        s_right = scorer(w_right)

        def expand_step(carry, _):
            w_left, w_right, s_left, s_right, cur_step = carry
            # Check sign change: s_left >= 0 and s_right < 0
            found = (s_left >= 0.0) & (s_right < 0.0)
            # Interpolate if found
            m = (s_right - s_left) / (w_right - w_left)
            interp = jnp.where(jnp.abs(m) < 1e-30, 0.5 * (w_left + w_right),
                               w_left - s_left / m)

            # Extend left
            new_wl = w_left / cur_step
            new_sl = scorer(new_wl)
            # Check sign change at left
            found_left = (new_sl >= 0.0) & (s_left < 0.0)
            m_left = (s_left - new_sl) / (w_left - new_wl)
            interp_left = jnp.where(jnp.abs(m_left) < 1e-30, 0.5 * (new_wl + w_left),
                                    new_wl - new_sl / m_left)

            # Extend right
            new_wr = w_right * cur_step
            new_sr = scorer(new_wr)
            found_right = (s_right >= 0.0) & (new_sr < 0.0)
            m_right = (new_sr - s_right) / (new_wr - w_right)
            interp_right = jnp.where(jnp.abs(m_right) < 1e-30, 0.5 * (w_right + new_wr),
                                     w_right - s_right / m_right)

            # Update probes
            new_w_left = jnp.where(found | found_left, w_left, new_wl)
            new_s_left = jnp.where(found | found_left, s_left, new_sl)
            new_w_right = jnp.where(found | found_right, w_right, new_wr)
            new_s_right = jnp.where(found | found_right, s_right, new_sr)

            # Pick best result if found
            result = jnp.where(found, interp,
                      jnp.where(found_left, interp_left,
                        jnp.where(found_right, interp_right, 0.0)))
            any_found = found | found_left | found_right

            return (new_w_left, new_w_right, new_s_left, new_s_right,
                    cur_step * step_increase), result

        carry = (w_left, w_right, s_left, s_right, step)
        _, final_result = lax.scan(expand_step, carry, None, length=max_iter)

        # Use the last non-zero result
        wl = final_result[-1]
        # Fallback: if no sign change found, return best scorer
        best_wl = jnp.where(jnp.abs(s_left) < jnp.abs(s_right), w_left, w_right)
        wl = jnp.where(jnp.abs(wl) < 1e-10, best_wl, wl)
        return wl

    @jax.jit
    def cost_fn(bore_radii):
        def _cost_single(args):
            wl_near, fs_p = args
            return _find_resonance(wl_near, bore_radii, fs_p)
        resonant_wls = jax.vmap(_cost_single)((tw, fs_padded))
        actual_freqs = SPEED_OF_SOUND / resonant_wls
        cents = 1200.0 * jnp.log2(actual_freqs / tf)
        corrected = cents - jnp.mean(cents)
        return jnp.sqrt(jnp.mean(corrected ** 2))

    return cost_fn


def make_intonation_profile_cost(chain, target_freqs, fingering_sets, target_wavelengths):
    """Build intonation profile cost function."""
    n = len(fingering_sets)
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

    fs_padded = jnp.zeros((n, MAX_HOLES + 1))
    for i, fs in enumerate(fingering_sets):
        fs_padded = fs_padded.at[i, :len(fs)].set(fs)

    tf = jnp.array(target_freqs)
    tw = jnp.array(target_wavelengths)
    ti = jnp.diff(1200.0 * jnp.log2(tf[1:] / tf[:-1]))

    def _resonance_phase(wavelength, bore_radii, fs_pad):
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
            return jnp.where(act == 0, pp, jnp.where(act == 1, pj, ph)), None
        phase, _ = lax.scan(scan_step, jnp.array(0.5), jnp.arange(n_actions))
        return phase + jnp.where(closed_top, 0.0, 0.5)

    def _find_resonance(wl_near, bore_radii, fs_pad):
        step_cents = 2.0
        step = 2.0 ** (step_cents / 1200.0)
        step_increase = 1.05
        hs = jnp.sqrt(step)
        max_iter = 20

        def scorer(w):
            p = _resonance_phase(w, bore_radii, fs_pad)
            return ((p + 0.5) % 1.0) - 0.5

        w_left = wl_near / hs
        w_right = wl_near * hs
        s_left = scorer(w_left)
        s_right = scorer(w_right)

        def expand_step(carry, _):
            w_left, w_right, s_left, s_right, cur_step = carry
            found = (s_left >= 0.0) & (s_right < 0.0)
            m = (s_right - s_left) / (w_right - w_left)
            interp = jnp.where(jnp.abs(m) < 1e-30, 0.5 * (w_left + w_right), w_left - s_left / m)

            new_wl = w_left / cur_step
            new_sl = scorer(new_wl)
            found_left = (new_sl >= 0.0) & (s_left < 0.0)
            m_left = (s_left - new_sl) / (w_left - new_wl)
            interp_left = jnp.where(jnp.abs(m_left) < 1e-30, 0.5 * (new_wl + w_left), new_wl - new_sl / m_left)

            new_wr = w_right * cur_step
            new_sr = scorer(new_wr)
            found_right = (s_right >= 0.0) & (new_sr < 0.0)
            m_right = (new_sr - s_right) / (new_wr - w_right)
            interp_right = jnp.where(jnp.abs(m_right) < 1e-30, 0.5 * (w_right + new_wr), w_right - s_right / m_right)

            new_w_left = jnp.where(found | found_left, w_left, new_wl)
            new_s_left = jnp.where(found | found_left, s_left, new_sl)
            new_w_right = jnp.where(found | found_right, w_right, new_wr)
            new_s_right = jnp.where(found | found_right, s_right, new_sr)

            result = jnp.where(found, interp, jnp.where(found_left, interp_left, jnp.where(found_right, interp_right, 0.0)))
            return (new_w_left, new_w_right, new_s_left, new_s_right, cur_step * step_increase), result

        carry = (w_left, w_right, s_left, s_right, step)
        _, final_result = lax.scan(expand_step, carry, None, length=max_iter)
        wl = final_result[-1]
        best_wl = jnp.where(jnp.abs(s_left) < jnp.abs(s_right), w_left, w_right)
        return jnp.where(jnp.abs(wl) < 1e-10, best_wl, wl)

    @jax.jit
    def cost_fn(bore_radii):
        def find_one(args):
            return _find_resonance(args[0], bore_radii, args[1])
        resonant_wls = jax.vmap(find_one)((tw, fs_padded))
        actual_freqs = SPEED_OF_SOUND / resonant_wls
        cents = 1200.0 * jnp.log2(actual_freqs / tf)
        return jnp.sqrt(jnp.mean((jnp.diff(cents) - ti) ** 2))

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
