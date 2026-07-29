"""
Comprehensive multi-instrument optimization using all available methods.

Methods:
  1. pareto_sweep (weighted-sum multi-objective, n_weights=8)
  2. refine_sequential w_int=1.0 (intonation-only baseline)
  3. refine_sequential w_int=0.5 (balanced intonation+timbre)
  4. two_phase_optimizer (Noreland DE -> L-BFGS-B) where applicable

Parallelized with Dask across instruments.
"""
import json, os, sys, time, math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

OUT_DIR = PROJECT_ROOT / "test_output" / "instruments"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_FILE = PROJECT_ROOT / "test_output" / "comprehensive_results.json"

# ---------------------------------------------------------------------------
# Instrument configs - diverse set including brass, non-traditional keys
# ---------------------------------------------------------------------------

def _freq(name):
    """Approximate frequency for a note name."""
    notes = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
    n = name.rstrip('0123456789')
    o = int(name[len(n):]) if name[len(n):] else 4
    if n in notes:
        return 440.0 * 2**((notes[n] - 9 + (o-4)*12) / 12.0)
    return 440.0

INSTRUMENTS_CFG = {
    # === BRASS (open-open, stub holes) ===
    "tenor_trombone_Bb": {
        "desc": "Tenor Trombone in Bb (open-open brass)",
        "closed_top": False, "bore_radius": 10.5, "outer_diameter": 52.0,
        "hole_diameter": 5.0, "hole_length": 1.0,
        "targets": [58.27, 61.74, 65.41, 73.42, 82.41, 87.31, 98.00, 110.00, 116.54, 130.81],
        "fingerings": [["closed"]*2]*10, "n_registers": [2]*10,
    },
    "f_horn_F": {
        "desc": "F Horn in F (conical brass, non-regular key)",
        "closed_top": False, "bore_radius": 12.0, "outer_diameter": 60.0,
        "hole_diameter": 5.5, "hole_length": 1.0,
        "targets": [87.31, 98.00, 110.00, 116.54, 130.81, 146.83, 155.56, 174.61, 196.00, 220.00],
        "fingerings": [["closed"]*2]*10, "n_registers": [2]*10,
    },
    "trumpet_Bb": {
        "desc": "Bb Trumpet (open-open brass)",
        "closed_top": False, "bore_radius": 6.5, "outer_diameter": 32.0,
        "hole_diameter": 3.0, "hole_length": 0.8,
        "targets": [233.08, 277.18, 311.13, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25],
        "fingerings": [["closed"]*2]*10, "n_registers": [2]*10,
    },
    "alto_trombone_Eb": {
        "desc": "Alto Trombone in Eb (open-open brass, non-regular key)",
        "closed_top": False, "bore_radius": 8.5, "outer_diameter": 42.0,
        "hole_diameter": 4.0, "hole_length": 1.0,
        "targets": [155.56, 174.61, 196.00, 220.00, 246.94, 277.18, 311.13, 349.23],
        "fingerings": [["closed"]*2]*8, "n_registers": [2]*8,
    },
    "flugelhorn_Bb": {
        "desc": "Flugelhorn in Bb (open-open brass, non-regular key)",
        "closed_top": False, "bore_radius": 7.5, "outer_diameter": 38.0,
        "hole_diameter": 3.5, "hole_length": 0.8,
        "targets": [233.08, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 466.16, 523.25, 587.33],
        "fingerings": [["closed"]*2]*10, "n_registers": [2]*10,
    },

    # === SAXOPHONES (open-open, conical) ===
    "soprano_sax_Bb": {
        "desc": "Soprano Saxophone in Bb (open-open, conical)",
        "closed_top": False, "bore_radius": 6.5, "outer_diameter": 28.0,
        "hole_diameter": 5.5, "hole_length": 2.0,
        "targets": [233.08, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 622.25, 659.25],
        "fingerings": [
            ["closed"]*20, ["open"]+["closed"]*19,
            ["closed","open"]+["closed"]*18, ["closed"]*2+["open"]+["closed"]*17,
            ["closed"]*3+["open"]+["closed"]*16, ["closed"]*4+["open"]+["closed"]*15,
            ["closed"]*5+["open"]+["closed"]*14, ["closed"]*6+["open"]+["closed"]*13,
            ["closed"]*7+["open"]+["closed"]*12, ["closed"]*8+["open"]+["closed"]*11,
            ["closed"]*9+["open"]+["closed"]*10, ["closed"]*10+["open"]+["closed"]*9,
            ["closed"]*11+["open"]+["closed"]*8,
        ],
        "n_registers": [2]*13,
    },
    "alto_sax_Eb": {
        "desc": "Alto Saxophone in Eb (open-open, conical)",
        "closed_top": False, "bore_radius": 8.5, "outer_diameter": 34.0,
        "hole_diameter": 6.5, "hole_length": 2.5,
        "targets": [311.1, 349.2, 392.0, 440.0, 493.9, 554.4, 587.3, 622.3, 659.3, 698.5, 784.0, 880.0],
        "fingerings": [
            ["closed"]*23, ["open"]+["closed"]*22,
            ["closed","open"]+["closed"]*21, ["closed"]*2+["open"]+["closed"]*19,
            ["closed"]*3+["open"]+["closed"]*18, ["closed"]*4+["open"]+["closed"]*17,
            ["closed"]*5+["open"]+["closed"]*16, ["closed"]*6+["open"]+["closed"]*15,
            ["closed"]*7+["open"]+["closed"]*14, ["closed"]*8+["open"]+["closed"]*13,
            ["closed"]*9+["open"]+["closed"]*12, ["closed"]*10+["open"]+["closed"]*11,
        ],
        "n_registers": [2]*12,
    },
    "baritone_sax_Bb": {
        "desc": "Baritone Saxophone in Bb (open-open, conical)",
        "closed_top": False, "bore_radius": 12.0, "outer_diameter": 70.0,
        "hole_diameter": 9.0, "hole_length": 3.5,
        "targets": [61.74, 65.41, 73.42, 82.41, 87.31, 98.00, 110.00, 116.54, 130.81, 146.83, 155.56, 164.81],
        "fingerings": [
            ["closed"]*23, ["open"]+["closed"]*22,
            ["closed","open"]+["closed"]*21, ["closed"]*2+["open"]+["closed"]*19,
            ["closed"]*3+["open"]+["closed"]*18, ["closed"]*4+["open"]+["closed"]*17,
            ["closed"]*5+["open"]+["closed"]*16, ["closed"]*6+["open"]+["closed"]*15,
            ["closed"]*7+["open"]+["closed"]*14, ["closed"]*8+["open"]+["closed"]*13,
            ["closed"]*9+["open"]+["closed"]*12, ["closed"]*10+["open"]+["closed"]*11,
        ],
        "n_registers": [2]*12,
    },
    "tenor_sax_Bb": {
        "desc": "Tenor Saxophone in Bb (open-open, conical)",
        "closed_top": False, "bore_radius": 10.0, "outer_diameter": 50.0,
        "hole_diameter": 7.5, "hole_length": 3.0,
        "targets": [103.83, 110.00, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00],
        "fingerings": [
            ["closed"]*22, ["open"]+["closed"]*21,
            ["closed","open"]+["closed"]*20, ["closed"]*2+["open"]+["closed"]*19,
            ["closed"]*3+["open"]+["closed"]*18, ["closed"]*4+["open"]+["closed"]*17,
            ["closed"]*5+["open"]+["closed"]*16, ["closed"]*6+["open"]+["closed"]*15,
            ["closed"]*7+["open"]+["closed"]*14, ["closed"]*8+["open"]+["closed"]*13,
            ["closed"]*9+["open"]+["closed"]*12, ["closed"]*10+["open"]+["closed"]*11,
        ],
        "n_registers": [2]*12,
    },
    "sopranino_sax_Eb": {
        "desc": "Sopranino Saxophone in Eb (open-open, conical, non-regular key)",
        "closed_top": False, "bore_radius": 5.5, "outer_diameter": 24.0,
        "hole_diameter": 4.5, "hole_length": 1.5,
        "targets": [415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 783.99],
        "fingerings": [
            ["closed"]*18, ["open"]+["closed"]*17,
            ["closed","open"]+["closed"]*16, ["closed"]*2+["open"]+["closed"]*15,
            ["closed"]*3+["open"]+["closed"]*14, ["closed"]*4+["open"]+["closed"]*13,
            ["closed"]*5+["open"]+["closed"]*12, ["closed"]*6+["open"]+["closed"]*11,
            ["closed"]*7+["open"]+["closed"]*10, ["closed"]*8+["open"]+["closed"]*9,
            ["closed"]*9+["open"]+["closed"]*8, ["closed"]*10+["open"]+["closed"]*7,
        ],
        "n_registers": [2]*12,
    },
    "bass_sax_Bb": {
        "desc": "Bass Saxophone in Bb (open-open, conical, non-regular key)",
        "closed_top": False, "bore_radius": 15.0, "outer_diameter": 85.0,
        "hole_diameter": 11.0, "hole_length": 4.0,
        "targets": [46.25, 49.00, 51.91, 55.00, 58.27, 61.74, 65.41, 69.30, 73.42, 77.78, 82.41, 87.31],
        "fingerings": [
            ["closed"]*25, ["open"]+["closed"]*24,
            ["closed","open"]+["closed"]*23, ["closed"]*2+["open"]+["closed"]*22,
            ["closed"]*3+["open"]+["closed"]*21, ["closed"]*4+["open"]+["closed"]*20,
            ["closed"]*5+["open"]+["closed"]*19, ["closed"]*6+["open"]+["closed"]*18,
            ["closed"]*7+["open"]+["closed"]*17, ["closed"]*8+["open"]+["closed"]*16,
            ["closed"]*9+["open"]+["closed"]*15, ["closed"]*10+["open"]+["closed"]*14,
        ],
        "n_registers": [2]*12,
    },

    # === FLUTES (open-open, cylindrical) ===
    "concert_flute_C": {
        "desc": "Concert Flute in C (open-open, cylindrical Boehm)",
        "closed_top": False, "bore_radius": 9.5, "outer_diameter": 22.0,
        "hole_diameter": 7.0, "hole_length": 3.0,
        "targets": [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25],
        "fingerings": [
            ["closed"]*17, ["open"]+["closed"]*16,
            ["open"]*2+["closed"]*15, ["open"]*3+["closed"]*14,
            ["open"]*4+["closed"]*13, ["open"]*5+["closed"]*12,
            ["open"]*6+["closed"]*11, ["open"]*7+["closed"]*10,
            ["open"]*8+["closed"]*9, ["open"]*9+["closed"]*8,
            ["open"]*10+["closed"]*7, ["open"]*11+["closed"]*6,
            ["open"]*12+["closed"]*5,
        ],
        "n_registers": [3]*13,
    },
    "alto_flute_G": {
        "desc": "Alto Flute in G (open-open, cylindrical, non-regular key)",
        "closed_top": False, "bore_radius": 11.0, "outer_diameter": 18.0,
        "hole_diameter": 9.0, "hole_length": 3.0,
        "targets": [196.0, 220.0, 246.9, 261.6, 293.7, 329.6, 369.9],
        "fingerings": [
            ["closed"]*6, ["open"]+["closed"]*5,
            ["open"]*2+["closed"]*4, ["open"]*3+["closed"]*3,
            ["open"]*4+["closed"]*2, ["open"]*5+["closed"]*1,
            ["open"]*6,
        ],
        "n_registers": [2]*7,
    },
    "flute_F": {
        "desc": "Flute in F (open-open, cylindrical, non-regular key)",
        "closed_top": False, "bore_radius": 10.0, "outer_diameter": 20.0,
        "hole_diameter": 6.5, "hole_length": 2.5,
        "targets": [174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63, 349.23],
        "fingerings": [
            ["closed"]*16, ["open"]+["closed"]*15,
            ["open"]*2+["closed"]*14, ["open"]*3+["closed"]*13,
            ["open"]*4+["closed"]*12, ["open"]*5+["closed"]*11,
            ["open"]*6+["closed"]*10, ["open"]*7+["closed"]*9,
            ["open"]*8+["closed"]*8, ["open"]*9+["closed"]*7,
            ["open"]*10+["closed"]*6, ["open"]*11+["closed"]*5,
            ["open"]*12+["closed"]*4,
        ],
        "n_registers": [2]*13,
    },
    "bass_flute_C": {
        "desc": "Bass Flute in C (open-open, cylindrical, non-regular key)",
        "closed_top": False, "bore_radius": 12.0, "outer_diameter": 28.0,
        "hole_diameter": 6.0, "hole_length": 3.0,
        "targets": [130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63],
        "fingerings": [
            ["closed"]*15, ["open"]+["closed"]*14,
            ["open"]*2+["closed"]*13, ["open"]*3+["closed"]*12,
            ["open"]*4+["closed"]*11, ["open"]*5+["closed"]*10,
            ["open"]*6+["closed"]*9, ["open"]*7+["closed"]*8,
            ["open"]*8+["closed"]*7, ["open"]*9+["closed"]*6,
            ["open"]*10+["closed"]*5, ["open"]*11+["closed"]*4,
            ["open"]*12+["closed"]*3,
        ],
        "n_registers": [2]*13,
    },
    "diatonic_whistle_D": {
        "desc": "Tin Whistle in D (open-open, cylindrical, diatonic)",
        "closed_top": False, "bore_radius": 5.0, "outer_diameter": 12.0,
        "hole_diameter": 5.0, "hole_length": 1.5,
        "targets": [587.33, 659.25, 739.99, 783.99, 880.00, 987.77, 1108.73, 1174.66],
        "fingerings": [
            ["closed"]*6, ["open"]+["closed"]*5,
            ["open"]*2+["closed"]*4, ["open"]*3+["closed"]*3,
            ["open"]*4+["closed"]*2, ["open"]*5+["closed"]*1,
            ["open"]*6, ["open"]*6,
        ],
        "n_registers": [2]*8,
    },

    # === CLARINETS (closed-open, cylindrical) ===
    "clarinet_Bb": {
        "desc": "Bb Clarinet (closed-open, cylindrical Boehm)",
        "closed_top": True, "bore_radius": 7.0, "outer_diameter": 20.0,
        "hole_diameter": 6.0, "hole_length": 2.0,
        "targets": [233.08, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99],
        "fingerings": [
            ["closed"]*24, ["open"]+["closed"]*23,
            ["closed","open"]+["closed"]*22, ["closed"]*2+["open"]+["closed"]*21,
            ["closed"]*3+["open"]+["closed"]*20, ["closed"]*4+["open"]+["closed"]*19,
            ["closed"]*5+["open"]+["closed"]*18, ["closed"]*6+["open"]+["closed"]*17,
            ["closed"]*7+["open"]+["closed"]*16, ["closed"]*8+["open"]+["closed"]*15,
            ["closed"]*9+["open"]+["closed"]*14, ["closed"]*10+["open"]+["closed"]*13,
            ["closed"]*11+["open"]+["closed"]*12,
        ],
        "n_registers": [1,1,1,1,1,1,1,1,2,2,2,2,2],
    },
    "clarinet_D": {
        "desc": "D Clarinet (closed-open, cylindrical, non-regular key)",
        "closed_top": True, "bore_radius": 6.0, "outer_diameter": 18.0,
        "hole_diameter": 5.0, "hole_length": 1.5,
        "targets": [293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99],
        "fingerings": [
            ["closed"]*20, ["open"]+["closed"]*19,
            ["closed","open"]+["closed"]*18, ["closed"]*2+["open"]+["closed"]*17,
            ["closed"]*3+["open"]+["closed"]*16, ["closed"]*4+["open"]+["closed"]*15,
            ["closed"]*5+["open"]+["closed"]*14, ["closed"]*6+["open"]+["closed"]*13,
            ["closed"]*7+["open"]+["closed"]*12, ["closed"]*8+["open"]+["closed"]*11,
            ["closed"]*9+["open"]+["closed"]*10,
        ],
        "n_registers": [1,1,1,1,1,1,1,2,2,2,2],
    },
    "clarinet_A": {
        "desc": "A Clarinet (closed-open, cylindrical, non-regular key)",
        "closed_top": True, "bore_radius": 7.3, "outer_diameter": 21.0,
        "hole_diameter": 6.0, "hole_length": 2.0,
        "targets": [220.0, 246.94, 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25],
        "fingerings": [
            ["closed"]*23, ["open"]+["closed"]*22,
            ["closed","open"]+["closed"]*21, ["closed"]*2+["open"]+["closed"]*20,
            ["closed"]*3+["open"]+["closed"]*19, ["closed"]*4+["open"]+["closed"]*18,
            ["closed"]*5+["open"]+["closed"]*17, ["closed"]*6+["open"]+["closed"]*16,
            ["closed"]*7+["open"]+["closed"]*15, ["closed"]*8+["open"]+["closed"]*14,
            ["closed"]*9+["open"]+["closed"]*13, ["closed"]*10+["open"]+["closed"]*12,
        ],
        "n_registers": [1,1,1,1,1,1,1,1,2,2,2,2],
    },
    "clarinet_Eb_soprano": {
        "desc": "Eb Soprano Clarinet (closed-open, cylindrical, non-regular key)",
        "closed_top": True, "bore_radius": 6.3, "outer_diameter": 18.0,
        "hole_diameter": 5.0, "hole_length": 1.5,
        "targets": [311.13, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77],
        "fingerings": [
            ["closed"]*20, ["open"]+["closed"]*19,
            ["closed","open"]+["closed"]*18, ["closed"]*2+["open"]+["closed"]*17,
            ["closed"]*3+["open"]+["closed"]*16, ["closed"]*4+["open"]+["closed"]*15,
            ["closed"]*5+["open"]+["closed"]*14, ["closed"]*6+["open"]+["closed"]*13,
            ["closed"]*7+["open"]+["closed"]*12, ["closed"]*8+["open"]+["closed"]*11,
            ["closed"]*9+["open"]+["closed"]*10, ["closed"]*10+["open"]+["closed"]*9,
        ],
        "n_registers": [1,1,1,1,1,1,2,2,2,2,2,2],
    },

    # === RECORDERS ===
    "recorder_F": {
        "desc": "Soprano Recorder in F (open-open, cylindrical, non-regular key)",
        "closed_top": False, "bore_radius": 5.5, "outer_diameter": 14.0,
        "hole_diameter": 4.0, "hole_length": 1.5,
        "targets": [698.46, 739.99, 783.99, 880.00, 987.77, 1046.50, 1108.73, 1174.66],
        "fingerings": [
            ["closed"]*7, ["open"]+["closed"]*6,
            ["open"]*2+["closed"]*5, ["open"]*3+["closed"]*4,
            ["open"]*4+["closed"]*3, ["open"]*5+["closed"]*2,
            ["open"]*6+["closed"]*1, ["open"]*7,
        ],
        "n_registers": [2]*8,
    },
    "recorder_C": {
        "desc": "Soprano Recorder in C (open-open, cylindrical)",
        "closed_top": False, "bore_radius": 5.0, "outer_diameter": 12.0,
        "hole_diameter": 4.0, "hole_length": 1.5,
        "targets": [523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50],
        "fingerings": [
            ["closed"]*7, ["open"]+["closed"]*6,
            ["open"]*2+["closed"]*5, ["open"]*3+["closed"]*4,
            ["open"]*4+["closed"]*3, ["open"]*5+["closed"]*2,
            ["open"]*6+["closed"]*1, ["open"]*7,
        ],
        "n_registers": [2]*8,
    },
    "recorder_F_alto": {
        "desc": "Alto Recorder in F (open-open, cylindrical, non-regular key)",
        "closed_top": False, "bore_radius": 7.0, "outer_diameter": 16.0,
        "hole_diameter": 5.0, "hole_length": 2.0,
        "targets": [349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99],
        "fingerings": [
            ["closed"]*8, ["open"]+["closed"]*7,
            ["open"]*2+["closed"]*6, ["open"]*3+["closed"]*5,
            ["open"]*4+["closed"]*4, ["open"]*5+["closed"]*3,
            ["open"]*6+["closed"]*2, ["open"]*7+["closed"]*1,
            ["open"]*8,
        ],
        "n_registers": [2]*9,
    },
}

