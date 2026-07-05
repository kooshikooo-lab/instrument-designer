import os
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QComboBox, QSpinBox, QLabel, QTextEdit, QFileDialog, QProgressBar,
    QFormLayout, QMessageBox, QCheckBox, QLineEdit
)
from PySide6.QtCore import QThread, Signal, Qt

from ..engine.demakein_wrapper import DemakeinDesigner, HAVE_DEMAKEIN
from ..engine.remote_client import RemoteDesigner


class DesignWorker(QThread):
    finished = Signal(object)
    progress = Signal(str)

    def __init__(self, designer, preset, transpose, output_dir):
        super().__init__()
        self.designer = designer
        self.preset = preset
        self.transpose = transpose
        self.output_dir = output_dir

    def run(self):
        display = self.designer.PRESET_DISPLAY_NAMES.get(self.preset, self.preset)
        self.progress.emit(f"Starting design: {display} (transpose={self.transpose})...")
        result = self.designer.design(
            preset=self.preset,
            transpose=self.transpose,
            output_dir=self.output_dir,
            on_progress=lambda msg: self.progress.emit(msg),
        )
        self.progress.emit("Design complete." if result.success else "Design failed.")
        self.finished.emit(result)


class DesignWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.designer = DemakeinDesigner()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        config_group = QGroupBox("Design Configuration")
        config_layout = QFormLayout(config_group)

        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet("color: #D4A76A; font-style: italic; padding: 2px 0 6px 6px;")

        cat_row = QHBoxLayout()
        self.family_combo = QComboBox()
        self.family_combo.addItems(self.designer.list_families())
        self.family_combo.currentTextChanged.connect(self._on_family_changed)
        cat_row.addWidget(self.family_combo, stretch=1)

        self.sub_combo = QComboBox()
        self.sub_combo.currentTextChanged.connect(self._on_sub_changed)
        cat_row.addWidget(self.sub_combo, stretch=1)

        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_index_changed)
        cat_row.addWidget(self.preset_combo, stretch=2)

        config_layout.addRow("Instrument:", cat_row)
        config_layout.addRow("", self.desc_label)

        self.transpose_spin = QSpinBox()
        self.transpose_spin.setRange(-24, 24)
        self.transpose_spin.setValue(0)
        self.transpose_spin.setSuffix(" semitones")
        config_layout.addRow("Transpose:", self.transpose_spin)

        self.output_path = QLabel("(auto)")
        config_layout.addRow("Output:", self.output_path)

        layout.addWidget(config_group)

        # -- Remote server --
        server_box = QGroupBox("Remote Compute")
        server_box.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #4a4a4a; border-radius: 6px; "
            "margin-top: 10px; padding-top: 14px; background: #1e1e1e; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #D4A76A; }"
        )
        server_layout = QHBoxLayout(server_box)

        self.remote_check = QCheckBox("Use Remote Server")
        self.remote_check.setStyleSheet("color: #C0B0A0;")
        server_layout.addWidget(self.remote_check)

        self.server_url_input = QLineEdit("http://localhost:8000")
        self.server_url_input.setStyleSheet(
            "QLineEdit { padding: 4px 8px; border: 1px solid #4a4a4a; border-radius: 4px; "
            "background: #2a2a2a; color: #C0B0A0; }"
            "QLineEdit:hover { border-color: #C99B5C; }"
        )
        server_layout.addWidget(self.server_url_input, stretch=1)

        self.test_btn = QPushButton("Test")
        self.test_btn.setStyleSheet(
            "QPushButton { padding: 4px 12px; border: 1px solid #4a4a4a; border-radius: 4px; "
            "background: #2a2a2a; color: #C0B0A0; }"
            "QPushButton:hover { background: #3a3a3a; border-color: #C99B5C; }"
        )
        self.test_btn.clicked.connect(self._test_server)
        server_layout.addWidget(self.test_btn)

        self.server_status = QLabel("")
        self.server_status.setStyleSheet("color: #8B5E3C; font-size: 11px; padding-left: 4px;")
        server_layout.addWidget(self.server_status)

        server_layout.addStretch()
        layout.addWidget(server_box)

        actions = QHBoxLayout()
        self.run_btn = QPushButton("Run Design")
        self.run_btn.clicked.connect(self._run_design)
        self.run_btn.setEnabled(HAVE_DEMAKEIN)
        actions.addWidget(self.run_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        actions.addWidget(self.cancel_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        actions.addWidget(self.progress_bar)

        layout.addLayout(actions)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output, stretch=1)

        self._on_family_changed(self.family_combo.currentText())

    def _current_preset_key(self) -> str:
        idx = self.preset_combo.currentIndex()
        return self.preset_combo.itemData(idx) or ""

    def _on_family_changed(self, family):
        self.sub_combo.blockSignals(True)
        self.sub_combo.clear()
        self.sub_combo.addItems(self.designer.list_subcategories(family))
        self.sub_combo.blockSignals(False)
        self._on_sub_changed(self.sub_combo.currentText())

    def _on_sub_changed(self, sub):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        family = self.family_combo.currentText()
        presets = self.designer.list_presets(family, sub)
        if presets:
            for key in presets:
                display = self.designer.PRESET_DISPLAY_NAMES.get(key, key)
                self.preset_combo.addItem(display, userData=key)
            self.preset_combo.blockSignals(False)
            self._on_preset_index_changed(0)
        else:
            self.preset_combo.addItem("(no presets available)")
            self.preset_combo.blockSignals(False)

    def _on_preset_index_changed(self, idx):
        key = self.preset_combo.itemData(idx) or ""
        desc = self.designer.get_description(key)
        self.desc_label.setText(desc)

    def _get_designer(self):
        if self.remote_check.isChecked():
            url = self.server_url_input.text().strip()
            return RemoteDesigner(url)
        return self.designer

    def _run_design(self):
        key = self._current_preset_key()
        if not key:
            return

        designer = self._get_designer()
        out_dir = os.path.join(tempfile.gettempdir(), f"woodwind_{key}")
        self.log_output.clear()
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.show()

        self._worker = DesignWorker(
            designer, key,
            self.transpose_spin.value(), out_dir
        )
        self._worker.progress.connect(lambda msg: self.log_output.append(msg))
        self._worker.finished.connect(self._on_design_done)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self.log_output.append("Design cancelled.")
        self._reset_ui()

    def _on_design_done(self, result):
        self._reset_ui()
        if result.success:
            self.log_output.append(f"Completed: {result.log}")
            for stl in result.stl_files:
                sz = os.path.getsize(stl) / 1024 if os.path.exists(stl) else 0
                self.log_output.append(f"  STL: {stl} ({sz:.1f} KB)")
        else:
            self.log_output.append(f"Failed: {result.log}")

    def _test_server(self):
        url = self.server_url_input.text().strip()
        client = RemoteDesigner(url)
        if client.health():
            self.server_status.setText("Connected")
            self.server_status.setStyleSheet("color: #6AAB6A; font-size: 11px; padding-left: 4px;")
            self.log_output.append(f"Connected to server at {url}")
        else:
            self.server_status.setText("No response")
            self.server_status.setStyleSheet("color: #C04040; font-size: 11px; padding-left: 4px;")
            self.log_output.append(f"Failed to reach server at {url}")

    def select_preset(self, preset: str):
        family, sub = self.designer.find_preset_category(preset)
        if family:
            self.family_combo.setCurrentText(family)
        if sub:
            self.sub_combo.setCurrentText(sub)
        for i in range(self.preset_combo.count()):
            if self.preset_combo.itemData(i) == preset:
                self.preset_combo.setCurrentIndex(i)
                display = self.designer.PRESET_DISPLAY_NAMES.get(preset, preset)
                self.log_output.append(f"Loaded: {display}")
                return

    def _reset_ui(self):
        self.run_btn.setEnabled(HAVE_DEMAKEIN or self.remote_check.isChecked())
        self.cancel_btn.setEnabled(False)
        self.progress_bar.hide()
