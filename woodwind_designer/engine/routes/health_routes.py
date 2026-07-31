"""
Health and presets routes.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ..demakein_wrapper import DemakeinDesigner

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health():
    from ..design_server import app
    return HealthResponse(status="ok", version=app.version)


@router.get("/presets")
def list_presets():
    designer = DemakeinDesigner()
    presets = {}
    for family in designer.list_families():
        for sub in designer.list_subcategories(family):
            for key in designer.list_presets(family, sub):
                presets[key] = designer.PRESET_DISPLAY_NAMES.get(key, key)
    return {"presets": presets}