# ---------------------------------------------------------------------------
# Library benchmark references from cadquery_export
# ---------------------------------------------------------------------------

def _find_library_matches(name: str) -> list[dict]:
    """Find matching cadquery_export INSTRUMENTS entries for a config name."""
    from backend.cadquery_export import INSTRUMENTS as LIB
    cfg_parts = set(name.lower().replace('_', ' ').split())
    matches = []
    for lib_name, v in LIB.items():
        lib_parts = set(lib_name.lower().replace('_', ' ').split())
        overlap = cfg_parts & lib_parts
        # Match if 2+ words overlap or one name contains the other
        if len(overlap) >= 2 or cfg_parts <= lib_parts or lib_parts <= cfg_parts:
            bl = v.get('bore_length', None)
            bd = v.get('bore_diameter', None)
            wall = v.get('wall_thickness', None)
            ct = v.get('closed_top', None)
            n_holes = len(v.get('holes', []))
            matches.append({
                'lib_name': lib_name,
                'bore_length_mm': bl,
                'bore_diameter_mm': bd,
                'wall_thickness_mm': wall,
                'closed_top': ct,
                'n_holes': n_holes,
            })
    return matches


# ---------------------------------------------------------------------------
# Optimization function (runs locally or on Dask worker)
# ---------------------------------------------------------------------------

