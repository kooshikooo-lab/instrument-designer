"""Acoustics subpackage — TMM implementation split into focused modules.

Modules:
- tmm_math       — Core math functions (phase, junctions, corrections)
- profile        — Stepped bore profile representation
- tmm_instrument — TMMInstrument class (resonance computation)
- factory        — Factory functions (from_radii, from_network)
"""
from backend.acoustics.tmm_math import (  # noqa: F401
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
)
from backend.acoustics.profile import Profile  # noqa: F401
from backend.acoustics.tmm_instrument import (  # noqa: F401
    TMMInstrument,
    Hole,
)
from backend.acoustics.factory import (  # noqa: F401
    tmm_instrument_from_radii,
    tmm_instrument_from_network,
)

__all__ = [
    "SPEED_OF_SOUND",
    "circle_area",
    "tanner",
    "untanner",
    "pipe_reply_phase",
    "pipe_reply_phase_with_loss",
    "junction2_reply_phase",
    "junction3_reply_phase",
    "end_flange_length_correction",
    "hole_length_correction",
    "Profile",
    "TMMInstrument",
    "Hole",
    "tmm_instrument_from_radii",
    "tmm_instrument_from_network",
]