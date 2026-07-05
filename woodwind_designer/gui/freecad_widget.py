import os
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QComboBox, QLabel, QTextEdit, QFileDialog, QProgressBar,
    QFormLayout, QCheckBox, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Qt

from ..engine.freecad_engine import (
    generate_instrument, bore_from_yaml, is_available as fc_available
)


class FreeCADWorker(QThread):
    finished = Signal(object)
    progress = Signal(str)

    def __init__(self, yaml_path, output_dir, export_stl, export_step, export_fcstd):
        super().__init__()
        self.yaml_path = yaml_path
        self.output_dir = output_dir
        self.export_stl = export_stl
        self.export_step = export_step
        self.export_fcstd = export_fcstd

    def run(self):
        self.progress.emit("Reading YAML config...")
        try:
            bore, holes = bore_from_yaml(self.yaml_path)
        except Exception as e:
            self.finished.emit(type("R", (), {"success": False, "log": f"Failed to read YAML: {e}"})())
            return

        self.progress.emit(f"Found bore: {len(bore)} segments, holes: {len(holes)}")
        self.progress.emit("Launching FreeCAD...")

        result = generate_instrument(
            output_dir=self.output_dir,
            bore_segments=bore,
            tone_holes=holes,
            export_stl=self.export_stl,
            export_step=self.export_step,
            export_fcstd=self.export_fcstd,
        )
        self.progress.emit("Done." if result.success else "Failed.")
        self.finished.emit(result)


class FreeCADWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        config_group = QGroupBox("FreeCAD 3D Export")
        config_layout = QFormLayout(config_group)

        yaml_row = QHBoxLayout()
        self.yaml_label = QLabel("(none selected)")
        self.browse_btn = QPushButton("Browse YAML...")
        self.browse_btn.clicked.connect(self._browse)
        yaml_row.addWidget(self.yaml_label, stretch=1)
        yaml_row.addWidget(self.browse_btn)
        config_layout.addRow("Config File:", yaml_row)

        self.stl_cb = QCheckBox("Export STL (for 3D printing)")
        self.stl_cb.setChecked(True)
        config_layout.addRow("", self.stl_cb)

        self.step_cb = QCheckBox("Export STEP (CAD exchange)")
        config_layout.addRow("", self.step_cb)

        self.fcstd_cb = QCheckBox("Export FCStd (FreeCAD native)")
        config_layout.addRow("", self.fcstd_cb)

        layout.addWidget(config_group)

        actions = QHBoxLayout()
        self.run_btn = QPushButton("Generate 3D Model in FreeCAD")
        self.run_btn.clicked.connect(self._run)
        self.run_btn.setEnabled(fc_available())
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

        if not fc_available():
            help_text = QLabel(
                "FreeCAD 1.1 not found.\n"
                "Install from: https://www.freecad.org/downloads.php\n"
                f"(expected at: C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe)"
            )
            help_text.setStyleSheet("color: #D4A76A; padding: 10px;")
            layout.addWidget(help_text)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output, stretch=1)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select YAML Config", "",
            "YAML files (*.yaml *.yml);;All files (*.*)"
        )
        if path:
            self.yaml_label.setText(path)

    def _run(self):
        yaml_path = self.yaml_label.text()
        if not yaml_path or yaml_path == "(none selected)" or not os.path.exists(yaml_path):
            self.log_output.append("Please select a YAML config file first.")
            return

        out_dir = os.path.join(os.path.dirname(yaml_path), "freecad_" + Path(yaml_path).stem)

        self.log_output.clear()
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.show()

        self._worker = FreeCADWorker(
            yaml_path, out_dir,
            self.stl_cb.isChecked(),
            self.step_cb.isChecked(),
            self.fcstd_cb.isChecked(),
        )
        self._worker.progress.connect(lambda m: self.log_output.append(m))
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self.log_output.append("Cancelled.")
        self._reset_ui()

    def _on_done(self, result):
        self._reset_ui()
        if result.success:
            self.log_output.append(f"Success: {result.log}")
            for f in result.files:
                size = os.path.getsize(f) if os.path.exists(f) else 0
                self.log_output.append(f"  {f} ({size / 1024:.1f} KB)")
        else:
            self.log_output.append(f"Failed: {result.log}")

    def _reset_ui(self):
        self.run_btn.setEnabled(fc_available())
        self.cancel_btn.setEnabled(False)
        self.progress_bar.hide()
