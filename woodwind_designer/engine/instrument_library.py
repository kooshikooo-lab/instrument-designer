from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InstrumentEntry:
    name: str
    family: str
    subcategory: str
    description: str
    type_label: str
    range: str
    key: str
    source: str
    source_url: str = ""
    download_url: str = ""
    image_url: str = ""
    audio_url: str = ""
    demakein_preset: str = ""
    tags: list = field(default_factory=list)
    difficulty: str = "Beginner"


LIBRARY: list[InstrumentEntry] = [
    # ##############################################################
    # WIND > FLUTE
    # ##############################################################
    InstrumentEntry(
        name="Penny Whistle (Tin Whistle)",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="D",
        source="Demakein Built-in",
        demakein_preset="folk_whistle",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tin_whistle_in_D.JPG/640px-Tin_whistle_in_D.JPG",
        audio_url="https://www.youtube.com/watch?v=DMZcX8joXG8",
        download_url="https://github.com/pfh/demakein",
        tags=["beginner", "folk", "irish", "6-hole"],
        difficulty="Beginner",
        description="Classic 6-hole tin whistle in D. The most popular starter flute. "
                    "Pennywhistle fingering, two full octaves.",
    ),
    InstrumentEntry(
        name="Folk Flute",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="D",
        source="Demakein Built-in",
        demakein_preset="folk_flute",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tin_whistle_in_D.JPG/640px-Tin_whistle_in_D.JPG",
        audio_url="https://www.youtube.com/watch?v=SJ2ScDqRMAA",
        download_url="https://github.com/pfh/demakein",
        tags=["beginner", "folk", "6-hole"],
        difficulty="Beginner",
        description="Pennywhistle-style folk flute with 6 finger holes. "
                    "Simple fingering system based on the penny whistle.",
    ),
    InstrumentEntry(
        name="Recorder (Soprano)",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="recorder",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Soprano_recorder.jpg/640px-Soprano_recorder.jpg",
        audio_url="https://www.youtube.com/watch?v=Z3NqPppUIMk",
        download_url="https://github.com/pfh/demakein",
        tags=["beginner", "baroque", "8-hole", "classical"],
        difficulty="Beginner",
        description="Full soprano recorder with Baroque fingering system. "
                    "8 holes covering two octaves.",
    ),
    InstrumentEntry(
        name="Dorian Whistle",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="D (Dorian)",
        source="Demakein Built-in",
        demakein_preset="dorian_whistle",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tin_whistle_in_D.JPG/640px-Tin_whistle_in_D.JPG",
        audio_url="https://www.youtube.com/watch?v=DMZcX8joXG8",
        download_url="https://github.com/pfh/demakein",
        tags=["beginner", "folk", "modal"],
        difficulty="Beginner",
        description="Whistle tuned to the Dorian mode. "
                    "Produces a moody, minor-style scale ideal for folk music.",
    ),
    InstrumentEntry(
        name="Three-Hole Whistle (Tabor Pipe)",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="D",
        source="Demakein Built-in",
        demakein_preset="three_hole_whistle",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Galoubet.JPG/640px-Galoubet.JPG",
        audio_url="https://www.youtube.com/watch?v=4NfWf-hURQc",
        download_url="https://github.com/pfh/demakein",
        tags=["beginner", "medieval", "folk", "3-hole"],
        difficulty="Beginner",
        description="Medieval three-hole tabor pipe. Played with one hand "
                    "while the other hand plays a drum (tabor).",
    ),
    InstrumentEntry(
        name="BASS Tin Whistle (in A)",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Bass", key="A",
        source="Printables – Tofu_Panda",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=DMZcX8joXG8",
        download_url="https://www.printables.com/model/1499495-bass-tin-whistle-in-a",
        tags=["intermediate", "whistle", "bass", "low-a", "large"],
        difficulty="Intermediate",
        description="A low A bass tin whistle. Produces a deep, rich whistle tone "
                    "a fourth below the classic D tin whistle. Larger build, "
                    "satisfying low-end sound for folk and ambient music.",
    ),
    InstrumentEntry(
        name="Pan Flute",
        family="Wind", subcategory="Flute", type_label="Pan Flute",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="pflute",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Pan_flute.jpg/640px-Pan_flute.jpg",
        audio_url="https://www.youtube.com/watch?v=0hnsJ-42Vns",
        download_url="https://github.com/pfh/demakein",
        tags=["intermediate", "panpipes", "folk", "multiple-pipes"],
        difficulty="Intermediate",
        description="Multi-pipe pan flute (panpipes) with graduated tubes. "
                    "Each pipe produces one note. Layout similar to the "
                    "traditional Andean siku or Romanian nai.",
    ),
    InstrumentEntry(
        name="Whistle Pan Flute",
        family="Wind", subcategory="Flute", type_label="Pan Flute",
        range="Soprano", key="C",
        source="Printables – dp makes",
        image_url="https://media.printables.com/media/prints/160312/images/314365_eb3987af-4fb2-4f38-a6f1-35687d3681d8/thumbs/inside/1600x1200/jpg/20210828_134813.webp",
        audio_url="https://www.youtube.com/watch?v=0hnsJ-42Vns",
        download_url="https://www.printables.com/model/160312-whistle-pan-flute",
        tags=["beginner", "panpipes", "whistle", "printable", "no-supports"],
        difficulty="Beginner",
        description="A 7-pipe whistle-style pan flute. Each pipe is a "
                    "separate whistle tuned by length. No supports needed.",
    ),
    InstrumentEntry(
        name="Daphnis Pan Flute",
        family="Wind", subcategory="Flute", type_label="Pan Flute",
        range="Alto", key="C",
        source="Printables – DSpecter",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=0hnsJ-42Vns",
        download_url="https://www.printables.com/model/439762-daphnis-a-3d-printable-pan-flute-v10",
        tags=["intermediate", "panpipes", "classical", "tuned", "multi-pipe"],
        difficulty="Intermediate",
        description="A tuned 3D-printable pan flute. Graduated pipes in a "
                    "curved arrangement for easy playability. Print each pipe "
                    "separately, tune by sanding the tops, then glue together.",
    ),
    InstrumentEntry(
        name="Slide Whistle",
        family="Wind", subcategory="Flute", type_label="Slide Whistle",
        range="Soprano", key="Variable",
        source="Printables – Tangibility",
        image_url="https://media.printables.com/media/prints/560049/images/4463295_78a5db32-0bb8-4baf-95fd-9c8664997be9/thumbs/inside/1600x1200/jpg/20230821_214012.webp",
        audio_url="https://www.youtube.com/watch?v=Q3rYRUG6Q2I",
        download_url="https://www.printables.com/model/560049-slide-whistle",
        tags=["beginner", "slide", "glissando", "whistle", "fun"],
        difficulty="Beginner",
        description="A slide whistle (piston flute) that varies pitch via "
                    "a sliding piston. Great for sound effects and glissandi.",
    ),
    InstrumentEntry(
        name="Transverse Flute (C)",
        family="Wind", subcategory="Flute", type_label="Transverse Flute",
        range="Soprano", key="C",
        source="Printables – ORM",
        image_url="https://media.printables.com/media/prints/577149/images/4747814_2525ccfd-4678-4bb3-9c43-3e5f3429249c/thumbs/inside/1600x1200/jpg/20240619_131025.webp",
        audio_url="https://www.youtube.com/watch?v=7aEyHc3N4BY",
        download_url="https://www.printables.com/model/577149-transverse-flute-in-the-key-of-c",
        tags=["intermediate", "side-blown", "classical", "6-hole"],
        difficulty="Intermediate",
        description="Side-blown transverse flute in the key of C. "
                    "6 finger holes, based on simple-system flute design.",
    ),
    InstrumentEntry(
        name="Axianov Irish Flute (D)",
        family="Wind", subcategory="Flute", type_label="Transverse Flute",
        range="Tenor", key="D",
        source="Printables – Marat Axianoff",
        image_url="https://woozle.org/blog/2024/12-04-3d-printed-flute/flute-on-chair.jpg",
        audio_url="https://www.youtube.com/watch?v=tF9X-xXbwEQ",
        download_url="https://www.printables.com/model/1097180-axianov-irish-flute",
        tags=["intermediate", "side-blown", "irish", "6-hole", "keyless", "historical"],
        difficulty="Intermediate",
        description="Keyless Irish transverse flute in D, designed by professional "
                    "Russian flutemaker Marat Axianoff. Open-hole, no keys, based on "
                    "pre-Boehm 1600s design. Hundreds of successful builds worldwide. "
                    "3-piece construction, prints for ~$5 of PLA. No post-processing needed.",
    ),
    InstrumentEntry(
        name="Side-Blown Flute in A Major",
        family="Wind", subcategory="Flute", type_label="Transverse Flute",
        range="Alto", key="A",
        source="Printables – Nicolas Bras",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=UJITjxPpH4E",
        download_url="https://www.printables.com/model/1001883-side-blown-flute-in-a-major",
        tags=["intermediate", "side-blown", "6-hole", "professional"],
        difficulty="Intermediate",
        description="3-part side-blown flute in A major by professional musician "
                    "Nicolas Bras. 6 finger holes, glue-together assembly. Sand holes "
                    "lightly, then ready to play. Well-tested design with good intonation.",
    ),
    InstrumentEntry(
        name="Traditional Bansuri B Natural",
        family="Wind", subcategory="Flute", type_label="Transverse Flute",
        range="Tenor", key="B (Natural)",
        source="Cults3D – Odell-Creations",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=9LqKIB8Vx0M",
        download_url="https://cults3d.com/en/3d-model/gadget/traditional-keyless-north-indian-bansuri-b-natural-transverse-flute",
        tags=["intermediate", "bansuri", "indian", "large-bore", "keyless"],
        difficulty="Intermediate",
        description="Traditional keyless North Indian Bansuri in B Natural. Designed "
                    "to match genuine bamboo bansuri as closely as possible with 3D "
                    "printing. Large bore, deep mellow sound. PETG recommended, prints "
                    "without supports. 3-piece design with tight-fitting joints.",
    ),
    InstrumentEntry(
        name="Dragon Recorder",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="C",
        source="Printables – P1lotz",
        image_url="https://media.printables.com/media/prints/400647/images/3296182_6a660404-4a45-448e-b29b-dc3ab0d7a5d3/thumbs/inside/1600x1200/jpg/20230420_220007.webp",
        audio_url="https://www.youtube.com/watch?v=Z3NqPppUIMk",
        download_url="https://www.printables.com/model/400647-dragon-recorder",
        tags=["beginner", "recorder", "dragon", "decorative", "printable"],
        difficulty="Beginner",
        description="A soprano recorder shaped like a dragon. Fully "
                    "playable with Baroque fingering. Fun decorative design.",
    ),
    InstrumentEntry(
        name="Glissonardo",
        family="Wind", subcategory="Flute", type_label="Fipple Flute",
        range="Soprano", key="C",
        source="Printables – Glissonic Instruments",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=WkO2SY7WfpI",
        download_url="https://www.printables.com/model/1516682-glissonardo",
        tags=["intermediate", "recorder", "glissando", "da-vinci", "historical"],
        difficulty="Intermediate",
        description="Small recorder-type wind instrument based on Leonardo da "
                    "Vinci's 'fissure flute' from the Codex Atlanticus. Uses a "
                    "sliding finger over a slit for continuous pitch changes. "
                    "Range over an octave. Designed by Glissonic Instruments.",
    ),
    # -- Ocarinas --
    InstrumentEntry(
        name="12-Hole Ocarina (Alto C)",
        family="Wind", subcategory="Flute", type_label="Vessel Flute",
        range="Alto", key="C",
        source="Printables – Mikolas Zuza",
        image_url="https://media.printables.com/media/prints/24540/images/40728_f1b60cd5-5a62-4c04-8bb8-6dbe59fc7496/thumbs/inside/1600x1200/jpg/20191208_104619.webp",
        audio_url="https://www.youtube.com/watch?v=kE9Q1YHQ_nw",
        download_url="https://www.printables.com/model/24540-12-hole-playable-ocarina",
        tags=["intermediate", "ocarina", "vessel", "12-hole", "tuned"],
        difficulty="Intermediate",
        description="Fully playable 12-hole ocarina in Alto C. "
                    "Covers over an octave with accurate tuning. "
                    "Round vessel flute design with extended range.",
    ),
    InstrumentEntry(
        name="Small 5-Hole Ocarina",
        family="Wind", subcategory="Flute", type_label="Vessel Flute",
        range="Soprano", key="C",
        source="Printables – Julius3E8",
        image_url="https://media.printables.com/media/prints/249010/images/198208_c0e531ad-b62d-48cc-9d33-b22e45893f2e/thumbs/inside/1600x1200/jpg/20220524_125106.webp",
        audio_url="https://www.youtube.com/watch?v=kE9Q1YHQ_nw",
        download_url="https://www.printables.com/model/249010-small-5-hole-ocarina-for-kids",
        tags=["beginner", "ocarina", "kids", "small", "vessel"],
        difficulty="Beginner",
        description="Small 5-hole ocarina for kids (C5–D6). "
                    "Prints without supports, plays right off the build plate.",
    ),

    # ##############################################################
    # WIND > WOODWIND
    # ##############################################################
    InstrumentEntry(
        name="Reedpipe",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="reedpipe",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Practice_chanter.jpg/640px-Practice_chanter.jpg",
        audio_url="https://www.youtube.com/watch?v=FYH5Nhf3J0o",
        download_url="https://github.com/pfh/demakein",
        tags=["beginner", "reed", "clarinet-like", "practice"],
        difficulty="Beginner",
        description="Simple single-reed pipe. Like a clarinet practice chanter. "
                    "Great introduction to reed instruments.",
    ),
    InstrumentEntry(
        name="Modern Chalumeau in C (Clarinet)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="C",
        source="Printables – Tom",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=weU1eW8vMQA",
        download_url="https://www.printables.com/model/752555-clarinet-modern-chalumeau-in-c",
        tags=["intermediate", "clarinet", "chalumeau", "single-reed", "keyed"],
        difficulty="Intermediate",
        description="Simple clarinet in C with two extension keys. Suitable for "
                    "Vandoren Eb clarinet mouthpiece. 3-part body with bell, barrel, "
                    "and main section. Updated with corrected finger hole positions. "
                    "Good entry point for 3D-printed clarinet builds.",
    ),
    InstrumentEntry(
        name="C Clarinet Remix (14mm Bore)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="C",
        source="Printables – Gubbledenut",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=weU1eW8vMQA",
        download_url="https://www.printables.com/model/888905-c-clarinet-remix",
        tags=["intermediate", "clarinet", "chalumeau", "14mm-bore", "remix", "tunable"],
        difficulty="Intermediate",
        description="Remix of Tom's Chalumeau with 14mm bore (vs original narrower "
                    "bore), 3-part split body, and adjustable tuning via bell and barrel. "
                    "Fixes intonation issues of the original design. Barrel fits standard "
                    "Eb mouthpiece. RAised key blocks away from body.",
    ),
    InstrumentEntry(
        name="Membrane Clarinet",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="Variable",
        source="Printables – DrJones",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=Jk7J4_bneZo",
        download_url="https://www.printables.com/model/495171-membrane-clarinet",
        tags=["intermediate", "clarinet", "membrane", "no-reed", "screw-together"],
        difficulty="Intermediate",
        description="Fully 3D-printed clarinet with no metal keys or reeds needed. "
                    "Uses a thin plastic sheet (bag foil or space blanket) as a membrane "
                    "reed. 3 screw-together parts with left-hand/right-hand threads. "
                    "Membrane holder offers 2 degrees of freedom for tuning. Inspired "
                    "by Nicolas Bras' membrane clarinet concept.",
    ),
    InstrumentEntry(
        name="Curvy Clarinet",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="C",
        source="Printables – Nkosi Smith",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=weU1eW8vMQA",
        download_url="https://www.printables.com/model/1605969-curvy-clarinet",
        tags=["intermediate", "clarinet", "curvy", "compact", "soprano-sax-mouthpiece"],
        difficulty="Intermediate",
        description="Compact curvy clarinet with a soprano saxophone mouthpiece. "
                    "6-note pentatonic layout with a relaxed, mellow tone. 3D-printed "
                    "body with elegant curved design. Good for beginners and as a "
                    "portable practice instrument.",
    ),
    InstrumentEntry(
        name="Alto Saxophone Hybrid (Zaxophone)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Alto", key="Bb",
        source="Cults3D – BEENRA",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=7fg7nB6I1n0",
        download_url="https://cults3d.com/en/3d-model/gadget/3d-printable-alto-saxophone-hybrid-instrument",
        tags=["advanced", "saxophone", "alto", "hybrid", "conical-bore", "3d-printable"],
        difficulty="Advanced",
        description="3D-printable alto saxophone hybrid (Zaxophone) combining an alto sax "
                    "mouthpiece with a recorder-like body and fingering system. Conical bore "
                    "tuned to Bb (fundamental Bb3, ~116.5 Hz). Uses standard alto sax "
                    "mouthpiece and reed. Print in sections (neck, body, bell) in PETG or ABS. "
                    "Simplified fingering for accessibility. Designed by BEENRA.",
    ),
    InstrumentEntry(
        name="3DP Minisax (Pocket Sax)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="Bb",
        source="Thingiverse – mldotjs",
        image_url="",
        audio_url="https://youtu.be/deijf9jOcm4",
        download_url="https://www.thingiverse.com/thing:4732605",
        tags=["intermediate", "saxophone", "mini", "pocket", "xaphoon", "single-reed"],
        difficulty="Intermediate",
        description="3D-printed variant of the MiniSax / Xaphoon / pocket sax. A compact "
                    "single-reed instrument with a simple tube body and finger holes. "
                    "Designed as an affordable alternative to commercial pocket saxophones. "
                    "Uses a standard soprano sax or clarinet mouthpiece. Free STL files.",
    ),
    InstrumentEntry(
        name="Bb Soprano Clarinet (Body STL)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="Bb",
        source="JDWoodwinds (Commercial STL)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=weU1eW8vMQA",
        download_url="https://jdwoodwind.com/shop/p/3d-clarinet-model",
        tags=["expert", "clarinet", "boehm", "keywork-required", "commercial-stl"],
        difficulty="Expert",
        description="STL file for 3D-printable Bb soprano clarinet body, barrel, and bell. "
                    "Designed for Eastar keywork (donor clarinet required). Output is the "
                    "printed body only — you must install real clarinet keys. Recommended "
                    "for experienced clarinet repair technicians. By JDWoodwinds.",
    ),
    InstrumentEntry(
        name="Piccolo Clarinet in A Natural",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Sopranino", key="A",
        source="JDWoodwinds (Commercial STL)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=weU1eW8vMQA",
        download_url="https://jdwoodwind.com/shop/p/piccolo-clarinet-stl",
        tags=["expert", "clarinet", "piccolo", "high-pitch", "rare", "commercial-stl"],
        difficulty="Expert",
        description="STL file for a piccolo clarinet in A natural — a rare high-pitch "
                    "member of the clarinet family. Requires donor keywork for assembly. "
                    "Very compact instrument, pitches higher than the standard Bb clarinet. "
                    "For expert builders only. By JDWoodwinds.",
    ),
    InstrumentEntry(
        name="Bass Clarinet in G (STL)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Bass", key="G",
        source="JDWoodwinds (Commercial STL)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=_qg4z5eXno4",
        download_url="https://jdwoodwind.com/shop/p/stl-files-bass-clarinet-in-g",
        tags=["expert", "clarinet", "bass", "g-clarinet", "keywork-required", "commercial-stl"],
        difficulty="Expert",
        description="STL files for a 3D-printable bass clarinet in G. Simplified Boehm "
                    "system keywork, 30mm bass clarinet pad, bell procured from China (eBay). "
                    "Requires donor keywork and bass clarinet pads. Minimum 250mm build "
                    "height. PLA+ recommended. Expert level — requires clarinet repair "
                    "skills. By JDWoodwinds.",
    ),
    InstrumentEntry(
        name="EEEb Octocontra-alto Clarinet",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Sub-contrabass", key="EEEb",
        source="JDWoodwinds (Commercial 3MF)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=yNtABfHKjDs",
        download_url="https://jdwoodwind.com/shop/p/3mf-octocontra-alto-clarinet",
        tags=["expert", "clarinet", "octocontra", "sub-contrabass", "largest", "commercial-stl"],
        difficulty="Expert",
        description="3MF file for an EEEb octocontra-alto clarinet — one of the largest "
                    "and rarest members of the clarinet family. Pitched a fifth below the "
                    "Bb contrabass clarinet and one octave below the Eb contra-alto. Only "
                    "two prototype examples were ever built historically (Leblanc, 1930s). "
                    "This is a 3D-printable recreation. Expert level only. By JDWoodwinds.",
    ),
    InstrumentEntry(
        name="17-Key Boehm Clarinet (Display)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="Bb",
        source="Cults3D – kwyk_Mini",
        image_url="",
        audio_url="",
        download_url="https://cults3d.com/en/3d-model/various/clarinette-boehm-17-clef",
        tags=["beginner", "clarinet", "boehm", "decorative", "display", "resin"],
        difficulty="Beginner",
        description="Detailed 17-key Boehm clarinet model for 3D printing. Body and "
                    "keys printed as a single solid piece (bore is solid, not hollow). "
                    "Designed for resin printing. Decorative/display only — not playable "
                    "without significant modification. Good for props, teaching aids, "
                    "or miniatures when scaled down.",
    ),
    InstrumentEntry(
        name="Heckelphone-clarinet (Heckelphon-Klarinette)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Baritone", key="Bb",
        source="Historical (Wilhelm Heckel, 1907)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=MkSnRRGqMFc",
        download_url="",
        tags=["museum", "historical", "heckel", "conical-bore", "rare", "single-reed"],
        difficulty="Expert",
        description="The heckelphone-clarinet (Heckelphon-Klarinette) is an extremely rare "
                    "woodwind invented in 1907 by Wilhelm Heckel. Despite the name, it is "
                    "essentially a wooden saxophone — wide conical bore, red-stained maple, "
                    "single reed, overblowing the octave. Only 12-15 were ever made. Serial "
                    "#2 is the only surviving example in private hands. Range D3-C6. Softer "
                    "tone than saxophone. No STL files available — historical reference.",
    ),
    InstrumentEntry(
        name="Saxonette (Clariphon / Claribel)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="Bb/C/A",
        source="Historical (Buescher, 1918)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=M_x5UfmZ-14",
        download_url="",
        tags=["museum", "historical", "clarinet", "curved", "saxophone-shaped", "1920s"],
        difficulty="Expert",
        description="The saxonette (also Clariphon or Claribel) is a soprano clarinet in "
                    "Bb, C, or A with a curved metal barrel and upturned bell — giving it "
                    "the visual shape of a saxophone while remaining a standard cylindrical-"
                    "bore clarinet. Produced by Buescher (1918-1921) and Gretsch (1923). "
                    "Albert system, occasionally Boehm. No STL files available.",
    ),
    InstrumentEntry(
        name="Conn-o-Sax",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Soprano", key="F",
        source="Historical (C.G. Conn, 1928)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=KCVCca5dqJw",
        download_url="",
        tags=["museum", "historical", "conn", "hybrid", "rare", "single-reed", "1920s"],
        difficulty="Expert",
        description="The Conn-o-Sax is a rare hybrid woodwind built by C.G. Conn in 1928. "
                    "A single-reed instrument pitched in F (between alto and soprano sax), "
                    "with a straight body, curved neck, and spherical bell. Only a small "
                    "number were produced. Designed as a novelty instrument for jazz and "
                    "dance bands. No STL files available — historical reference.",
    ),
    InstrumentEntry(
        name="Folk Shawm",
        family="Wind", subcategory="Woodwind", type_label="Double Reed",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="folk_shawm",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Shawm.jpg/640px-Shawm.jpg",
        audio_url="https://www.youtube.com/watch?v=HwL5ISrEe_M",
        download_url="https://github.com/pfh/demakein",
        tags=["intermediate", "double-reed", "folk", "shawn"],
        difficulty="Intermediate",
        description="Double-reed folk shawm with compact hole placement. "
                    "Related to the oboe, bombarde, and traditional shawm. "
                    "Uses a drinking-straw reed.",
    ),
    InstrumentEntry(
        name="Shawm",
        family="Wind", subcategory="Woodwind", type_label="Double Reed",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="shawm",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Shawm.jpg/640px-Shawm.jpg",
        audio_url="https://www.youtube.com/watch?v=JoaiLceiFZA",
        download_url="https://github.com/pfh/demakein",
        tags=["advanced", "double-reed", "medieval", "full-size"],
        difficulty="Advanced",
        description="Full-size double-reed shawm. Larger and more "
                    "powerful than the folk shawm, with a wider bore "
                    "and traditional exterior profile.",
    ),
    InstrumentEntry(
        name="Reed Drone",
        family="Wind", subcategory="Woodwind", type_label="Single Reed",
        range="Bass", key="C",
        source="Demakein Built-in",
        demakein_preset="reed_drone",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Practice_chanter.jpg/640px-Practice_chanter.jpg",
        audio_url="https://www.youtube.com/watch?v=jQKjFGIAXjA",
        download_url="https://github.com/pfh/demakein",
        tags=["intermediate", "drone", "bagpipe", "continuous"],
        difficulty="Intermediate",
        description="Continuous-sounding reed drone pipe. "
                    "Intended for use as a bagpipe drone or held drone instrument.",
    ),
    InstrumentEntry(
        name="Rackett (Sausage Bassoon)",
        family="Wind", subcategory="Woodwind", type_label="Double Reed",
        range="Bass", key="C",
        source="Printables – PyroSteel",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=QwPgiVCVxEA",
        download_url="https://www.printables.com/model/1014532-rackett",
        tags=["advanced", "double-reed", "renaissance", "historical", "compact-bass"],
        difficulty="Advanced",
        description="Renaissance-era double reed instrument, also known as the "
                    "sausage bassoon or cervalas. Achieves a very low bass range "
                    "in a compact body by folding multiple parallel bores. Quiet, "
                    "mellow tone. Requires reed making skills.",
    ),
    InstrumentEntry(
        name="Glissotar (Soprano)",
        family="Wind", subcategory="Woodwind", type_label="Single Reed + Slit",
        range="Soprano", key="C",
        source="Custom Design",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Practice_chanter.jpg/640px-Practice_chanter.jpg",
        audio_url="https://www.youtube.com/watch?v=35HX0DXYB_0",
        download_url="",
        tags=["advanced", "experimental", "glissando", "continuous"],
        difficulty="Advanced",
        description="Continuous glissando woodwind. Conical bore with a "
                    "sliding slit mechanism for seamless pitch bends. "
                    "Hybrid between a tarogato and experimental acoustics.",
    ),
    InstrumentEntry(
        name="Glissotar Bass Clarinet",
        family="Wind", subcategory="Woodwind", type_label="Single Reed + Slit",
        range="Bass", key="Bb",
        source="Custom Design",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Bass_clarinet.jpg/640px-Bass_clarinet.jpg",
        audio_url="https://www.youtube.com/watch?v=35HX0DXYB_0",
        download_url="",
        tags=["advanced", "experimental", "glissando", "bass"],
        difficulty="Advanced",
        description="Hybrid bass clarinet with continuous glissando slit. "
                    "Combines deep bass clarinet tone with smooth pitch sliding. "
                    "Cylindrical bore, bass reed, 900mm length.",
    ),
    InstrumentEntry(
        name="Kazoo",
        family="Wind", subcategory="Woodwind", type_label="Free Reed",
        range="Soprano", key="Variable",
        source="Printables – PistonPin",
        image_url="https://media.printables.com/media/prints/30637/images/54951_a3a14df9-198a-4d95-b4f4-5122122e1cb0/thumbs/inside/1600x1200/jpg/kazoo.webp",
        audio_url="https://www.youtube.com/watch?v=iC65ufGUvKM",
        download_url="https://www.printables.com/model/30637-kazoo",
        tags=["beginner", "kazoo", "free-reed", "membrane", "fun"],
        difficulty="Beginner",
        description="Classic kazoo — a membrane free-reed instrument. "
                    "Hum into it to produce a buzzing tone. Quick print.",
    ),
    InstrumentEntry(
        name="Double Native American Flute",
        family="Wind", subcategory="Woodwind", type_label="Fipple Flute",
        range="Tenor", key="F#",
        source="Printables – Pro3Druk",
        image_url="https://media.printables.com/media/prints/452234/images/3711074_005a2640-4814-44ce-8f25-5557859a28a3/thumbs/inside/1600x1200/jpg/20230717_104256.webp",
        audio_url="https://www.youtube.com/watch?v=DSkOyh5yVTI",
        download_url="https://www.printables.com/model/452234-double-flute",
        tags=["intermediate", "native-american", "drone", "double"],
        difficulty="Intermediate",
        description="Double Native American style flute in F#. "
                    "Features a melody pipe and a separate drone pipe. "
                    "Plays with a haunting, rich harmony.",
    ),

    # ##############################################################
    # WIND > BRASS
    # ##############################################################
    InstrumentEntry(
        name="Overly-Complicated Trumpet",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Soprano", key="Bb",
        source="Printables – GCV3D",
        image_url="https://media.printables.com/media/prints/492588/images/4003235_9b8be94b-5141-4516-b68e-7677b04a60b9/thumbs/inside/1600x1200/jpg/20230902_220315.webp",
        audio_url="https://www.youtube.com/watch?v=ZNs3KedfB5I",
        download_url="https://www.printables.com/model/492588-overly-complicated-trumpet-fully-3d-printed-projec",
        tags=["advanced", "brass", "trumpet", "valve", "large-print"],
        difficulty="Advanced",
        description="Fully 3D-printed trumpet with 6 slide-based valves. "
                    "Based on Bb trumpet tubing lengths. Large multi-part print.",
    ),
    InstrumentEntry(
        name="Kudu Horn Trumpet (Shofar)",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Alto", key="Variable",
        source="Printables – Bob",
        image_url="https://media.printables.com/media/prints/217052/images/170379_fa1bc7d4-6c16-4915-812c-4b407524394b/thumbs/inside/1600x1200/jpg/kudu_horn_trumpet_shofar.webp",
        audio_url="https://www.youtube.com/watch?v=2jNqvVKOlKM",
        download_url="https://www.printables.com/model/217052-kudu-horn-trumpet-shofar",
        tags=["intermediate", "brass", "horn", "shofar", "decorative"],
        difficulty="Intermediate",
        description="Functional Kudu horn trumpet (shofar). "
                    "Smooth spiral shape, plays as a natural brass instrument. "
                    "~660mm tall, can be printed in sections.",
    ),
    InstrumentEntry(
        name="Mini Ophicleide (Keyless Serpent)",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Bass", key="C",
        source="Printables – Melmaking",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=t9mB72TC8Kw",
        download_url="https://www.printables.com/model/478359-mini-ophicleide",
        tags=["advanced", "brass", "ophicleide", "serpent", "keyless", "historical"],
        difficulty="Advanced",
        description="Keyless mini ophicleide / serpent. A compact bass brass "
                    "instrument based on the 19th-century ophicleide and the "
                    "older serpent. Uses a cup mouthpiece (trumpet mouthpiece). "
                    "6 finger holes produce a chromatic bass range. Compact and portable.",
    ),
    InstrumentEntry(
        name="PrintBone Trombone (3D-Printed)",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Tenor", key="Bb",
        source="Printables – PieterB",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=H_VVgddzFDI",
        download_url="https://www.printables.com/model/80017-the-printbone-v11-a-fully-printable-playable-tromb",
        tags=["advanced", "trombone", "brass", "slide", "openscad", "large-print"],
        difficulty="Advanced",
        description="The PrintBone v1.1 is a fully 3D-printed playable trombone. 8.5-inch "
                    "bell, fits a Bach 42 or 50 slide connector. Can be paired with a brass "
                    "slide or PVC/ carbon fiber slide. OpenSCAD sources on GitHub allow "
                    "parameterized customization. Large build volume required (210x220x200mm "
                    "minimum). 25-40% infill recommended. By PieterB.",
    ),
    InstrumentEntry(
        name="Jazzophone (Sax-Shaped Trumpet)",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Soprano", key="Bb",
        source="Historical (1920s, Graslitz)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=uMhE4qk8G6c",
        download_url="",
        tags=["museum", "historical", "jazzophone", "1920s", "two-bell", "sax-shaped"],
        difficulty="Expert",
        description="The Jazzophone is a rare 1920s brass instrument — a trumpet built in "
                    "the shape of a saxophone with two bells. One bell sounds like a normal "
                    "trumpet, the other like a muted trumpet (built-in wah-wah mute). Three "
                    "regular trumpet valves plus a 4th upside-down valve to switch bells. "
                    "Invented in Graslitz (Czechoslovakia) as a cheaper alternative to the "
                    "saxophone in jazz bands. ~100 made. No STL files available.",
    ),
    InstrumentEntry(
        name="Normaphone (Sax-Shaped Brass)",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Tenor", key="Bb",
        source="Historical (Heber, 1924)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=4LAkLc-qUvE",
        download_url="",
        tags=["museum", "historical", "normaphone", "1920s", "sax-shaped", "jazz"],
        difficulty="Expert",
        description="The Normaphone is a 1920s saxophone-shaped brass instrument invented "
                    "by Richard Oskar Heber in Markneukirchen, Germany. Built as a cheaper "
                    "alternative to the saxophone — any trumpeter, hornist, or bassist could "
                    "play it without retraining. Four sizes: soprano, alto, tenor, bass. "
                    "Three Perinet or rotary valves. Advertised as 'very appropriate for "
                    "jazz bands and other effect ensembles'. ~100 produced. No STL available.",
    ),
    InstrumentEntry(
        name="Sudrophone (Ophicleide Brass + Mirliton)",
        family="Wind", subcategory="Brass", type_label="Brass",
        range="Baritone", key="C/Bb",
        source="Historical (Sudre, 1892)",
        image_url="",
        audio_url="https://www.youtube.com/watch?v=R6v9UfqHYCM",
        download_url="",
        tags=["museum", "historical", "sudrophone", "ophicleide", "mirliton", "1890s"],
        difficulty="Expert",
        description="The Sudrophone is a brass instrument invented by François Sudre in "
                    "1892. Conical bore, 3–4 Perinet valves, ophicleide-shaped body. Its "
                    "unique feature: a mirliton (kazoo-like silk membrane) on the bell "
                    "that can be engaged to create a nasal cello-like or bassoon-like tone. "
                    "Designed to stand out from the saxhorn family. No STL files available.",
    ),

    # ##############################################################
    # WIND > DRONE & OTHERS
    # ##############################################################
    InstrumentEntry(
        name="HEXADIDG Didgeridoo",
        family="Wind", subcategory="Drone & Others", type_label="Drone",
        range="Bass", key="Variable",
        source="Printables – L3V3C",
        image_url="https://media.printables.com/media/prints/734618/images/5890934_9ab37dbc-c6e1-4e4d-99a7-31962d1b6091/thumbs/inside/1600x1200/jpg/20240720_180706.webp",
        audio_url="https://www.youtube.com/watch?v=W3UdnEIjowU",
        download_url="https://www.printables.com/model/734618-hexadidg-and-hexadidg-mini-3d-printable-didgeridoo",
        tags=["intermediate", "didgeridoo", "drone", "australian", "hexagonal"],
        difficulty="Intermediate",
        description="3D-printable hexagonal didgeridoo. Produces a deep "
                    "drone tone. Two sizes: full and mini. "
                    "Designed to be printed in segments and glued.",
    ),
    InstrumentEntry(
        name="D5 Drone Flute",
        family="Wind", subcategory="Drone & Others", type_label="Drone",
        range="Alto", key="D (Hijaz)",
        source="MakerWorld – pitchblackcat",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tin_whistle_in_D.JPG/640px-Tin_whistle_in_D.JPG",
        audio_url="https://www.youtube.com/watch?v=DSkOyh5yVTI",
        download_url="https://makerworld.com/en/models/566278-d5-drone-flute-v1-hijaz-tuning",
        tags=["intermediate", "drone", "flute", "hijaz", "modal"],
        difficulty="Intermediate",
        description="Drone flute in D, tuned to the Hijaz maqam. "
                    "Produces a continuous droning sound with a middle-eastern scale.",
    ),
    # ##############################################################
    # WIND > PARTS & ACCESSORIES
    # ##############################################################
    # -- Clarinet / Bass Clarinet --
    InstrumentEntry(
        name="Clarinet Mouthpiece (Playable)",
        family="Wind", subcategory="Parts & Accessories", type_label="Mouthpiece",
        range="Bb", key="N/A",
        source="Printables – Dave Yeagly",
        image_url="https://media.printables.com/media/prints/557889/images/4472165_2a477c32-4f05-4ef1-a7ab-7962379767e1/thumbs/inside/1600x1200/jpg/20230813_191035.webp",
        audio_url="",
        download_url="https://www.printables.com/model/557889-clarinet-mouthpiece",
        tags=["clarinet", "mouthpiece", "single-reed", "playable", "sanding"],
        difficulty="Intermediate",
        description="Playable Bb clarinet mouthpiece. Flexible bulb eliminates "
                    "need for cork. Requires light sanding on reed-mating surface. "
                    "Tip opening 1.28mm. Print with minimal supports.",
    ),
    InstrumentEntry(
        name="Clarinet Barrels (Set of 4)",
        family="Wind", subcategory="Parts & Accessories", type_label="Barrel",
        range="Bb", key="N/A",
        source="Printables – D. Eichenbaum",
        image_url="https://media.printables.com/media/prints/446074/images/3656251_dd4ab8f3-412f-4931-a345-5f20e93fff72/thumbs/inside/1600x1200/jpg/20230705_210015.webp",
        audio_url="",
        download_url="https://www.printables.com/model/446074-3d-printable-clarinet-barrels",
        tags=["clarinet", "barrel", "tuning", "buffet", "advanced"],
        difficulty="Advanced",
        description="Four Bb clarinet barrels: Moennig-style, Beta 1 (straight "
                    "reverse taper), Beta 2 (higher choke), and 'Phil' (67mm). "
                    "Designed for Buffet instruments. 100% infill, concentric pattern.",
    ),
    InstrumentEntry(
        name="Bass Clarinet Mouthpiece Cover",
        family="Wind", subcategory="Parts & Accessories", type_label="Mouthpiece",
        range="Bass", key="N/A",
        source="Printables – luckyinstesign",
        image_url="https://media.printables.com/media/prints/727244/images/5832745_c76c001f-eb03-4597-8fc6-8ac5a3575c19/thumbs/inside/1600x1200/jpg/20240117_182138.webp",
        audio_url="",
        download_url="https://www.printables.com/model/727244-bass-clarinet-mouthpiece-cover",
        tags=["bass-clarinet", "mouthpiece", "cover", "protection"],
        difficulty="Beginner",
        description="Protective cover for bass clarinet mouthpiece. "
                    "Sized to fit standard bass clarinet mouthpieces. Quick print.",
    ),
    InstrumentEntry(
        name="3D-Printed Clarinet Reed (PLA)",
        family="Wind", subcategory="Parts & Accessories", type_label="Reed",
        range="Bb", key="N/A",
        source="Printables – vishal lokesh",
        image_url="https://media.printables.com/media/prints/1302786/images/10428885_4a8084b6-7ee4-4215-9a4c-ddc31105ecad/thumbs/inside/1600x1200/jpg/20250520_223650.webp",
        audio_url="",
        download_url="https://www.printables.com/model/1302786-3d-printed-clarinet-reed-pla-practice-display-or-t",
        tags=["clarinet", "reed", "practice", "teaching", "display"],
        difficulty="Beginner",
        description="PLA clarinet reed for practice, display, or teaching. "
                    "Fits standard Bb clarinet mouthpiece. Not intended for "
                    "performance use but great for silent practice.",
    ),
    # -- Saxophone --
    InstrumentEntry(
        name="Alto Saxophone Reed",
        family="Wind", subcategory="Parts & Accessories", type_label="Reed",
        range="Alto", key="Eb",
        source="Printables – Bommelpro",
        image_url="https://media.printables.com/media/prints/1180660/images/9400389_bf112639-0bdb-4686-a9f8-c451e86e9180/thumbs/inside/1600x1200/jpg/20250206_082452.webp",
        audio_url="",
        download_url="https://www.printables.com/model/1180660-alto-saxophone-reed",
        tags=["saxophone", "alto", "reed", "working"],
        difficulty="Intermediate",
        description="Working alto saxophone reed. Print at 0.08mm layer height "
                    "with 75% hexagon infill in PLA. Fits standard alto mouthpieces.",
    ),
    InstrumentEntry(
        name="Saxophone Ligatures",
        family="Wind", subcategory="Parts & Accessories", type_label="Ligature",
        range="Various", key="N/A",
        source="Printables – mrusk",
        image_url="https://media.printables.com/media/prints/1211918/images/9668945_b4ea9c14-d260-4a56-8452-5e0fb8b3a1e1/thumbs/inside/1600x1200/jpg/20250309_083249.webp",
        audio_url="",
        download_url="https://www.printables.com/model/1211918-windy-city-woodwinds-saxophone-ligatures",
        tags=["saxophone", "ligature", "reed", "accessory"],
        difficulty="Intermediate",
        description="Windy City Woodwinds saxophone ligatures. "
                    "Secures reed to mouthpiece. Multiple sizes available.",
    ),
    # -- Brass / Trumpet --
    InstrumentEntry(
        name="Trumpet Mouthpiece 3C",
        family="Wind", subcategory="Parts & Accessories", type_label="Mouthpiece",
        range="Bb", key="N/A",
        source="Printables – Gauthier",
        image_url="https://media.printables.com/media/prints/446505/images/3659168_259b1ea2-280e-4490-8a02-1c2f02bdfc35/thumbs/inside/1600x1200/jpg/20230706_175018.webp",
        audio_url="",
        download_url="https://www.printables.com/model/446505-trumpet-3c-mouthpiece",
        tags=["trumpet", "mouthpiece", "3c", "playable"],
        difficulty="Intermediate",
        description="Trumpet 3C mouthpiece based on Kanstul comparator profiles. "
                    "Features break-away foot for post-processing. Fully functional.",
    ),
    InstrumentEntry(
        name="Trumpet Mouthpiece 7C",
        family="Wind", subcategory="Parts & Accessories", type_label="Mouthpiece",
        range="Bb", key="N/A",
        source="Printables – MucusLaser",
        image_url="https://media.printables.com/media/prints/100591/images/188785_d3e9d7e6-46e8-48d0-9810-050aca724ba6/thumbs/inside/1600x1200/jpg/trumpet_mouthpiece_7c.webp",
        audio_url="",
        download_url="https://www.printables.com/model/100591-trumpet-mouthpiece-7c",
        tags=["trumpet", "mouthpiece", "7c", "playable", "standard"],
        difficulty="Beginner",
        description="Standard 7C trumpet mouthpiece. Print on its side for "
                    "strength. Works well for practice and casual playing.",
    ),
    InstrumentEntry(
        name="Trombone Mouthpieces (Set)",
        family="Wind", subcategory="Parts & Accessories", type_label="Mouthpiece",
        range="Tenor", key="N/A",
        source="Printables – Nicholas Oclassen",
        image_url="https://media.printables.com/media/prints/984672/images/7925650_b7439a10-ca47-4545-9ede-689f3ee67e89/thumbs/inside/1600x1200/jpg/20240824_140305.webp",
        audio_url="",
        download_url="https://www.printables.com/model/984672-trombone-mouthpieces-updated",
        tags=["trombone", "mouthpiece", "wedge", "bach", "schilke"],
        difficulty="Beginner",
        description="Set of trombone mouthpieces based on Wedge/Bach/Schilke "
                    "profiles. Each labeled with model number. Print with no supports.",
    ),
    # -- Brass accessory tools --
    InstrumentEntry(
        name="Trumpet Mouthpiece Puller",
        family="Wind", subcategory="Parts & Accessories", type_label="Tool",
        range="N/A", key="N/A",
        source="Printables – tnord",
        image_url="https://media.printables.com/media/prints/692679/images/5560577_fedc73fe-afd7-4a65-b7a2-40d5ad1a72d5/thumbs/inside/1600x1200/jpg/20231224_142818.webp",
        audio_url="",
        download_url="https://www.printables.com/model/692679-trumpet-mouthpiece-puller",
        tags=["trumpet", "tool", "mouthpiece", "puller", "repair"],
        difficulty="Beginner",
        description="Tool for removing stuck mouthpieces from trumpets. "
                    "Uses 1/4-20 hardware. 4 printed parts + bolts and wingnuts.",
    ),
]


