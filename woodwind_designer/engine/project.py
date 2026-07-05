"""
Project system for Woodwind and Flute Designer.
A project is a folder (*.wfp directory) containing:
  - project.json        (metadata + parameters)
  - config.yaml         (instrument YAML config)
  - models/             (STL, STEP, FCStd files)
  - simulations/        (simulation results + plots)
"""

import os
import json
import shutil
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


PROJECT_EXT = ".wfp"


@dataclass
class ProjectMeta:
    name: str
    version: str = "1.0"
    created: str = ""
    modified: str = ""
    instrument_type: str = ""
    preset: str = ""
    transpose: int = 0
    description: str = ""

    def __post_init__(self):
        now = datetime.datetime.now().isoformat()
        if not self.created:
            self.created = now
        self.modified = now


class Project:
    def __init__(self, path: str):
        self.path = Path(path)
        self.meta: Optional[ProjectMeta] = None
        self._config_yaml: str = ""

    @property
    def name(self) -> str:
        return self.path.stem if self.path.suffix == PROJECT_EXT else self.path.name

    @property
    def exists(self) -> bool:
        return self.path.exists() and (self.path / "project.json").exists()

    @property
    def models_dir(self) -> Path:
        return self.path / "models"

    @property
    def simulations_dir(self) -> Path:
        return self.path / "simulations"

    @property
    def config_path(self) -> Path:
        return self.path / "config.yaml"

    @property
    def meta_path(self) -> Path:
        return self.path / "project.json"

    def create(self, meta: ProjectMeta, config_yaml: str = "") -> "Project":
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "models").mkdir(exist_ok=True)
        (self.path / "simulations").mkdir(exist_ok=True)
        self.meta = meta
        self._config_yaml = config_yaml
        self._save_meta()
        if config_yaml:
            self.config_path.write_text(config_yaml, encoding="utf-8")
        return self

    def load(self) -> "Project":
        if not self.exists:
            raise FileNotFoundError(f"Project not found: {self.path}")
        with open(self.meta_path, "r") as f:
            self.meta = ProjectMeta(**json.load(f))
        if self.config_path.exists():
            self._config_yaml = self.config_path.read_text(encoding="utf-8")
        return self

    def save(self):
        if self.meta:
            self.meta.modified = datetime.datetime.now().isoformat()
            self._save_meta()
        if self._config_yaml:
            old = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else ""
            if old != self._config_yaml:
                self.config_path.write_text(self._config_yaml, encoding="utf-8")

    def _save_meta(self):
        with open(self.meta_path, "w") as f:
            json.dump(asdict(self.meta), f, indent=2)

    def add_model(self, src_path: str) -> str:
        src = Path(src_path)
        if not src.exists():
            return ""
        dest = self.models_dir / src.name
        shutil.copy2(str(src), str(dest))
        return str(dest)

    def add_simulation(self, src_dir: str) -> list[str]:
        src = Path(src_dir)
        if not src.exists():
            return []
        copied = []
        for f in src.iterdir():
            if f.is_file():
                dest = self.simulations_dir / f.name
                shutil.copy2(str(f), str(dest))
                copied.append(str(dest))
        return copied

    def list_models(self) -> list[Path]:
        if not self.models_dir.exists():
            return []
        return sorted(self.models_dir.iterdir())

    def get_config_yaml(self) -> str:
        return self._config_yaml

    def set_config_yaml(self, yaml_str: str):
        self._config_yaml = yaml_str
        if self.path.exists():
            self.config_path.write_text(yaml_str, encoding="utf-8")


def create_project(base_dir: str, name: str, preset: str = "",
                   instrument_type: str = "", transpose: int = 0,
                   config_yaml: str = "") -> Project:
    meta = ProjectMeta(
        name=name,
        instrument_type=instrument_type,
        preset=preset,
        transpose=transpose,
    )
    proj_dir = Path(base_dir) / (name + PROJECT_EXT)
    project = Project(str(proj_dir))
    project.create(meta, config_yaml)
    return project


def open_project(path: str) -> Project:
    p = Path(path)
    if p.suffix != PROJECT_EXT:
        p = p / (p.name + PROJECT_EXT)
    project = Project(str(p))
    project.load()
    return project


def list_projects(directory: str) -> list[Project]:
    projects = []
    for item in Path(directory).iterdir():
        if item.is_dir() and item.suffix == PROJECT_EXT:
            try:
                proj = Project(str(item))
                proj.load()
                projects.append(proj)
            except Exception:
                pass
    return projects
