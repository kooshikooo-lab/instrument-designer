import subprocess
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
script = os.path.join(BACKEND_DIR, "run_test.py")

result = subprocess.run(
    [sys.executable, script],
    capture_output=True,
    text=True,
    timeout=600,
    cwd=BACKEND_DIR,
)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Return code:", result.returncode)
