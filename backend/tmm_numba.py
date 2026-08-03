"""
Numba-accelerated helper for TMM resonance phase evaluation.

This module provides a guarded numba implementation of the resonance_phase
loop. It compiles a simple numeric loop that walks a compact action array and
computes the phase for a given wavelength and fingering mask. The implementation
focuses on the lossless path (loss_model=None) to keep the compiled loop simple
and robust; the Python codepath remains authoritative for other cases.

Usage:
    from backend.tmm_numba import numba_resonance_phase, build_action_arrays

    actions = inst.actions
    types, p1, p2, p3, p4, p5 = build_action_arrays(actions)
    # fingerings as list of 'open'/'closed' -> mask array of ints (1=open,0=closed)
    mask = np.array([1 if f==Hole.OPEN else 0 for f in fingerings], dtype=np.int32)
    phase = numba_resonance_phase(types, p1, p2, p3, p4, p5, mask, wavelength, closed_top=False)

If numba is not available, `numba_resonance_phase` will raise ImportError with
instructions to install numba. The helper `build_action_arrays` always works
and can be used to inspect the numeric action representation.
"""

from typing import List, Tuple
import numpy as np

try:
    import numba
    from numba import njit
    _NUMBA_AVAILABLE = True
except Exception:
    _NUMBA_AVAILABLE = False


def build_action_arrays(actions: List[Tuple]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert the instrument actions (list of tuples) into compact numpy arrays
    that the numba-compiled function can consume.

    Encoding:
      types: int32 array: 0=pipe, 1=junction2, 2=hole
      p1..p5: float64 arrays containing arguments. Semantics vary by type:
        pipe: p1=seg_length, p2=seg_diameter
        junction2: p1=area_a, p2=area_b
        hole: p1=hole_idx (as float), p2=area_bore, p3=hole_area, p4=open_length, p5=closed_length
    """
    n = len(actions)
    types = np.zeros(n, dtype=np.int32)
    p1 = np.zeros(n, dtype=np.float64)
    p2 = np.zeros(n, dtype=np.float64)
    p3 = np.zeros(n, dtype=np.float64)
    p4 = np.zeros(n, dtype=np.float64)
    p5 = np.zeros(n, dtype=np.float64)

    for i, action in enumerate(actions):
        kind = action[0]
        if kind == 'pipe':
            _, seg_length, seg_diameter = action
            types[i] = 0
            p1[i] = float(seg_length)
            p2[i] = float(seg_diameter)
        elif kind == 'junction2':
            _, area_a, area_b = action
            types[i] = 1
            p1[i] = float(area_a)
            p2[i] = float(area_b)
        elif kind == 'hole':
            _, hole_idx, area_bore, hole_area, open_length, closed_length = action
            types[i] = 2
            p1[i] = float(hole_idx)
            p2[i] = float(area_bore)
            p3[i] = float(hole_area)
            p4[i] = float(open_length)
            p5[i] = float(closed_length)
        else:
            # unknown action - leave zeros and type -1 marker
            types[i] = -1
    return types, p1, p2, p3, p4, p5


if _NUMBA_AVAILABLE:
    @njit
    def _compiled_resonance_phase(types, p1, p2, p3, p4, p5, fingering_mask, wavelength, closed_top):
        phase = 0.5
        n = types.shape[0]
        for i in range(n):
            t = types[i]
            if t == 0:
                seg_length = p1[i]
                # seg_diameter = p2[i]
                phase = phase + 2.0 * (seg_length / wavelength)
            elif t == 1:
                area_a = p1[i]
                area_b = p2[i]
                # junction2: untanner(area_b/area_a * tanner(phase-shift)) + shift
                shift = np.floor(phase + 0.5)
                phase = np.arctan((area_b / area_a) * np.tan((phase - shift) * np.pi)) / np.pi + shift
            elif t == 2:
                hole_idx = int(p1[i])
                area_bore = p2[i]
                hole_area = p3[i]
                open_length = p4[i]
                closed_length = p5[i]
                is_open = fingering_mask[hole_idx] == 1
                if is_open:
                    hole_phase = (-0.5) + 2.0 * (open_length / wavelength)
                else:
                    hole_phase = 0.0 + 2.0 * (closed_length / wavelength)
                # junction3: untanner(a1/a0 * tanner(p1-shift1) + a2/a0 * tanner(p2-shift2)) + shift1 + shift2
                shift1 = np.floor(phase + 0.5)
                shift2 = np.floor(hole_phase + 0.5)
                val = (area_bore / area_bore) * np.tan((phase - shift1) * np.pi) + (hole_area / area_bore) * np.tan((hole_phase - shift2) * np.pi)
                phase = np.arctan(val) / np.pi + shift1 + shift2
            else:
                # ignore unknown actions
                pass
        if not closed_top:
            phase = phase + 0.5
        return phase

    def numba_resonance_phase(types, p1, p2, p3, p4, p5, fingering_mask, wavelength, closed_top=False):
        """Call the compiled resonance phase evaluator.

        Args:
            types, p1..p5: arrays produced by build_action_arrays
            fingering_mask: int32 array (1=open, 0=closed)
            wavelength: float
            closed_top: bool
        Returns:
            phase (float)
        """
        # Ensure numpy arrays are of expected dtypes
        types_a = np.asarray(types, dtype=np.int32)
        p1_a = np.asarray(p1, dtype=np.float64)
        p2_a = np.asarray(p2, dtype=np.float64)
        p3_a = np.asarray(p3, dtype=np.float64)
        p4_a = np.asarray(p4, dtype=np.float64)
        p5_a = np.asarray(p5, dtype=np.float64)
        mask_a = np.asarray(fingering_mask, dtype=np.int32)
        return float(_compiled_resonance_phase(types_a, p1_a, p2_a, p3_a, p4_a, p5_a, mask_a, float(wavelength), bool(closed_top)))

else:
    def numba_resonance_phase(*args, **kwargs):
        raise ImportError("numba is not available. Install numba (pip install numba) to use the compiled TMM path.")

