from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl


SECTION_STYLE = (
    "QGroupBox { font-weight: bold; border: 1px solid #4a4a4a; border-radius: 6px; "
    "margin-top: 12px; padding-top: 16px; background: #1e1e1e; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #D4A76A; }"
)

LINK_STYLE = (
    "QPushButton { text-align: left; border: none; color: #C99B5C; "
    "padding: 3px 0; font-size: 12px; background: transparent; }"
    "QPushButton:hover { color: #E8D5B7; text-decoration: underline; }"
)

TIP_STYLE = "color: #C0B0A0; font-size: 12px; padding: 2px 0; line-height: 1.5;"


class _LinkButton(QPushButton):
    def __init__(self, text, url):
        super().__init__(text)
        self._url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(LINK_STYLE)
        self.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self._url)))


class ResourcesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        # -- Title --
        title = QLabel("Resources & Design Tips")
        tf = QFont()
        tf.setPointSize(14)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #D4A76A; padding: 8px 0 4px 0;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Design tips, community projects, tutorials, and reference materials "
            "for 3D-printed musical instruments."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #A09080; padding-bottom: 10px;")
        layout.addWidget(subtitle)

        # -- 1. Design Tips --
        tips_box = QGroupBox("Design Tips for 3D-Printed Instruments")
        tips_box.setStyleSheet(SECTION_STYLE)
        tips_layout = QVBoxLayout(tips_box)

        tips = [
            "<b>Tuning Precision:</b> Woodwind hole placement must be precise within ~0.1 mm "
            "for accurate pitch. Always calibrate your printer before printing an instrument.",
            "<b>Post-Processing:</b> Sand bore interiors smooth (200-400 grit). Seal porous "
            "filaments with epoxy or acrylic spray for better acoustics and hygiene.",
            "<b>Material Choice:</b> PLA is easiest but may warp in heat. PETG offers better "
            "durability. Resin (SLA) gives the smoothest finish for bores and tone holes.",
            "<b>String Instruments:</b> Use metal truss rods or carbon fiber inserts inside "
            "the neck to handle string tension (50-100 lbs for guitar). PLA alone will bend.",
            "<b>Assembly:</b> Design multi-part instruments with alignment pins/dowels. "
            "Use CA glue for permanent joints; rubber bands or threaded inserts for "
            "disassemblable sections.",
            "<b>Acoustics:</b> Thicker walls (>2 mm) reduce unwanted resonance. For wind "
            "instruments, a smooth bore is more important than wall thickness.",
            "<b>Brass Instruments:</b> 3D-printed mouthpieces work well. For the body, "
            "print in sections and assemble. Consider electroplating for a metallic finish.",
            "<b>Experimentation:</b> Print a simple whistle or ocarina first to calibrate "
            "your workflow before attempting a full clarinet or violin.",
        ]
        for tip in tips:
            lbl = QLabel(tip)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(TIP_STYLE)
            tips_layout.addWidget(lbl)

        layout.addWidget(tips_box)

        # -- 2. Open-Source Instrument Projects --
        proj_box = QGroupBox("Open-Source 3D-Printable Instrument Projects")
        proj_box.setStyleSheet(SECTION_STYLE)
        proj_layout = QVBoxLayout(proj_box)

        projects = [
            ("Demakein", "https://github.com/introlab/demakein",
             "Python library for designing and optimizing woodwind instruments. Used by this app."),
            ("OpenWInD", "https://github.com/OpenWind/OpenWind",
             "Acoustic simulation software for wind instruments (Inria)."),
            ("FreeCAD", "https://www.freecad.org/",
             "Free parametric 3D CAD modeler. Used by this app for STL export."),
            ("Hovalin - 3D Printed Violin", "https://hovalin.com/",
             "Open-source 3D printable acoustic violin. Files on GitHub."),
            ("OpenFab PDX / Strata Violins", "https://openfabpdx.com/",
             "Professional 3D-printed electric violins. Open-source platform."),
            ("FFFiddle", "https://openfabpdx.com/fffiddle/",
             "First consumer 3D-printable electric violin (2012)."),
            ("Afflato Historical Woodwinds", "https://afflato.com/",
             "Hand-finished 3D-printed replicas of historical woodwinds (traverso, oboe, clarinet)."),
            ("VLNLAB 3D Printed Violin", "https://www.vlnlab.com/",
             "Playable 3D-printed violin and viola models."),
            ("McMele Ukulele", "https://www.printables.com/model/584113-mcmele-ukulele",
             "Fully 3D-printable ukulele on Printables."),
        ]
        for name, url, desc in projects:
            row = QHBoxLayout()
            row.setSpacing(8)
            link = _LinkButton(name, url)
            link.setFixedWidth(260)
            row.addWidget(link)
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #908070; font-size: 11px;")
            row.addWidget(d, stretch=1)
            proj_layout.addLayout(row)

        layout.addWidget(proj_box)

        # -- 3. STL Repositories --
        stl_box = QGroupBox("STL Repositories & Model Libraries")
        stl_box.setStyleSheet(SECTION_STYLE)
        stl_layout = QVBoxLayout(stl_box)

        repos = [
            ("Printables.com – Music", "https://www.printables.com/tag/music",
             "Massive free library: flutes, ocarinas, trumpets, violins, ukuleles."),
            ("MakerWorld – Instruments", "https://makerworld.com/en/collections/5699452-musical-instruments",
             "Large collection: playable trumpet, trombone, flutes, ocarinas, didgeridoo."),
            ("Cults3D – Free Musical Instruments", "https://cults3d.com/en/tags/musical%2Binstrument?only_free=true",
             "Filter by free: guitars, violins, brass, woodwinds, percussion."),
            ("Thingiverse – Music", "https://www.thingiverse.com/musical/instruments",
             "Classic repository with hundreds of instrument designs."),
            ("Yeggi – Musical Instruments", "https://www.yeggi.com/q/musical+instrument/",
             "Cross-platform 3D model search engine."),
            ("Thangs – Wind Instruments", "https://thangs.com/search/wind%20instrument?scope=models&sort=popular&period=all",
             "Vector search across Printables, Thingiverse, Cults3D, and more."),
            ("MyMiniFactory – Music", "https://www.myminifactory.com/search/?category=music&q=instrument",
             "Curated free & premium 3D printable instrument models."),
            ("YouMagine – Instruments", "https://www.youmagine.com/search?q=instrument",
             "Open-source 3D printing community with instrument designs."),
            ("GrabCAD – Musical Instruments", "https://grabcad.com/library?page=1&time=all_time&query=musical+instrument",
             "Engineering-focused CAD library with many instrument models."),
            ("Pinshape – Music", "https://pinshape.com/search?q=instrument&sort=popular",
             "Free and premium 3D printable instrument files."),
            ("3DExport – Instruments", "https://3dexport.com/free-3d-models/instruments",
             "Free 3D instrument models in STL and other formats."),
            ("Sketchfab – Wind Instruments", "https://sketchfab.com/tags/wind-instrument",
             "Free 3D models of wind instruments (CC0/CC-BY licensed)."),
        ]
        for name, url, desc in repos:
            row = QHBoxLayout()
            row.setSpacing(8)
            link = _LinkButton(name, url)
            link.setFixedWidth(280)
            row.addWidget(link)
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #908070; font-size: 11px;")
            row.addWidget(d, stretch=1)
            stl_layout.addLayout(row)

        layout.addWidget(stl_box)

        # -- 4. Articles & Tutorials --
        art_box = QGroupBox("Articles, Blogs & Video Tutorials")
        art_box.setStyleSheet(SECTION_STYLE)
        art_layout = QVBoxLayout(art_box)

        articles = [
            ("Hovalin: An Open Source 3D Printed Violin (Opensource.com)",
             "https://opensource.com/life/16/5/hovalin",
             "How a husband-wife team created an open-source 3D-printed violin."),
            ("RCM 3D-Printed Historical Instruments",
             "https://www.rcm.ac.uk/about/news/all/2024-02-223dprintedinstruments.aspx",
             "Royal College of Music creates 3D copies of rare historical woodwinds."),
            ("3D Printing a Playable Trumpet (YouTube)",
             "https://www.youtube.com/results?search_query=3d+printed+trumpet+playable",
             "Search results for playable 3D-printed trumpet builds."),
            ("Making a 3D Printed Violin (YouTube Series)",
             "https://www.youtube.com/results?search_query=3d+printed+violin+playable",
             "Step-by-step builds of functional 3D-printed violins."),
            ("Demakein Documentation",
             "https://demakein.readthedocs.io/",
             "Official docs for the Demakein instrument design library."),
            ("OpenWInD Tutorial & Examples",
             "https://github.com/OpenWind/OpenWind",
             "Acoustic simulation tutorials and example scripts."),
        ]
        for name, url, desc in articles:
            row = QHBoxLayout()
            row.setSpacing(8)
            link = _LinkButton(name, url)
            link.setFixedWidth(360)
            row.addWidget(link)
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #908070; font-size: 11px;")
            row.addWidget(d, stretch=1)
            art_layout.addLayout(row)

        layout.addWidget(art_box)

        # -- 5. AI Design Tools --
        ai_box = QGroupBox("AI-Powered Design Tools (Image/Text to STL)")
        ai_box.setStyleSheet(SECTION_STYLE)
        ai_layout = QVBoxLayout(ai_box)

        ai_tools = [
            ("Meshy AI – Text/Image to 3D", "https://www.meshy.ai/",
             "Free tier: generate 3D models from text or image. Exports STL/OBJ/GLB. Great for rapid prototyping of instrument parts."),
            ("Tripo AI – Text/Image to 3D", "https://www.tripo3d.ai/",
             "Fast, free AI model generator. High-quality watertight meshes ready for printing."),
            ("Hyper3D Rodin – Image to STL", "https://hyper3d.ai/features/image-to-3d",
             "AI-powered photo to 3D conversion. Free tier available. Integrates with Blender."),
            ("ImageToSTL.com", "https://imagetostl.com/",
             "Free online tool converts JPG/PNG to STL with heightmap or extrude modes. No registration."),
            ("Sloyd – Text/Image to STL", "https://www.sloyd.ai/use-case/3d-printing",
             "Free AI 3D model generator optimized for 3D printing. Unlimited STL/OBJ exports."),
            ("Remeshy – Free STL Creator", "https://remeshy.com/stl-creator",
             "Browser-based AI generator. Text or image input, download ready-to-print STL."),
            ("MakeIt3D – Photo to 3D", "https://makeit3d.app/",
             "Turn photos into 3D printable models with AI. No 3D skills required."),
            ("Zoo.dev – Text to CAD (STEP)", "https://zoo.dev/",
             "Conversational AI that generates precise, editable STEP geometry for functional parts. Watertight, parametric CAD output."),
            ("Backflip AI – Scan to CAD", "https://www.backflip.ai/",
             "AI foundation model that creates digital twins from 3D scans. Outputs CAD for CNC or 3D printing."),
            ("Adam CAD – Text to Parametric CAD", "https://www.adamcad.com/",
             "Generate parametric 3D models from text descriptions with real dimensions and sliders."),
        ]
        for name, url, desc in ai_tools:
            row = QHBoxLayout()
            row.setSpacing(8)
            link = _LinkButton(name, url)
            link.setFixedWidth(280)
            row.addWidget(link)
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #908070; font-size: 11px;")
            row.addWidget(d, stretch=1)
            ai_layout.addLayout(row)

        layout.addWidget(ai_box)

        # -- 6. Community --
        comm_box = QGroupBox("Community & Forums")
        comm_box.setStyleSheet(SECTION_STYLE)
        comm_layout = QVBoxLayout(comm_box)

        communities = [
            ("r/3Dprinting on Reddit", "https://www.reddit.com/r/3Dprinting/",
             "Active community with regular instrument printing posts."),
            ("r/FunctionalPrint (Instruments)", "https://www.reddit.com/r/functionalprint/",
             "Functional 3D prints including musical instruments."),
            ("Printables Community", "https://www.printables.com/",
             "Post makes, share tips, and discuss instrument designs."),
            ("FreeCAD Forum", "https://forum.freecad.org/",
             "Help with parametric modeling for instrument design."),
        ]
        for name, url, desc in communities:
            row = QHBoxLayout()
            row.setSpacing(8)
            link = _LinkButton(name, url)
            link.setFixedWidth(260)
            row.addWidget(link)
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #908070; font-size: 11px;")
            row.addWidget(d, stretch=1)
            comm_layout.addLayout(row)

        layout.addWidget(comm_box)

        layout.addStretch()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
