from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont, QPixmap

from .. import __app_name__, __version__
from .design_widget import DesignWidget
from .simulation_widget import SimulationWidget
from .freecad_widget import FreeCADWidget
from .library_widget import LibraryWidget
from .project_widget import ProjectWidget
from .resources_widget import ResourcesWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1200, 800)

        self._setup_menu()
        self._setup_ui()
        self._setup_status()

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("&Tools")
        for name, callback in [
            ("Open Workspace Folder", lambda: self._open_workspace()),
        ]:
            act = QAction(name, self)
            act.triggered.connect(callback)
            tools_menu.addAction(act)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.library_tab = LibraryWidget()
        self.library_tab.preset_selected.connect(self._on_preset_from_library)
        self.resources_tab = ResourcesWidget()
        self.project_tab = ProjectWidget()
        self.design_tab = DesignWidget()
        self.sim_tab = SimulationWidget()
        self.freecad_tab = FreeCADWidget()

        self.tabs.addTab(self.library_tab, "Library")
        self.tabs.addTab(self.resources_tab, "Resources")
        self.tabs.addTab(self.project_tab, "Projects")
        self.tabs.addTab(self.design_tab, "Design")
        self.tabs.addTab(self.sim_tab, "Simulate")
        self.tabs.addTab(self.freecad_tab, "3D Export")

        self.setCentralWidget(self.tabs)

    def _setup_status(self):
        self.status = QStatusBar()
        status_font = QFont()
        status_font.setPointSize(9)
        self.status.setFont(status_font)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #E8D5B7;")
        self.status.addWidget(self.status_label, 1)

        ver_label = QLabel(f"v{__version__}")
        ver_label.setStyleSheet("color: #8B5E3C; padding-right: 8px;")
        self.status.addPermanentWidget(ver_label)

        self.setStatusBar(self.status)

    def _on_preset_from_library(self, preset: str):
        self.tabs.setCurrentWidget(self.design_tab)
        self.design_tab.select_preset(preset)
        self.status_label.setText(f"Loaded preset: {preset} from library")

    def _open_workspace(self):
        path = str(Path.home() / "WoodwindProjects")
        Path(path).mkdir(parents=True, exist_ok=True)
        import os
        os.startfile(path)

    def _show_about(self):
        QMessageBox.about(
            self, f"About {__app_name__}",
            f"<h2>{__app_name__}</h2>"
            f"<p><b>Version {__version__}</b></p>"
            "<p>A premium desktop application for designing, simulating, "
            "and 3D-printing musical instruments.</p>"
            "<hr>"
            "<p><b>Powered by:</b></p>"
            "<ul>"
            "<li><b>Demakein</b> &mdash; Instrument design &amp; optimization</li>"
            "<li><b>OpenWInD</b> &mdash; Acoustic simulation (Inria)</li>"
            "<li><b>FreeCAD</b> &mdash; 3D parametric modeling</li>"
            "<li><b>PySide6</b> &mdash; Graphical interface</li>"
            "</ul>"
            "<hr>"
            "<p>GPL v3 Licensed &bull; Open source</p>"
        )
