"""List available instruments from cadquery_export library."""
from backend.cadquery_export import INSTRUMENTS

keys = sorted(INSTRUMENTS.keys())
print(f"Total instruments: {len(keys)}")

# Find interesting ones for optimization
# brass, non-traditional keys, etc.
interesting = []
for k, v in INSTRUMENTS.items():
    desc = v.get('desc', '')
    targets = v.get('targets', [])
    closed_top = v.get('closed_top', '?')
    n_targets = len(targets) if isinstance(targets, list) else 0
    f0 = targets[0] if targets else '?'
    has_tests = v.get('test_instrument', False)
    info = (k, desc, closed_top, n_targets, f0, has_tests)
    interesting.append(info)

# Sort by f0
interesting.sort(key=lambda x: float(x[4]) if isinstance(x[4], (int, float)) else 0)

print(f"\nInstruments sorted by fundamental frequency:")
for k, desc, ct, nt, f0, test in interesting[:20]:
    print(f"  {k:40s}  f0={f0:>8}Hz  closed_top={ct!s:5}  targets={nt}  test={test}")
print(f"  ...")
for k, desc, ct, nt, f0, test in interesting[-5:]:
    print(f"  {k:40s}  f0={f0:>8}Hz  closed_top={ct!s:5}  targets={nt}  test={test}")
