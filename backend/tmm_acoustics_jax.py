"""
JAX-differentiable Transfer Matrix Method (TMM) acoustics.

Port of tmm_acoustics.py to JAX for automatic differentiation.
Enables exact gradients via jax.grad() instead of finite differences.

Architecture:
  1. build_action_chain() — precomputed ONCE from concrete geometry positions.
     Stores integer indices into the bore_radii array, NOT precomputed areas.
  2. resonance_phase_jax() — executes chain with JAX arrays. Looks up
     bore_radii by index at execution time. Fully differentiable.
  3. Cost functions (rms_cost_jax, etc.) — pass bore_radii as JAX arrays.
     Chain is precomputed from bore_positions (fixed). Only areas are
     computed from the radii, enabling smooth gradients.

Based on:
  - Chalumier/Demakein phase-based TMM (ResonanceMath.kt)
  - Ernoult et al. (2020) phase resonance detection
  - JAX automatic differentiation (https://jax.readthedocs.io)

Usage:
    from backend.tmm_acoustics_jax import rms_cost_jax

    cost = rms_cost_jax(
        bore_radii_jax,
        bore_positions=[0, 100, 200, ...],
        outer_diameter=22.0,
        hole_positions=[60, 100, ...],
        hole_diameters=[7.0, 7.0, ...],
        hole_lengths=[3.75, 3.75, ...],
        closed_top=False,
        target_freqs=jnp.array([...]),
        fingering_sets=[...],
        target_wavelengths=jnp.array([...]),
    )
"""

import jax
import jax.numpy as jnp
from jax import lax
from typing import List, Tuple, Optional

# Matches chalumier's SPEED_OF_SOUND exactly (mm/s)
SPEED_OF_SOUND = 346100.0


# ============================================================================
# Core JAX TMM math — all operations are JAX-traceable
# ============================================================================

def circle_area_jax(diameter: jnp.ndarray) -> jnp.ndarray:
    r = diameter / 2.0
    return jnp.pi * r * r


def circle_area_from_radii(radii: jnp.ndarray) -> jnp.ndarray:
    return jnp.pi * radii * radii


def tanner_jax(phase: jnp.ndarray) -> jnp.ndarray:
    return jnp.tan(phase * jnp.pi)


def untanner_jax(x: jnp.ndarray) -> jnp.ndarray:
    return jnp.arctan(x) / jnp.pi


def pipe_reply_phase_jax(phase: jnp.ndarray, length_on_wavelength: jnp.ndarray) -> jnp.ndarray:
    return phase + length_on_wavelength * 2.0


def junction2_reply_phase_jax(a0: jnp.ndarray, a1: jnp.ndarray, p1: jnp.ndarray) -> jnp.ndarray:
    shift = jnp.floor(p1 + 0.5)
    return untanner_jax(a1 / a0 * tanner_jax(p1 - shift)) + shift


def junction3_reply_phase_jax(
    a0: jnp.ndarray, a1: jnp.ndarray, a2: jnp.ndarray,
    p1: jnp.ndarray, p2: jnp.ndarray,
) -> jnp.ndarray:
    shift1 = jnp.floor(p1 + 0.5)
    shift2 = jnp.floor(p2 + 0.5)
    return untanner_jax(
        a1 / a0 * tanner_jax(p1 - shift1) + a2 / a0 * tanner_jax(p2 - shift2)
    ) + shift1 + shift2


def end_flange_length_correction_jax(outer_diameter: float, inner_diameter: float) -> float:
    a = inner_diameter / 2.0
    w = (outer_diameter - inner_diameter) / 2.0
    return a * (0.821 - 0.13 * (0.42 + w / a) ** (-0.54))


def hole_length_correction_jax(hole_diameter: float, bore_diameter: float, closed: bool) -> float:
    if closed:
        return 0.0
    outer_correction = 0.7
    inner_correction = 1.3 - 0.9 * hole_diameter / bore_diameter
    a = hole_diameter / 2.0
    return a * (inner_correction + outer_correction)


# ============================================================================
# Action chain — precomputed from concrete positions, stores BORE INDICES
# ============================================================================