def optimize_instrument(name: str, cfg: dict, methods: list[str] | None = None) -> dict:
    """Run all optimization methods for an instrument.

    Returns dict with results from each method.
    """
    if methods is None:
        methods = ['pareto_sweep', 'refine_1_0', 'refine_0_5', 'two_phase']

    from backend.pareto_optimizer import pareto_sweep
    from backend.jax_optimizer import refine_sequential
    from backend.two_phase_optimizer import two_phase_optimize

    lib_matches = _find_library_matches(name)
    lib_ref = lib_matches[0] if lib_matches else None
    results = {
        'name': name,
        'desc': cfg.get('desc', ''),
        'closed_top': cfg.get('closed_top', False),
        'bore_radius': cfg.get('bore_radius', 0),
        'n_targets': len(cfg.get('targets', [])),
        'f0': min(cfg.get('targets', [0])),
        'library_ref': lib_ref,
        'library_matches': lib_matches,
        'results': {},
    }

    for method in methods:
        t0 = time.time()
        try:
            if method == 'pareto_sweep':
                sweep = pareto_sweep(cfg, n_cp=6, seed=42, n_weights=6, maxiter=80, verbose=False)
                w, int_c, timbre_c, L = min(sweep, key=lambda r: abs(r[0] - 0.5)) if sweep else (0, 0, 0, 0)
                rms_best = min(r[1] for r in sweep)
                best_w = min(sweep, key=lambda r: r[1])[0]
                results['results'][method] = {
                    'rms_c': rms_best,
                    'timbre': timbre_c,
                    'L_mm': L,
                    'best_w_int': best_w,
                    'n_points': len(sweep),
                    'time_s': round(time.time() - t0, 1),
                }

            elif method == 'refine_1_0':
                rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
                    cfg, verbose=False, use_jax_bore=False, w_int=1.0, w_mono=0.3,
                )
                results['results'][method] = {
                    'rms_c': float(rms),
                    'L_mm': float(L),
                    'n_holes': len(hp),
                    'hp': [round(p, 1) for p in hp],
                    'hd': [round(d, 1) for d in hd],
                    'time_s': round(t_refine, 1),
                }

            elif method == 'refine_0_5':
                rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
                    cfg, verbose=False, use_jax_bore=False, w_int=0.5, w_mono=0.3,
                )
                results['results'][method] = {
                    'rms_c': float(rms),
                    'L_mm': float(L),
                    'n_holes': len(hp),
                    'hp': [round(p, 1) for p in hp],
                    'hd': [round(d, 1) for d in hd],
                    'time_s': round(t_refine, 1),
                }

            elif method == 'two_phase':
                n_holes = len(cfg.get('targets', []))
                hole_lens = [cfg.get('hole_length', 2.0)] * n_holes
                bore_est = max(200, 343000 / (2 * min(cfg.get('targets', [261]))) * (1 if cfg.get('closed_top') else 2))
                fingerings_str = []
                for f in cfg.get('fingerings', []):
                    s = ''.join('o' if x == 'open' else 'x' for x in f[:n_holes])
                    fingerings_str.append(s)
                res = two_phase_optimize(
                    bore_length=bore_est, n_holes=n_holes, hole_lens=hole_lens,
                    targets=cfg['targets'], fingerings=fingerings_str,
                    n_register=cfg.get('n_registers', [2])[0],
                    bore_bounds_range=(cfg.get('bore_radius', 7.0)*0.3, cfg.get('bore_radius', 7.0)*2.0),
                    weight_timbre=0.0, verbose=False,
                )
                p2 = res.get('phase2', {})
                results['results'][method] = {
                    'final_cost': res.get('final_cost', 0),
                    'L_mm': float(cfg.get('bore_radius', 0)),
                    'n_holes': len(res.get('hole_diameters', [])),
                    'time_s': round(res.get('total_time', time.time() - t0), 1),
                    'phase1_cost': res.get('phase1', {}).get('cost', 0),
                    'phase2_cost': p2.get('cost', 0),
                }

        except Exception as e:
            results['results'][method] = {
                'error': str(e)[:200],
                'time_s': round(time.time() - t0, 1),
            }

    return results


