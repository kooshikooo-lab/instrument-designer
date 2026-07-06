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
from .parameter_editor import ParameterEditor

QUICK_HELP = (
    "Quick Draft uses faster optimization (smaller pool, looser convergence) "
    "and lower-quality STL meshes. Results are less refined but produced much faster."
)


class DesignWorker(QThread):
    finished = Signal(object)
    progress = Signal(str)

    def __init__(self, designer, preset, transpose, output_dir, quick=False):
        super().__init__()
        self.designer = designer
        self.preset = preset
        self.transpose = transpose
        self.output_dir = output_dir
        self.quick = quick

    def run(self):
        display = self.designer.PRESET_DISPLAY_NAMES.get(self.preset, self.preset)
        label = f"Quick Draft: {display}" if self.quick else f"Starting design: {display}"
        self.progress.emit(f"{label} (transpose={self.transpose})...")
        result = self.designer.design(
            preset=self.preset,
            transpose=self.transpose,
            output_dir=self.output_dir,
            on_progress=lambda msg: self.progress.emit(msg),
            quick=self.quick,
        )
        self.progress.emit("Design complete." if result.success else "Design failed.")
        self.finished.emit(result)


class BatchDesignWorker(QThread):
    finished = Signal(object)
    progress = Signal(str)

    def __init__(self, designer, preset, transpose_range, output_base, quick):
        super().__init__()
        self.designer = designer
        self.preset = preset
        self.transpose_range = transpose_range
        self.output_base = output_base
        self.quick = quick
        self.results = []

    def run(self):
        total = len(self.transpose_range)
        for i, transp in enumerate(self.transpose_range):
            display = self.designer.PRESET_DISPLAY_NAMES.get(self.preset, self.preset)
            self.progress.emit(f"[{i+1}/{total}] Transpose={transp:+d}: {display}")
            out_dir = os.path.join(self.output_base, f"t{transp:+d}")
            try:
                result = self.designer.design(
                    preset=self.preset, transpose=transp,
                    output_dir=out_dir,
                    on_progress=lambda msg: None,
                    quick=self.quick,
                )
                self.results.append((transp, result))
                if result.success:
                    self.progress.emit(f"[{i+1}/{total}] {display} transpose={transp:+d} OK")
                else:
                    self.progress.emit(f"[{i+1}/{total}] {display} transpose={transp:+d} FAILED")
            except Exception as e:
                self.progress.emit(f"[{i+1}/{total}] transpose={transp:+d} ERROR: {e}")
                from ..engine.demakein_wrapper import DesignResult
                self.results.append((transp, DesignResult(
                    output_dir=out_dir, ident="", log=str(e), success=False
                )))
        self.finished.emit(self.results)


