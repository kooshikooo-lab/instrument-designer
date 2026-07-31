"""
Export routes: STEP, STL, SVG, CadQuery.
"""
import os
import uuid
import threading
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from ..shared_state import get_app, get_jobs, get_lock
from ..demakein_wrapper import DemakeinDesigner

router = APIRouter()

app = get_app()
_jobs = get_jobs()
_lock = get_lock()


class SvgExportRequest(BaseModel):
    preset: str
    transpose: int = 0


@router.get("/cadquery/instruments")
def list_cadquery_instruments():
    """List available CadQuery instrument presets."""
    designer = DemakeinDesigner()
    presets = {}
    for family in designer.list_families():
        for sub in designer.list_subcategories(family):
            for key in designer.list_presets(family, sub):
                presets[key] = {
                    "bore_length": 300,
                    "bore_diameter": 14,
                    "closed_top": False,
                    "holes": 6,
                }
    return presets


class CadQueryExportRequest(BaseModel):
    preset: str


@router.post("/cadquery")
def export_cadquery(req: CadQueryExportRequest):
    """Export instrument using CadQuery."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.cadquery_export import export_cadquery_instrument

    stl_bytes = export_cadquery_instrument(req.preset)
    return StreamingResponse(
        iter([stl_bytes]),
        media_type="application/sla",
        headers={"Content-Disposition": f"attachment; filename={req.preset}.stl"},
    )


@router.post("/export/svg")
def export_svg(req: SvgExportRequest):
    """Export instrument bore profile as SVG."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.svg_export import generate_bore_svg

    svg_bytes = generate_bore_svg(req.preset, req.transpose)
    return StreamingResponse(
        iter([svg_bytes]),
        media_type="image/svg+xml",
        headers={"Content-Disposition": f"attachment; filename={req.preset}.svg"},
    )