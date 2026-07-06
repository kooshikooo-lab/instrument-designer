import os
import yaml
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QGroupBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt


class ParameterEditor(QDialog):
    def __init__(self, yaml_path: str, parent=None):
        super().__init__(parent)
        self.yaml_path = yaml_path
        self.setWindowTitle("Edit Instrument Parameters")
        self.setMinimumSize(700, 500)
        self._config = self._load_yaml()
        self._setup_ui()

    def _load_yaml(self):
        with open(self.yaml_path, "r") as f:
            return yaml.safe_load(f) or {}

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(f"File: {self.yaml_path}")
        info.setStyleSheet("color: #D4A76A; padding: 4px 0;")
        layout.addWidget(info)

        tabs = QTabWidget()

        bore_tab = QWidget()
        bore_layout = QVBoxLayout(bore_tab)
        bore_label = QLabel("Bore Profile — each row is a point along the bore center-line")
        bore_label.setStyleSheet("color: #C0B0A0;")
        bore_layout.addWidget(bore_label)

        self.bore_table = QTableWidget()
        self.bore_table.setColumnCount(2)
        self.bore_table.setHorizontalHeaderLabels(["Position (mm)", "Radius (mm)"])
        self.bore_table.horizontalHeader().setStretchLastSection(True)
        bore_profile = self._config.get("bore_profile", [])
        self.bore_table.setRowCount(len(bore_profile))
        for i, (pos, rad) in enumerate(bore_profile):
            self.bore_table.setItem(i, 0, QTableWidgetItem(f"{pos:.3f}"))
            self.bore_table.setItem(i, 1, QTableWidgetItem(f"{rad:.3f}"))
        bore_layout.addWidget(self.bore_table)
        tabs.addTab(bore_tab, "Bore Profile")

        holes_tab = QWidget()
        holes_layout = QVBoxLayout(holes_tab)
        holes_label = QLabel("Tone Holes — position, radius, and chimney height")
        holes_label.setStyleSheet("color: #C0B0A0;")
        holes_layout.addWidget(holes_label)

        self.holes_table = QTableWidget()
        self.holes_table.setColumnCount(3)
        self.holes_table.setHorizontalHeaderLabels(
            ["Position (mm)", "Radius (mm)", "Chimney Height (mm)"]
        )
        self.holes_table.horizontalHeader().setStretchLastSection(True)
        tone_holes = self._config.get("tone_holes", [])
        self.holes_table.setRowCount(len(tone_holes))
        for i, h in enumerate(tone_holes):
            self.holes_table.setItem(i, 0, QTableWidgetItem(f"{h.get('position', 0):.3f}"))
            self.holes_table.setItem(i, 1, QTableWidgetItem(f"{h.get('radius', 0):.3f}"))
            self.holes_table.setItem(i, 2, QTableWidgetItem(f"{h.get('chimney_height', 0):.3f}"))
        holes_layout.addWidget(self.holes_table)
        tabs.addTab(holes_tab, "Tone Holes")

        layout.addWidget(tabs, stretch=1)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save & Update YAML")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        btn_row.addStretch()

        len_group = QGroupBox("Bore Length")
        len_layout = QHBoxLayout(len_group)
        self.length_label = QLabel(f"{self._config.get('bore_length', 0):.3f} m")
        self.length_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E8D5B7;")
        len_layout.addWidget(self.length_label)
        len_layout.addStretch()
        btn_row.addWidget(len_group)

        layout.addLayout(btn_row)

    def _save(self):
        bore_profile = []
        for row in range(self.bore_table.rowCount()):
            pos_item = self.bore_table.item(row, 0)
            rad_item = self.bore_table.item(row, 1)
            if pos_item and rad_item:
                try:
                    pos = float(pos_item.text())
                    rad = float(rad_item.text())
                    bore_profile.append([pos, rad])
                except ValueError:
                    continue

        tone_holes = []
        for row in range(self.holes_table.rowCount()):
            pos_item = self.holes_table.item(row, 0)
            rad_item = self.holes_table.item(row, 1)
            ch_item = self.holes_table.item(row, 2)
            if pos_item and rad_item:
                try:
                    pos = float(pos_item.text())
                    rad = float(rad_item.text())
                    ch = float(ch_item.text()) if ch_item and ch_item.text() else 8.0
                    tone_holes.append({
                        "position": pos, "radius": rad,
                        "chimney_height": ch
                    })
                except ValueError:
                    continue

        bore_length = self._config.get("bore_length", 0)
        if bore_profile and len(bore_profile) >= 2:
            bore_length = bore_profile[-1][0] - bore_profile[0][0]

        self._config["bore_profile"] = bore_profile
        self._config["tone_holes"] = tone_holes
        self._config["bore_length"] = bore_length

        with open(self.yaml_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

        QMessageBox.information(self, "Saved",
                                f"Updated YAML config with {len(bore_profile)} bore points "
                                f"and {len(tone_holes)} tone holes.\n"
                                f"Bore length: {bore_length:.1f} mm")
        self.accept()
