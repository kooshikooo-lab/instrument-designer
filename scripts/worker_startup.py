"""
Worker plugin to install the instrument-designer package on each worker.
"""
import os
import subprocess
import sys

def install_package():
    """Install the instrument-designer package in development mode."""
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", 
            root, "--quiet"
        ], check=True, capture_output=True)
        return "Package installed successfully"
    except subprocess.CalledProcessError as e:
        return f"Failed to install package: {e}"

# Install on worker startup
result = install_package()
print(f"Worker startup: {result}")