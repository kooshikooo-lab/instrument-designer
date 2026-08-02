# compare_bench.py
"""
Compare two benchmark summary outputs produced by scripts/bench_tmm_micro.py.

Usage:
    python scripts/compare_bench.py baseline.txt new.txt

If the input file contains extra log lines, the script will extract the JSON
block printed after the line "Summary:" and parse that.
"""
import json
import sys


def load_summary(path):
    with open(path, 'r') as f:
        txt = f.read()
    if "Summary:" in txt:
        j = txt.split("Summary:\n",1)[1].strip()
    else:
        j = txt.strip()
    return json.loads(j)


if len(sys.argv) < 3:
    print("Usage: python scripts/compare_bench.py baseline.txt new.txt")
    sys.exit(1)

base = load_summary(sys.argv[1])
new = load_summary(sys.argv[2])

for key in ("find_resonance_mean", "resonance_phase_mean"):
    if key in base and key in new:
        b = base[key]
        n = new[key]
        change = 100.0 * (b - n) / b if b != 0 else 0.0
        print(f"{key}: baseline={b:.6f}s new={n:.6f}s improvement={change:.2f}%")
    else:
        print(f"{key} missing in files")
