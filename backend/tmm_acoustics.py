"""
TMM Acoustics — backward-compatible re-export layer.

All implementation has moved to the ``backend.acoustics`` subpackage:

- ``backend.acoustics.tmm_math``     — Core math (phase, junctions, corrections)
- ``backend.acoustics.profile``      — Stepped bore Profile class
- ``backend.acoustics.tmm_instrument`` — TMMInstrument class
- ``backend.acoustics.factory``      — Factory functions (from_radii, from_network)

This module re-exports all public names so existing imports continue working.
"""
from backend.acoustics import (  # noqa: F401
    SPEED_OF_SOUND,
    circle_area,
    tanner,
    untanner,
    pipe_reply_phase,
    pipe_reply_phase_with_loss,
    junction2_reply_phase,
    junction3_reply_phase,
    end_flange_length_correction,
    hole_length_correction,
    Profile,
    TMMInstrument,
    Hole,
    tmm_instrument_from_radii,
    tmm_instrument_from_network,
)