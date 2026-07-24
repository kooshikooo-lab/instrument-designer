import sys
sys.path.insert(0, '.')
from backend.cadquery_export import INSTRUMENTS
print(f'{len(INSTRUMENTS)} instruments loaded')
families = {}
for k, v in INSTRUMENTS.items():
    fam = v.get('_meta', {}).get('family', '?')
    families.setdefault(fam, []).append(k)
for f in sorted(families):
    names = families[f]
    print(f"  {f}: {len(names)} - {', '.join(names[:4])}{'...' if len(names)>4 else ''}")
