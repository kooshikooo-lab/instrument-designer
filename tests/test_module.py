from backend.cadquery_export import generate_by_name, INSTRUMENTS
print(f"Module loaded. {len(INSTRUMENTS)} instruments available.")
print(f"Instruments: {list(INSTRUMENTS.keys())}")

r = generate_by_name("koncovka_C", "test_output/instruments")
print(f"\nKoncovka test:")
print(f"  STL: {r['stl_path']} ({r['stl_size_kb']} KB, {r['stl_time']}s)")
print(f"  STEP: {r['step_path']} ({r['step_size_kb']} KB, {r['step_time']}s)")
print("Module works.")
