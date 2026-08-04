"""Target frequency computation for spectral validation.

Reuses backend.target_frequencies as the single source of truth.
"""

from __future__ import annotations

from backend.target_frequencies import get_targets, get_preset_info


def get_spectral_targets(
    preset: str | None = None,
    fundamental: float | None = None,
    n_notes: int = 8,
    note_range: tuple[str, str] | None = None,
) -> list[float]:
    """Get target frequencies for spectral validation.

    Delegates to backend.target_frequencies.get_targets.

    Args:
        preset: instrument preset key (e.g. 'folk_whistle', 'clarinet_Bb')
        fundamental: base frequency in Hz (auto-calculated if None)
        n_notes: number of target frequencies
        note_range: (low_note, high_note) tuple, overrides n_notes

    Returns:
        list of target frequencies in Hz
    """
    if preset is not None:
        info = get_preset_info(preset)
        if info is not None:
            return info["targets"]

    return get_targets(
        preset or "folk_whistle",
        fundamental=fundamental,
        n_notes=n_notes,
        note_range=note_range,
    )