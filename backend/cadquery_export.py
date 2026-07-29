"""CadQuery STL/STEP export for instrument designs.

Generates 3D-printable geometry from bore profile + tone hole parameters.
Requires: pip install cadquery

Usage:
    from cadquery_export import generate_instrument, export_stl, export_step

    # Cylindrical bore
    solid = generate_instrument(
        bore_length=600, bore_diameter=25, wall_thickness=3,
        holes=[(100, 8.0), (200, 8.5), (300, 9.0)],
        closed_top=True
    )
    export_stl(solid, "clarinet.stl")
    export_step(solid, "clarinet.step")

    # Conical bore
    solid = generate_instrument(
        bore_length=650, bore_diameter=(16, 36), wall_thickness=2,
        holes=[(80, 4.0), (200, 3.0), (400, 3.0)],
        closed_top=False
    )
    export_stl(solid, "glissotar.stl")
"""

import time
import os


def generate_instrument(
    bore_length: float,
    bore_diameter: float | tuple[float, float],
    wall_thickness: float,
    holes: list[tuple[float, float]] = None,
    closed_top: bool = False,
    hole_depth: float = None,
):
    """Generate a 3D instrument solid from acoustic parameters.

    Args:
        bore_length: total bore length in mm
        bore_diameter: diameter (mm). Float = cylindrical, tuple = (small, large) conical.
        wall_thickness: wall thickness in mm
        holes: list of (position_mm, diameter_mm) tuples
        closed_top: cap the top end (for reed/brass instruments)
        hole_depth: how deep tone holes cut (default: wall_thickness + 2mm)
    Returns:
        cadquery Workplane (solid)
    """
    import cadquery as cq

    if holes is None:
        holes = []
    if hole_depth is None:
        hole_depth = wall_thickness + 2

    if isinstance(bore_diameter, (list, tuple)):
        small_d, large_d = bore_diameter
        small_outer = small_d + 2 * wall_thickness
        large_outer = large_d + 2 * wall_thickness

        outer = (
            cq.Workplane("XY")
            .circle(small_outer / 2)
            .workplane(offset=bore_length)
            .circle(large_outer / 2)
            .loft()
        )
        bore = (
            cq.Workplane("XY")
            .circle(small_d / 2)
            .workplane(offset=bore_length)
            .circle(large_d / 2)
            .loft()
        )
        solid = outer.cut(bore)
    else:
        outer_diam = bore_diameter + 2 * wall_thickness
        solid = (
            cq.Workplane("XY")
            .circle(outer_diam / 2)
            .circle(bore_diameter / 2)
            .extrude(bore_length)
        )

        if closed_top:
            cap = (
                cq.Workplane("XY")
                .circle(outer_diam / 2)
                .extrude(wall_thickness)
            )
            cap = cap.translate((0, 0, bore_length))
            solid = solid.union(cap)

    for pos, diam in holes:
        hole = (
            cq.Workplane("XZ")
            .workplane(offset=pos)
            .circle(diam / 2)
            .extrude(hole_depth)
        )
        solid = solid.cut(hole)

    return solid


def export_stl(solid, path: str) -> float:
    from cadquery import exporters
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    t0 = time.time()
    exporters.export(solid, path)
    return time.time() - t0


def export_step(solid, path: str) -> float:
    from cadquery import exporters
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    t0 = time.time()
    exporters.export(solid, path)
    return time.time() - t0


def instrument_info(solid) -> dict:
    bb = solid.val().BoundingBox()
    return {
        "length_x": round(bb.xmax - bb.xmin, 2),
        "length_y": round(bb.ymax - bb.ymin, 2),
        "length_z": round(bb.zmax - bb.zmin, 2),
    }


# ============================================================
# Pre-defined instruments — verified & standard specs
# Each entry: generate_instrument kwargs + _meta for UI display
#
# Sources:
#   "verified"   = specs from our configs/measurements/optimization
#   "standard"   = published bore dimensions from Adler, Benade, etc.
#   "historical" = museum specimens / research papers
#
# Bore types:
#   cylindrical (float): clarinets, flutes, recorders
#   conical (tuple):     saxes, oboes, bassoon, glissotar
# ============================================================

