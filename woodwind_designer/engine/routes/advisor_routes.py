"""
AI Advisor routes.
"""
import os
import threading
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..shared_state import get_app, get_jobs, get_lock

router = APIRouter()

app = get_app()
_jobs = get_jobs()
_lock = get_lock()


class AdvisorAnalyzeRequest(BaseModel):
    optimization_result: dict
    target_frequencies: list[float]


class AdvisorStoreRequest(BaseModel):
    name: str
    notes: str = ""
    optimization_result: dict
    target_frequencies: list[float]


@router.get("/status")
def advisor_status():
    return {"available": True, "provider": "llm"}


@router.post("/analyze")
def advisor_analyze(req: AdvisorAnalyzeRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.ai_advisor import analyze_optimization_result, get_llm_suggestion

    result = analyze_optimization_result(req.optimization_result, req.target_frequencies)
    suggestion = get_llm_suggestion(result)
    return {"analysis": result, "suggestion": suggestion}


@router.post("/analyze-sequential")
def advisor_analyze_sequential(req: AdvisorAnalyzeRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend.ai_advisor import analyze_sequential_result, sequential_result_for_llm, get_llm_suggestion

    result = analyze_sequential_result(req.optimization_result, req.target_frequencies)
    llm_input = sequential_result_for_llm(result)
    suggestion = get_llm_suggestion(llm_input)
    return {"analysis": result, "suggestion": suggestion}


@router.post("/store")
def advisor_store(req: AdvisorStoreRequest):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from woodwind_designer.engine.instrument_library import save_novel_instrument

    instrument = save_novel_instrument(
        name=req.name,
        notes=req.notes,
        optimization_result=req.optimization_result,
        target_frequencies=req.target_frequencies,
    )
    return {"saved": True, "instrument": instrument}


@router.get("/history")
def advisor_history():
    from woodwind_designer.engine.instrument_library import list_instruments
    return {"instruments": list_instruments()}