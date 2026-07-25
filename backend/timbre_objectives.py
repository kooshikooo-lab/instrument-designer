"""
Timbre objectives for wind instrument optimization.

Based on:
- Ernoult et al. (2020): Intonation and timbre (a2/a1 ratio) are inherently at odds
- Wolfe (UNSW): Peak spacing -> timbre brightness
- Keefe (1982): Peak height -> timbre/loudness, coupled with position
"""

import numpy as np
from scipy.signal import find_peaks
from typing import List, Tuple, Optional, Dict


def compute_inharmonicity(peak_freqs: np.ndarray, peak_mags: np.ndarray, 
                          fundamental_freq: float, max_harmonic: int = 10) -> float:
    """
    Compute inharmonicity: deviation of harmonic frequencies from ideal integer multiples.
    
    Inharmonicity coefficient B where fn = n*f0 * sqrt(1 + B*n^2)
    For small B: inharmonicity ~ (fn / (n*f0) - 1)
    
    Args:
        peak_freqs: frequencies of impedance peaks (Hz)
        peak_mags: magnitudes of impedance peaks
        fundamental_freq: expected fundamental frequency (Hz)
        max_harmonic: maximum harmonic number to consider
        
    Returns:
        Inharmonicity score (0 = perfect harmonic, higher = more inharmonic)
    """
    if len(peak_freqs) == 0 or fundamental_freq <= 0:
        return 1e10
    
    # Find peaks that correspond to expected harmonics
    expected_harmonics = np.arange(1, max_harmonic + 1) * fundamental_freq
    deviations = []
    
    for expected in expected_harmonics:
        # Find nearest peak
        idx = np.argmin(np.abs(peak_freqs - expected))
        if idx < len(peak_freqs):
            actual = peak_freqs[idx]
            if actual > 0:
                rel_error = actual / expected - 1.0
                deviations.append(abs(rel_error))
    
    if not deviations:
        return 1e10
    
    # Return RMS of relative deviations
    return float(np.sqrt(np.mean(np.array(deviations) ** 2)))


def compute_phase_slope_sharpness(peak_freqs: np.ndarray, peak_mags: np.ndarray,
                                  fundamental_freq: float) -> float:
    """
    Compute phase-slope sharpness proxy from peak amplitude ratios.
    
    Based on:
    - Wolfe: Peak spacing -> timbre brightness
    - Keefe (1982): Peak height correlates with timbre/loudness
    - Ernoult: a2/a1 ratio is a key timbre parameter
    
    Higher even/odd harmonic ratio = brighter/sharper timbre
    For closed-open pipes: odd harmonics dominate (1, 3, 5...)
    For open-open pipes: all harmonics (1, 2, 3, 4...)
    
    Returns:
        Negative sharpness (so minimizing = maximizing sharpness)
    """
    if len(peak_freqs) < 2 or fundamental_freq <= 0:
        return 0.0
    
    # Find peaks near expected harmonics
    max_harmonic = min(10, len(peak_freqs))
    expected_harmonics = np.arange(1, max_harmonic + 1) * fundamental_freq
    
    harmonic_mags = []
    harmonic_nums = []
    
    for n, expected in enumerate(expected_harmonics, 1):
        idx = np.argmin(np.abs(peak_freqs - expected))
        if idx < len(peak_freqs):
            harmonic_mags.append(peak_mags[idx])
            harmonic_nums.append(n)
    
    if len(harmonic_mags) < 2:
        return 0.0
    
    harmonic_mags = np.array(harmonic_mags)
    harmonic_nums = np.array(harmonic_nums)
    
    # Even/odd ratio as timbre proxy
    even_mask = harmonic_nums % 2 == 0
    odd_mask = harmonic_nums % 2 == 1
    
    if np.any(even_mask) and np.any(odd_mask):
        even_mags = harmonic_mags[even_mask]
        odd_mags = harmonic_mags[odd_mask]
        even_odd_ratio = np.mean(even_mags) / (np.mean(odd_mags) + 1e-10)
    else:
        even_odd_ratio = 0.0
    
    # Spectral centroid (brightness proxy)
    if np.sum(harmonic_mags) > 0:
        centroid = np.sum(harmonic_nums * harmonic_mags) / np.sum(harmonic_mags)
    else:
        centroid = 0.0
    
    # Combine: higher even/odd ratio + higher centroid = sharper timbre
    # Return negative so minimizing = maximizing sharpness
    sharpness = even_odd_ratio + centroid / 10.0
    return float(-sharpness)


