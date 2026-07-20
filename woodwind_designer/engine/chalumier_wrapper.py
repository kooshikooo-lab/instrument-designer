"""
chalumier_wrapper.py — Interface to Chalumier (Kotlin instrument designer).

Chalumier performs acoustic optimization for woodwind instruments.
It's much faster than demakein (5 min vs 20 min for simple instruments,
10 min vs 3+ days for complex ones).

Chalumier is DESIGN-ONLY — it produces JSON parameters and SVG diagrams,
not STL files. For 3D model generation, combine with demakein's make phase
or use our own STL generation from bore profiles.

Prerequisites: JDK 17+ must be installed.
Build: gradlew.bat shadowJar (in chalumier/ directory)

Usage:
    from woodwind_designer.engine.chalumier_wrapper import ChalumierDesigner
    
    d = ChalumierDesigner()
    result = d.design("dwhistle.chal", output_dir="./output")
    print(result.svg_path)   # Visual design diagram
    print(result.json_path)  # Machine-readable parameters
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChalumierResult:
    output_dir: str
    svg_path: str = ""
    json_path: str = ""
    log: str = ""
    success: bool = False
    bore_profile: list = field(default_factory=list)
    hole_positions: list = field(default_factory=list)
    hole_diameters: list = field(default_factory=list)
    length: float = 0.0


class ChalumierDesigner:
    """Interface to the Chalumier instrument design tool."""

    # Available .chal files in our repo
    PRESET_FILES = {
        "d_whistle": "dwhistle.chal",
        "d_major_flute": "dmajor-folk-flute.chal",
        "e_minor_flute": "eminor-7hole-flute.chal",
        "recorder": "recorder.chal",
        "folk_shawm": "folkshawm.chal",
        "simple_shawm": "simple-shawm.chal",
    }

    PRESET_DISPLAY_NAMES = {
        "d_whistle": "D Pennywhistle",
        "d_major_flute": "D Major Folk Flute (7-hole)",
        "e_minor_flute": "E Minor Chromatic Flute",
        "recorder": "Recorder (8-hole)",
        "folk_shawm": "Folk Shawm",
        "simple_shawm": "Simple Shawm",
    }

    def __init__(self, chalumier_dir: Optional[str] = None):
        """
        Args:
            chalumier_dir: Path to chalumier repo root. If None, looks in
                          ../chalumier relative to this file.
        """
        if chalumier_dir is None:
            chalumier_dir = str(Path(__file__).parent.parent.parent / "chalumier")
        self.chalumier_dir = Path(chalumier_dir)
        self.examples_dir = self.chalumier_dir / "examples"
        self._jar_path = None

    def _find_jar(self) -> Optional[Path]:
        """Find the built chalumier JAR."""
        if self._jar_path and self._jar_path.exists():
            return self._jar_path
        build_dir = self.chalumier_dir / "app" / "build" / "libs"
        if build_dir.exists():
            for f in build_dir.glob("chalumier*.jar"):
                if "shadow" in f.name or "all" in f.name:
                    self._jar_path = f
                    return f
            for f in build_dir.glob("chalumier*.jar"):
                self._jar_path = f
                return f
        return None

    def is_available(self) -> bool:
        """Check if chalumier is built and JDK is available."""
        jar = self._find_jar()
        if jar is None:
            return False
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build(self) -> tuple[bool, str]:
        """Build chalumier from source. Returns (success, log)."""
        gradlew = self.chalumier_dir / "gradlew.bat"
        if not gradlew.exists():
            return False, f"gradlew.bat not found at {gradlew}"

        try:
            result = subprocess.run(
                [str(gradlew), "shadowJar"],
                cwd=str(self.chalumier_dir),
                capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                jar = self._find_jar()
                if jar:
                    return True, f"Build successful. JAR: {jar}"
                return False, "Build succeeded but JAR not found"
            return False, f"Build failed:\n{result.stderr[-2000:]}"
        except subprocess.TimeoutExpired:
            return False, "Build timed out after 10 minutes"

    def list_presets(self) -> dict[str, str]:
        """Return available preset names."""
        available = {}
        for key, filename in self.PRESET_FILES.items():
            chal_path = self.examples_dir / filename
            if chal_path.exists():
                available[key] = self.PRESET_DISPLAY_NAMES.get(key, key)
        return available

    def get_chal_content(self, preset_key: str) -> str:
        """Read a .chal file's content."""
        filename = self.PRESET_FILES.get(preset_key)
        if not filename:
            return ""
        chal_path = self.examples_dir / filename
        if chal_path.exists():
            return chal_path.read_text()
        return ""

    def design(self, chal_file: str, output_dir: Optional[str] = None,
               on_progress=None) -> ChalumierResult:
        """
        Run chalumier design on a .chal file.

        Args:
            chal_file: Path to .chal specification file, or a preset key
            output_dir: Where to write output files
            on_progress: Optional callback for progress messages

        Returns:
            ChalumierResult with paths to output files
        """
        jar = self._find_jar()
        if jar is None:
            return ChalumierResult(
                output_dir=output_dir or "",
                success=False,
                log="Chalumier JAR not found. Build with: gradlew.bat shadowJar"
            )

        # Resolve preset key to file path
        if chal_file in self.PRESET_FILES:
            chal_path = self.examples_dir / self.PRESET_FILES[chal_file]
        else:
            chal_path = Path(chal_file)

        if not chal_path.exists():
            return ChalumierResult(
                output_dir=output_dir or "",
                success=False,
                log=f"Chal file not found: {chal_path}"
            )

        if output_dir is None:
            output_dir = str(Path(tempfile.gettempdir()) / f"chalumier_{chal_path.stem}")
        os.makedirs(output_dir, exist_ok=True)

        if on_progress:
            on_progress(f"Running chalumier design: {chal_path.name}")

        try:
            result = subprocess.run(
                ["java", "-jar", str(jar), "design",
                 "--output-dir", output_dir, str(chal_path)],
                capture_output=True, text=True, timeout=600
            )

            log = result.stdout + "\n" + result.stderr

            # Find output files
            svg_files = list(Path(output_dir).glob("*.svg"))
            json_files = list(Path(output_dir).glob("*-parameters.json"))

            bore_profile = []
            hole_positions = []
            hole_diameters = []
            length = 0.0

            if json_files:
                try:
                    with open(json_files[0]) as f:
                        params = json.load(f)
                    # Extract bore profile if available
                    if "bore" in params:
                        bore_profile = params["bore"]
                    if "holes" in params:
                        hole_positions = [h.get("position", 0) for h in params["holes"]]
                        hole_diameters = [h.get("diameter", 0) for h in params["holes"]]
                    if "length" in params:
                        length = params["length"]
                except (json.JSONDecodeError, KeyError):
                    pass

            success = result.returncode == 0 and (svg_files or json_files)

            if on_progress:
                on_progress("Design complete." if success else "Design failed.")

            return ChalumierResult(
                output_dir=output_dir,
                svg_path=str(svg_files[0]) if svg_files else "",
                json_path=str(json_files[0]) if json_files else "",
                log=log.strip(),
                success=success,
                bore_profile=bore_profile,
                hole_positions=hole_positions,
                hole_diameters=hole_diameters,
                length=length,
            )

        except subprocess.TimeoutExpired:
            return ChalumierResult(
                output_dir=output_dir,
                success=False,
                log="Design timed out after 10 minutes"
            )
        except Exception as e:
            return ChalumierResult(
                output_dir=output_dir,
                success=False,
                log=f"Error: {e}"
            )
