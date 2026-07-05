import sys, glob, os

fc_bin = r"C:\Program Files\FreeCAD 1.1\bin"
fc_lib = os.path.join(fc_bin, "..", "lib")

sys.path.insert(0, fc_bin)
sys.path.insert(0, fc_lib)

# Find FreeCAD .pyd files
for root, dirs, files in os.walk(fc_lib):
    for f in files:
        if "FreeCAD" in f and f.endswith(".pyd"):
            print(os.path.join(root, f))

# Try importing
try:
    import FreeCAD
    print("FreeCAD imported OK")
    print(FreeCAD.Version)
except Exception as e:
    print(f"Import failed: {e}")