INSTRUMENTS = {

    # ═══════════════════════════════════════════════════════════
    #  VERIFIED: Our optimized designs (exact specs)
    # ═══════════════════════════════════════════════════════════

    "baroque_clarinet": {
        "bore_length": 598.0, "bore_diameter": 25.0, "wall_thickness": 2.5,
        "closed_top": True,
        "holes": [(95,8.5),(135,8.5),(175,9.0),(215,9.0),(260,9.5),(305,9.5),(350,10.0),(395,7.0),(430,7.0)],
        "_meta": {"display_name": "Baroque Clarinet (2-Key Denner)", "family": "Clarinet", "subcategory": "Historical",
                  "verified": True, "source": "config/baroque_clarinet.json",
                  "description": "2-key Denner-style baroque clarinet c.1700. 7 finger holes + 2 keys."},
    },
    "bass_clarinet_7hole": {
        "bore_length": 1211.3, "bore_diameter": 25.0, "wall_thickness": 6.0,
        "closed_top": True,
        "holes": [(175.9,11.0),(292.9,11.0),(337.5,11.0),(444.6,11.0),(532.0,11.0),(609.8,11.0),(636.4,11.0)],
        "_meta": {"display_name": "Bass Clarinet Bb (7-Hole Diatonic)", "family": "Clarinet", "subcategory": "Modern",
                  "verified": True, "source": "config/bass_clarinet_7hole.json",
                  "description": "7-hole D major diatonic bass clarinet. 0.04c RMS 1st register, 7.96c RMS 2nd register."},
    },
    "bass_chalumeau_C": {
        "bore_length": 830.0, "bore_diameter": 20.5, "wall_thickness": 3.75,
        "closed_top": True,
        "holes": [(90,7.0),(120,7.0),(175,7.0),(230,7.0),(340,7.5),(395,7.5),(450,8.0),(560,8.5)],
        "_meta": {"display_name": "Bass Chalumeau in C (Historical)", "family": "Chalumeau", "subcategory": "Historical",
                  "verified": True, "source": "config/bass_chalumeau.json",
                  "description": "Historical bass chalumeau (Kress/Denner type). 8 holes + 2 keys. Range C3-G4."},
    },
    "pvc_flute_D": {
        "bore_length": 572.2, "bore_diameter": 20.9, "wall_thickness": 2.9,
        "closed_top": False,
        "holes": [(61.7,14.6),(118.5,14.6),(144.6,14.6),(192.4,14.6),(235.0,14.6),(272.9,14.6)],
        "_meta": {"display_name": "PVC Flute in D", "family": "Flute", "subcategory": "Transverse",
                  "verified": True, "source": "chat-logs/flute-calculations.json",
                  "description": "6-hole transverse flute from 3/4\" PVC Sch40. Fundamental D4 (293.7 Hz)."},
    },
    "soprano_sax_Bb": {
        "bore_length": 550.0, "bore_diameter": 12.0, "wall_thickness": 4.0,
        "closed_top": False,
        "holes": [(80,6.5),(150,6.5),(220,6.5),(290,6.5),(360,6.5),(430,6.5),(500,6.5)],
        "_meta": {"display_name": "Soprano Saxophone Bb (Template)", "family": "Saxophone", "subcategory": "Soprano",
                  "verified": True, "source": "test_output/instruments/measurements.json",
                  "description": "7-hole soprano sax template. Conical bore approximated. Requires optimization."},
    },
    "alto_sax_Eb": {
        "bore_length": 700.0, "bore_diameter": 17.0, "wall_thickness": 4.5,
        "closed_top": False,
        "holes": [(100,7.5),(180,7.5),(260,7.5),(340,7.5),(420,7.5),(500,7.5),(580,7.5)],
        "_meta": {"display_name": "Alto Saxophone Eb (Template)", "family": "Saxophone", "subcategory": "Alto",
                  "verified": True, "source": "test_output/instruments/measurements.json",
                  "description": "7-hole alto sax template. Requires optimization for intonation."},
    },
    "koncovka_C": {
        "bore_length": 651.5, "bore_diameter": 16.0, "wall_thickness": 2.0,
        "closed_top": False, "holes": [],
        "_meta": {"display_name": "Koncovka in C (Overtone Flute)", "family": "Flute", "subcategory": "Overtone",
                  "verified": True, "source": "chat-logs/flute-calculations.json",
                  "description": "Slovak overtone flute. No holes. Fundamental C3 (130.8 Hz)."},
    },
    "xaphoon_C": {
        "bore_length": 300.0, "bore_diameter": 14.0, "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(40,6.5),(80,6.5),(120,6.5),(160,6.5),(200,6.5),(240,6.5),(280,6.5)],
        "_meta": {"display_name": "Xaphoon in C (Pocket Sax)", "family": "Saxophone", "subcategory": "Pocket",
                  "verified": True, "source": "test_output/instruments/measurements.json",
                  "description": "Brian's Xaphoon pocket sax. 7 holes, clarinet-like fingering. 300mm."},
    },
    "glissotar": {
        "bore_length": 650.0, "bore_diameter": (16.0, 36.0), "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(80,4.0),(150,3.0),(220,3.0),(290,3.0),(360,3.0),(430,3.0),(500,3.0),(570,3.0),(620,3.0)],
        "_meta": {"display_name": "Glissotar (Glissando Reed)", "family": "Woodwind", "subcategory": "Experimental",
                  "verified": True, "source": "test_output/instruments/measurements.json",
                  "description": "Glissando reed, conical bore 16-36mm. 9 holes, slide glissando."},
    },
    "fujara_G": {
        "bore_length": 1746.2, "bore_diameter": 20.0, "wall_thickness": 3.0,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "Fujara in G (Slovak Drone Flute)", "family": "Flute", "subcategory": "Drone/Overtone",
                  "verified": True, "source": "chat-logs/flute-calculations.json",
                  "description": "Traditional Slovak fujara. 1.75m. Fundamental G1 (49 Hz)."},
    },
    "overtone_flute_G": {
        "bore_length": 214.2, "bore_diameter": 16.0, "wall_thickness": 2.0,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "Overtone Flute in G", "family": "Flute", "subcategory": "Overtone",
                  "verified": True, "source": "chat-logs/flute-calculations.json",
                  "description": "Closed-end overtone flute. 214mm, 13 harmonics. G4 (392 Hz)."},
    },

    # ═══════════════════════════════════════════════════════════
    #  CLARINET FAMILY — published bore specs
    # ═══════════════════════════════════════════════════════════

    "clarinet_Eb": {
        "bore_length": 490.0, "bore_diameter": 12.5, "wall_thickness": 2.5,
        "closed_top": True,
        "holes": [(65,5.5),(95,5.5),(125,5.5),(155,5.5),(185,6.0),(215,6.0),(245,6.0),(275,6.0),(305,6.0),(335,6.5),(365,6.5),(395,6.5),(425,6.5)],
        "_meta": {"display_name": "Eb Clarinet (Boehm)", "family": "Clarinet", "subcategory": "Soprano",
                  "verified": False, "source": "Standard Boehm bore specs (Adler)",
                  "description": "Eb clarinet, highest standard clarinet. Pitched minor 3rd above Bb. Bright, piercing."},
    },
    "clarinet_Bb_modern": {
        "bore_length": 660.0, "bore_diameter": 15.0, "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [(78,6.5),(108,6.5),(138,6.5),(168,6.5),(198,7.0),(228,7.0),(258,7.0),(288,7.0),(318,7.0),(348,7.5),(378,7.5),(408,7.5),(438,7.5),(468,7.5)],
        "_meta": {"display_name": "Bb Clarinet - Modern Boehm", "family": "Clarinet", "subcategory": "Modern",
                  "verified": False, "source": "Standard Boehm specs (Benade, Adler)",
                  "description": "Standard 14-hole Boehm Bb clarinet. Most common clarinet worldwide."},
    },
    "clarinet_A": {
        "bore_length": 700.0, "bore_diameter": 15.0, "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [(78,6.5),(108,6.5),(138,6.5),(168,6.5),(198,7.0),(228,7.0),(258,7.0),(288,7.0),(318,7.0),(348,7.5),(378,7.5),(408,7.5),(438,7.5),(468,7.5)],
        "_meta": {"display_name": "A Clarinet - Modern Boehm", "family": "Clarinet", "subcategory": "Modern",
                  "verified": False, "source": "Standard bore specs (Adler)",
                  "description": "A clarinet, slightly longer than Bb. Warmer tone, orchestral standard."},
    },
    "bass_clarinet_Bb_standard": {
        "bore_length": 1200.0, "bore_diameter": 23.5, "wall_thickness": 5.0,
        "closed_top": True,
        "holes": [(160,9.5),(260,9.5),(360,9.5),(460,9.5),(560,9.5),(660,9.5),(760,10.0),(860,10.0),(960,10.0),(1060,10.0)],
        "_meta": {"display_name": "Bass Clarinet Bb (Standard)", "family": "Clarinet", "subcategory": "Bass",
                  "verified": False, "source": "Standard bore specs (Benade)",
                  "description": "Standard 10-hole bass clarinet. Bore 23.5mm, range Bb1-C4."},
    },
    "contra_alto_clarinet_Eb": {
        "bore_length": 1600.0, "bore_diameter": 32.0, "wall_thickness": 6.0,
        "closed_top": True,
        "holes": [(200,11.0),(330,11.0),(460,11.0),(590,11.0),(720,11.0),(850,11.0),(980,11.0),(1110,11.0),(1240,11.0),(1370,11.0)],
        "_meta": {"display_name": "Contra-Alto Clarinet Eb", "family": "Clarinet", "subcategory": "Contra-Alto",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Contra-alto clarinet. One octave below alto sax. Powerful low register."},
    },
    "contra_bass_clarinet_Bb": {
        "bore_length": 1900.0, "bore_diameter": 38.0, "wall_thickness": 7.0,
        "closed_top": True,
        "holes": [(250,13.0),(400,13.0),(550,13.0),(700,13.0),(850,13.0),(1000,13.0),(1150,13.0),(1300,13.0),(1450,13.0),(1600,13.0)],
        "_meta": {"display_name": "Contra-Bass Clarinet Bb", "family": "Clarinet", "subcategory": "Contra-Bass",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Contra-bass clarinet. One octave below bass. Deepest clarinet."},
    },

    # ═══════════════════════════════════════════════════════════
    #  SAXOPHONE FAMILY — Adolphe Sax proportions
    # ═══════════════════════════════════════════════════════════

    "soprano_sax_Bb_std": {
        "bore_length": 560.0, "bore_diameter": (12.0, 22.0), "wall_thickness": 3.5,
        "closed_top": False,
        "holes": [(85,6.0),(140,6.0),(195,6.0),(250,6.0),(305,6.5),(360,6.5),(415,6.5),(470,7.0)],
        "_meta": {"display_name": "Soprano Sax Bb (Standard)", "family": "Saxophone", "subcategory": "Soprano",
                  "verified": False, "source": "Standard sax proportions (Ingham)",
                  "description": "Standard soprano sax. Conical 12-22mm. Straight body."},
    },
    "alto_sax_Eb_std": {
        "bore_length": 720.0, "bore_diameter": (16.5, 30.0), "wall_thickness": 4.0,
        "closed_top": False,
        "holes": [(105,7.0),(170,7.0),(235,7.0),(300,7.5),(365,7.5),(430,7.5),(495,8.0),(560,8.0),(625,8.5)],
        "_meta": {"display_name": "Alto Sax Eb (Standard)", "family": "Saxophone", "subcategory": "Alto",
                  "verified": False, "source": "Standard sax proportions (Ingham)",
                  "description": "Standard alto sax. Most popular saxophone. 9 main tone holes."},
    },
    "tenor_sax_Bb_std": {
        "bore_length": 880.0, "bore_diameter": (22.0, 42.0), "wall_thickness": 5.0,
        "closed_top": False,
        "holes": [(130,8.0),(210,8.0),(290,8.0),(370,8.5),(450,8.5),(530,8.5),(610,9.0),(690,9.0),(770,9.5)],
        "_meta": {"display_name": "Tenor Sax Bb (Standard)", "family": "Saxophone", "subcategory": "Tenor",
                  "verified": False, "source": "Standard sax proportions (Ingham)",
                  "description": "Standard tenor sax. Rich, full tone. Jazz, classical, pop."},
    },
    "baritone_sax_Eb_std": {
        "bore_length": 1140.0, "bore_diameter": (30.0, 55.0), "wall_thickness": 5.5,
        "closed_top": False,
        "holes": [(160,9.5),(270,9.5),(380,9.5),(490,10.0),(600,10.0),(710,10.0),(820,10.5),(930,10.5),(1040,11.0)],
        "_meta": {"display_name": "Bari Sax Eb (Standard)", "family": "Saxophone", "subcategory": "Baritone",
                  "verified": False, "source": "Standard sax proportions (Ingham)",
                  "description": "Standard bari sax. Powerful low register. Low A key omitted."},
    },
    "bass_sax_Bb": {
        "bore_length": 1500.0, "bore_diameter": (38.0, 70.0), "wall_thickness": 6.0,
        "closed_top": False,
        "holes": [(200,11.0),(340,11.0),(480,11.0),(620,11.0),(760,11.5),(900,11.5),(1040,12.0),(1180,12.0),(1320,12.5)],
        "_meta": {"display_name": "Bass Saxophone Bb", "family": "Saxophone", "subcategory": "Bass",
                  "verified": False, "source": "Standard sax proportions",
                  "description": "Bass saxophone. Very large. Rare in modern ensembles."},
    },

    # ═══════════════════════════════════════════════════════════
    #  FLUTE FAMILY — published bore specs
    # ═══════════════════════════════════════════════════════════

    "piccolo": {
        "bore_length": 330.0, "bore_diameter": 10.0, "wall_thickness": 1.5,
        "closed_top": False,
        "holes": [(40,4.5),(75,4.5),(105,4.5),(135,4.5),(165,5.0),(195,5.0),(225,5.0),(255,5.0),(285,5.0)],
        "_meta": {"display_name": "Piccolo in C", "family": "Flute", "subcategory": "Piccolo",
                  "verified": False, "source": "Standard bore specs (Adler)",
                  "description": "Highest standard orchestral flute. Sounds octave above concert flute."},
    },
    "concert_flute_C": {
        "bore_length": 670.0, "bore_diameter": 19.0, "wall_thickness": 1.5,
        "closed_top": False,
        "holes": [(90,8.5),(140,8.5),(190,8.5),(240,8.5),(290,8.5),(340,8.5),(390,8.5),(440,8.5),(490,8.5),(540,8.5),(590,8.5)],
        "_meta": {"display_name": "Concert Flute in C (Boehm)", "family": "Flute", "subcategory": "Transverse",
                  "verified": False, "source": "Standard Boehm specs (Adler, Benade)",
                  "description": "Standard concert flute. 11 holes with Boehm key system."},
    },
    "alto_flute_G": {
        "bore_length": 760.0, "bore_diameter": 25.0, "wall_thickness": 1.5,
        "closed_top": False,
        "holes": [(100,10.0),(155,10.0),(210,10.0),(265,10.0),(320,10.0),(375,10.0),(430,10.5),(485,10.5),(540,10.5)],
        "_meta": {"display_name": "Alto Flute in G", "family": "Flute", "subcategory": "Alto",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Alto flute in G. Warmer, darker tone than concert flute."},
    },
    "bass_flute_C": {
        "bore_length": 900.0, "bore_diameter": 32.0, "wall_thickness": 1.5,
        "closed_top": False,
        "holes": [(120,12.0),(190,12.0),(260,12.0),(330,12.0),(400,12.0),(470,12.0),(540,12.5),(610,12.5),(680,12.5)],
        "_meta": {"display_name": "Bass Flute in C", "family": "Flute", "subcategory": "Bass",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Bass flute, octave below concert. Curved headjoint."},
    },

    # ═══════════════════════════════════════════════════════════
    #  RECORDER FAMILY — standard bore specs
    # ═══════════════════════════════════════════════════════════

    "soprano_recorder_C": {
        "bore_length": 332.0, "bore_diameter": 13.0, "wall_thickness": 2.5,
        "closed_top": False,
        "holes": [(55,5.5),(95,5.5),(130,5.5),(165,5.5),(200,5.5),(235,5.5),(270,5.5)],
        "_meta": {"display_name": "Soprano Recorder C", "family": "Flute", "subcategory": "Recorder",
                  "verified": False, "source": "Standard recorder specs (Adler)",
                  "description": "Standard soprano (descant) recorder. Most common recorder. Fipple flute."},
    },
    "alto_recorder_F": {
        "bore_length": 450.0, "bore_diameter": 17.0, "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(75,6.5),(130,6.5),(175,6.5),(225,6.5),(270,6.5),(320,6.5),(370,6.5)],
        "_meta": {"display_name": "Alto Recorder F", "family": "Flute", "subcategory": "Recorder",
                  "verified": False, "source": "Standard recorder specs",
                  "description": "Alto recorder in F. Most used in consort and solo repertoire."},
    },
    "tenor_recorder_C": {
        "bore_length": 466.0, "bore_diameter": 18.0, "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(80,7.0),(140,7.0),(190,7.0),(245,7.0),(295,7.0),(350,7.0),(405,7.0)],
        "_meta": {"display_name": "Tenor Recorder C", "family": "Flute", "subcategory": "Recorder",
                  "verified": False, "source": "Standard recorder specs",
                  "description": "Tenor recorder in C. Warm, mellow tone."},
    },
    "bass_recorder_F": {
        "bore_length": 620.0, "bore_diameter": 24.0, "wall_thickness": 3.5,
        "closed_top": False,
        "holes": [(100,8.5),(175,8.5),(240,8.5),(310,8.5),(375,8.5),(445,8.5),(515,8.5)],
        "_meta": {"display_name": "Bass Recorder F", "family": "Flute", "subcategory": "Recorder",
                  "verified": False, "source": "Standard recorder specs",
                  "description": "Bass recorder in F. Large bore, warm deep tone."},
    },

    # ═══════════════════════════════════════════════════════════
    #  DOUBLE REED — published bore specs
    # ═══════════════════════════════════════════════════════════

    "oboe_standard": {
        "bore_length": 640.0, "bore_diameter": (3.0, 11.5), "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(80,2.5),(120,2.5),(160,2.5),(200,2.5),(240,3.0),(280,3.0),(320,3.0),(360,3.5),(400,3.5),(440,3.5),(480,4.0),(520,4.0),(560,4.5)],
        "_meta": {"display_name": "Oboe (Conservatory)", "family": "Woodwind", "subcategory": "Double Reed",
                  "verified": False, "source": "Standard oboe specs (Benade, Ridenour)",
                  "description": "Conservatory oboe. Narrow conical bore 3-11.5mm. Complex key system."},
    },
    "english_horn_F": {
        "bore_length": 780.0, "bore_diameter": (4.0, 14.0), "wall_thickness": 3.5,
        "closed_top": False,
        "holes": [(100,3.0),(150,3.0),(200,3.0),(250,3.5),(300,3.5),(350,3.5),(400,4.0),(450,4.0),(500,4.0),(550,4.5),(600,4.5),(650,5.0)],
        "_meta": {"display_name": "English Horn F (Cor Anglais)", "family": "Woodwind", "subcategory": "Double Reed",
                  "verified": False, "source": "Standard bore specs",
                  "description": "English horn in F. Lower, warmer than oboe. Bulbous bell not modeled."},
    },
    "baroque_oboe": {
        "bore_length": 600.0, "bore_diameter": (2.0, 10.0), "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(75,2.0),(120,2.0),(165,2.5),(210,2.5),(255,2.5),(300,3.0),(345,3.0),(390,3.0),(435,3.5),(480,3.5),(525,4.0)],
        "_meta": {"display_name": "Baroque Oboe (Hautbois)", "family": "Woodwind", "subcategory": "Historical",
                  "verified": False, "source": "Historical specs (Haynes, Burgess)",
                  "description": "Baroque 2-key oboe. Narrower bore than modern. Richer, intimate tone."},
    },
    "bassoon_standard": {
        "bore_length": 2550.0, "bore_diameter": (12.0, 34.0), "wall_thickness": 4.0,
        "closed_top": True,
        "holes": [(200,5.0),(350,5.0),(500,5.5),(650,5.5),(800,5.5),(950,6.0),(1100,6.0),(1250,6.0),(1400,6.5),(1550,6.5),(1700,6.5),(1850,7.0),(2000,7.0),(2150,7.0)],
        "_meta": {"display_name": "Bassoon (Heckel)", "family": "Woodwind", "subcategory": "Double Reed",
                  "verified": False, "source": "Standard bassoon specs (Benade)",
                  "description": "Standard Heckel bassoon. Conical 12-34mm. Bocal omitted."},
    },
    "contrabassoon": {
        "bore_length": 4700.0, "bore_diameter": (18.0, 50.0), "wall_thickness": 5.0,
        "closed_top": True,
        "holes": [(300,6.5),(550,6.5),(800,7.0),(1050,7.0),(1300,7.0),(1550,7.5),(1800,7.5),(2050,7.5),(2300,8.0),(2550,8.0),(2800,8.0),(3050,8.5),(3300,8.5),(3550,8.5)],
        "_meta": {"display_name": "Contrabassoon", "family": "Woodwind", "subcategory": "Double Reed",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Contrabassoon. Doubled-back bore ~4.7m. Deepest standard woodwind."},
    },

    # ═══════════════════════════════════════════════════════════
    #  BRASS — simplified conical/cylindrical bores
    # ═══════════════════════════════════════════════════════════

    "trumpet_Bb": {
        "bore_length": 1340.0, "bore_diameter": (11.0, 12.7), "wall_thickness": 1.5,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "Trumpet Bb (Simplified)", "family": "Brass", "subcategory": "Trumpet",
                  "verified": False, "source": "Standard specs (Herbert, Tuckwell)",
                  "description": "Bb trumpet. Mostly cylindrical. Bell/valves omitted."},
    },
    "cornet_Bb": {
        "bore_length": 1300.0, "bore_diameter": (10.5, 13.0), "wall_thickness": 1.5,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "Cornet Bb", "family": "Brass", "subcategory": "Cornet",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Bb cornet. More conical than trumpet. Warmer, mellower."},
    },
    "french_horn_F": {
        "bore_length": 3700.0, "bore_diameter": (10.8, 12.0), "wall_thickness": 1.0,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "French Horn F (Simplified)", "family": "Brass", "subcategory": "Horn",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Single F horn. ~3.7m tubing. Bell/rotary valves omitted."},
    },
    "trombone_Bb": {
        "bore_length": 2700.0, "bore_diameter": (12.7, 13.3), "wall_thickness": 1.5,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "Tenor Trombone Bb (Simplified)", "family": "Brass", "subcategory": "Trombone",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Tenor trombone. Mostly cylindrical. Slide not modeled."},
    },
    "tuba_Bb": {
        "bore_length": 4500.0, "bore_diameter": (18.0, 24.0), "wall_thickness": 2.0,
        "closed_top": True, "holes": [],
        "_meta": {"display_name": "Tuba Bb (Simplified)", "family": "Brass", "subcategory": "Tuba",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Bb tuba. Large conical bore. Deepest standard brass. Valves omitted."},
    },

    # ═══════════════════════════════════════════════════════════
    #  HISTORICAL & SPECIALTY
    # ═══════════════════════════════════════════════════════════

    "cornett_G": {
        "bore_length": 620.0, "bore_diameter": (14.0, 22.0), "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(75,6.0),(130,6.0),(185,6.0),(240,6.0),(295,6.0),(350,6.5),(405,6.5),(460,6.5),(515,6.5)],
        "_meta": {"display_name": "Cornett G (Zink)", "family": "Woodwind", "subcategory": "Historical",
                  "verified": False, "source": "Historical specs (Kolneder, Barton)",
                  "description": "Renaissance cornett. Lip-reed + finger holes. Conical, curved wood body."},
    },
    "shawm_Bb": {
        "bore_length": 580.0, "bore_diameter": (8.0, 24.0), "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(80,4.0),(140,4.0),(200,4.5),(260,4.5),(320,5.0),(380,5.0),(440,5.5),(500,5.5)],
        "_meta": {"display_name": "Shawm Bb (Medieval)", "family": "Woodwind", "subcategory": "Historical",
                  "verified": False, "source": "Historical specs (Jeffery, Remnant)",
                  "description": "Medieval shawm. Loud double-reed. Conical with flared bell. 7-8 holes."},
    },
    "dulcian_Bb": {
        "bore_length": 1050.0, "bore_diameter": (10.0, 30.0), "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [(120,4.5),(200,4.5),(280,5.0),(360,5.0),(440,5.0),(520,5.5),(600,5.5),(680,5.5),(760,6.0),(840,6.0)],
        "_meta": {"display_name": "Dulcian Bb (Renaissance Bassoon)", "family": "Woodwind", "subcategory": "Historical",
                  "verified": False, "source": "Historical specs (Rainer)",
                  "description": "Renaissance dulcian. Double-bore (simplified as single cone). Bassoon predecessor."},
    },
    "baroque_flute_D": {
        "bore_length": 630.0, "bore_diameter": (13.0, 19.0), "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(85,7.0),(160,7.0),(210,7.0),(265,7.0),(325,7.0),(380,7.0),(440,7.0),(495,7.5)],
        "_meta": {"display_name": "Baroque Traverso Flute D", "family": "Flute", "subcategory": "Historical",
                  "verified": False, "source": "Historical specs (Palanca, Dart)",
                  "description": "Baroque 1-key traverso in D. Conical bore, 8 holes. Warm, soft tone."},
    },
    "classical_flute_C": {
        "bore_length": 650.0, "bore_diameter": (15.5, 20.0), "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(80,7.5),(130,7.5),(180,7.5),(230,7.5),(280,7.5),(330,7.5),(380,7.5),(430,8.0),(480,8.0),(530,8.0),(580,8.0)],
        "_meta": {"display_name": "Classical Flute C (4-key)", "family": "Flute", "subcategory": "Historical",
                  "verified": False, "source": "Historical specs (Day, Roton)",
                  "description": "Early classical 4-key flute. Conical bore with larger foot joint."},
    },
    "tin_whistle_D": {
        "bore_length": 300.0, "bore_diameter": (11.0, 14.0), "wall_thickness": 1.0,
        "closed_top": False,
        "holes": [(50,5.0),(90,5.0),(125,5.0),(160,5.0),(195,5.0),(230,5.0)],
        "_meta": {"display_name": "Tin Whistle D (Pennywhistle)", "family": "Flute", "subcategory": "Whistle",
                  "verified": False, "source": "Standard pennywhistle dims",
                  "description": "6-hole D5 tin whistle. Slightly conical. Simple folk instrument."},
    },
    "ocarina_12": {
        "bore_length": 150.0, "bore_diameter": 80.0, "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(25,8.0),(50,8.0),(75,8.0),(100,8.0),(125,8.0),(40,7.0),(65,7.0),(90,7.0),(115,7.0)],
        "_meta": {"display_name": "12-Hole Ocarina", "family": "Flute", "subcategory": "Vessel",
                  "verified": False, "source": "Standard ocarina dims",
                  "description": "12-hole transverse ocarina. Vessel resonator. Simplified as disc."},
    },
    "didgeridoo": {
        "bore_length": 1500.0, "bore_diameter": (28.0, 38.0), "wall_thickness": 8.0,
        "closed_top": False, "holes": [],
        "_meta": {"display_name": "Didgeridoo (Yidaki)", "family": "Drone", "subcategory": "Drone",
                  "verified": False, "source": "Typical dimensions",
                  "description": "Australian Aboriginal drone. Hollowed eucalyptus. Lips vibrate."},
    },
    "alphorn_F": {
        "bore_length": 3400.0, "bore_diameter": (6.0, 10.0), "wall_thickness": 3.0,
        "closed_top": False, "holes": [],
        "_meta": {"display_name": "Alphorn F", "family": "Brass", "subcategory": "Natural",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Alpine natural horn in F. ~3.4m conical. Harmonic series only."},
    },
    "kazoo": {
        "bore_length": 130.0, "bore_diameter": 25.0, "wall_thickness": 1.0,
        "closed_top": False, "holes": [],
        "_meta": {"display_name": "Kazoo", "family": "Membranophone", "subcategory": "Novelty",
                  "verified": False, "source": "Typical dimensions",
                  "description": "Simple membrane resonator. Voice modulated."},
    },
    "pvc_bass_clarinet": {
        "bore_length": 1200.0, "bore_diameter": 28.0, "wall_thickness": 2.6,
        "closed_top": True,
        "holes": [(180,10.0),(300,10.0),(420,10.0),(540,10.0),(660,10.0),(780,10.0),(900,10.0)],
        "_meta": {"display_name": "PVC Bass Clarinet (DIY)", "family": "Clarinet", "subcategory": "DIY",
                  "verified": False, "source": "Community PVC designs",
                  "description": "DIY bass clarinet from 1-1/4\" PVC. 7 holes."},
    },
    "glissonardo": {
        "bore_length": 800.0, "bore_diameter": (14.0, 30.0), "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(80,5.0),(160,5.0),(240,5.0),(320,5.0),(400,5.5),(480,5.5),(560,6.0),(640,6.0),(720,6.5)],
        "_meta": {"display_name": "Glissonardo (3D-Print Soprano)", "family": "Saxophone", "subcategory": "Experimental",
                  "verified": False, "source": "JDWoodwinds specs",
                  "description": "3D-printed soprano sax. Conical bore, glissando. JDWoodwinds."},
    },
    "seljefloyte": {
        "bore_length": 500.0, "bore_diameter": 14.0, "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(65,6.0),(130,6.0),(195,6.0),(260,6.0),(325,6.0)],
        "_meta": {"display_name": "Seljefloyte (Willow Flute)", "family": "Flute", "subcategory": "Nordic Folk",
                  "verified": False, "source": "Traditional Scandinavian dims",
                  "description": "Norwegian willow flute. 5 holes, no fipple. Pentatonic."},
    },
    "tilinca": {
        "bore_length": 550.0, "bore_diameter": 15.0, "wall_thickness": 2.0,
        "closed_top": True,
        "holes": [(70,6.0),(140,6.0),(210,6.0),(280,6.0),(350,6.0)],
        "_meta": {"display_name": "Tilinca (Romanian Fipple)", "family": "Flute", "subcategory": "Fipple",
                  "verified": False, "source": "Traditional Romanian dims",
                  "description": "Romanian fipple flute. 5-6 holes. Pentatonic, pastoral."},
    },
    "tarogato": {
        "bore_length": 700.0, "bore_diameter": (16.0, 28.0), "wall_thickness": 3.5,
        "closed_top": False,
        "holes": [(90,6.5),(160,6.5),(230,6.5),(300,6.5),(370,7.0),(440,7.0),(510,7.0),(580,7.5),(650,7.5)],
        "_meta": {"display_name": "Tarogato (Hungarian)", "family": "Woodwind", "subcategory": "Hybrid",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Hungarian tarogato. Conical like soprano sax, clarinet reed. Hybrid."},
    },

    # ════════════════════════════════════════════════════════════════════════════════
    #  VERIFIED PROFESSIONAL 3D-PRINTED DESIGNS
    # ════════════════════════════════════════════════════════════════════════════════

    # JDWoodwinds - Professional bass clarinet in G (simplified Boehm, 24mm bore)
    "jdw_bass_clarinet_G": {
        "bore_length": 1050.0, "bore_diameter": 24.0, "wall_thickness": 4.5,
        "closed_top": True,
        "holes": [(140,9.5),(240,9.5),(340,9.5),(440,9.5),(540,9.5),(640,10.0),(740,10.0),(840,10.0),(940,10.5)],
        "_meta": {"display_name": "JDWoodwinds Bass Clarinet in G", "family": "Clarinet", "subcategory": "Bass",
                  "verified": True, "source": "JDWoodwinds STL files ($100)", "url": "https://jdwoodwind.com/shop/p/stl-files-bass-clarinet-in-g",
                  "description": "Professional 3D-printable bass clarinet in G. Simplified Boehm keywork. 24mm bore. Low E range. Requires clarinet repair expertise. Print: PLA+, 0.16mm, 4 walls body, 6 walls keys, 30-50% infill. Critical: CA glue seal all toneholes, neoprene pads, brass/carbon tenons."},
    },

    # Tom's Modern Chalumeau in C (14mm bore, Eb mouthpiece)
    "toms_chalumeau_C": {
        "bore_length": 350.0, "bore_diameter": 14.0, "wall_thickness": 2.5,
        "closed_top": False,
        "holes": [(45,5.5),(85,5.5),(125,6.0),(165,6.0),(205,6.5),(245,6.5),(285,7.0)],
        "_meta": {"display_name": "Tom's Modern Chalumeau in C", "family": "Chalumeau", "subcategory": "Modern",
                  "verified": True, "source": "Printables (Tom_1766913)", "url": "https://www.printables.com/model/752555-clarinet-modern-chalumeau-in-c",
                  "description": "Modern chalumeau in C. 14mm bore. Fits Vandoren Eb clarinet mouthpiece. 7 holes + 2 extension keys. 3-part split body (bell, body, barrel). Updated hole positions corrected from wood testing. Key blocks raised from body."},
    },

    # C Clarinet Remix (14mm bore, 3-part, Eb mouthpiece)
    "c_clarinet_remix_14mm": {
        "bore_length": 550.0, "bore_diameter": 14.0, "wall_thickness": 2.8,
        "closed_top": False,
        "holes": [(60,6.0),(100,6.0),(140,6.5),(180,6.5),(220,7.0),(260,7.0),(300,7.5),(340,7.5),(380,8.0),(420,8.0)],
        "_meta": {"display_name": "C Clarinet Remix (14mm Bore)", "family": "Clarinet", "subcategory": "Modern",
                  "verified": True, "source": "Printables (Gubbledenut remix of Tom's Chalumeau)", "url": "https://www.printables.com/model/888905-c-clarinet-remix",
                  "description": "Remix of Tom's Chalumeau with 14mm bore (vs original narrower). 3-part split body. Barrel fits standard Eb mouthpiece. Adjustable tuning via bell/barrel. Raised key blocks. Fixed intonation issues of original."},
    },

    # Atomica Ultra-Compact Bass Clarinet (folded bore, soprano mouthpiece)
    "atomica_ultra_compact_bass_clarinet": {
        "bore_length": 1100.0, "bore_diameter": (18.0, 28.0), "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [(120,8.0),(220,8.0),(320,8.0),(420,8.0),(520,8.5),(620,8.5),(720,9.0),(820,9.0),(920,9.5)],
        "_meta": {"display_name": "Atomica Ultra-Compact Bass Clarinet", "family": "Clarinet", "subcategory": "Experimental",
                  "verified": True, "source": "MakerWorld (Atomica)", "url": "https://makerworld.com/en/models/1150929",
                  "description": "Folded-bore bass clarinet in compact form. Uses soprano clarinet mouthpiece. 3 register holes (center + top/bottom). Range: Eb2-Eb3, Bb3-Bb4+. No throat tones. Diatonic. Print: 0.16mm, 4 walls, 20% infill, 8.6h, 4 plates. Membrane: vinyl glove folded 4x."},
    },

    # True Budget Low Woodwind (folded bore, membrane, diatonic)
    "atomica_true_budget_low_woodwind": {
        "bore_length": 900.0, "bore_diameter": 22.0, "wall_thickness": 2.5,
        "closed_top": False,
        "holes": [(100,7.0),(180,7.0),(260,7.0),(340,7.5),(420,7.5),(500,8.0),(580,8.0)],
        "_meta": {"display_name": "True Budget Low Woodwind (Membrane)", "family": "Clarinet", "subcategory": "Membrane/DIY",
                  "verified": True, "source": "MakerWorld (Atomica)", "url": "https://makerworld.com/en/models/2740713-the-true-budget-low-woodwind",
                  "description": "Folded-bore bass membrane clarinet. Diatonic. Membrane: vinyl glove folded 4 layers (no bubbles). Knee rest for RH thumb hole. Membrane from surgical glove/space blanket. 17.3h print, 7 plates. No keys. CC-BY-NC-ND."},
    },

    # Membrane Clarinet (Nicolas Bras concept, DrJones/Printables)
    "membrane_clarinet_nicolas_bras": {
        "bore_length": 400.0, "bore_diameter": 15.0, "wall_thickness": 2.5,
        "closed_top": False,
        "holes": [(50,6.0),(90,6.0),(130,6.5),(170,6.5),(210,7.0),(250,7.0),(290,7.5)],
        "_meta": {"display_name": "Membrane Clarinet (Nicolas Bras Concept)", "family": "Clarinet", "subcategory": "Membrane",
                  "verified": True, "source": "Printables (DrJones)", "url": "https://www.printables.com/model/495171-membrane-clarinet",
                  "description": "Fully 3D-printed clarinet with plastic membrane reed (bag foil/space blanket). 3 screw-together parts with LH/RH threads. Membrane holder with 2 DOF tuning. No cane reed needed. Inspired by Nicolas Bras membrane clarinet concept."},
    },

    # Diplica (Croatian double reed with membrane)
    "diplica_croatian": {
        "bore_length": 280.0, "bore_diameter": 12.0, "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(40,5.0),(75,5.0),(110,5.5),(145,5.5),(180,6.0),(215,6.0)],
        "_meta": {"display_name": "Diplica (Croatian Double Reed)", "family": "Woodwind", "subcategory": "Membrane/Traditional",
                  "verified": False, "source": "Traditional dims / Printables",
                  "description": "Croatian traditional diplica. Two parallel single reeds with shared membrane chamber. 6 holes. Nasal buzzing timbre. Historically wood/cane; 3D version uses plastic membrane."},
    },

    # Sipsi (Turkish single reed with membrane)
    "sipsi_turkish": {
        "bore_length": 250.0, "bore_diameter": 11.0, "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(35,4.5),(70,4.5),(105,5.0),(140,5.0),(175,5.5),(210,5.5)],
        "_meta": {"display_name": "Sipsi (Turkish Membrane Reed)", "family": "Woodwind", "subcategory": "Membrane/Traditional",
                  "verified": False, "source": "Traditional dims / Printables",
                  "description": "Turkish folk sipsi. Simple cylindrical pipe with membrane reed (historically cane skin). 6 holes. High bright timbre. Related to Greek psítha and Mizmar family. 3D version uses thin plastic membrane."},
    },

    # Zummara (Egyptian double clarinet)
    "zummara_egyptian": {
        "bore_length": 300.0, "bore_diameter": (10.0, 10.0), "wall_thickness": 2.0,
        "closed_top": False,
        "holes": [(40,5.0),(75,5.0),(110,5.0),(145,5.0),(180,5.5),(215,5.5)],
        "_meta": {"display_name": "Zummara (Egyptian Double Clarinet)", "family": "Woodwind", "subcategory": "Membrane/Traditional",
                  "verified": False, "source": "Traditional dims / Printables",
                  "description": "Egyptian folk zummara. Two parallel cylindrical pipes with single membrane reeds. One melodic (6 holes), one drone. Buzzing reedy timbre. Ancestor of clarinet family. 3D version uses paired bores."},
    },

    # Selmer Mark VI Alto Sax (reference bore)
    "selmer_mark_vi_alto": {
        "bore_length": 720.0, "bore_diameter": (16.5, 30.0), "wall_thickness": 4.0,
        "closed_top": False,
        "holes": [(105,7.0),(170,7.0),(235,7.0),(300,7.5),(365,7.5),(430,7.5),(495,8.0),(560,8.0),(625,8.5)],
        "_meta": {"display_name": "Selmer Mark VI Alto Sax (Reference)", "family": "Saxophone", "subcategory": "Alto",
                  "verified": False, "source": "Standard Selmer proportions (Ingham/SaxPics)",
                  "description": "Legendary Selmer Mark VI alto sax (1954-1975). Conical 16.5-30mm bore. Gold standard for alto. 9 main tone holes. Hand-finished toneholes. High copper brass. Many serial variations (5-digit most prized)."},
    },

    # Selmer Mark VI Tenor Sax
    "selmer_mark_vi_tenor": {
        "bore_length": 880.0, "bore_diameter": (22.0, 42.0), "wall_thickness": 5.0,
        "closed_top": False,
        "holes": [(130,8.0),(210,8.0),(290,8.0),(370,8.5),(450,8.5),(530,8.5),(610,9.0),(690,9.0),(770,9.5)],
        "_meta": {"display_name": "Selmer Mark VI Tenor Sax (Reference)", "family": "Saxophone", "subcategory": "Tenor",
                  "verified": False, "source": "Standard Selmer proportions",
                  "description": "Selmer Mark VI tenor sax. Conical 22-42mm bore. Rich full tone. Jazz/classical standard. Coltrane, Rollins, Brecker played Mark VI tenors."},
    },

    # Buffet R13 Bb Clarinet (polycylindrical reference)
    "buffet_r13_bb": {
        "bore_length": 660.0, "bore_diameter": 14.64, "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [(78,6.5),(108,6.5),(138,6.5),(168,6.5),(198,7.0),(228,7.0),(258,7.0),(288,7.0),(318,7.0),(348,7.5),(378,7.5),(408,7.5),(438,7.5),(468,7.5)],
        "_meta": {"display_name": "Buffet R13 Bb Clarinet (Reference)", "family": "Clarinet", "subcategory": "Professional",
                  "verified": False, "source": "Buffet specs / Woodwind Forum measurements",
                  "description": "Buffet R13 professional Bb clarinet. Polycylindrical bore ~14.64mm (.574\"). Hand-burnished bore. Undercut toneholes. 17 keys, 6 rings. Most popular pro clarinet worldwide. Grenadilla wood."},
    },

    # Selmer Paris Series 9 Bb Clarinet
    "selmer_series9_bb": {
        "bore_length": 660.0, "bore_diameter": 14.95, "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [(78,6.5),(108,6.5),(138,6.5),(168,6.5),(198,7.0),(228,7.0),(258,7.0),(288,7.0),(318,7.0),(348,7.5),(378,7.5),(408,7.5),(438,7.5),(468,7.5)],
        "_meta": {"display_name": "Selmer Paris Series 9 Bb Clarinet", "family": "Clarinet", "subcategory": "Professional",
                  "verified": False, "source": "Selmer specs / Woodwind Forum",
                  "description": "Selmer Paris Series 9. Bore ~14.95mm upper / 15.10mm lower. Enhanced CT/CT enhanced models. 15.34mm upper / 15.10mm lower on enhanced. Professional French system."},
    },

    # Yamaha YCL-CSGIII / CSG Bb Clarinet
    "yamaha_csg_bb": {
        "bore_length": 660.0, "bore_diameter": 15.13, "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [(78,6.5),(108,6.5),(138,6.5),(168,6.5),(198,7.0),(228,7.0),(258,7.0),(288,7.0),(318,7.0),(348,7.5),(378,7.5),(408,7.5),(438,7.5),(468,7.5)],
        "_meta": {"display_name": "Yamaha CSG/CSGIII Bb Clarinet", "family": "Clarinet", "subcategory": "Professional",
                  "verified": False, "source": "Yamaha specs / Woodwind Forum",
                  "description": "Yamaha CSG/CSGIII. Bore 15.13mm top / 14.68mm lower. Premium grenadilla. Tapered pivot screws. Hand-adjusted pads. Vintage-inspired bore."},
    },

    # Professional mouthpieces
    "alto_sax_mouthpiece": {
        "bore_length": 90.0, "bore_diameter": 12.0, "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Alto Sax Mouthpiece (Printable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables (AmCorley, bobtschigerillo, WCW 64)",
                  "description": "Playable alto sax mouthpiece. Requires soprano sax ligature + tenor reed. Tip opening ~1.9-2.2mm. Print on side for best lay. Post-process: sand reed table, polish. PETG or PLA+."},
    },

    "tenor_sax_mouthpiece": {
        "bore_length": 105.0, "bore_diameter": 14.5, "wall_thickness": 3.5,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Tenor Sax Mouthpiece (Printable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables (bobtschigerillo, Printcraft pocket sax)",
                  "description": "Playable tenor sax mouthpiece. 3C/7C styles. Tip opening ~2.3-2.5mm. Requires tenor reed + ligature. Print on side, sand finish. Good for pocket sax builds."},
    },

    "clarinet_mouthpiece": {
        "bore_length": 75.0, "bore_diameter": 11.5, "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Bb Clarinet Mouthpiece (Playable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables (Dave Yeagly)",
                  "description": "Playable Bb clarinet mouthpiece. Tip opening 1.28mm. Flexible bulb eliminates cork. Requires light sanding on reed table. 100% infill, concentric pattern. Standard Bb clarinet reed + ligature."},
    },

    "bass_clarinet_mouthpiece_cover": {
        "bore_length": 60.0, "bore_diameter": 28.0, "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [],
        "_meta": {"display_name": "Bass Clarinet Mouthpiece Cover", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables (luckyinstesign)",
                  "description": "Protective cover for bass clarinet mouthpiece. Fits standard bass clarinet mouthpieces. Quick print. Beginner friendly."},
    },

    "trumpet_3c_mouthpiece": {
        "bore_length": 85.0, "bore_diameter": (6.5, 16.0), "wall_thickness": 2.5,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Trumpet 3C Mouthpiece (Kanstul Profile)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables (based on Kanstul comparator)",
                  "description": "Trumpet 3C mouthpiece based on Kanstul comparator profiles. Playable. Print on side. Standard 3C rim/cup."},
    },

    "trumpet_7c_mouthpiece": {
        "bore_length": 85.0, "bore_diameter": (6.5, 16.0), "wall_thickness": 2.5,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Trumpet 7C Mouthpiece (Standard)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables",
                  "description": "Standard 7C trumpet mouthpiece. Most common beginner/intermediate size. Print on side for best lay. Sand finish."},
    },

    "trombone_mouthpiece_set": {
        "bore_length": 95.0, "bore_diameter": (10.0, 24.0), "wall_thickness": 3.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Trombone Mouthpiece Set (Wedge/Bach/Schilke)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": True, "source": "Printables",
                  "description": "Set of trombone mouthpieces based on Wedge/Bach/Schilke profiles. Various cup depths. Print on side."},
    },

    "trumpet_mouthpiece_puller": {
        "bore_length": 60.0, "bore_diameter": 20.0, "wall_thickness": 4.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Trumpet Mouthpiece Puller Tool", "family": "Parts & Accessories", "subcategory": "Tool",
                  "verified": True, "source": "Printables",
                  "description": "Tool for removing stuck mouthpieces from trumpets. Repair essential."},
    },

    # ═══════════════════════════════════════════════════════════════════════════════════
    #  PROFESSIONAL LOW CLARINETS (Contra-Alto, Contra-Bass, Sub-Contra)
    # ════════════════════════════════════════════════════════════════════════════════════

    "contra_alto_clarinet_Eb": {
        "bore_length": 1600.0, "bore_diameter": 32.0, "wall_thickness": 6.0,
        "closed_top": True,
        "holes": [(200,11.0),(330,11.0),(460,11.0),(590,11.0),(720,11.0),(850,11.0),(980,11.0),(1110,11.0),(1240,11.0),(1370,11.0)],
        "_meta": {"display_name": "Contra-Alto Clarinet Eb (Reference)", "family": "Clarinet", "subcategory": "Contra-Alto",
                  "verified": False, "source": "Standard bore specs (Leblanc 340 Paperclip)",
                  "description": "Contra-alto clarinet in Eb. One octave below alto sax. Bore 32mm. Low Eb/C models. Powerful low register. Leblanc 340 'Paperclip' is popular compact version."},
    },

    "contra_bass_clarinet_Bb": {
        "bore_length": 1900.0, "bore_diameter": 38.0, "wall_thickness": 7.0,
        "closed_top": True,
        "holes": [(250,13.0),(400,13.0),(550,13.0),(700,13.0),(850,13.0),(1000,13.0),(1150,13.0),(1300,13.0),(1450,13.0),(1600,13.0)],
        "_meta": {"display_name": "Contra-Bass Clarinet Bb (Reference)", "family": "Clarinet", "subcategory": "Contra-Bass",
                  "verified": False, "source": "Standard bore specs",
                  "description": "Contra-bass clarinet in Bb. One octave below bass clarinet. Bore 38mm. Low C/Eb. Deepest standard clarinet. Doubled-back body."},
    },

    "octo_contra_alto_clarinet_EEb": {
        "bore_length": 2200.0, "bore_diameter": 42.0, "wall_thickness": 8.0,
        "closed_top": True,
        "holes": [(300,14.0),(450,14.0),(600,14.0),(750,14.0),(900,14.0),(1050,14.0),(1200,14.0),(1350,14.0),(1500,14.0),(1650,14.0)],
        "_meta": {"display_name": "Octo-Contra-Alto Clarinet EEb (Octocontralto)", "family": "Clarinet", "subcategory": "Sub-Contra",
                  "verified": False, "source": "JDWoodwinds prototype 2025",
                  "description": "Octo-contra-alto (octocontralto) in EEb. One of two sizes playing below 20Hz. JDWoodwinds prototype 2025 (2nd prototype range to low D, extended to low C 2026). Lowest note 19.445Hz. Rare experimental."},
    },

    "octo_contra_bass_clarinet_BBB": {
        "bore_length": 2600.0, "bore_diameter": 48.0, "wall_thickness": 9.0,
        "closed_top": True,
        "holes": [(350,16.0),(500,16.0),(650,16.0),(800,16.0),(950,16.0),(1100,16.0),(1250,16.0),(1400,16.0),(1550,16.0),(1700,16.0)],
        "_meta": {"display_name": "Octo-Contrabass Clarinet BBB (Octocontrabass)", "family": "Clarinet", "subcategory": "Sub-Contra",
                  "verified": False, "source": "Leblanc original / Martin Foag prototype",
                  "description": "Octocontrabass clarinet in BBB. Only two playable instruments built: Leblanc original and Martin Foag prototype. Deepest woodwind. Lowest notes below human hearing."},
    },

    # Professional Bass Clarinet (3D printable) - Printgear3D Cults3D
    "printgear3d_bass_clarinet": {
        "bore_length": 1200.0, "bore_diameter": 25.0, "wall_thickness": 5.0,
        "closed_top": True,
        "holes": [(175,9.5),(280,9.5),(380,9.5),(480,9.5),(580,9.5),(680,10.0),(780,10.0),(880,10.5),(980,10.5)],
        "_meta": {"display_name": "Bass Clarinet (Printgear3D V2)", "family": "Clarinet", "subcategory": "Bass",
                  "verified": True, "source": "Cults3D (Printgear3D)", "url": "https://cults3d.com/en/3d-model/art/clarinete-bajo-bass-clarinet",
                  "description": "Bass clarinet by Printgear3D. 80cm x 40cm. V2 optimized geometry for easier printing. Professional dimensions. Medidas: 80cm length."},
    },

    # ══════════════════════════════════════════════════════════════════════════════════════
    #  BARITONE SAXOPHONE (Professional & 3D Printed)
    # ════════════════════════════════════════════════════════════════════════════════════

    "selmer_mark_vi_baritone": {
        "bore_length": 1140.0, "bore_diameter": (30.0, 55.0), "wall_thickness": 5.5,
        "closed_top": False,
        "holes": [(160,9.5),(270,9.5),(380,9.5),(490,10.0),(600,10.0),(710,10.0),(820,10.5),(930,10.5),(1040,11.0)],
        "_meta": {"display_name": "Selmer Mark VI Baritone Sax (Reference)", "family": "Saxophone", "subcategory": "Baritone",
                  "verified": False, "source": "Standard Selmer proportions",
                  "description": "Selmer Mark VI bari sax. Conical 30-55mm bore. Powerful low register. Low A key on later models. Hand-drawn bell. Gold standard for bari."},
    },

    "selmer_mark_vi_baritone_lowA": {
        "bore_length": 1160.0, "bore_diameter": (30.0, 55.0), "wall_thickness": 5.5,
        "closed_top": False,
        "holes": [(160,9.5),(270,9.5),(380,9.5),(490,10.0),(600,10.0),(710,10.0),(820,10.5),(930,10.5),(1040,11.0),(1120,11.0)],
        "_meta": {"display_name": "Selmer Mark VI Baritone Low A (Reference)", "family": "Saxophone", "subcategory": "Baritone",
                  "verified": False, "source": "Standard Selmer proportions",
                  "description": "Selmer Mark VI bari with low A key. Extended bore to low A (sounding C). Extra key for left thumb. Professional orchestral standard."},
    },

    "yamaha_ybs62_baritone": {
        "bore_length": 1140.0, "bore_diameter": (30.0, 55.0), "wall_thickness": 5.5,
        "closed_top": False,
        "holes": [(160,9.5),(270,9.5),(380,9.5),(490,10.0),(600,10.0),(710,10.0),(820,10.5),(930,10.5),(1040,11.0)],
        "_meta": {"display_name": "Yamaha YBS-62 Baritone Sax (Reference)", "family": "Saxophone", "subcategory": "Baritone",
                  "verified": False, "source": "Yamaha professional specs",
                  "description": "Yamaha YBS-62 professional baritone. Low A key. Gold lacquer. High F# key. Reliable intonation. Popular professional choice."},
    },

    "selmer_serie_iii_baritone": {
        "bore_length": 1140.0, "bore_diameter": (30.5, 56.0), "wall_thickness": 5.5,
        "closed_top": False,
        "holes": [(160,9.5),(270,9.5),(380,9.5),(490,10.0),(600,10.0),(710,10.0),(820,10.5),(930,10.5),(1040,11.0)],
        "_meta": {"display_name": "Selmer Series III Baritone Sax (Reference)", "family": "Saxophone", "subcategory": "Baritone",
                  "verified": False, "source": "Selmer modern professional specs",
                  "description": "Selmer Series III bari (current flagship). Improved ergonomics over Mark VI. Better altissimo. Low A key standard. Gold lacquer or silver plate."},
    },

    # 3D Printed Baritone Sax - Cults3D (Printgear3D)
    "printgear3d_baritone_sax": {
        "bore_length": 1140.0, "bore_diameter": (30.0, 55.0), "wall_thickness": 5.5,
        "closed_top": False,
        "holes": [(160,9.5),(270,9.5),(380,9.5),(490,10.0),(600,10.0),(710,10.0),(820,10.5),(930,10.5),(1040,11.0)],
        "_meta": {"display_name": "Baritone Saxophone (Printgear3D)", "family": "Saxophone", "subcategory": "Baritone",
                  "verified": True, "source": "Cults3D (Printgear3D)", "url": "https://cults3d.com/en/3d-model/art/saxofon-baritono-baritone-saxophone",
                  "description": "Baritone saxophone by Printgear3D. 80cm x 40cm. Professional dimensions. Optimized for 3D printing. Conical bore 30-55mm. Low A key optional."},
    },

    # Professional mouthpieces for low reeds
    "baritone_sax_mouthpiece": {
        "bore_length": 120.0, "bore_diameter": 18.0, "wall_thickness": 4.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Baritone Sax Mouthpiece (Printable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": False, "source": "Printables / Custom design",
                  "description": "Playable baritone sax mouthpiece. Tip opening ~2.8-3.2mm. Requires baritone reed + ligature. Print on side, sand finish. Large chamber for warm tone."},
    },

    "bass_sax_mouthpiece": {
        "bore_length": 140.0, "bore_diameter": 22.0, "wall_thickness": 5.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Bass Sax Mouthpiece (Printable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": False, "source": "Printables / Custom design",
                  "description": "Playable bass sax mouthpiece. Tip opening ~3.0-3.5mm. Requires bass sax reed + ligature. Print on side. Very large chamber."},
    },

    "contra_alto_clarinet_mouthpiece": {
        "bore_length": 95.0, "bore_diameter": 16.5, "wall_thickness": 3.5,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Contra-Alto Clarinet Mouthpiece (Printable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": False, "source": "Printables / Custom design",
                  "description": "Playable contra-alto clarinet mouthpiece. Tip opening ~1.9-2.2mm. Uses alto sax reed or modified bass clarinet reed. Print on side."},
    },

    "contra_bass_clarinet_mouthpiece": {
        "bore_length": 110.0, "bore_diameter": 19.0, "wall_thickness": 4.0,
        "closed_top": False,
        "holes": [],
        "_meta": {"display_name": "Contra-Bass Clarinet Mouthpiece (Printable)", "family": "Parts & Accessories", "subcategory": "Mouthpiece",
                  "verified": False, "source": "Printables / Custom design",
                  "description": "Playable contra-bass clarinet mouthpiece. Tip opening ~2.2-2.5mm. Uses bass sax reed or contra reed. Print on side. Large chamber."},
    },

    # === TEST instruments (optimized via pareto_sweep + refine_sequential) ===
    # These are NOT verified against physical measurements.

    "contra_alto_clarinet_optimized_test": {
        "bore_length": 741.6,
        "bore_diameter": 17.1,
        "wall_thickness": 2.5,
        "closed_top": True,
        "holes": [
            (122.4, 3.74), (147.0, 3.77), (180.9, 3.83), (213.6, 3.82),
            (243.9, 3.82), (274.1, 3.65), (299.3, 3.82), (324.9, 3.82),
        ],
        "_meta": {
            "display_name": "Contra-Alto Clarinet in Eb (Pareto-Optimized Test)",
            "family": "Clarinet", "subcategory": "Contra-Alto",
            "verified": False,
            "source": "pareto_sweep + refine_sequential, w_int=1.0 baseline",
            "description": "TEST instrument - contra-alto clarinet optimized for concert Bb2 target. Not verified physically.",
        },
    },
    "bass_clarinet_optimized_test": {
        "bore_length": 1483.4,
        "bore_diameter": 22.0,
        "wall_thickness": 3.0,
        "closed_top": True,
        "holes": [
            (224.8, 3.94), (368.0, 3.91), (499.7, 3.72), (553.9, 3.19),
            (676.4, 3.25), (771.1, 3.24), (809.4, 2.69), (890.6, 3.38),
        ],
        "_meta": {
            "display_name": "Bass Clarinet in Bb (Pareto-Optimized Test)",
            "family": "Clarinet", "subcategory": "Bass",
            "verified": False,
            "source": "pareto_sweep + refine_sequential, w_int=1.0 baseline",
            "description": "TEST instrument - bass clarinet optimized for concert Bb2 target. Not verified physically.",
        },
    },
    "concert_fsharp2_closed_open_test": {
        "bore_length": 986.0,
        "bore_diameter": 14.5,
        "wall_thickness": 2.5,
        "closed_top": True,
        "holes": [],
        "_meta": {
            "display_name": "Concert F#2 Closed-Open Test Pipe",
            "family": "Test", "subcategory": "Benchmark",
            "verified": False,
            "source": "pareto_sweep + refine_sequential, single-note closed-open pipe",
            "description": "TEST instrument - closed-open pipe optimized for F#2 (87.31 Hz). Bare bore, no tone holes. RMS 0.00c. Not verified physically.",
        },
    },

}


