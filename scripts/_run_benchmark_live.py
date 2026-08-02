"""Run benchmark_dask.py against the live cluster address (runner to avoid shell mangling)."""
import os, sys

os.environ["JAX_ENABLE_X64"] = "1"

src = open(os.path.join("backend", "benchmark_dask.py"), encoding="utf-8").read()
patched = src.replace("tcp://100.69.113.41:8786", "tcp://100.100.66.117:8786")
open(os.path.join("backend", "_benchmark_dask_live.py"), "w", encoding="utf-8").write(patched)

import runpy
runpy.run_path(os.path.join("backend", "_benchmark_dask_live.py"), run_name="__main__")
