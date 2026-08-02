import subprocess
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
TARGET = os.path.join(BACKEND_DIR, "run_test.py")
if not os.path.exists(TARGET):
    raise FileNotFoundError(f"{TARGET} does not exist on this branch")

result = subprocess.run(["python", TARGET], capture_output=True, text=True, timeout=600, cwd=BACKEND_DIR)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Return code:", result.returncode)