# ---------------------------------------------------------------------------
# STL generation for best results
# ---------------------------------------------------------------------------

def generate_stl(name: str, cfg: dict, results: dict, out_dir: Path = OUT_DIR) -> tuple[str | None, str | float]:
    """Generate STL for the best result from refine_sequential (w_int=1.0)."""
    import numpy as np
    from backend.jax_optimizer import refine_sequential
    from backend.stl_export import make_capped_bore

    stl_name = f"{name}_optimized.stl"
    stl_path = out_dir / stl_name

    try:
        rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
            cfg, verbose=False, use_jax_bore=False, w_int=1.0, w_mono=0.3,
        )
        L = float(L)

        n_profile = 128
        profile_pos = np.linspace(0, L, n_profile)
        radii_arr = np.array(radii)
        cp_pos = np.linspace(0, L, len(radii_arr))
        profile_radii = np.interp(profile_pos, cp_pos, radii_arr)

        wall = cfg.get('outer_diameter', 30.0) / 2 - cfg.get('bore_radius', 7.0)
        wall = max(wall, 1.5)

        solid = make_capped_bore(
            profile_pos.astype(float), profile_radii.astype(float),
            wall_thickness=wall, n_angular=64, cap_thickness=wall * 0.67,
        )
        solid.export(str(stl_path))
        stl_kb = os.path.getsize(stl_path) / 1024
        return str(stl_path), stl_kb

    except Exception as e:
        return None, str(e)[:200]


