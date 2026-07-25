# Entry point for pyinstaller - runs the FastAPI server
import uvicorn
from woodwind_designer.engine.design_server import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")