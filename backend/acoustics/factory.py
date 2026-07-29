"""Factory functions for creating TMMInstrument from various input formats."""
from __future__ import annotations

from typing import List, Optional

import numpy as np

from backend.acoustics.tmm_instrument import TMMInstrument


def tmm_instrument_from_radii(
    radii_mm: np.ndarray,
    bore_length_mm: float,
    hole_positions_mm: List[float],
    hole_diameters_mm: List[float],
    hole_lengths_mm: List[float],
    outer_diameter_mm: float = 22.0,
    closed_top: bool = False,
    cone_step: float = 0.5,
    loss_model: Optional[object] = None,
) -> TMMInstrument:
    """Create a TMMInstrument from an array of bore radii.

    Args:
        radii_mm: bore radii in mm at evenly-spaced positions
        bore_length_mm: total bore length in mm
        hole_positions_mm: position of each hole along the bore (mm)
        hole_diameters_mm: diameter of each hole (mm)
        hole_lengths_mm: effective length of each hole channel (mm)
        outer_diameter_mm: outer diameter of the instrument body (mm)
        closed_top: True for clarinets (closed reed end)
        cone_step: maximum step size for profile smoothing
        loss_model: optional viscothermal loss model (e.g., KeefeLoss)

    Returns:
        TMMInstrument instance
    """
    bore_length_scalar = float(bore_length_mm)
    n = max(len(radii_mm), 2)
    if len(radii_mm) < 2:
        r = float(radii_mm[0]) if len(radii_mm) == 1 else 7.0
        positions = [0.0, bore_length_scalar]
        diameters = [r * 2.0, r * 2.0]
    else:
        positions = np.linspace(0, bore_length_scalar, n).tolist()
        diameters = (np.asarray(radii_mm, dtype=float) * 2.0).tolist()
    outer_diams = [outer_diameter_mm] * n

    return TMMInstrument(
        inner_positions=positions,
        inner_diameters=diameters,
        outer_diameters=outer_diams,
        hole_positions=hole_positions_mm,
        hole_diameters=hole_diameters_mm,
        hole_lengths=hole_lengths_mm,
        closed_top=closed_top,
        cone_step=cone_step,
        loss_model=loss_model,
    )


def tmm_instrument_from_network(
    network: "AcousticNetwork",
    cone_step: float = 0.5,
    loss_model: Optional[object] = None,
) -> TMMInstrument:
    """Create a TMMInstrument from an AcousticNetwork.

    Parameters
    ----------
    network : AcousticNetwork
        Solver-agnostic network representation.
    cone_step : float, optional
        Maximum step size for profile smoothing (mm).  Default 0.5.
    loss_model : object or None, optional
        Viscothermal loss model.  None for lossless.

    Returns
    -------
    TMMInstrument
        Fully constructed TMM instrument.
    """
    from backend.core.network import AcousticNetwork

    z = [p[0] for p in network.bore_points]
    inner_diams = [p[1] * 2.0 for p in network.bore_points]
    outer_diams = [p[2] * 2.0 for p in network.bore_points]
    hole_pos = [h[0] for h in network.holes]
    hole_diams = [h[1] * 2.0 for h in network.holes]
    hole_lengths = [h[2] for h in network.holes]

    return TMMInstrument(
        inner_positions=z,
        inner_diameters=inner_diams,
        outer_diameters=outer_diams,
        hole_positions=hole_pos,
        hole_diameters=hole_diams,
        hole_lengths=hole_lengths,
        closed_top=network.closed_top,
        cone_step=cone_step,
        loss_model=loss_model,
    )