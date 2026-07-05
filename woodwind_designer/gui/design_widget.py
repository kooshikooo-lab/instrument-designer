import os
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QComboBox, QSpinBox, QLabel, QTextEdit, QFileDialog, QProgressBar,
    QFormLayout, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Qt

from ..engine.demakein_wrapper import DemakeinDesigner, HAVE_DEMAKEIN


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

    def _run_design(self):
        key = self._current_preset_key()
        if not key:
            return

        out_dir = os.path.join(tempfile.gettempdir(), f"woodwind_{key}")
        self.log_output.clear()
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.show()

        self._worker = DesignWorker(
            self.designer, key,
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
        self.run_btn.setEnabled(HAVE_DEMAKEIN)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.hide()
