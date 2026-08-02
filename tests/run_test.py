import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)

TARGET = os.path.join(BACKEND_DIR, "test_full_2reg.py")
if not os.path.exists(TARGET):
    raise FileNotFoundError(f"{TARGET} does not exist on this branch")

exec(open(TARGET).read())
