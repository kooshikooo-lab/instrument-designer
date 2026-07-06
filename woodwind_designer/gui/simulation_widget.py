import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTextEdit, QFileDialog, QProgressBar, QLabel, QFormLayout,
    QDoubleSpinBox, QSpinBox, QSplitter
)
from PySide6.QtCore import QThread, Signal, Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from ..engine.openwind_wrapper import OpenWindSimulator, HAVE_OPENWIND, SimulationResult
from ..engine.sound_synthesizer import generate_from_peaks


class SimulationWorker(QThread):
    finished = Signal(object)
    progress = Signal(str)

    def __init__(self, simulator, yaml_path, output_dir, f_min, f_max, n_points):
        super().__init__()
        self.sim = simulator
        self.yaml_path = yaml_path
        self.output_dir = output_dir
        self.f_min = f_min
        self.f_max = f_max
        self.n_points = n_points

    def run(self):
        self.progress.emit("Running OpenWInD simulation...")
        result = self.sim.simulate_from_yaml(
            self.yaml_path, self.output_dir,
            self.f_min, self.f_max, self.n_points
        )
        self.progress.emit("Simulation complete." if result.success else "Simulation failed.")
        self.finished.emit(result)


class SimulationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.simulator = OpenWindSimulator()
        self._worker = None
        self._last_result = None
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.7)
        self._player.mediaStatusChanged.connect(self._on_play_status)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()

        config_group = QGroupBox("YAML Configuration")
        config_layout = QFormLayout(config_group)

        yaml_row = QHBoxLayout()
        self.yaml_path_label = QLabel("(none selected)")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_yaml)
        yaml_row.addWidget(self.yaml_path_label, stretch=1)
        yaml_row.addWidget(self.browse_btn)
        config_layout.addRow("Config File:", yaml_row)

        self.f_min_spin = QDoubleSpinBox()
        self.f_min_spin.setRange(10, 1000)
        self.f_min_spin.setValue(20)
        self.f_min_spin.setSuffix(" Hz")
        config_layout.addRow("Min Frequency:", self.f_min_spin)

        self.f_max_spin = QDoubleSpinBox()
        self.f_max_spin.setRange(100, 10000)
        self.f_max_spin.setValue(3000)
        self.f_max_spin.setSuffix(" Hz")
        config_layout.addRow("Max Frequency:", self.f_max_spin)

        self.n_points_spin = QSpinBox()
        self.n_points_spin.setRange(500, 10000)
        self.n_points_spin.setValue(2000)
        self.n_points_spin.setStepType(QSpinBox.AdaptiveDecimalStepType)
        config_layout.addRow("Frequency Points:", self.n_points_spin)

        top_row.addWidget(config_group, stretch=1)

        actions = QVBoxLayout()
        self.run_btn = QPushButton("Run Simulation")
        self.run_btn.clicked.connect(self._run_simulation)
        self.run_btn.setEnabled(HAVE_OPENWIND)
        actions.addWidget(self.run_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        actions.addWidget(self.cancel_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        actions.addWidget(self.progress_bar)

        self.save_plot_btn = QPushButton("Save Plot...")
        self.save_plot_btn.clicked.connect(self._save_plot)
        self.save_plot_btn.setEnabled(False)
        actions.addWidget(self.save_plot_btn)

        self.save_data_btn = QPushButton("Save Data (CSV)...")
        self.save_data_btn.clicked.connect(self._save_data)
        self.save_data_btn.setEnabled(False)
        actions.addWidget(self.save_data_btn)

        self.play_sound_btn = QPushButton("Play Sound")
        self.play_sound_btn.clicked.connect(self._play_sound)
        self.play_sound_btn.setEnabled(False)
        actions.addWidget(self.play_sound_btn)

        actions.addStretch()
        top_row.addLayout(actions)

        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Vertical)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        splitter.addWidget(self.log_output)

        self.plot_label = QLabel("Run a simulation to see the impedance plot")
        self.plot_label.setAlignment(Qt.AlignCenter)
        self.plot_label.setMinimumHeight(300)
        self.plot_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        splitter.addWidget(self.plot_label)

        splitter.setSizes([200, 400])
        layout.addWidget(splitter, stretch=1)

    def load_yaml(self, yaml_path: str):
        if os.path.exists(yaml_path):
            self.yaml_path_label.setText(yaml_path)
            self.log_output.append(f"Loaded config: {yaml_path}")
        else:
            self.log_output.append(f"Config not found: {yaml_path}")

    def _browse_yaml(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select YAML Config",
            "", "YAML files (*.yaml *.yml);;All files (*.*)"
        )
        if path:
            self.yaml_path_label.setText(path)

    def _run_simulation(self):
        yaml_path = self.yaml_path_label.text()
        if not yaml_path or yaml_path == "(none selected)" or not os.path.exists(yaml_path):
            self.log_output.append("✗ Please select a valid YAML config file first.")
            return

        out_dir = os.path.join(
            os.path.dirname(yaml_path),
            "simulation_" + Path(yaml_path).stem
        )

        self.log_output.clear()
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.show()

        self._worker = SimulationWorker(
            self.simulator, yaml_path, out_dir,
            self.f_min_spin.value(), self.f_max_spin.value(),
            self.n_points_spin.value()
        )
        self._worker.progress.connect(lambda msg: self.log_output.append(msg))
        self._worker.finished.connect(self._on_sim_done)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self.log_output.append("Simulation cancelled.")
        self._reset_ui()

    def _on_sim_done(self, result):
        self._reset_ui()
        self._last_result = result if result.success else None
        self.save_plot_btn.setEnabled(result.success and bool(result.plot_path))
        self.save_data_btn.setEnabled(result.success)
        self.play_sound_btn.setEnabled(result.success and bool(result.peak_freqs))
        if result.success:
            self.log_output.append(f"✓ {result.log}")
            if result.peak_freqs:
                self.log_output.append("\nResonance Peaks:")
                for i, (freq, note) in enumerate(zip(result.peak_freqs, result.peak_notes), 1):
                    self.log_output.append(f"  {i:2d}. {freq:8.1f} Hz → {note}")
            else:
                self.log_output.append("\nNo significant resonance peaks found.")
            if result.plot_path and os.path.exists(result.plot_path):
                pixmap = QPixmap(result.plot_path)
                if not pixmap.isNull():
                    w = max(1, self.plot_label.width() - 20)
                    scaled = pixmap.scaledToWidth(w)
                    self.plot_label.setPixmap(scaled)
                    self.plot_label.setText("")
                else:
                    self.plot_label.setText(f"Plot saved: {result.plot_path}")
        else:
            self.log_output.append(f"✗ {result.log}")

    def _save_plot(self):
        if not self._last_result or not self._last_result.plot_path:
            return
        dst, _ = QFileDialog.getSaveFileName(
            self, "Save Impedance Plot",
            os.path.join(os.path.expanduser("~"), "impedance_plot.png"),
            "PNG Images (*.png);;All files (*.*)"
        )
        if dst:
            import shutil
            shutil.copy2(self._last_result.plot_path, dst)
            self.log_output.append(f"Plot saved: {dst}")

    def _save_data(self):
        if not self._last_result:
            return
        dst, _ = QFileDialog.getSaveFileName(
            self, "Save Simulation Data",
            os.path.join(os.path.expanduser("~"), "simulation_data.csv"),
            "CSV files (*.csv);;All files (*.*)"
        )
        if dst:
            freqs = self._last_result.frequencies
            impedances = self._last_result.impedance
            with open(dst, "w") as f:
                f.write("frequency_hz,impedance_magnitude\n")
                for f_val, z_val in zip(freqs, impedances):
                    f.write(f"{f_val},{abs(z_val)}\n")
            self.log_output.append(f"Data saved: {dst}")

    def _play_sound(self):
        if not self._last_result or not self._last_result.peak_freqs:
            return
        path = generate_from_peaks(self._last_result.peak_freqs)
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self.play_sound_btn.setText("Playing...")
        self.play_sound_btn.setEnabled(False)

    def _on_play_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.play_sound_btn.setText("Play Sound")
            self.play_sound_btn.setEnabled(True)

    def _reset_ui(self):
        self.run_btn.setEnabled(HAVE_OPENWIND)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.hide()
