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
        download_url="https://github.com/introlab/demakein",
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
        download_url="https://github.com/introlab/demakein",
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
        download_url="https://github.com/introlab/demakein",
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
        download_url="https://github.com/introlab/demakein",
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
        download_url="https://github.com/introlab/demakein",
        tags=["beginner", "medieval", "folk", "3-hole"],
        difficulty="Beginner",
        description="Medieval three-hole tabor pipe. Played with one hand "
                    "while the other hand plays a drum (tabor).",
    ),
    InstrumentEntry(
        name="Pan Flute",
        family="Wind", subcategory="Flute", type_label="Pan Flute",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="pflute",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Pan_flute.jpg/640px-Pan_flute.jpg",
        audio_url="https://www.youtube.com/watch?v=0hnsJ-42Vns",
        download_url="https://github.com/introlab/demakein",
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
        download_url="https://github.com/introlab/demakein",
        tags=["beginner", "reed", "clarinet-like", "practice"],
        difficulty="Beginner",
        description="Simple single-reed pipe. Like a clarinet practice chanter. "
                    "Great introduction to reed instruments.",
    ),
    InstrumentEntry(
        name="Folk Shawm",
        family="Wind", subcategory="Woodwind", type_label="Double Reed",
        range="Soprano", key="C",
        source="Demakein Built-in",
        demakein_preset="folk_shawm",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Shawm.jpg/640px-Shawm.jpg",
        audio_url="https://www.youtube.com/watch?v=FBpXOL7W0mE",
        download_url="https://github.com/introlab/demakein",
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
        audio_url="https://www.youtube.com/watch?v=FBpXOL7W0mE",
        download_url="https://github.com/introlab/demakein",
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
        download_url="https://github.com/introlab/demakein",
        tags=["intermediate", "drone", "bagpipe", "continuous"],
        difficulty="Intermediate",
        description="Continuous-sounding reed drone pipe. "
                    "Intended for use as a bagpipe drone or held drone instrument.",
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
        audio_url="https://www.youtube.com/watch?v=B_ dátummalYLQ8",
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
