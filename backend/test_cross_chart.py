"""Test: ChatGPT's cross-fingering chart for 12-hole chromatic."""
import sys, time
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

N_FREE = 12
N_FIXED = 1

# Chart from ChatGPT (13 notes x 13 holes)
# Format: [H1, H2, H3, H4, H5, H6, H7, H8, H9, H10, H11, H12, R]
chart = [
    # D  (all closed)
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    # D# (cross: H7+H9 open, H8 closed between)
    [0,0,0,0,0,0,1,0,1,0,0,0,0],
    # E  (H7 only)
    [0,0,0,0,0,0,1,0,0,0,0,0,0],
    # F  (H6+H7)
    [0,0,0,0,0,1,1,0,0,0,0,0,0],
    # F# (cross: H5+H7+H8+H9, H6 closed)
    [0,0,0,0,1,0,1,1,0,0,0,0,0],
    # G  (H5+H6+H7)
    [0,0,0,0,1,1,1,0,0,0,0,0,0],
    # G# (cross: H4+H6+H7+H8, H5 closed)
    [0,0,0,1,0,1,1,1,0,0,0,0,0],
    # A  (H4+H5+H6+H7)
    [0,0,0,1,1,1,1,0,0,0,0,0,0],
    # Bb (cross: H3+H5+H6+H7+H8, H4 closed)
    [0,0,1,0,1,1,1,1,0,0,0,0,0],
    # B  (H3+H4+H5+H6+H7)
    [0,0,1,1,1,1,1,0,0,0,0,0,0],
    # C  (cross: H2+H4+H5+H6+H7+H8+H11, H3 closed, H11 vent)
    [0,1,0,1,1,1,1,1,0,0,1,0,0],
    # C# (cross: H1+H3+H4+H5+H6+H7+H9+H12, H2 closed, H12 vent)
    [1,0,1,1,1,1,1,0,1,0,0,1,0],
    # D  (H1-H7 open, sequential)
    [1,1,1,1,1,1,1,0,0,0,0,0,0],
]
chart_str = [["open" if c else "closed" for c in row] for row in chart]

print("=== ChatGPT Cross-Fingering Chart ===")
for i, (name, row) in enumerate(zip(names, chart_str)):
    pat = "".join("O" if s=="open" else "X" for s in row[:12])
    print(f"  {name}: {pat}  R={'O' if row[12]=='open' else 'X'}")

print("\n=== Two-register optimization ===")
t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart_str,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.15, 1.0),
)

hole_positions = [88, 176, 234, 293, 338, 392, 445, 488, 532, 571, 610, 636]
result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=False, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
positions = result['free_hole_positions']
print(f"Holes: {[f'{p:.0f}' for p in positions]}")