def compute_timbre_objective(peak_freqs: np.ndarray, peak_mags: np.ndarray,
                             fundamental_freq: float, 
                             weight_inharmonicity: float = 1.0,
                             weight_sharpness: float = 1.0) -> float:
    """
    Combined timbre objective: inharmonicity + sharpness.
    
    Args:
        peak_freqs: impedance peak frequencies
        peak_mags: impedance peak magnitudes
        fundamental_freq: expected fundamental frequency
        weight_inharmonicity: weight for inharmonicity term
        weight_sharpness: weight for sharpness term
        
    Returns:
        Combined timbre cost (lower = better timbre match)
    """
    inharm = compute_inharmonicity(peak_freqs, peak_mags, fundamental_freq)
    sharp = compute_phase_slope_sharpness(peak_freqs, peak_mags, fundamental_freq)
    
    return weight_inharmonicity * inharm + weight_sharpness * sharp


def compute_harmonic_signature(peak_freqs: np.ndarray, peak_mags: np.ndarray,
                               fundamental_freq: float) -> Dict:
    """
    Compute full harmonic signature for analysis.
    
    Returns:
        Dictionary with harmonic structure info
    """
    if len(peak_freqs) == 0 or fundamental_freq <= 0:
        return {}
    
    max_harmonic = min(15, len(peak_freqs))
    expected = np.arange(1, max_harmonic + 1) * fundamental_freq
    
    signature = {
        'fundamental': fundamental_freq,
        'harmonics': [],
        'inharmonicity': 0.0,
        'even_odd_ratio': 0.0,
        'centroid': 0.0,
        'sharpness': 0.0
    }
    
    harmonic_mags = []
    harmonic_nums = []
    deviations = []
    
    for n, exp_freq in enumerate(expected, 1):
        idx = np.argmin(np.abs(peak_freqs - exp_freq))
        if idx < len(peak_freqs):
            actual_freq = peak_freqs[idx]
            actual_mag = peak_mags[idx]
            rel_dev = actual_freq / exp_freq - 1.0
            
            signature['harmonics'].append({
                'n': n,
                'expected_hz': exp_freq,
                'actual_hz': actual_freq,
                'magnitude': actual_mag,
                'deviation_cents': 1200 * np.log2(actual_freq / exp_freq) if actual_freq > 0 else 0
            })
            
            harmonic_nums.append(n)
            harmonic_mags.append(actual_mag)
            deviations.append(abs(rel_dev))
    
    if deviations:
        signature['inharmonicity'] = float(np.sqrt(np.mean(np.array(deviations) ** 2)))
    
    harmonic_mags = np.array(harmonic_mags)
    harmonic_nums = np.array(harmonic_nums)
    
    if len(harmonic_mags) > 1:
        even_mask = harmonic_nums % 2 == 0
        odd_mask = harmonic_nums % 2 == 1
        
        if np.any(even_mask) and np.any(odd_mask):
            signature['even_odd_ratio'] = float(
                np.mean(harmonic_mags[even_mask]) / (np.mean(harmonic_mags[odd_mask]) + 1e-10)
            )
        
        if np.sum(harmonic_mags) > 0:
            signature['centroid'] = float(
                np.sum(harmonic_nums * harmonic_mags) / np.sum(harmonic_mags)
            )
        
        signature['sharpness'] = signature['even_odd_ratio'] + signature['centroid'] / 10.0
    
    return signature


# Convenience function for optimizer integration
def timbre_cost_from_bore(bore_points, fundamental_freq: float, 
                          freq_range=(50, 3000), n_freqs=5000, temperature=20.0):
    """
    Compute timbre cost directly from bore points.
    
    For use in optimization cost functions.
    """
    from .bore_optimizer import _compute_impedance_from_bore
    
    imp_result = _compute_impedance_from_bore(
        bore_points, freq_range, n_freqs, temperature
    )
    
    peak_freqs = imp_result["peak_frequencies"]
    peak_mags = imp_result["peak_magnitudes"]
    
    return compute_timbre_objective(peak_freqs, peak_mags, fundamental_freq)


if __name__ == "__main__":
    # Quick test
    print("Testing timbre objectives...")
    
    # Simulate some peaks for a closed-open pipe (odd harmonics)
    f0 = 200.0  # Hz
    harmonics = np.arange(1, 11, 2)  # 1, 3, 5, 7, 9
    peak_freqs = harmonics * f0 * (1 + 0.001 * harmonics**2)  # slight inharmonicity
    peak_mags = np.array([1.0, 0.6, 0.3, 0.15, 0.08])  # decreasing magnitudes
    
    inharm = compute_inharmonicity(peak_freqs, peak_mags, f0)
    sharp = compute_phase_slope_sharpness(peak_freqs, peak_mags, f0)
    timbre = compute_timbre_objective(peak_freqs, peak_mags, f0)
    
    print(f"Inharmonicity: {inharm:.6f}")
    print(f"Sharpness: {sharp:.6f}")
    print(f"Combined timbre: {timbre:.6f}")
    
    # Test signature
    sig = compute_harmonic_signature(peak_freqs, peak_mags, f0)
    print(f"\nSignature: inharm={sig['inharmonicity']:.6f}, "
          f"even/odd={sig['even_odd_ratio']:.3f}, "
          f"centroid={sig['centroid']:.2f}, "
          f"sharpness={sig['sharpness']:.3f}")