# ---------------------------------------------------------------------------
# Main: local sequential execution
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--instruments", default="",
                        help="Comma-separated subset of instrument names")
    parser.add_argument("--no-stl", action="store_true",
                        help="Skip STL generation")
    parser.add_argument("--methods", default="refine_1_0,refine_0_5",
                        help="Comma-separated methods to run (default: refine_1_0,refine_0_5)")
    parser.add_argument("--dask", action="store_true",
                        help="Parallelize across instruments using local threaded Dask cluster")
    parser.add_argument("--dask-workers", type=int, default=4,
                        help="Number of Dask worker threads (default: 4)")
    args = parser.parse_args()

    methods = args.methods.split(",")

    # Select instruments
    if args.instruments:
        selected = {}
        for name in args.instruments.split(","):
            name = name.strip()
            if name in INSTRUMENTS_CFG:
                selected[name] = INSTRUMENTS_CFG[name]
            else:
                print(f"Warning: instrument {name!r} not found")
        if not selected:
            print("No valid instruments selected, using all")
            selected = INSTRUMENTS_CFG
    else:
        selected = INSTRUMENTS_CFG

    print(f"Optimizing {len(selected)} instruments with methods: {methods}")
    print(f"Methods: {methods}")
    if args.dask:
        print(f"Using Dask local thread cluster with {args.dask_workers} workers")
        from distributed import Client
        client = Client(processes=False, n_workers=args.dask_workers,
                        threads_per_worker=1)
        print(f"Dask dashboard: {client.dashboard_link}")

        futures = {}
        for name, cfg in selected.items():
            f = client.submit(optimize_instrument, name, cfg, methods=methods)
            futures[name] = f

        all_results = {}
        for i, (name, f) in enumerate(futures.items()):
            print(f"\n{'='*60}")
            print(f"  [{i+1}/{len(selected)}] {name} (waiting...)")
            print(f"{'='*60}")
            try:
                res = f.result(timeout=600)
                all_results[name] = res
                r = res['results']
                lib_ref = res.get('library_ref')
                line = f"  {name:35s}"
                if 'refine_1_0' in r and 'rms_c' in r['refine_1_0']:
                    line += f"  RMS={r['refine_1_0']['rms_c']:.4f}c  L={r['refine_1_0']['L_mm']:.0f}mm"
                if 'pareto_sweep' in r and 'rms_c' in r['pareto_sweep']:
                    line += f"  Pareto={r['pareto_sweep']['rms_c']:.4f}c"
                if lib_ref:
                    lib_L = lib_ref['bore_length_mm']
                    opt_L = r.get('refine_1_0', {}).get('L_mm', 0)
                    delta = abs(lib_L - opt_L) if lib_L and opt_L else None
                    line += f"  libL={lib_L}mm" + (f" diff={delta:.0f}mm" if delta is not None else "")
                print(line)
            except Exception as e:
                all_results[name] = {'name': name, 'error': str(e)[:200]}
                print(f"  {name:35s}  ERROR: {e}")

        client.close()

    else:
        all_results = {}
        for i, (name, cfg) in enumerate(selected.items()):
            print(f"\n{'='*60}")
            print(f"  [{i+1}/{len(selected)}] {name}")
            print(f"{'='*60}")
            try:
                res = optimize_instrument(name, cfg, methods=methods)
                all_results[name] = res
                r = res['results']
                lib_ref = res.get('library_ref')
                line = f"  {name:35s}"
                if 'refine_1_0' in r and 'rms_c' in r['refine_1_0']:
                    line += f"  RMS={r['refine_1_0']['rms_c']:.4f}c  L={r['refine_1_0']['L_mm']:.0f}mm"
                if 'pareto_sweep' in r and 'rms_c' in r['pareto_sweep']:
                    line += f"  Pareto={r['pareto_sweep']['rms_c']:.4f}c"
                if lib_ref:
                    lib_L = lib_ref['bore_length_mm']
                    opt_L = r.get('refine_1_0', {}).get('L_mm', 0)
                    delta = abs(lib_L - opt_L) if lib_L and opt_L else None
                    line += f"  libL={lib_L}mm" + (f" diff={delta:.0f}mm" if delta is not None else "")
                print(line)
            except Exception as e:
                all_results[name] = {'name': name, 'error': str(e)[:200]}
                print(f"  {name:35s}  ERROR: {e}")

    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {RESULTS_FILE}")

    # Generate STLs for best results
    if not args.no_stl:
        print("\nGenerating STLs for best results...")
        for name, res in all_results.items():
            if 'error' in res:
                continue
            cfg = selected.get(name)
            if cfg is None:
                continue
            stl_path, stl_info = generate_stl(name, cfg, res)
            if stl_path:
                print(f"  {name:35s}  STL: {stl_path} ({stl_info:.0f} KB)")
            else:
                print(f"  {name:35s}  STL error: {stl_info}")

    print("\nDone.")


if __name__ == "__main__":
    main()
