import sys
import os

# Run the test script from the current repo (path-portable, unlike the old
# hardcoded desktop path that this file previously referenced).
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, BACKEND_DIR)

script = os.path.join(BACKEND_DIR, "test_full_2reg.py")
if not os.path.exists(script):
    raise SystemExit(f"run_test.py: {script} not found (historical script removed)")

exec(open(script).read())
