import sys, os, time, math, numpy as np
sys.path.insert(0, 'backend')
from benchmark_all import eval_all, INSTRUMENTS

cfg = INSTRUMENTS['chalumeau_C']

# Run the optimizer with verbose to see what's happening
from tmm_optimizer_sequential import SequentialBoreOptimizer

opt = SequentialBoreOptimizer(
    target_frequencies=cfg["targets"],
    fingering_sets=cfg["fingerings"],
    bore_radius=cfg["bore_radius"],
    outer_diameter=cfg["outer_diameter"],
    closed_top=cfg["closed_top"],
    hole_diameter=cfg["hole_diameter"],
    hole_length=cfg["hole_length"],
)
result = opt.run(verbose=True)
