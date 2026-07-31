"""
Routes package for Instrument Designer Server.
"""
from . import health_routes
from . import design_routes
from . import optimize_routes
from . import cad_routes
from . import advisor_routes
from . import export_routes
from . import bore_routes
from . import auto_design_routes

__all__ = [
    "health_routes",
    "design_routes",
    "optimize_routes",
    "cad_routes",
    "advisor_routes",
    "export_routes",
    "bore_routes",
    "auto_design_routes",
]