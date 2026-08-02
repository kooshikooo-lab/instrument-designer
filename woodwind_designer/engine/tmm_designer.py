"""
tmm_designer.py — Primary instrument designer using our TMM optimizer.
==========================================================================

Part of the Instrument Designer project. This replaces demakein_wrapper.py
with our own TMM-based optimizer.

Architecture
------------
Our TMM engine (backend/tmm_acoustics.py) provides:
  - Instrument parameterization (from cadquery_export.py)
  - Two-phase optimizer (DE + L-BFGS-B) from two_phase_optimizer.py
  - Acoustic scoring (resonance quality)
  - JAX autodiff for gradient-based refinement

This module wraps our TMM with:
  - A clean async-friendly API (TMMDesigner.design())
  - stdout/stderr interception for progress reporting in the GUI
  - YAML config export for manufacturing
  - CadQuery-based STL/STEP generation (replaces broken Maker pipeline)

Usage
-----
    from woodwind_designer.engine.tmm_designer import TMMDesigner

    d = TMMDesigner(output_base="designs")
    result = d.design("folk_flute", transpose=0, quick=True,
                      on_progress=lambda msg: print(msg))
    if result.success:
        print(f"YAML config: {result.config_yaml}")
"""

import os
import sys
import io
import re
import math
import time
import yaml
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# Import our backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.cadquery_export import (
    generate_variable_bore_instrument, export_stl, export_step,
    INSTRUMENTS as CAD_INSTRUMENTS,
)
from backend.two_phase_optimizer import two_phase_optimize


@dataclass
class DesignResult:
    output_dir: str
    ident: str
    stl_files: list = field(default_factory=list)
    config_yaml: str = ""
    log: str = ""
    success: bool = False


