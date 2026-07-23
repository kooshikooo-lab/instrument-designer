"""
Target frequency generation for wind instrument optimization.

Different instrument types produce different harmonic series:
  - Open-open pipe (flute, recorder, whistle): all harmonics  f, 2f, 3f, 4f...
  - Closed-open pipe (clarinet, reedpipe): odd harmonics     f, 3f, 5f, 7f...
  - Conical bore (shawm, oboe, sax): all harmonics (acts open-open)

Usage:
    from backend.target_frequencies import get_targets

    # For a clarinet in C (closed-open = odd harmonics)
    targets = get_targets("clarinet_Bb", fundamental=261.6, n_notes=8)

    # For a flute in D (open-open = all harmonics)
    targets = get_targets("penny_whistle_D", fundamental=293.7, n_notes=8)
"""

INSTRUMENT_TYPES: dict[str, str] = {
    # Flutes — open-open pipe, all harmonics
    "folk_flute": "open-open",
    "folk_whistle": "open-open",
    "tin_whistle": "open-open",
    "recorder": "open-open",
    "dorian_whistle": "open-open",
    "three_hole_whistle": "open-open",
    "pflute": "open-open",
    # Clarinets — closed-open pipe, odd harmonics only
    "reedpipe": "closed-open",
    "reed_drone": "closed-open",
    "clarinet_Bb": "closed-open",
    "chalumeau": "closed-open",
    # Shawms — conical bore, all harmonics (acts open-open)
    "folk_shawm": "open-open",
    "shawm": "open-open",
    "oboe": "open-open",
    "bassoon": "open-open",
    # Saxophones — conical bore, all harmonics
    "soprano_sax": "open-open",
    "alto_sax": "open-open",
    "tenor_sax": "open-open",
    "baritone_sax": "open-open",
    # Brass — closed-open pipe but bell flare + cup mouthpiece give all harmonics
    "trumpet_bb": "open-open",
    "trombone": "open-open",
    "french_horn": "open-open",
    "tuba": "open-open",
}

# Standard pitch reference
A4 = 440.0
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_MAP = {"Bb": "A#", "Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#"}


def freq_from_note(note: str) -> float:
    """Convert note name (e.g. 'C4', 'A4', 'Bb3') to frequency in Hz."""
    name = note.rstrip("0123456789")
    octave = int(note[len(name):]) if note[len(name):] else 4
    name = FLAT_MAP.get(name, name)
    semitones = (octave - 4) * 12 + (NOTES.index(name) - 9)
    return A4 * 2 ** (semitones / 12)


def get_instrument_type(preset: str) -> str:
    """Determine the acoustic type of an instrument preset."""
    return INSTRUMENT_TYPES.get(preset, "open-open")


def get_targets(
    preset: str,
    fundamental: float | None = None,
    n_notes: int = 8,
    note_range: tuple[str, str] | None = None,
) -> list[float]:
    """
    Generate correct target frequencies for an instrument preset.

    Args:
        preset: Instrument preset key (e.g. 'folk_whistle', 'reedpipe')
        fundamental: Base frequency in Hz. Auto-calculated if None.
        n_notes: Number of target frequencies to generate.
        note_range: (low_note, high_note) e.g. ('C4', 'C6').
                    Overrides n_notes if provided.

    Returns:
        List of target frequencies in Hz, sorted ascending.

    Examples:
        >>> get_targets("folk_whistle", fundamental=293.7, n_notes=6)
        [293.7, 587.4, 881.1, 1174.8, 1468.5, 1762.2]  # all harmonics

        >>> get_targets("reedpipe", fundamental=261.6, n_notes=4)
        [261.6, 784.8, 1308.0, 1831.2]  # odd harmonics only
    """
    if fundamental is None:
        fundamental = 261.6  # default C4

    instrument_type = get_instrument_type(preset)

    if note_range is not None:
        low_freq = freq_from_note(note_range[0])
        high_freq = freq_from_note(note_range[1])
        targets = _generate_in_range(fundamental, instrument_type, low_freq, high_freq)
    else:
        targets = _generate_n_notes(fundamental, instrument_type, n_notes)

    return targets


def _generate_n_notes(fundamental: float, instrument_type: str, n: int) -> list[float]:
    """Generate n target frequencies starting from fundamental."""
    targets = []
    harmonic_idx = 1
    while len(targets) < n:
        if instrument_type == "closed-open":
            freq = fundamental * (2 * harmonic_idx - 1)  # 1, 3, 5, 7...
        else:
            freq = fundamental * harmonic_idx  # 1, 2, 3, 4...
        targets.append(round(freq, 1))
        harmonic_idx += 1
    return targets


