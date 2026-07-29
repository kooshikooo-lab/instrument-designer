"""Musical scale definitions for microtonal and non-Western tunings."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScaleDefinition:
    """A musical scale with interval structure and origin."""
    name: str
    family: str  # western, indian, arabic, experimental, etc.
    intervals_cents: list[float]  # intervals from root in cents
    description: str
    n_notes: int = 0

    def __post_init__(self):
        if not self.n_notes:
            self.n_notes = len(self.intervals_cents)


SCALES: dict[str, ScaleDefinition] = {
    # ── WESTERN ──────────────────────────────────────────────────────
    "12_tet": ScaleDefinition(
        name="12-TET (Equal Temperament)",
        family="western",
        intervals_cents=[0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100],
        description="Standard Western tuning. 12 equal semitones per octave.",
    ),
    "major": ScaleDefinition(
        name="Major (Ionian)",
        family="western",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1100],
        description="Major scale: W-W-H-W-W-W-H.",
    ),
    "natural_minor": ScaleDefinition(
        name="Natural Minor (Aeolian)",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 800, 1000],
        description="Natural minor: W-H-W-W-H-W-W.",
    ),
    "harmonic_minor": ScaleDefinition(
        name="Harmonic Minor",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 800, 1100],
        description="Minor with raised 7th. Augmented 2nd between 6th and 7th.",
    ),
    "melodic_minor": ScaleDefinition(
        name="Melodic Minor (ascending)",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 900, 1100],
        description="Minor with raised 6th and 7th ascending.",
    ),
    "dorian": ScaleDefinition(
        name="Dorian Mode",
        family="western",
        intervals_cents=[0, 200, 300, 500, 700, 900, 1000],
        description="Minor with raised 6th. Popular in jazz/folk.",
    ),
    "mixolydian": ScaleDefinition(
        name="Mixolydian Mode",
        family="western",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1000],
        description="Major with flattened 7th. Common in folk/rock.",
    ),
    "lydian": ScaleDefinition(
        name="Lydian Mode",
        family="western",
        intervals_cents=[0, 200, 400, 600, 700, 900, 1100],
        description="Major with raised 4th. Bright, dreamy quality.",
    ),
    "phrygian": ScaleDefinition(
        name="Phrygian Mode",
        family="western",
        intervals_cents=[0, 100, 300, 500, 700, 800, 1000],
        description="Minor with flattened 2nd. Spanish/flamenco flavor.",
    ),
    "locrian": ScaleDefinition(
        name="Locrian Mode",
        family="western",
        intervals_cents=[0, 100, 300, 500, 600, 800, 1000],
        description="Diminished 5th. Rarely used as tonal center.",
    ),
    "pentatonic_major": ScaleDefinition(
        name="Major Pentatonic",
        family="western",
        intervals_cents=[0, 200, 400, 700, 900],
        description="5-note scale (omit 4th and 7th). No semitones.",
    ),
    "pentatonic_minor": ScaleDefinition(
        name="Minor Pentatonic",
        family="western",
        intervals_cents=[0, 300, 500, 700, 1000],
        description="5-note minor scale. Blues/rock staple.",
    ),
    "blues": ScaleDefinition(
        name="Blues Scale",
        family="western",
        intervals_cents=[0, 300, 500, 600, 700, 1000],
        description="Minor pentatonic with added flat 5 (blue note).",
    ),
    "whole_tone": ScaleDefinition(
        name="Whole Tone Scale",
        family="western",
        intervals_cents=[0, 200, 400, 600, 800, 1000],
        description="6 equal whole steps. No tonal center.",
    ),
    "diminished": ScaleDefinition(
        name="Diminished (Octatonic)",
        family="western",
        intervals_cents=[0, 200, 300, 500, 600, 800, 900, 1100],
        description="Alternating W-H. Symmetric, 8 notes.",
    ),

    # ── MICROTONAL / QUARTER-TONE ────────────────────────────────────
    "24_tet": ScaleDefinition(
        name="24-TET (Quarter-tone Equal Temperament)",
        family="microtonal",
        intervals_cents=[i * 50 for i in range(24)],
        description="24 equal quarter-tones per octave. Standard microtonal system.",
    ),
    "31_tet": ScaleDefinition(
        name="31-TET (Diesis Temperament)",
        family="microtonal",
        intervals_cents=[i * (1200 / 31) for i in range(31)],
        description="31 equal steps. Good for meantone approximations.",
    ),
    "53_tet": ScaleDefinition(
        name="53-TET (Mercator's Temperament)",
        family="microtonal",
        intervals_cents=[i * (1200 / 53) for i in range(53)],
        description="53 equal steps. Excellent approximation of just intonation.",
    ),
    "19_tet": ScaleDefinition(
        name="19-TET",
        family="microtonal",
        intervals_cents=[i * (1200 / 19) for i in range(19)],
        description="19 equal steps. Good for meantone, close to 1/3 comma meantone.",
    ),

    # ── INDIAN (HINDUSTANI/CARNATIC) ────────────────────────────────
    "thaat_bilawal": ScaleDefinition(
        name="Thaat Bilawal (Major/Ionian)",
        family="indian",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1100],
        description="Equivalent to major scale. All shuddha (natural) notes.",
    ),
    "thaat_khamaj": ScaleDefinition(
        name="Thaat Khamaj (Mixolydian)",
        family="indian",
        intervals_cents=[0, 200, 400, 500, 700, 900, 1000],
        description="Mixolydian equivalent. Komal ni (flat 7).",
    ),
    "thaat_kafi": ScaleDefinition(
        name="Thaat Kafi (Dorian)",
        family="indian",
        intervals_cents=[0, 200, 300, 500, 700, 900, 1000],
        description="Dorian equivalent. Komal ga, komal ni.",
    ),
    "thaat_asavari": ScaleDefinition(
        name="Thaat Asavari (Phrygian-ish)",
        family="indian",
        intervals_cents=[0, 200, 300, 500, 700, 800, 1000],
        description="Komal ga, dha, ni. Minor flavor.",
    ),
    "thaat_bhairavi": ScaleDefinition(
        name="Thaat Bhairavi (Double Harmonic-ish)",
        family="indian",
        intervals_cents=[0, 100, 400, 500, 700, 800, 1000],
        description="All komal except shuddha Ma and Pa. Phrygian dominant feel.",
    ),
    "thaat_bhairav": ScaleDefinition(
        name="Thaat Bhairav",
        family="indian",
        intervals_cents=[0, 100, 400, 500, 700, 800, 1100],
        description="Komal re, komal dha. Unusual intervals.",
    ),
    "thaat_kalyan": ScaleDefinition(
        name="Thaat Kalyan (Lydian)",
        family="indian",
        intervals_cents=[0, 200, 400, 600, 700, 900, 1100],
        description="Tivra Ma (sharp 4th). Lydian equivalent.",
    ),
    "thaat_marwa": ScaleDefinition(
        name="Thaat Marwa",
        family="indian",
        intervals_cents=[0, 100, 400, 600, 700, 900, 1100],
        description="Komal re, tivra Ma. No Pa.",
    ),
    "thaat_purvi": ScaleDefinition(
        name="Thaat Purvi",
        family="indian",
        intervals_cents=[0, 100, 400, 600, 700, 800, 1100],
        description="Komal re, komal dha, tivra Ma.",
    ),
    "thaat_todi": ScaleDefinition(
        name="Thaat Todi",
        family="indian",
        intervals_cents=[0, 100, 300, 600, 700, 800, 1100],
        description="Komal re, komal ga, tivra Ma, komal dha. Complex.",
    ),

    # ── ARABIC / MIDDLE EASTERN ──────────────────────────────────────
    "maqam_rast": ScaleDefinition(
        name="Maqam Rast",
        family="arabic",
        intervals_cents=[0, 204, 408, 498, 702, 906, 996, 1200],
        description="Major-like maqam. Neutral 3rd (~350c), neutral 7th.",
    ),
    "maqam_bayati": ScaleDefinition(
        name="Maqam Bayati",
        family="arabic",
        intervals_cents=[0, 160, 408, 498, 702, 864, 1100, 1200],
        description="Minor-like with neutral 2nd and 6th. Very common.",
    ),
    "maqam_hijaz": ScaleDefinition(
        name="Maqam Hijaz",
        family="arabic",
        intervals_cents=[0, 160, 408, 498, 702, 812, 1100, 1200],
        description="Augmented 2nd between 2nd and 3rd degree. Exotic sound.",
    ),
    "maqam_nahawand": ScaleDefinition(
        name="Maqam Nahawand",
        family="arabic",
        intervals_cents=[0, 204, 294, 498, 702, 792, 996, 1200],
        description="Minor-like. Close to harmonic minor but with neutral intervals.",
    ),
    "maqam_kurd": ScaleDefinition(
        name="Maqam Kurd",
        family="arabic",
        intervals_cents=[0, 204, 294, 498, 702, 792, 996, 1200],
        description="Minor with neutral 3rd and 7th.",
    ),
    "maqam_saba": ScaleDefinition(
        name="Maqam Saba",
        family="arabic",
        intervals_cents=[0, 160, 408, 498, 650, 812, 1100, 1200],
        description="Diminished 4th and neutral 7th. Distinctive dark character.",
    ),

    # ── OTHER WORLD SCALES ───────────────────────────────────────────
    "slendro": ScaleDefinition(
        name="Slendro (Javanese Pentatonic)",
        family="indonesian",
        intervals_cents=[0, 240, 480, 720, 960],
        description="5 roughly equal steps per octave. Gamelan tuning.",
    ),
    "pelog": ScaleDefinition(
        name="Pelog (Javanese Heptatonic)",
        family="indonesian",
        intervals_cents=[0, 120, 360, 540, 720, 840, 1080],
        description="7-note scale with uneven intervals. Gamelan core.",
    ),
    "hirajoshi": ScaleDefinition(
        name="Hirajoshi (Japanese Pentatonic)",
        family="japanese",
        intervals_cents=[0, 200, 300, 700, 800],
        description="Japanese pentatonic. Two semitone clusters.",
    ),
    "iwato": ScaleDefinition(
        name="Iwato (Japanese Pentatonic)",
        family="japanese",
        intervals_cents=[0, 100, 500, 600, 1000],
        description="Used for koto/shakuhachi. Very distinctive intervals.",
    ),
    "ryukyu": ScaleDefinition(
        name="Ryukyu Scale (Okinawan)",
        family="japanese",
        intervals_cents=[0, 200, 500, 700, 1000],
        description="Okinawan pentatonic. Major triad + perfect 4th + minor 7th.",
    ),
    "miyako": ScaleDefinition(
        name="Miyako-bushi (Japanese)",
        family="japanese",
        intervals_cents=[0, 100, 500, 600, 1000],
        description="Japanese In scale variant. Semitone clusters at bottom/top.",
    ),
    "rupak": ScaleDefinition(
        name="Raga Rupak (7-beat, hexatonic)",
        family="indian",
        intervals_cents=[0, 200, 300, 500, 700, 900],
        description="Hexatonic. Omit 4th degree. 7-beat cycle.",
    ),
    "malkauns": ScaleDefinition(
        name="Raga Malkauns (Minor Pentatonic)",
        family="indian",
        intervals_cents=[0, 300, 500, 800, 1000],
        description="Same as minor pentatonic. Very popular night raga.",
    ),
    "bhairav": ScaleDefinition(
        name="Raga Bhairav",
        family="indian",
        intervals_cents=[0, 100, 400, 500, 700, 800, 1100],
        description="Komal re, komal dha. Morning raga.",
    ),
    "todi": ScaleDefinition(
        name="Raga Todi",
        family="indian",
        intervals_cents=[0, 100, 300, 600, 700, 800, 1100],
        description="Komal re, ga, dha; tivra Ma. Complex morning raga.",
    ),

    # ── EXPERIMENTAL / SYMMETRIC ─────────────────────────────────────
    "tritone": ScaleDefinition(
        name="Tritone Scale",
        family="experimental",
        intervals_cents=[0, 600, 1200],
        description="Just root and tritone. Maximum dissonance.",
    ),
    "augmented": ScaleDefinition(
        name="Augmented Scale (Hexatonic)",
        family="experimental",
        intervals_cents=[0, 400, 600, 1000, 1200],
        description="Alternating minor 3rd and semitone. Symmetric.",
    ),
    "prometheus": ScaleDefinition(
        name="Prometheus Scale (Scriabin)",
        family="experimental",
        intervals_cents=[0, 200, 400, 600, 900, 1000],
        description="Mystic chord as scale. Lydian dominant + #11.",
    ),
    "acoustic": ScaleDefinition(
        name="Acoustic Scale (Lydian Dominant)",
        family="experimental",
        intervals_cents=[0, 200, 400, 600, 700, 900, 1000],
        description="Mode 4 of melodic minor. Lydian with flat 7.",
    ),
}