class TMMDesigner:
    """Instrument designer using our TMM optimizer instead of demakein."""
    
    # Available presets from cadquery_export.py
    PRESET_KEYS = list(CAD_INSTRUMENTS.keys())
    
    # Human-readable display names
    PRESET_DISPLAY_NAMES = {
        k: v.get("_meta", {}).get("display_name", k) for k, v in CAD_INSTRUMENTS.items()
    }
    
    PRESET_DESCRIPTIONS = {
        k: v.get("_meta", {}).get("description", "") for k, v in CAD_INSTRUMENTS.items()
    }
    
    # Category mapping
    PRESET_CATEGORIES = {}
    for k, v in CAD_INSTRUMENTS.items():
        cat = v.get("_meta", {}).get("family", "Unknown")
        sub = v.get("_meta", {}).get("subcategory", "Unknown")
        if cat not in PRESET_CATEGORIES:
            PRESET_CATEGORIES[cat] = {}
        PRESET_CATEGORIES[cat][sub] = PRESET_CATEGORIES[cat].get(sub, []) + [k]

    def __init__(self, output_base: str = "designs"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)

    def list_families(self) -> list[str]:
        return list(self.PRESET_CATEGORIES.keys())

    def list_subcategories(self, family: str) -> list[str]:
        return list(self.PRESET_CATEGORIES.get(family, {}).keys())

    def list_presets(self, family: str, subcategory: str) -> list[str]:
        return self.PRESET_CATEGORIES.get(family, {}).get(subcategory, [])

    def find_preset_category(self, preset: str) -> tuple[str, str]:
        for family, subs in self.PRESET_CATEGORIES.items():
            for sub, presets in subs.items():
                if preset in presets:
                    return family, sub
        return ("", "")

    def get_description(self, preset: str) -> str:
        return self.PRESET_DESCRIPTIONS.get(preset, "")

    def design(self, preset: str, transpose: int = 0, output_dir: Optional[str] = None,
               on_progress=None, quick: bool = False,
               optimizer_strategy: str = "accurate",
               optimizer_enable_timbre: bool = False,
               optimizer_max_time: int = 60,
               optimizer_target_accuracy: float = 3.0) -> DesignResult:
        """Design an instrument using our TMM optimizer."""
        
        if preset not in self.PRESET_KEYS:
            return DesignResult(
                output_dir=output_dir or "",
                ident="",
                success=False,
                log=f"Unknown preset '{preset}'. Available: {', '.join(self.PRESET_KEYS)}"
            )

        instrument_config = CAD_INSTRUMENTS[preset]
        
        design_dir = output_dir or str(self.output_base / f"{preset}_design")
        os.makedirs(design_dir, exist_ok=True)

        # Progress reporting setup
        _orig_stdout = sys.stdout or io.StringIO()
        _orig_stderr = sys.stderr or io.StringIO()
        _ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\W')

        class _ProgressStream:
            _recursing = False
            def __init__(self, stream, callback):
                self.stream = stream or io.StringIO()
                self.callback = callback
                self.buf = ""
            def isatty(self): return False
            def fileno(self): raise OSError()
            def _extract(self, raw): return _ANSI_RE.sub('', raw).strip()
            def write(self, text):
                self.stream.write(text)
                if self._recursing: return
                self.buf += text
                if "\r" in self.buf:
                    line = self._extract(self.buf.rsplit("\r", 1)[-1])
                    if line and self.callback:
                        _ProgressStream._recursing = True
                        try:
                            _orig_stdout.write(f"[progress] {line}\n")
                            _orig_stdout.flush()
                            self.callback(line)
                        finally:
                            _ProgressStream._recursing = False
                    self.buf = self.buf[self.buf.rfind("\r") + 1:]
                if "\n" in self.buf:
                    lines = self.buf.split("\n")
                    for line in lines[:-1]:
                        line = self._extract(line)
                        if line and self.callback:
                            _ProgressStream._recursing = True
                            try:
                                _orig_stdout.write(f"[progress] {line}\n")
                                _orig_stdout.flush()
                                self.callback(line)
                            finally:
                                _ProgressStream._recursing = False
                        self.buf = lines[-1]
            def flush(self):
                try: self.stream.flush()
                except (OSError, AttributeError): pass

        sys.stdout = _ProgressStream(sys.stdout, on_progress)
        sys.stderr = _ProgressStream(sys.stderr, on_progress)

        t0 = time.time()
        try:
            if on_progress:
                mode = "Quick Draft" if quick else "Full optimization"
                on_progress(f"{mode} in progress (may take several minutes)...")

            # Get instrument configuration
            config = CAD_INSTRUMENTS[preset]
            meta = config.get("_meta", {})
            
            # Build bore profile from config
            bore_profile = config.get("bore_profile", [])
            if not bore_profile:
                # Build from bore_length and bore_diameter
                bore_length = config.get("bore_length", 300)
                bore_diameter = config.get("bore_diameter", 15)
                bore_profile = [
                    (0, bore_diameter / 2),
                    (bore_length, bore_diameter / 2)
                ]
            
            holes = config.get("holes", [])
            wall_thickness = config.get("wall_thickness", 3.0)
            closed_top = config.get("closed_top", False)
            
            # Run optimization if not quick mode
            if not quick:
                if on_progress:
                    on_progress("Running TMM optimization...")
                
                # Prepare targets from config
                targets = config.get("targets", [])
                fingerings = config.get("fingerings", [])
                
                if targets:
                    # Run our two-phase optimizer
                    from backend.two_phase_optimizer import two_phase_optimize
                    
                    result = two_phase_optimize(
                        bore_profile=bore_profile,
                        targets=targets,
                        fingerings=fingerings,
                        closed_top=config.get("closed_top", False),
                        wall_thickness=wall_thickness,
                        outer_diameter=config.get("outer_diameter", 22.0),
                        max_time=optimizer_max_time,
                        target_accuracy=optimizer_target_accuracy,
                    )
                    
                    if result.get("success"):
                        # Update bore profile with optimized result
                        bore_profile = result.get("bore_profile", bore_profile)
                        holes = result.get("holes", holes)
                        if on_progress:
                            on_progress(f"Optimization complete: {result.get('rms_cents', 0):.2f}c RMS")
            
            if on_progress:
                on_progress("Generating 3D model (STL)...")

            # Generate STL/STEP using CadQuery
            stl_files = []
            config_yaml = ""
            
            try:
                # Build bore profile for CadQuery
                bore_profile_cq = []
                if isinstance(bore_profile[0], (list, tuple)):
                    bore_profile_cq = bore_profile
                else:
                    # Convert from [r1, r2, ...] to [(pos, radius), ...]
                    if len(bore_profile) > 1:
                        n = len(bore_profile)
                        bore_length = config.get("bore_length", 300)
                        positions = [i * config.get("bore_length", 300) / (n - 1) for i in range(n)]
                        bore_profile = [(positions[i], bore_profile[i]) for i in range(n)]
                        bore_profile_cq = bore_profile

                solid = generate_variable_bore_instrument(
                    bore_profile=bore_profile_cq,
                    wall_thickness=config.get("wall_thickness", 3.0),
                    bore_length=config.get("bore_length", 300),
                    holes=config.get("holes", []),
                    closed_top=config.get("closed_top", False),
                )

                stl_path = os.path.join(design_dir, f"{preset}.stl")
                export_stl(solid, stl_path)
                stl_files = [stl_path]

                step_path = os.path.join(design_dir, f"{preset}.step")
                export_step(solid, step_path)

                # Generate YAML config
                n_samples = 64
                positions = [inst.length * i / (n_samples - 1) for i in range(n_samples)]
                bore_profile_yaml = [[round(p, 4), round(inst.inner(p) / 2.0, 4)] for p in positions]
                
                tone_holes = [
                    {"position": round(p, 4), "radius": round(d / 2.0, 4),
                     "chimney_height": round(h, 4)}
                    for p, d, h in zip(config.get("hole_positions", []), config.get("hole_diameters", []), config.get("hole_lengths", []))
                ]

                yaml_cfg = {
                    "bore_length": round(inst.length, 4),
                    "bore_length_unit": "mm",
                    "bore_profile": bore_profile_yaml,
                    "tone_holes": tone_holes,
                }
                yaml_path = os.path.join(design_dir, f"{preset}_config.yaml")
                with open(yaml_path, "w") as _yh:
                    yaml.dump(yaml_cfg, _yh, default_flow_style=None)
                config_yaml = yaml_path

            except Exception as e:
                traceback.print_exc()
                pass

            return DesignResult(
                output_dir=design_dir,
                ident=preset,
                stl_files=[str(f) for f in stl_files],
                config_yaml=config_yaml,
                success=True,
                log=f"Design '{preset}' completed. {len(stl_files)} STL files."
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
            sys.stdout = _orig_stdout
            sys.stderr = _orig_stderr


# Module-level constants and exports
HAVE_TMM = True  # Replaces HAVE_DEMAKEIN constant

# Export the main classes and constants
__all__ = ["TMMDesigner", "DesignResult", "HAVE_TMM"]