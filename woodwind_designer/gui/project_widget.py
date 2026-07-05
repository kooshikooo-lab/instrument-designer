import os
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QTextEdit, QSplitter,
    QLineEdit, QFormLayout, QMessageBox, QFileDialog, QDialog,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..engine.project import (
    Project, ProjectMeta, create_project, open_project,
    list_projects, PROJECT_EXT
)


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. My Folk Flute")
        layout.addRow("Project Name:", self.name_edit)

        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("e.g. Flute, Woodwind")
        layout.addRow("Instrument Type:", self.type_edit)

        self.preset_edit = QLineEdit()
        self.preset_edit.setPlaceholderText("e.g. folk_flute, reedpipe")
        layout.addRow("Preset:", self.preset_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("Optional description...")
        layout.addRow("Description:", self.desc_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_project_info(self):
        return {
            "name": self.name_edit.text().strip(),
            "type": self.type_edit.text().strip(),
            "preset": self.preset_edit.text().strip(),
            "desc": self.desc_edit.toPlainText().strip(),
        }


class ProjectWidget(QWidget):
    project_opened = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_project: Project | None = None
        self._workspace = str(Path.home() / "WoodwindProjects")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Project Manager")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #D4A76A; padding: 8px 0;")
        layout.addWidget(title)

        actions = QHBoxLayout()
        self.new_btn = QPushButton("New Project")
        self.new_btn.clicked.connect(self._new_project)
        actions.addWidget(self.new_btn)

        self.open_btn = QPushButton("Open Project")
        self.open_btn.clicked.connect(self._open_project)
        actions.addWidget(self.open_btn)

        self.save_btn = QPushButton("Save Project")
        self.save_btn.clicked.connect(self._save_project)
        self.save_btn.setEnabled(False)
        actions.addWidget(self.save_btn)

        self.set_workspace_btn = QPushButton("Set Workspace...")
        self.set_workspace_btn.clicked.connect(self._set_workspace)
        actions.addWidget(self.set_workspace_btn)

        actions.addStretch()
        layout.addLayout(actions)

        splitter = QSplitter(Qt.Horizontal)

        self.project_list = QListWidget()
        self.project_list.currentRowChanged.connect(self._on_project_selected)
        self.project_list.setStyleSheet(
            "QListWidget { background-color: #1e1e1e; border: 1px solid #4a4a4a; border-radius: 4px; }"
            "QListWidget::item { padding: 10px; border-bottom: 1px solid #333; color: #E8D5B7; }"
            "QListWidget::item:selected { background-color: #8B5E3C; color: #fff; }"
        )
        splitter.addWidget(self.project_list)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)

        self.proj_name = QLabel("No project selected")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.proj_name.setFont(name_font)
        self.proj_name.setStyleSheet("color: #E8D5B7;")
        detail_layout.addWidget(self.proj_name)

        self.proj_meta = QLabel("")
        self.proj_meta.setStyleSheet("color: #D4A76A;")
        detail_layout.addWidget(self.proj_meta)

        info_group = QGroupBox("Project Contents")
        info_layout = QVBoxLayout(info_group)
        self.models_label = QLabel("Models: -")
        info_layout.addWidget(self.models_label)
        self.simulations_label = QLabel("Simulations: -")
        info_layout.addWidget(self.simulations_label)
        self.config_label = QLabel("Config: -")
        info_layout.addWidget(self.config_label)
        detail_layout.addWidget(info_group)

        self.open_folder_btn = QPushButton("Open Project Folder")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        detail_layout.addWidget(self.open_folder_btn)

        detail_layout.addStretch()
        splitter.addWidget(detail)
        splitter.setSizes([250, 550])

        layout.addWidget(splitter, stretch=1)

        self._refresh_list()

    def _refresh_list(self):
        self.project_list.blockSignals(True)
        self.project_list.clear()
        Path(self._workspace).mkdir(parents=True, exist_ok=True)
        projects = list_projects(self._workspace)
        for proj in projects:
            item = QListWidgetItem(f"{proj.name}")
            item.setData(Qt.UserRole, str(proj.path))
            self.project_list.addItem(item)
        self.project_list.blockSignals(False)

    def _on_project_selected(self, row):
        if row < 0:
            self._current_project = None
            self.proj_name.setText("No project selected")
            self.proj_meta.setText("")
            self.models_label.setText("Models: -")
            self.simulations_label.setText("Simulations: -")
            self.config_label.setText("Config: -")
            self.open_folder_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            return

        item = self.project_list.item(row)
        if not item:
            return

        try:
            proj = Project(item.data(Qt.UserRole))
            proj.load()
            self._current_project = proj

            self.proj_name.setText(proj.meta.name)
            created = proj.meta.created[:10] if proj.meta.created else "?"
            modified = proj.meta.modified[:10] if proj.meta.modified else "?"
            self.proj_meta.setText(
                f"{proj.meta.instrument_type or '-'}  |  "
                f"Preset: {proj.meta.preset or '-'}  |  "
                f"Transpose: {proj.meta.transpose}"
            )

            models = proj.list_models()
            sims = list(proj.simulations_dir.iterdir()) if proj.simulations_dir.exists() else []
            has_config = proj.config_path.exists()

            self.models_label.setText(f"Models: {len(models)} file(s)")
            self.simulations_label.setText(f"Simulations: {len(sims)} file(s)")
            self.config_label.setText(f"Config: {'Yes' if has_config else 'No'}")
            self.open_folder_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

            self.project_opened.emit(proj.meta.preset or "")

        except Exception as e:
            self._current_project = None
            self.proj_name.setText("Error loading project")
            self.proj_meta.setText(str(e))

    def _new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            info = dialog.get_project_info()
            if not info["name"]:
                QMessageBox.warning(self, "Error", "Project name is required.")
                return
            try:
                proj = create_project(
                    base_dir=self._workspace,
                    name=info["name"],
                    instrument_type=info["type"],
                    preset=info["preset"],
                )
                if info["desc"]:
                    proj.meta.description = info["desc"]
                    proj.save()
                self._refresh_list()
                QMessageBox.information(
                    self, "Project Created",
                    f"Project '{info['name']}' created at:\n{proj.path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project: {e}")

    def _open_project(self):
        path = QFileDialog.getExistingDirectory(
            self, "Open Project Folder", self._workspace
        )
        if path:
            self._workspace = str(Path(path).parent)
            self._refresh_list()

    def _save_project(self):
        if self._current_project:
            self._current_project.save()
            QMessageBox.information(self, "Saved", "Project saved.")

    def _set_workspace(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Workspace Folder", self._workspace
        )
        if path:
            self._workspace = path
            self._refresh_list()

    def _open_folder(self):
        if self._current_project and self._current_project.path.exists():
            os.startfile(str(self._current_project.path))
