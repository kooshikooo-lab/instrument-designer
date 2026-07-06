import os
import json
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from demakein import (
        Design_reedpipe, Design_folk_flute, Design_folk_shawm,
        Design_folk_whistle, Design_recorder, Design_dorian_whistle,
        Design_pflute, Design_reed_drone, Design_shawm,
        Design_three_hole_whistle,
    )
    from demakein.design import Instrument_designer
    HAVE_DEMAKEIN = True
except ImportError:
    HAVE_DEMAKEIN = False


@dataclass
class DesignResult:
    output_dir: str
    ident: str
    stl_files: list = field(default_factory=list)
    config_yaml: str = ""
    log: str = ""
    success: bool = False


class DemakeinDesigner:
    CATEGORIES = {
        "Wind": {
            "Woodwind": {
                "reedpipe": Design_reedpipe if HAVE_DEMAKEIN else None,
                "folk_shawm": Design_folk_shawm if HAVE_DEMAKEIN else None,
                "shawm": Design_shawm if HAVE_DEMAKEIN else None,
                "reed_drone": Design_reed_drone if HAVE_DEMAKEIN else None,
            },
            "Flute": {
                "folk_flute": Design_folk_flute if HAVE_DEMAKEIN else None,
                "folk_whistle": Design_folk_whistle if HAVE_DEMAKEIN else None,
                "recorder": Design_recorder if HAVE_DEMAKEIN else None,
                "dorian_whistle": Design_dorian_whistle if HAVE_DEMAKEIN else None,
                "pflute": Design_pflute if HAVE_DEMAKEIN else None,
                "three_hole_whistle": Design_three_hole_whistle if HAVE_DEMAKEIN else None,
            },
        },
    }

    PRESET_DISPLAY_NAMES = {
        "reedpipe": "Reedpipe",
        "folk_shawm": "Folk Shawm",
        "shawm": "Shawm",
        "reed_drone": "Reed Drone",
        "folk_flute": "Folk Flute",
        "folk_whistle": "Penny Whistle (Tin Whistle)",
        "recorder": "Soprano Recorder",
        "dorian_whistle": "Dorian Whistle",
        "pflute": "Pan Flute",
        "three_hole_whistle": "Three-Hole Whistle (Tabor Pipe)",
    }

    PRESET_DESCRIPTIONS = {
        "reedpipe": "Simple single-reed pipe (like a clarinet practice chanter)",
        "folk_shawm": "Compact double-reed folk shawm",
        "shawm": "Full double-reed shawm",
        "reed_drone": "Continuous-sounding reed drone pipe",
        "folk_flute": "Pennywhistle-style folk flute, 6 holes",
        "folk_whistle": "Tin whistle with pennywhistle fingering",
        "recorder": "Recorder with full fingering system",
        "dorian_whistle": "Whistle tuned to the Dorian mode",
        "pflute": "Pan flute with multiple pipes",
        "three_hole_whistle": "Medieval three-hole tabor pipe",
    }

    def __init__(self, output_base: str = "designs"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)
        self._current_designer: Optional[Instrument_designer] = None

    def list_families(self) -> list[str]:
        return list(self.CATEGORIES.keys())

    def list_subcategories(self, family: str) -> list[str]:
        subs = self.CATEGORIES.get(family, {})
        return list(subs.keys())

    def list_presets(self, family: str, subcategory: str) -> list[str]:
        subs = self.CATEGORIES.get(family, {})
        presets = subs.get(subcategory, {})
        return [k for k, v in presets.items() if v is not None]

    def find_preset_category(self, preset: str) -> tuple[str, str]:
        for family, subs in self.CATEGORIES.items():
            for sub, presets in subs.items():
                if preset in presets:
                    return family, sub
        return ("", "")

    def get_description(self, preset: str) -> str:
        return self.PRESET_DESCRIPTIONS.get(preset, "")

    _ORIG_IMPROVE = None

    def _patch_optimize(self, quick: bool):
        import demakein.optimize as _opt
        if self._ORIG_IMPROVE is None:
            self._ORIG_IMPROVE = _opt.improve
        if quick:
            pool = 1; ftol_val = 0.5; acc = 0.05; xtol_val = 1e-3
        else:
            pool = 3; ftol_val = 5e-4; acc = 0.002; xtol_val = 1e-6
        def _patched_improve(comment, constrainer, scorer, start_x, **kw):
            kw["workers"] = 1
            kw["pool_factor"] = pool
            kw["ftol"] = ftol_val
            kw["initial_accuracy"] = acc
            kw["xtol"] = xtol_val
            return self._ORIG_IMPROVE(comment, constrainer, scorer, start_x, **kw)
        _opt.improve = _patched_improve

    def design(self, preset: str, transpose: int = 0, output_dir: Optional[str] = None,
               on_progress=None, quick: bool = False) -> DesignResult:
        if not HAVE_DEMAKEIN:
            return DesignResult(
                output_dir=output_dir or "",
                ident="",
                success=False,
                log="Demakein library not installed. Run: pip install demakein"
            )

        cls = None
        for subs in self.CATEGORIES.values():
            for presets in subs.values():
                if preset in presets:
                    cls = presets[preset]
                    break
        if cls is None:
            return DesignResult(
                output_dir="",
                ident="",
                success=False,
                log=f"Unknown preset '{preset}'"
            )

        design_dir = output_dir or str(self.output_base / f"{preset}_design")
        os.makedirs(design_dir, exist_ok=True)

        designer = cls(output_dir=design_dir, transpose=transpose)
        self._current_designer = designer

        self._patch_optimize(quick)
        if quick:
            os.environ["DEMAKEIN_DRAFT"] = "1"

        import sys as _sys
        import io as _io

        _orig_stdout = _sys.stdout or _io.StringIO()

        class _ProgressStream:
            _recursing = False

            def __init__(self, stream, callback):
                self.stream = stream or _io.StringIO()
                self.callback = callback
                self.buf = ""

            def write(self, text):
                self.stream.write(text)
                if self._recursing:
                    return
                self.buf += text
                if "\r" in self.buf:
                    line = self.buf.rsplit("\r", 1)[-1]
                    stripped = line.strip()
                    if stripped and self.callback:
                        _ProgressStream._recursing = True
                        try:
                            _orig_stdout.write(f"[progress] {stripped}\n")
                            _orig_stdout.flush()
                            self.callback(stripped)
                        finally:
                            _ProgressStream._recursing = False
                if "\n" in self.buf:
                    lines = self.buf.split("\n")
                    for line in lines[:-1]:
                        stripped = line.strip()
                        if stripped and self.callback:
                            _ProgressStream._recursing = True
                            try:
                                _orig_stdout.write(f"[progress] {stripped}\n")
                                _orig_stdout.flush()
                                self.callback(stripped)
                            finally:
                                _ProgressStream._recursing = False
                    self.buf = lines[-1]

            def flush(self):
                try:
                    self.stream.flush()
                except (OSError, AttributeError):
                    pass

            def __getattr__(self, name):
                return getattr(self.stream, name)

        _sys.stdout = _ProgressStream(_sys.stdout, on_progress)

        try:
            if on_progress:
                mode = "Quick Draft" if quick else "Full optimization"
                on_progress(f"{mode} in progress (may take several minutes)...")
            designer.run()
            if on_progress:
                on_progress("Optimization complete — generating 3D model...")
            designer.process_make()
            stl_files = sorted(Path(design_dir).rglob("*.stl"))

            config_yaml = ""
            try:
                sf = getattr(designer, 'state_filename', None)
                if sf and os.path.exists(sf):
                    with open(sf) as _fh:
                        state_vec = json.load(_fh)
                    inst = designer.unpack(state_vec)
                    if inst is not None:
                        import yaml as _yaml
                        _n = 60
                        _positions = [inst.length * i / (_n - 1) for i in range(_n)]
                        bore_profile = [[round(p, 4), round(inst.inner(p) / 2.0, 4)] for p in _positions]
                        tone_holes = [
                            {"position": round(p, 4), "radius": round(d / 2.0, 4),
                             "chimney_height": round(h, 4)}
                            for p, d, h in zip(inst.hole_positions, inst.hole_diameters, inst.hole_lengths)
                        ]
                        yaml_cfg = {
                            "bore_length": round(inst.length / 1000.0, 4),
                            "bore_profile": bore_profile,
                            "tone_holes": tone_holes,
                        }
                        yaml_path = os.path.join(design_dir, f"{preset}_config.yaml")
                        with open(yaml_path, "w") as _yh:
                            _yaml.dump(yaml_cfg, _yh, default_flow_style=None)
                        config_yaml = yaml_path
            except Exception:
                pass

            return DesignResult(
                output_dir=design_dir,
                ident=designer.ident(),
                stl_files=[str(f) for f in stl_files],
                config_yaml=config_yaml,
                success=True,
                log=f"Design '{designer.ident()}' completed. {len(stl_files)} STL files."
            )
        except Exception as e:
            import traceback
            return DesignResult(
                output_dir=design_dir,
                ident="",
                success=False,
                log=f"Design failed: {e}\n{traceback.format_exc()}"
            )
        finally:
            _sys.stdout = _orig_stdout
