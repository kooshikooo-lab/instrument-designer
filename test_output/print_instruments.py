import json
data = json.load(open('test_output/instruments_list.json'))
print(f"{len(data)} instruments loaded\n")
families = {}
for i in data:
    fam = i.get('family', '?')
    families.setdefault(fam, []).append(i)
for f in sorted(families):
    items = families[f]
    print(f"  {f}: {len(items)} instruments")
    for i in sorted(items, key=lambda x: x['display_name']):
        v = "✓" if i.get('verified') else " "
        print(f"    [{v}] {i['display_name']} ({i['bore_length_mm']}mm)")