# Action types (integer tags for lax.switch)
_ACT_PIPE = 0
_ACT_JUNCTION2 = 1
_ACT_HOLE_OPEN = 2
_ACT_HOLE_CLOSED = 3

# Maximum number of holes supported (for fixed-size arrays)
MAX_HOLES = 24


def build_action_chain(
    bore_positions: List[float],
    bore_radii_template: List[float],
    outer_diameter: float,
    hole_positions: List[float],
    hole_diameters: List[float],
    hole_lengths: List[float],
    closed_top: bool,
) -> dict:
    """
    Precompute the action chain from concrete geometry.

    Stores bore_radii INDICES (not areas) for junction events, so the
    chain can be executed with JAX arrays during differentiation.

    Returns a dict with:
      - 'actions': list of action tuples (type, params...)
      - 'emission_area_index': index of last bore point for emission
      - 'n_actions': total number of actions
      - 'closed_top': bool
      - 'n_holes': number of holes
    """
    n_bore = len(bore_positions)
    length = bore_positions[-1]

    # Precompute template areas for end corrections (concrete)
    template_diameters = [r * 2.0 for r in bore_radii_template]
    end_correction = end_flange_length_correction_jax(outer_diameter, template_diameters[0])

    # Build event list: (position, type, index)
    events = []
    for i in range(1, n_bore - 1):
        events.append((bore_positions[i], 'step', i))
    for i, pos in enumerate(hole_positions):
        events.append((pos, 'hole', i))
    events.append((length, 'end', 0))
    events.sort(key=lambda e: e[0])

    # Walk events, building action descriptors
    actions = []
    position = -end_correction
    current_bore_idx = 0  # which bore segment we're in

    for pos, descriptor, index in events:
        seg_length = pos - position
        actions.append((_ACT_PIPE, seg_length))
        position = pos

        if descriptor == 'step':
            # Junction between bore segments
            actions.append((_ACT_JUNCTION2, current_bore_idx, index))
            current_bore_idx = index

        elif descriptor == 'hole':
            # Hole event: index is hole index
            # Store current_bore_idx so resonance_phase_jax can look up
            # the correct bore radius for the junction3 computation.
            bore_dia_at_hole = template_diameters[current_bore_idx]
            hole_dia = hole_diameters[index]
            true_length = hole_lengths[index]
            open_length = true_length + hole_length_correction_jax(hole_dia, bore_dia_at_hole, False)
            closed_length = true_length + hole_length_correction_jax(hole_dia, bore_dia_at_hole, True)
            hole_area = float(circle_area_jax(jnp.array(hole_dia)))
            actions.append((_ACT_HOLE_OPEN, index, hole_area, open_length, closed_length, current_bore_idx))

    emission_area_index = current_bore_idx

    return {
        'actions': actions,
        'emission_area_index': emission_area_index,
        'n_actions': len(actions),
        'closed_top': closed_top,
        'n_holes': len(hole_positions),
    }


# ============================================================================
# JAX TMM resonance phase — fully differentiable
# ============================================================================