def get_families() -> list[str]:
    seen = set()
    result = []
    for e in LIBRARY:
        if e.family not in seen:
            seen.add(e.family)
            result.append(e.family)
    return result


def get_subcategories(family: str) -> list[str]:
    seen = set()
    result = []
    for e in LIBRARY:
        if e.family == family and e.subcategory not in seen:
            seen.add(e.subcategory)
            result.append(e.subcategory)
    return result


def get_by_family(family: str) -> list[InstrumentEntry]:
    return [e for e in LIBRARY if e.family.lower() == family.lower()]


def get_by_subcategory(family: str, sub: str) -> list[InstrumentEntry]:
    return [e for e in LIBRARY if e.family.lower() == family.lower() and e.subcategory.lower() == sub.lower()]


def get_by_preset(preset: str) -> Optional[InstrumentEntry]:
    for e in LIBRARY:
        if e.demakein_preset == preset:
            return e
    return None


def get_type_labels(family: str, subcategory: str) -> list[str]:
    seen = set()
    result = []
    for e in LIBRARY:
        if e.family == family and e.subcategory == subcategory and e.type_label not in seen:
            seen.add(e.type_label)
            result.append(e.type_label)
    return result


def get_tags() -> list[str]:
    tags = set()
    for e in LIBRARY:
        for t in e.tags:
            tags.add(t)
    return sorted(tags)
