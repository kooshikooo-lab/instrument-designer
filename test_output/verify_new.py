import sys
sys.path.insert(0, '.')
from backend.cadquery_export import INSTRUMENTS
print(f'Total instruments: {len(INSTRUMENTS)}')
families = {}
for k, v in INSTRUMENTS.items():
    fam = v.get('_meta', {}).get('family', '?')
    families[fam] = families.get(fam, 0) + 1
for f, c in sorted(families.items()):
    print(f'  {f}: {c}')
new_keys = ['contra_alto_clarinet_Eb', 'contra_bass_clarinet_Bb', 'octo_contra_alto_clarinet_EEb', 
            'octo_contra_bass_clarinet_BBB', 'printgear3d_bass_clarinet', 
            'selmer_mark_vi_baritone', 'selmer_mark_vi_baritone_lowA', 
            'yamaha_ybs62_baritone', 'selmer_serie_iii_baritone',
            'printgear3d_baritone_sax']
for k in new_keys:
    if k in INSTRUMENTS:
        print(f'  OK {k}: {INSTRUMENTS[k]["_meta"]["display_name"]}')
    else:
        print(f'  MISSING: {k}')