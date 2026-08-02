"""Guard the public HTTP endpoint surface of the design server.

Asserts that kept endpoints are registered and that dead surfaces
(/optimize/tmm, /optimize/sequential) are no longer exposed.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _route_map(app):
    routes = {}
    for r in app.routes:
        if hasattr(r, "methods"):
            for m in r.methods:
                routes.setdefault(r.path, set()).add(m)
    return routes


def _paths(app):
    return {r.path for r in app.routes if hasattr(r, "methods")}


def test_design_server_imports():
    import woodwind_designer.engine.design_server  # noqa: F401


def test_core_design_endpoints_present():
    from woodwind_designer.engine.design_server import app

    paths = _paths(app)
    for p in ["/design", "/design/{job_id}/status", "/design/{job_id}/download", "/health", "/presets"]:
        assert p in paths, f"missing endpoint {p}"


def test_optimization_endpoints_present():
    from woodwind_designer.engine.design_server import app

    paths = _paths(app)
    for p in [
        "/optimize/start",
        "/optimize/{job_id}/status",
        "/optimize/evaluate",
        "/optimize/presets",
        "/optimize/cache/size",
        "/optimize/cache/clear",
        "/optimize/cache/stats",
    ]:
        assert p in paths, f"missing endpoint {p}"


def test_dead_optimization_endpoints_removed():
    from woodwind_designer.engine.design_server import app

    paths = _paths(app)
    for p in ["/optimize/tmm", "/optimize/tmm/{job_id}/status", "/optimize/sequential",
              "/optimize/sequential/{job_id}/status", "/optimize/sequential/{job_id}/stl",
              "/optimize/sequential/{job_id}/profile"]:
        assert p not in paths, f"dead endpoint still registered: {p}"


def test_export_endpoints_present():
    from woodwind_designer.engine.design_server import app

    paths = _paths(app)
    for p in ["/export/step", "/export/svg", "/export/cadquery", "/export/cadquery/instruments"]:
        assert p in paths, f"missing endpoint {p}"


def test_optimizer_backend_importable():
    """The lazy import used by /optimize/start and /optimize/evaluate must resolve."""
    from backend.optimizer import BoreOptimizer

    assert BoreOptimizer is not None
