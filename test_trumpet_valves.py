"""Quick trumpet valve calibration test - fixed targets"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
from backend.trumpet_acoustics import TrumpetModel, TrumpetBore, TRUMPET_VALVE_COMBOS, SPEED_OF_SOUND
import math
from scipy.optimize import minimize_scalar

bore = TrumpetBore.default_bb()
trumpet = TrumpetModel(bore)

open_freq = trumpet.resonance_frequency([], n_register=2)
print(f'Open: {open_freq:.1f} Hz')

# Correct Bb trumpet targets: valves LOWER pitch
# Open = Bb3 (highest), adding valves goes DOWN chromatically
# Target frequencies from MIDI (Bb3=MIDI58):
#   open: Bb3 (233 Hz)
#   2: A3 (220 Hz) — 1 semitone down
#   1: Ab3 (208 Hz) — 2 semitones down
#   1+2 / 3: G3 (196 Hz) — 3 semitones down
#   2+3: Gb3 (185 Hz) — 4 semitones down
#   1+3: F3 (175 Hz) — 5 semitones down
#   1+2+3: E3 (165 Hz) — 6 semitones down

target_notes = [
    ('open',   233.08),  # Bb3
    ('2',      220.00),  # A3
    ('1',      207.65),  # Ab3
    ('1+2',    196.00),  # G3
    ('3',      196.00),  # G3 (same as 1+2)
    ('2+3',    185.00),  # Gb3
    ('1+3',    174.61),  # F3
    ('1+2+3',  164.81),  # E3
]

total_err = 0
for name, target in target_notes:
    idx = [v[0] for v in TRUMPET_VALVE_COMBOS].index(name)
    indices = TRUMPET_VALVE_COMBOS[idx][1]
    freq = trumpet.resonance_frequency(indices, n_register=2)
    cents = 1200.0 * math.log2(freq / target) if freq > 0 else 0
    total_err += cents**2
    print(f'  {name:8s}: {freq:.1f} Hz  target {target:.1f} Hz  {cents:+.1f}c')

rms = math.sqrt(total_err / len(target_notes))
print(f'\nRMS with default tubes: {rms:.1f} cents')
print(f'Fundamental: {open_freq:.1f} Hz (target: 233.1 Hz, Bb3)')

# Now calibrate
def total_rms(tubes):
    bore_copy = TrumpetBore.default_bb()
    bore_copy.valve_tubes = list(tubes)
    t = TrumpetModel(bore_copy)
    errs = []
    for name, target in target_notes:
        idx = [v[0] for v in TRUMPET_VALVE_COMBOS].index(name)
        indices = TRUMPET_VALVE_COMBOS[idx][1]
        freq = t.resonance_frequency(indices, n_register=2)
        if freq > 0:
            errs.append((1200.0 * math.log2(freq / target))**2)
    return math.sqrt(sum(errs) / len(errs))

from scipy.optimize import minimize
result = minimize(total_rms, [160, 70, 270], method='Nelder-Mead',
                 options={'maxiter': 5000, 'xatol': 0.1, 'fatol': 0.01})
print(f'\nOptimized tubes: {[f"{t:.1f}" for t in result.x]}mm')
print(f'Optimized RMS: {result.fun:.1f} cents')

# Test with optimized tubes
bore_opt = TrumpetBore.default_bb()
bore_opt.valve_tubes = list(result.x)
trumpet_opt = TrumpetModel(bore_opt)
print('\nWith optimized tubes:')
total_err = 0
for name, target in target_notes:
    idx = [v[0] for v in TRUMPET_VALVE_COMBOS].index(name)
    indices = TRUMPET_VALVE_COMBOS[idx][1]
    freq = trumpet_opt.resonance_frequency(indices, n_register=2)
    cents = 1200.0 * math.log2(freq / target) if freq > 0 else 0
    total_err += cents**2
    print(f'  {name:8s}: {freq:.1f} Hz  target {target:.1f} Hz  {cents:+.1f}c')
rms_opt = math.sqrt(total_err / len(target_notes))
print(f'\nOptimized RMS: {rms_opt:.1f} cents')