def resonance_phase_jax(
    chain: dict,
    wavelength: jnp.ndarray,
    bore_radii: jnp.ndarray,
    fingering_state: jnp.ndarray,
) -> jnp.ndarray:
    """
    Compute resonance phase for a given wavelength and bore profile.

    The action chain is precomputed (from build_action_chain).
    Bore radii are looked up by stored indices, making this fully
    differentiable with respect to bore_radii.

    Args:
        chain: precomputed action chain
        wavelength: wavelength in mm (JAX scalar)
        bore_radii: bore radii array (JAX, differentiable)
        fingering_state: array of 0/1 for each hole

    Returns:
        phase value (integer at resonance)
    """
    phase = jnp.array(0.5)
    n_holes = chain['n_holes']

    for action in chain['actions']:
        act_type = action[0]

        if act_type == _ACT_PIPE:
            seg_length = action[1]
            phase = pipe_reply_phase_jax(phase, jnp.array(seg_length) / wavelength)

        elif act_type == _ACT_JUNCTION2:
            bore_idx_before = action[1]
            bore_idx_after = action[2]
            area_before = circle_area_from_radii(bore_radii[bore_idx_before])
            area_after = circle_area_from_radii(bore_radii[bore_idx_after])
            phase = junction2_reply_phase_jax(area_after, area_before, phase)

        elif act_type in (_ACT_HOLE_OPEN, _ACT_HOLE_CLOSED):
            hole_idx = action[1]
            hole_area = action[2]
            open_length = action[3]
            closed_length = action[4]
            bore_idx = action[5]  # bore segment at this hole position

            area_bore = circle_area_from_radii(bore_radii[bore_idx])

            is_open = fingering_state[hole_idx] if hole_idx < n_holes else 0.0

            hole_phase = lax.cond(
                is_open > 0,
                lambda _: pipe_reply_phase_jax(jnp.array(-0.5), jnp.array(open_length) / wavelength),
                lambda _: pipe_reply_phase_jax(jnp.array(0.0), jnp.array(closed_length) / wavelength),
                operand=None,
            )

            phase = junction3_reply_phase_jax(
                area_bore, area_bore, jnp.array(hole_area),
                phase, hole_phase,
            )

    if not chain['closed_top']:
        phase = phase + 0.5

    return phase


def find_resonance_jax(
    chain: dict,
    wavelength_near: float,
    bore_radii: jnp.ndarray,
    fingering_state: jnp.ndarray,
    n_register: int = 1,
    max_steps: int = 50,
) -> jnp.ndarray:
    """
    Find resonant wavelength near the given guess using secant method.
    Differentiable with respect to bore_radii.
    """
    step_cents = 2.0
    step = 2.0 ** (step_cents / 1200.0)
    half_step = jnp.sqrt(step)

    def scorer(w):
        p = resonance_phase_jax(chain, w, bore_radii, fingering_state)
        return ((p + 0.5) % 1.0) - 0.5

    w0 = wavelength_near / half_step
    w1 = wavelength_near * half_step
    s0 = scorer(w0)
    s1 = scorer(w1)

    def bisection_step(carry, _):
        w0, w1, s0, s1 = carry
        m = (s1 - s0) / (w1 - w0)
        w_new = jnp.where(jnp.abs(m) < 1e-30, 0.5 * (w0 + w1), w0 - s0 / m)
        s_new = scorer(w_new)

        new_w0 = jnp.where(s_new >= 0, w_new, w0)
        new_s0 = jnp.where(s_new >= 0, s_new, s0)
        new_w1 = jnp.where(s_new < 0, w_new, w1)
        new_s1 = jnp.where(s_new < 0, s_new, s1)

        return (new_w0, new_w1, new_s0, new_s1), None

    (w0, w1, s0, s1), _ = lax.scan(bisection_step, (w0, w1, s0, s1), None, length=max_steps)

    return jnp.where(jnp.abs(s0) < jnp.abs(s1), w0, w1)


# ============================================================================
# Cost functions for optimization
# ============================================================================

def compute_costs_jax(
    chain: dict,
    bore_radii: jnp.ndarray,
    target_freqs: jnp.ndarray,
    fingering_sets: List[jnp.ndarray],
    target_wavelengths: jnp.ndarray,
    n_register: int = 1,
) -> jnp.ndarray:
    """
    Compute cents error for all fingerings. Fully differentiable.
    """
    freqs = []
    for i, fs in enumerate(fingering_sets):
        wl = find_resonance_jax(chain, float(target_wavelengths[i]), bore_radii, fs, n_register)
        freq = SPEED_OF_SOUND / wl
        freqs.append(freq)
    actual_freqs = jnp.array(freqs)

    cents = 1200.0 * jnp.log2(actual_freqs / target_freqs)
    return cents