class DesignWidget(QWidget):
    design_completed = Signal(str, str)  # yaml_path, target
    design_succeeded = Signal(str)       # yaml_path (for auto-save)

    def __init__(self):
        super().__init__()
        self.designer = DemakeinDesigner()
        self._worker = None
        self._last_yaml = ""
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

        self.quick_check = QCheckBox("Quick Draft (faster, less refined)")
        self.quick_check.setToolTip(QUICK_HELP)
        self.quick_check.setStyleSheet("color: #C0B0A0; padding: 4px 0;")
        config_layout.addRow("", self.quick_check)

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
        self.remote_check.toggled.connect(lambda: self._update_run_btn())
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

        self.send_bar = QHBoxLayout()
        self.send_bar.setContentsMargins(0, 4, 0, 4)
        self.send_to_sim_btn = QPushButton("Send to Simulate")
        self.send_to_sim_btn.setEnabled(False)
        self.send_to_sim_btn.clicked.connect(self._send_to_simulate)
        self.send_bar.addWidget(self.send_to_sim_btn)
        self.send_to_fc_btn = QPushButton("Send to 3D Export")
        self.send_to_fc_btn.setEnabled(False)
        self.send_to_fc_btn.clicked.connect(self._send_to_freecad)
        self.send_bar.addWidget(self.send_to_fc_btn)
        self.edit_params_btn = QPushButton("Edit Parameters...")
        self.edit_params_btn.setEnabled(False)
        self.edit_params_btn.clicked.connect(self._edit_parameters)
        self.send_bar.addWidget(self.edit_params_btn)
        self.send_bar.addStretch()
        layout.addLayout(self.send_bar)

        # -- Batch mode --
        batch_box = QGroupBox("Batch Design")
        batch_layout = QVBoxLayout(batch_box)

        batch_top = QHBoxLayout()
        self.batch_check = QCheckBox("Enable Batch Mode")
        self.batch_check.toggled.connect(self._toggle_batch)
        self.batch_check.setStyleSheet("color: #C0B0A0;")
        batch_top.addWidget(self.batch_check)

        batch_top.addWidget(QLabel("From:"))
        self.batch_from = QSpinBox()
        self.batch_from.setRange(-24, 24)
        self.batch_from.setValue(-6)
        self.batch_from.setSuffix(" st")
        self.batch_from.setEnabled(False)
        batch_top.addWidget(self.batch_from)

        batch_top.addWidget(QLabel("To:"))
        self.batch_to = QSpinBox()
        self.batch_to.setRange(-24, 24)
        self.batch_to.setValue(6)
        self.batch_to.setSuffix(" st")
        self.batch_to.setEnabled(False)
        batch_top.addWidget(self.batch_to)

        self.batch_run_btn = QPushButton("Run Batch")
        self.batch_run_btn.clicked.connect(self._run_batch)
        self.batch_run_btn.setEnabled(False)
        batch_top.addWidget(self.batch_run_btn)

        batch_top.addStretch()
        batch_layout.addLayout(batch_top)
        layout.addWidget(batch_box)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output, stretch=1)

        self._update_run_btn()
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
        quick = self.quick_check.isChecked()
        out_dir = os.path.join(tempfile.gettempdir(), f"woodwind_{key}")
        self.log_output.clear()
        self.log_output.append("Design started — optimization in progress (may take several minutes)...")
        self.log_output.append("Tip: enable Quick Draft for faster but less refined results.")
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.show()

        self._worker = DesignWorker(
            designer, key,
            self.transpose_spin.value(), out_dir, quick
        )
        self._worker.progress.connect(lambda msg: self.log_output.append(msg))
        self._worker.finished.connect(self._on_design_done)

        from PySide6.QtCore import QTimer
        self._design_timer = QTimer()
        self._design_timer.setSingleShot(True)
        self._design_timer.timeout.connect(self._on_design_timeout)
        self._design_timer.start(900000)

        self._worker.start()

    def _on_design_timeout(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self.log_output.append("Design timed out after 15 minutes. Try Quick Draft or a simpler preset.")
            self._reset_ui()

    def _cancel(self):
        timer = getattr(self, '_design_timer', None)
        if timer:
            timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self.log_output.append("Design cancelled.")
        self._reset_ui()

    def _update_run_btn(self):
        enabled = HAVE_DEMAKEIN or self.remote_check.isChecked()
        self.run_btn.setEnabled(enabled)

    def _on_design_done(self, result):
        timer = getattr(self, '_design_timer', None)
        if timer:
            timer.stop()
        self._reset_ui()
        if result.success:
            self.log_output.append(f"Completed: {result.log}")
            for stl in result.stl_files:
                sz = os.path.getsize(stl) / 1024 if os.path.exists(stl) else 0
                self.log_output.append(f"  STL: {stl} ({sz:.1f} KB)")
            if result.config_yaml and os.path.exists(result.config_yaml):
                self._last_yaml = result.config_yaml
                self.send_to_sim_btn.setEnabled(True)
                self.send_to_fc_btn.setEnabled(True)
                self.edit_params_btn.setEnabled(True)
                self.log_output.append(f"\nConfig: {result.config_yaml}")
                self.log_output.append("↳ Use buttons to send to Simulate or 3D Export")
                self.design_succeeded.emit(result.config_yaml)
            else:
                self.log_output.append("\n(No YAML config generated for this preset)")
        else:
            self.log_output.append(f"Failed: {result.log}")

    def _edit_parameters(self):
        if not self._last_yaml or not os.path.exists(self._last_yaml):
            return
        dialog = ParameterEditor(self._last_yaml, self)
        dialog.exec()
        self.log_output.append(f"Parameters updated: {self._last_yaml}")

    def _toggle_batch(self, checked):
        self.batch_from.setEnabled(checked)
        self.batch_to.setEnabled(checked)
        self.batch_run_btn.setEnabled(checked)

    def _run_batch(self):
        key = self._current_preset_key()
        if not key:
            return
        if self.batch_from.value() > self.batch_to.value():
            QMessageBox.warning(self, "Invalid Range",
                                "Start transposition must be ≤ end transposition.")
            return

        transpose_values = list(range(self.batch_from.value(), self.batch_to.value() + 1))
        out_base = os.path.join(tempfile.gettempdir(), f"batch_{key}")
        quick = self.quick_check.isChecked()
        designer = self._get_designer()

        self.log_output.clear()
        self.log_output.append(f"Batch: {len(transpose_values)} transpositions "
                               f"({transpose_values[0]:+d} to {transpose_values[-1]:+d})")
        self.batch_run_btn.setEnabled(False)
        self.run_btn.setEnabled(False)
        self.progress_bar.show()

        self._batch_worker = BatchDesignWorker(
            designer, key, transpose_values, out_base, quick
        )
        self._batch_worker.progress.connect(lambda msg: self.log_output.append(msg))
        self._batch_worker.finished.connect(self._on_batch_done)
        self._batch_worker.start()

    def _on_batch_done(self, results):
        self.progress_bar.hide()
        self.batch_run_btn.setEnabled(self.batch_check.isChecked())
        self.run_btn.setEnabled(True)

        successes = sum(1 for _, r in results if r.success)
        failures = len(results) - successes
        self.log_output.append(f"\nBatch complete: {successes} OK, {failures} failed")

        header = f"  {'Transpose':>9}  {'Result':>8}  {'STLs':>6}  {'Config':>7}"
        self.log_output.append(header)
        self.log_output.append("  " + "-" * len(header))
        for transp, result in results:
            status = "OK" if result.success else "FAIL"
            n_stl = len(result.stl_files)
            has_yaml = "yes" if (result.config_yaml and os.path.exists(result.config_yaml)) else ""
            self.log_output.append(
                f"  {transp:+>+9d}  {status:>8}  {n_stl:>6}  {has_yaml:>7}"
            )

        last_success = None
        for transp, result in reversed(results):
            if result.success and result.config_yaml:
                last_success = (transp, result)
                break
        if last_success:
            _, last = last_success
            self._last_yaml = last.config_yaml
            self.send_to_sim_btn.setEnabled(True)
            self.send_to_fc_btn.setEnabled(True)
            self.edit_params_btn.setEnabled(True)
            self.log_output.append(f"\nLoaded last successful config: {last.config_yaml}")
            self.design_succeeded.emit(last.config_yaml)

    def _send_to_simulate(self):
        if self._last_yaml and os.path.exists(self._last_yaml):
            self.design_completed.emit(self._last_yaml, "simulate")

    def _send_to_freecad(self):
        if self._last_yaml and os.path.exists(self._last_yaml):
            self.design_completed.emit(self._last_yaml, "freecad")

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

    def get_state(self):
        key = self._current_preset_key()
        return key, self.transpose_spin.value(), self.quick_check.isChecked()

    def get_last_yaml(self) -> str:
        if self._last_yaml and os.path.exists(self._last_yaml):
            with open(self._last_yaml) as f:
                return f.read()
        return ""

    def _reset_ui(self):
        self.run_btn.setEnabled(HAVE_DEMAKEIN or self.remote_check.isChecked())
        self.cancel_btn.setEnabled(False)
        self.progress_bar.hide()
        self.edit_params_btn.setEnabled(False)
