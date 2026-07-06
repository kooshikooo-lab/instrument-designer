import sys
import os
import io
import multiprocessing

# PyInstaller sets sys.stdout=None when console=False.
# demakein worker processes crash on sys.stdout.isatty() / sys.stdout.write().
# Set a valid StringIO before any multiprocessing pool is created,
# so spawned workers inherit a non-None stdout too.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.path.insert(0, os.path.dirname(__file__))
    from woodwind_designer.main import main
    main()
