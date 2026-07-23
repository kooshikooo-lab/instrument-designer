"""Test desktop's fixes for open-open instruments"""
import sys
sys.path.insert(0, "C:\\instrument-designer")

from backend.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.tmm_acoustics import SPEED_OF_SOUND
import numpy as np

print("=== Testing desktop's open-open register fix ===")
print("n_register for open-open is now n_register + 1 (phase=2 for fundamental)")

# Soprano sax Bb (open-open, 6 holes)
target_freqs_sop = [277.18, 311.13, 329.63, 369.99, 415.30, 440.00, 493.88]
fingerings_sop = [
    ['closed','closed','closed','closed','closed','closed'],
    ['open','closed','closed','closed','closed','closed'],
    ['open','open','closed','closed','closed','closed'],
    ['open','open','open','closed','closed','closed'],
    ['open','open','open','open','closed','closed'],
    ['open','open','open','open','open','closed'],
    ['open','open','open','open','open','open'],
]

print("\n--- Soprano Sax Bb (6 holes, open-open) ---")
opt_sop = SequentialBoreOptimizer(
    target_frequencies=target_freqs_sop,
    fingering_sets=fingerings_sop,
    bore_radius=8.0,
    outer_diameter=14.0,
    closed_top=False,
    n_register=1,
    hole_diameter=6.0,
    hole_length=8.0,
)
result_sop = opt_sop.run(verbose=True)
print(f"\nSOPRANO SAX: {result_sop['rms_cents']:.2f} cents RMS")

# Alto sax Eb (open-open, 5 holes)
target_freqs_alto = [155.56, 174.61, 196.00, 220.00, 246.94]
fingerings_alto = [
    ['closed','closed','closed','closed','closed'],
    ['open','closed','closed','closed','closed'],
    ['open','open','closed','closed','closed'],
    ['open','open','open','closed','closed'],
    ['open','open','open','open','closed'],
    ['open','open','open','open','open'],
]

print("\n--- Alto Sax Eb (5 holes, open-open) ---")
opt_alto = SequentialBoreOptimizer(
    target_frequencies=target_freqs_alto,
    fingering_sets=fingerings_alto,
    bore_radius=9.5,
    outer_diameter=17.0,
    closed_top=False,
    n_register=1,
    hole_diameter=8.0,
    hole_length=10.0,
)
result_alto = opt_alto.run(verbose=True)
print(f"\nALTO SAX: {result_alto['rms_cents']:.2f} cents RMS")
