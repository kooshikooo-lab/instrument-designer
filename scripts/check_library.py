"""Check INSTRUMENTS dict structure."""
from backend.cadquery_export import INSTRUMENTS

# Check keys of first few entries
for name in list(INSTRUMENTS.keys())[:3]:
    v = INSTRUMENTS[name]
    print(f"\n{name}:")
    for k, val in v.items():
        if isinstance(val, (list, dict)):
            print(f"  {k}: {type(val).__name__} len={len(val)}")
        else:
            print(f"  {k}: {val!r}")