def _generate_in_range(
    fundamental: float, instrument_type: str, low: float, high: float
) -> list[float]:
    """Generate all target frequencies within [low - eps, high] Hz range."""
    targets = []
    harmonic_idx = 1
    eps_low = 0.05
    eps_high = 0.5
    while True:
        if instrument_type == "closed-open":
            freq = fundamental * (2 * harmonic_idx - 1)
        else:
            freq = fundamental * harmonic_idx
        if freq > high + eps_high:
            break
        if freq >= low - eps_low:
            targets.append(round(freq, 1))
        harmonic_idx += 1
    return targets


# ── Well-known instrument targets for quick reference ─────────────────────

PRESET_TARGETS: dict[str, dict] = {
    "folk_whistle": {
        "type": "open-open",
        "note": "D5",
        "range": ("D5", "D7"),
        "description": "Penny whistle in D — 2 octaves, all harmonics",
    },
    "folk_flute": {
        "type": "open-open",
        "note": "D5",
        "range": ("D5", "D7"),
        "description": "Folk flute in D — 2 octaves, all harmonics",
    },
    "tin_whistle": {
        "type": "open-open",
        "note": "D5",
        "range": ("D5", "C#6"),
        "description": "Tin whistle in D — 6 holes, all harmonics",
    },
    "concert_flute": {
        "type": "open-open",
        "note": "C4",
        "range": ("C4", "D5"),
        "description": "Concert flute in C (Boehm) — 6-hole simple system model",
    },
    "recorder": {
        "type": "open-open",
        "note": "C5",
        "range": ("C5", "C7"),
        "description": "Soprano recorder in C — 2 octaves, all harmonics",
    },
    "reedpipe": {
        "type": "closed-open",
        "note": "C4",
        "range": ("C4", "C6"),
        "description": "Reedpipe — odd harmonics only (clarinet-like)",
    },
    "folk_shawm": {
        "type": "open-open",
        "note": "C4",
        "range": ("C4", "C6"),
        "description": "Folk shawm in C — conical bore, all harmonics",
    },
    "shawm": {
        "type": "open-open",
        "note": "C4",
        "range": ("C4", "C6"),
        "description": "Shawm in C — conical bore, all harmonics",
    },
    "reed_drone": {
        "type": "closed-open",
        "note": "C3",
        "range": ("C3", "C5"),
        "description": "Reed drone — odd harmonics, bass range",
    },
    "clarinet_Bb": {
        "type": "closed-open",
        "note": "Bb3",
        "range": ("Bb3", "Bb5"),
        "description": "Bb clarinet — odd harmonics only",
    },
    "soprano_sax": {
        "type": "open-open",
        "note": "Bb4",
        "range": ("Bb4", "Bb6"),
        "description": "Soprano saxophone in Bb — conical bore, all harmonics",
    },
    "alto_sax": {
        "type": "open-open",
        "note": "Eb4",
        "range": ("Eb4", "Eb6"),
        "description": "Alto saxophone in Eb — conical bore, all harmonics",
    },
    "tenor_sax": {
        "type": "open-open",
        "note": "Bb3",
        "range": ("Bb3", "Bb5"),
        "description": "Tenor saxophone in Bb — conical bore, all harmonics",
    },
    "baritone_sax": {
        "type": "open-open",
        "note": "Eb3",
        "range": ("Eb3", "Eb5"),
        "description": "Baritone saxophone in Eb — conical bore, all harmonics",
    },
    "trumpet_bb": {
        "type": "open-open",
        "note": "Bb3",
        "range": ("Bb3", "Bb5"),
        "description": "Bb trumpet — cylindrical bore with bell, all harmonics",
    },
    "trombone": {
        "type": "open-open",
        "note": "Bb2",
        "range": ("Bb2", "Bb4"),
        "description": "Tenor trombone in Bb — cylindrical bore, all harmonics",
    },
    "french_horn": {
        "type": "open-open",
        "note": "F3",
        "range": ("F3", "F5"),
        "description": "French horn in F — conical bore, all harmonics",
    },
    "tuba": {
        "type": "open-open",
        "note": "Bb1",
        "range": ("Bb1", "Bb3"),
        "description": "Tuba in Bb — conical bore, all harmonics",
    },
}


def get_preset_info(preset: str) -> dict | None:
    """Get preset metadata including correct target frequencies."""
    if preset in PRESET_TARGETS:
        info = PRESET_TARGETS[preset].copy()
        info["preset"] = preset
        fundamental = freq_from_note(info["note"])
        info["fundamental"] = round(fundamental, 1)
        low, high = info["range"]
        targets = get_targets(
            preset,
            fundamental=fundamental,
            note_range=(low, high),
        )
        info["targets"] = targets
        return info
    return None


if __name__ == "__main__":
    print("Target Frequency Generator — Quick Test\n")
    for preset in ["folk_whistle", "reedpipe", "clarinet_Bb", "shawm"]:
        info = get_preset_info(preset)
        if info:
            print(f"{preset}:")
            print(f"  Type: {info['type']}")
            print(f"  Fundamental: {info['fundamental']} Hz")
            print(f"  Range: {info['range']}")
            print(f"  Targets ({len(info['targets'])}): {info['targets']}")
            print()