def rms_cost_jax(
    bore_radii: jnp.ndarray,
    chain: dict,
    target_freqs: jnp.ndarray,
    fingering_sets: List[jnp.ndarray],
    target_wavelengths: jnp.ndarray,
    n_register: int = 1,
) -> jnp.ndarray:
    """
    RMS cents error with global offset correction.
    Differentiable scalar cost for L-BFGS-B.

    NOTE: chain must be precomputed OUTSIDE this function (not during grad).
    """
    cents = compute_costs_jax(chain, bore_radii, target_freqs, fingering_sets, target_wavelengths, n_register)

    # Global offset correction
    global_offset = jnp.mean(cents)
    corrected = cents - global_offset
    rms = jnp.sqrt(jnp.mean(corrected ** 2))

    return rms


def intonation_profile_cost_jax(
    bore_radii: jnp.ndarray,
    chain: dict,
    target_freqs: jnp.ndarray,
    fingering_sets: List[jnp.ndarray],
    target_wavelengths: jnp.ndarray,
    n_register: int = 1,
) -> jnp.ndarray:
    """
    Intonation profile cost — relative deviations between fingerings.

    Instead of matching absolute frequencies, optimizes the RELATIVE
    pitch relationships between notes. More musically meaningful and
    more robust to global tuning offset.

    From: "Intonation profile of a recorder" (POMA 2025)
    """
    cents = compute_costs_jax(chain, bore_radii, target_freqs, fingering_sets, target_wavelengths, n_register)

    # Target intervals (in cents) between consecutive notes
    target_intervals = jnp.diff(1200.0 * jnp.log2(target_freqs[1:] / target_freqs[:-1]))

    # Actual intervals
    actual_intervals = jnp.diff(cents)

    interval_errors = actual_intervals - target_intervals
    rms = jnp.sqrt(jnp.mean(interval_errors ** 2))

    return rms


def multi_objective_cost_jax(
    bore_radii: jnp.ndarray,
    chain: dict,
    target_freqs: jnp.ndarray,
    fingering_sets: List[jnp.ndarray],
    target_wavelengths: jnp.ndarray,
    n_register: int = 1,
    intonation_weight: float = 1.0,
    playability_weight: float = 0.3,
) -> jnp.ndarray:
    """
    Multi-objective cost: intonation + playability.
    """
    intonation = rms_cost_jax(bore_radii, chain, target_freqs, fingering_sets, target_wavelengths, n_register)

    # Playability cost: smoothness of bore profile
    radii_smooth = bore_radii[1:] - bore_radii[:-1]
    smoothness_penalty = jnp.mean(radii_smooth ** 2)

    ideal_radius = 7.25
    deviation_penalty = jnp.mean((bore_radii - ideal_radius) ** 2)

    playability = smoothness_penalty + 0.1 * deviation_penalty

    return intonation_weight * intonation + playability_weight * playability


# ============================================================================
# Convenience wrapper (matches old TMMInstrumentJAX API)
# ============================================================================

class TMMInstrumentJAX:
    """
    Wrapper class that matches the old API.

    Usage:
        inst = TMMInstrumentJAX(bore_radii, bore_positions, outer_diameter,
                                hole_positions, hole_diameters, hole_lengths,
                                closed_top)
        cost = inst.rms_cost(target_freqs, fingering_sets, target_wavelengths)
    """

    def __init__(
        self,
        bore_radii,
        bore_positions,
        outer_diameter,
        hole_positions,
        hole_diameters,
        hole_lengths,
        closed_top=False,
    ):
        if isinstance(bore_radii, jnp.ndarray):
            self.bore_radii = bore_radii
        else:
            self.bore_radii = jnp.array(bore_radii, dtype=jnp.float32)

        self.bore_positions = bore_positions
        self.outer_diameter = outer_diameter
        self.hole_positions = hole_positions
        self.hole_diameters = hole_diameters
        self.hole_lengths = hole_lengths
        self.closed_top = closed_top

        # Precompute chain from template radii (concrete values)
        template_radii = self.bore_radii.tolist()
        self.chain = build_action_chain(
            bore_positions, template_radii, outer_diameter,
            hole_positions, hole_diameters, hole_lengths, closed_top,
        )

    def rms_cost(self, target_freqs, fingering_sets, target_wavelengths, n_register=1):
        return rms_cost_jax(
            self.bore_radii, self.chain, target_freqs, fingering_sets,
            target_wavelengths, n_register,
        )
