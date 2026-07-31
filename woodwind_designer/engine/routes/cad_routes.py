"""
CAD export and STL routes.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

router = APIRouter()


class CadQueryExportRequest(BaseModel):
    preset: str
    length: float = 300.0
    bore_diameter: float = 14.0
    wall_thickness: float = 3.0
    segments: int = 32


class StepExportParams(BaseModel):
    bore_profile: list[list[float]]
    wall_thickness: float = 3.0
    tone_holes: Optional[list[dict]] = None


class VariableStlRequest(BaseModel):
    bore_profile: list[list[float]]
    wall_thickness: float = 3.0
    holes: list[list[float]] = []
    closed_top: bool = False


class BoreGenerateRequest(BaseModel):
    bore_type: str
    params: dict
    length_mm: float = 300.0
    n_points: int = 200


@router.post("/export/cadquery")
def export_cadquery(req: CadQueryExportRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.cadquery_export import generate_instrument, export_stl

    try:
        import tempfile
        solid = generate_instrument(
            bore_length=req.length,
            bore_diameter=req.bore_diameter,
            wall_thickness=req.wall_thickness,
        )
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
            export_stl(solid, tmp.name)
            with open(tmp.name, "rb") as f:
                stl_bytes = f.read()
            os.unlink(tmp.name)
        return StreamingResponse(
            iter([stl_bytes]),
            media_type="application/sla",
            headers={"Content-Disposition": f"attachment; filename={req.preset}.stl"},
        )
    except Exception as e:
        raise HTTPException(500, f"CAD export failed: {e}")


@router.post("/export/step")
def export_step(req: StepExportParams):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.cadquery_export import generate_step

    try:
        step_bytes = generate_step(
            bore_profile=req.bore_profile,
            wall_thickness=req.wall_thickness,
            tone_holes=req.tone_holes,
        )
        return StreamingResponse(
            iter([step_bytes]),
            media_type="application/step",
            headers={"Content-Disposition": "attachment; filename=bore.step"},
        )
    except Exception as e:
        raise HTTPException(500, f"STEP export failed: {e}")


@router.post("/bore/export/variable-stl")
def export_variable_stl(req: VariableStlRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.cadquery_export import generate_variable_bore_instrument, export_stl

    try:
        import tempfile
        solid = generate_variable_bore_instrument(
            bore_profile=[(p[0], p[1]) for p in req.bore_profile],
            wall_thickness=req.wall_thickness,
            holes=[(h[0], h[1]) for h in req.holes],
            closed_top=req.closed_top,
        )
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
            export_stl(solid, tmp.name)
            with open(tmp.name, "rb") as f:
                stl_bytes = f.read()
            os.unlink(tmp.name)
        return StreamingResponse(
            iter([stl_bytes]),
            media_type="application/sla",
            headers={"Content-Disposition": "attachment; filename=variable_bore.stl"},
        )
    except Exception as e:
        raise HTTPException(500, f"Variable STL export failed: {e}")


@router.get("/bore/optimized-stls")
def list_optimized_stls():
    output_dir = Path(os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_output", "unconventional"))
    if not output_dir.exists():
        return {"files": []}
    files = []
    for f in output_dir.glob("*.stl"):
        stat = f.stat()
        files.append({
            "name": f.name,
            "size_bytes": stat.st_size,
            "url": f"/bore/optimized-stls/{f.name}",
        })
    return {"files": files}


@router.get("/bore/optimized-stls/{filename}")
def get_optimized_stl(filename: str):
    output_dir = Path(os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_output", "unconventional"))
    file_path = output_dir / filename
    if not file_path.exists() or not file_path.suffix == ".stl":
        raise HTTPException(404, "STL not found")
    return FileResponse(
        file_path,
        media_type="application/sla",
        filename=filename,
    )


@router.post("/bore/generate")
def generate_bore(req: BoreGenerateRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.physics.bore_generators import generate_bore_profile

    try:
        profile = generate_bore_profile(
            bore_type=req.bore_type,
            length_mm=req.length_mm,
            n_points=req.n_points,
            **req.params,
        )
        return {"profile": profile}
    except Exception as e:
        raise HTTPException(500, f"Bore generation failed: {e}")


@router.get("/bore-types")
def list_bore_types():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.physics.bore_generators import BORE_TYPE_META
    return BORE_TYPE_META