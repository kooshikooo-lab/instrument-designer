import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


FREECAD_CMD = r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe"
BACKEND_SCRIPT = Path(__file__).parent / "freecad_backend.py"


@dataclass
class FreeCADResult:
    files: list = field(default_factory=list)
    bore_length: float = 0.0
    n_holes: int = 0
    log: str = ""
    success: bool = False


def is_available() -> bool:
    return os.path.exists(FREECAD_CMD)


def generate_instrument(
    output_dir: str,
    bore_segments: list,
    tone_holes: list,
    export_stl: bool = True,
    export_step: bool = False,
    export_fcstd: bool = False,
) -> FreeCADResult:
    if not os.path.exists(FREECAD_CMD):
        return FreeCADResult(
            log=f"FreeCAD not found at {FREECAD_CMD}. Install FreeCAD 1.1 first.",
            success=False
        )
    if not BACKEND_SCRIPT.exists():
        return FreeCADResult(
            log=f"Backend script not found at {BACKEND_SCRIPT}",
            success=False
        )

    params = {
        "output_path": output_dir,
        "bore_segments": bore_segments,
        "tone_holes": tone_holes,
        "export_stl": export_stl,
        "export_step": export_step,
        "export_fcstd": export_fcstd,
    }

    os.makedirs(output_dir, exist_ok=True)

    try:
        env = os.environ.copy()
        env["FC_PARAMS"] = json.dumps(params)

        proc = subprocess.run(
            [FREECAD_CMD, str(BACKEND_SCRIPT)],
            capture_output=True, text=True, timeout=120, env=env,
        )

        if proc.returncode != 0:
            return FreeCADResult(
                log=f"FreeCAD process failed (code {proc.returncode}):\n{proc.stderr}",
                success=False
            )

        stdout_text = proc.stdout.strip()
        first_line = stdout_text.split("\n")[0] if stdout_text else ""
        result = json.loads(first_line)
        return FreeCADResult(
            files=result.get("files", []),
            bore_length=result.get("bore_length", 0),
            n_holes=result.get("n_holes", 0),
            log=f"FreeCAD generated {len(result.get('files', []))} file(s)",
            success=True
        )

    except subprocess.TimeoutExpired:
        return FreeCADResult(log="FreeCAD process timed out (120s)", success=False)
    except json.JSONDecodeError as e:
        return FreeCADResult(
            log=f"Failed to parse FreeCAD output: {e}\nstdout: {proc.stdout[:500]}",
            success=False
        )
    except Exception as e:
        import traceback
        return FreeCADResult(
            log=f"FreeCAD error: {e}\n{traceback.format_exc()}",
            success=False
        )


def bore_from_yaml(yaml_path: str) -> tuple:
    """Extract bore segments and tone holes from a YAML config file."""
    import yaml
    with open(yaml_path, "r") as f:
        cfg = yaml.safe_load(f)
    bore = cfg.get("bore_profile", [])
    holes = cfg.get("tone_holes", [])
    return bore, holes
