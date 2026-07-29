"""
Test Tier 3 of the inverse design pipeline:
timbre matching via NSGA-II bore radii optimization.

Synthesizes a G3 WAV, runs analyze_wav (Tier 1), creates a dummy
best_candidate (as Tier 2 would produce), and calls match_timbre.
"""
import sys, time, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.sound_analysis import (
    synthesize_harmonic, save_synthetic_wav, analyze_wav,
)
from backend.design_from_wav import match_timbre

t_start = time.time()

# Step 1: Synthesize G3 test WAV
print("Synthesizing G3 test WAV...")
samples = synthesize_harmonic(196.0, 8)
wav_path = os.path.join(tempfile.gettempdir(), "test_tier3_G3.wav")
save_synthetic_wav(wav_path, samples)
print(f"  Saved to {wav_path}")

# Step 2: Tier 1 — analyze WAV
print("Analyzing WAV (Tier 1)...")
analysis = analyze_wav(wav_path)
print(f"  F0: {analysis['fundamental_hz']:.2f} Hz")
print(f"  Confidence: {analysis['confidence']:.4f}")
print(f"  Harmonics detected: {len(analysis['harmonic_frequencies'])}")
for i, (f, m) in enumerate(zip(analysis["harmonic_frequencies"], analysis["harmonic_amplitudes"])):
    print(f"    H{i+1}: {f:.1f} Hz, amp={m:.4f}")

# Step 3: Create dummy best_candidate (as Tier 2 would produce)
best_candidate = {
    "bore_length_mm": 883,
    "bore_radii": [7.25] * 6,
    "hole_positions_mm": [48.6, 144.1, 156.5, 233.4, 249.3, 364.8],
    "hole_diameters_mm": [7.0] * 6,
}

# Step 4: Tier 3 — match timbre (small population for quick test)
print("\nRunning match_timbre (Tier 3)...")
t3_start = time.time()
result = match_timbre(best_candidate, analysis, n_gen=5, pop_size=15)
t3_elapsed = time.time() - t3_start
total_elapsed = time.time() - t_start

# Step 5: Report results
print(f"\n{'='*60}")
print("TIER 3 RESULTS")
print(f"{'='*60}")
print(f"  Success: {result.get('tier3_success', False)}")
print(f"  Cost initial:   {result.get('tier3_cost_initial', 'N/A'):.6f}")
print(f"  Cost optimized: {result.get('tier3_cost_optimized', 'N/A'):.6f}")
radi = result.get("bore_radii_initial", [])
rado = result.get("bore_radii_optimized", [])
print(f"  Radii initial:   {[f'{r:.3f}' for r in radi]}")
print(f"  Radii optimized: {[f'{r:.3f}' for r in rado]}")
if "tier3_error" in result:
    print(f"  Error: {result['tier3_error']}")
print(f"\n  Tier 3 time: {t3_elapsed:.2f}s")
print(f"  Total time:  {total_elapsed:.2f}s")
print(f"{'='*60}")
