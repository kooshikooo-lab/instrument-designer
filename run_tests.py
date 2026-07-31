import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("1. Running pytest on tests/ directory")
print("=" * 80)
result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], 
                       capture_output=True, text=True, timeout=300)
print(result.stdout[-10000:] if len(result.stdout) > 10000 else result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-5000:] if len(result.stderr) > 5000 else result.stderr)
print(f"Return code: {result.returncode}")

print("\n" + "=" * 80)
print("2. Running benchmark_all.py --no-dask --instruments chalumeau_C")
print("=" * 80)
result = subprocess.run([sys.executable, "backend/benchmark_all.py", "--no-dask", "--instruments", "chalumeau_C"], 
                       capture_output=True, text=True, timeout=300)
print(result.stdout[-10000:] if len(result.stdout) > 10000 else result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-5000:] if len(result.stderr) > 5000 else result.stderr)
print(f"Return code: {result.returncode}")

print("\n" + "=" * 80)
print("3. Running dask_benchmark.py --help")
print("=" * 80)
result = subprocess.run([sys.executable, "scripts/dask_benchmark.py", "--help"], 
                       capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Return code: {result.returncode}")

print("\n" + "=" * 80)
print("4. Checking design_server.py imports cleanly")
print("=" * 80)
result = subprocess.run([sys.executable, "-c", "from woodwind_designer.engine.design_server import app; print('OK')"], 
                       capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Return code: {result.returncode}")

print("\n" + "=" * 80)
print("5. Verify API endpoints match web/src/utils/api.ts")
print("=" * 80)
result = subprocess.run([sys.executable, "-c", "import json; import sys; spec = __import__('woodwind_designer.engine.design_server', fromlist=['app']).app; print(json.dumps([{'path': r.path, 'methods': list(r.methods)} for r in spec.routes if hasattr(r, 'methods')], indent=2))"], 
                       capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Return code: {result.returncode}")