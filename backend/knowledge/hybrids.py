"""Cross-family hybrid instrument specifications."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HybridInstrumentSpec:
    """Specification for a cross-family hybrid instrument."""
    name: str
    mouthpiece_family: str
    body_family: str
    description: str
    acoustic_challenges: list[str]
    feasibility: str  # "easy", "moderate", "hard", "experimental"
    key_considerations: list[str]

    @property
    def combined_challenges(self) -> list[str]:
        from backend.knowledge.families import INSTRUMENT_FAMILIES
        mp = INSTRUMENT_FAMILIES.get(self.mouthpiece_family)
        body = INSTRUMENT_FAMILIES.get(self.body_family)
        challenges = list(self.acoustic_challenges)
        if mp:
            challenges.extend([f"[mouthpiece] {c}" for c in mp.key_acoustic_challenges[:1]])
        if body:
            challenges.extend([f"[body] {c}" for c in body.key_acoustic_challenges[:1]])
        return challenges


HYBRID_INSTRUMENTS: list[HybridInstrumentSpec] = [
    HybridInstrumentSpec(
        name="Bass Clarinet Mouthpiece + Trombone Body",
        mouthpiece_family="clarinet",
        body_family="trombone",
        description="Single reed on cylindrical→conical bore. Combines reed warmth with brass projection.",
        acoustic_challenges=[
            "Impedance mismatch between reed and large bore",
            "Register breaks will be dramatic",
            "Exciter (reed) may not couple well to large-bore standing waves",
        ],
        feasibility="experimental",
        key_considerations=[
            "Bore taper must transition smoothly from reed to bell",
            "Valve/slide mechanism needed for chromatic play",
            "Reed may need to be larger for large bore",
        ],
    ),
    HybridInstrumentSpec(
        name="Saxophone Mouthpiece + Flute Body",
        mouthpiece_family="saxophone",
        body_family="flute",
        description="Single reed on cylindrical open bore. Reed articulation on flute body.",
        acoustic_challenges=[
            "Sax reed is designed for closed-top excitation",
            "Open bore changes harmonic content (all vs odd harmonics)",
            "Reed coupling to flute bore is untested territory",
        ],
        feasibility="experimental",
        key_considerations=[
            "Open bore means reed vibrates differently",
            "May need modified reed or mouthpiece facing",
            "Key mechanism from flute body preserved",
        ],
    ),
    HybridInstrumentSpec(
        name="Clarinet Mouthpiece + Saxophone Body",
        mouthpiece_family="clarinet",
        body_family="saxophone",
        description="Cylindrical reed on conical bore. Hybrid timbre between clarinet and sax.",
        acoustic_challenges=[
            "Bore taper mismatch (cylindrical mouthpiece → conical body)",
            "Harmonic content shifts from odd-only to all harmonics",
            "Register mechanism must accommodate both families",
        ],
        feasibility="moderate",
        key_considerations=[
            "Soprano sax body is closest in size to Bb clarinet",
            "Taper transition must be gradual to avoid reflections",
            "Fingering system can use sax layout",
        ],
    ),
    HybridInstrumentSpec(
        name="Flute Headjoint + Trombone Slide",
        mouthpiece_family="flute",
        body_family="trombone",
        description="Edge-tone excitation on trombone bore. Continuous pitch via slide.",
        acoustic_challenges=[
            "Flute embouchure requires very different air speed than trombone",
            "Trombone bore is too large for flute excitation efficiency",
            "Slide positions will be very far apart (long wavelengths)",
        ],
        feasibility="hard",
        key_considerations=[
            "Reducing bore diameter would help coupling",
            "Embouchure plate needs redesign for larger air column",
            "Could work as a novelty/experimental instrument",
        ],
    ),
    HybridInstrumentSpec(
        name="Recorder Fipple + Clarinet Body",
        mouthpiece_family="recorder",
        body_family="clarinet",
        description="Fipple mouthpiece on closed cylindrical bore. Simplicity of recorder on clarinet range.",
        acoustic_challenges=[
            "Fipple excites all harmonics, but closed bore reinforces odd only",
            "Register breaks will be unpredictable",
            "Fipple may not couple efficiently to larger bore",
        ],
        feasibility="moderate",
        key_considerations=[
            "Fipple geometry must be scaled for bore size",
            "Closed top creates odd-harmonic series (different from recorder)",
            "Could produce unique timbre — flute-like attack, clarinet-like sustain",
        ],
    ),
    HybridInstrumentSpec(
        name="Bassoon Reed + Trumpet Body",
        mouthpiece_family="bassoon",
        body_family="trumpet",
        description="Double reed on trumpet bore. Combines reed articulation with brass brightness.",
        acoustic_challenges=[
            "Double reed impedance must match trumpet bore impedance",
            "Trumpet bore is much wider than bassoon — coupling is critical",
            "Valve mechanism must handle reed vibration without damping it",
        ],
        feasibility="experimental",
        key_considerations=[
            "Bassoon reed could work if bore diameter is reduced",
            "Leadpipe geometry becomes critical coupling element",
            "May produce oboe-like timbre with brass projection",
        ],
    ),
    HybridInstrumentSpec(
        name="Oboe Reed + Flute Body",
        mouthpiece_family="oboe",
        body_family="flute",
        description="Double reed on open cylindrical bore. Bright oboe timbre with flute agility.",
        acoustic_challenges=[
            "Double reed is high impedance; flute bore is lower impedance",
            "Flute's large tone holes may not work with double reed",
            "Embouchure for double reed vs flute lip plate is completely different",
        ],
        feasibility="hard",
        key_considerations=[
            "Double reed staple must match flute bore diameter",
            "Might need modified double reed (wider cane)",
            "Could create a 'double-reed flute' with unique timbre",
        ],
    ),
    HybridInstrumentSpec(
        name="Shakuhachi Mouthpiece + Recorder Body",
        mouthpiece_family="shakuhachi",
        body_family="recorder",
        description="End-blown edge tone on conical bore. Japanese aesthetic with Western fingering.",
        acoustic_challenges=[
            "Shakuhachi requires precise air angle — hard on fipple recorder",
            "Recorder bore is conical but smaller than shakuhachi",
            "Pitch bending technique of shakuhachi may not transfer",
        ],
        feasibility="moderate",
        key_considerations=[
            "Shakuhachi utaguchi (blowing edge) must be adapted",
            "Recorder's fipple mechanism may conflict with end-blown technique",
            "Could create an accessible 'shakuhachi for Western players'",
        ],
    ),
]