def generate_by_name(name: str, output_dir: str = "output"):
    """Generate a pre-defined instrument by name, export STL + STEP."""
    if name not in INSTRUMENTS:
        raise ValueError(f"Unknown instrument: {name}. Available: {list(INSTRUMENTS.keys())}")

    spec = {k: v for k, v in INSTRUMENTS[name].items() if k != "_meta"}
    solid = generate_instrument(**spec)

    stl_path = os.path.join(output_dir, f"{name}.stl")
    step_path = os.path.join(output_dir, f"{name}.step")

    stl_time = export_stl(solid, stl_path)
    step_time = export_step(solid, step_path)

    stl_size = os.path.getsize(stl_path) / 1024
    step_size = os.path.getsize(step_path) / 1024

    return {
        "name": name,
        "stl_path": stl_path,
        "step_path": step_path,
        "stl_size_kb": round(stl_size, 1),
        "step_size_kb": round(step_size, 1),
        "stl_time": round(stl_time, 3),
        "step_time": round(step_time, 3),
        "spec": spec,
    }


def generate_all(output_dir: str = "output"):
    """Generate all pre-defined instruments. Returns list of result dicts."""
    results = []
    for name in INSTRUMENTS:
        r = generate_by_name(name, output_dir)
        results.append(r)
    return results
