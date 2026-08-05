#!/usr/bin/env python3
"""
Dask worker startup script with project path configured.
"""
import sys
import os

# Add project root to path BEFORE any other imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Verify imports work
try:
    import backend
    import backend.bore_optimizer_lbfgs
    import backend.tmm_acoustics
    import backend.timbre_objectives
    print(f"[worker] Imports OK from {PROJECT_ROOT}")
except ImportError as e:
    print(f"[worker] Import failed: {e}")
    sys.exit(1)

# Now start the Dask worker
from distributed.cli.dask_worker import main

if __name__ == "__main__":
    main()