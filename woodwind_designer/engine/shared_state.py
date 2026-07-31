"""
Shared state for the Instrument Designer Server.
"""
import threading

# Global app instance - will be set by design_server.py
app = None

# Background job state
_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def set_app(application):
    """Set the FastAPI app instance."""
    global app
    app = application


def get_app():
    """Get the FastAPI app instance."""
    return app


def get_jobs():
    """Get the jobs dict."""
    return _jobs


def get_lock():
    """Get the lock."""
    return _lock