# LLM Assistance Prompts for TMM Bore Optimizer Improvements

Based on research comparing our Python implementation with chalumier's reference Kotlin implementation.

---

## Prompt 1: Implement Cubic Mean Scoring (L3 Norm)

**Context:** Our optimizer uses RMS (L2 norm) for scoring: `sqrt(mean(cents²))`. Chalumier uses cubic mean (L3 norm): `cuberoot(mean(|cents|³))`. The cubic mean penalizes outliers ~2x more heavily than RMS, which is critical for instrument intonation quality.

**Chalumier reference (InstrumentDesigner.kt lines 462-508):**
```kotlin
fun intonationScore(i: Instrument): Double {
    val inst = patchInstrument(i)
    var score = 0.0
    var div = 0.0
    val s = 1200.0 / ln(2.0)
    for (idx in fingerings.indices) {
        val fingering = fingerings[idx]
        val fingers = fingering.fingers
        val desiredWavelength = fingering.wavelength(transpose)
        val actualWavelength = if (fingering.nth == null) {
            inst.trueWavelengthNear(desiredWavelength, fingers)
        } else {
            inst.trueNthWavelengthNear(desiredWavelength, fingers, fingering.nth)
        }
        val diff = abs(ln(desiredWavelength) - ln(actualWavelength)) * s
        val weight = 1.0
        score += weight * diff.pow(3)
        div += weight
    }
    return (score / div).pow(1.0 / 3.0)
}
```

**Our current code (tmm_optimizer_sequential.py line 497):**
```python
return float(np.sqrt(np.mean(c ** 2)))  # RMS
```

**Task:** Replace RMS with cubic mean scoring in:
1. `tmm_optimizer_sequential.py` `_refine_objective` function (line 497)
2. `benchmark_all.py` `eval_all` function (line 312)
3. All other places where RMS is used as the final score

**Implementation:**
```python
# Replace this:
return float(np.sqrt(np.mean(c ** 2)))

# With this (cubic mean):
return float(np.mean(np.abs(c) ** 3) ** (1.0/3.0))
```

**Verification:** Run `python benchmark_all.py` and compare results. Chalumier achieves:
- Chalumeau: 0.00c
- Recorder: 1.41c
- Bass Chalumeau: 0.00c
- Soprano Sax: 0.03c
- Alto Sax: 0.15c
- Tin Whistle: 0.91c

---

## Prompt 2: Implement Nearest-Resonance Search (trueWavelengthNear)

**Context:** Our `wavelength_near` function uses a fixed phase register (n_register), which causes issues with open-open pipes where the TMM creates a phantom first resonance. Chalumier's `trueWavelengthNear` finds the nearest resonance regardless of register, which is more robust.

**Chalumier reference (Instrument.kt lines 430-439):**
```kotlin
override fun trueWavelengthNear(
    wavelength: Double,
    fingers: List<Hole>,
    stepCents: Double,
    stepIncrease: Double,
    maxSteps: Int
): Double {
    val scorer = { probe: Double -> ((resonancePhase(probe, fingers) + 0.5) % 1.0) - 0.5 }
    return wavelengthNear(wavelength, fingers, stepCents, stepIncrease, maxSteps, scorer)
}
```

**Our current code (tmm_acoustics.py lines 408-474):**
```python
def wavelength_near(
    self,
    wavelength: float,
    fingerings: List[str],
    step_cents: float = 1.0,
    step_increase: float = 1.2,
    max_steps: int = 100,
    target_register: int = 1,
) -> float:
    step = 2.0 ** (step_cents / 1200.0)
    half_step = math.sqrt(step)

    def scorer(w):
        p = self.resonance_phase(w, fingerings)
        return ((p + 0.5) % 1.0) - 0.5  # Already matches chalumier!

    # ... search logic ...
```

**Task:** Our scorer already matches chalumier's `trueWavelengthNear`! The issue is that `find_resonance` passes `n_register` which is ignored. Fix:

1. Add a new method `true_wavelength_near` that matches chalumier's signature (no n_register parameter)
2. Add a new method `true_nth_wavelength_near` for specific register targeting
3. Update `find_resonance` to use the new method by default
4. Update the optimizer to use `true_wavelength_near` for standard fingerings and `true_nth_wavelength_near` for reed instruments with register breaks

**Implementation:**
```python
def true_wavelength_near(
    self,
    wavelength: float,
    fingerings: List[str],
    step_cents: float = 1.0,
    step_increase: float = 1.05,
    max_steps: int = 100,
) -> float:
    """Find the nearest resonant wavelength to the given guess.
    Port of Instrument.trueWavelengthNear() from chalumier."""
    # Use existing wavelength_near with modular scorer
    return self.wavelength_near(wavelength, fingerings, step_cents, step_increase, max_steps)

def true_nth_wavelength_near(
    self,
    wavelength: float,
    fingerings: List[str],
    n: int,
    step_cents: float = 1.0,
    step_increase: float = 1.5,
    max_steps: int = 20,
) -> float:
    """Find the nth resonant wavelength.
    Port of Instrument.trueNthWavelengthNear() from chalumier."""
    step = 2.0 ** (step_cents / 1200.0)
    half_step = math.sqrt(step)
    
    def scorer(w):
        p = self.resonance_phase(w, fingerings)
        return p - n  # Target specific phase integer
    
    # ... (copy search logic from wavelength_near but with this scorer)
```

---

## Prompt 3: Implement patchInstrument for Different Instrument Types

**Context:** Chalumier applies instrument-specific modifications BEFORE scoring. This is essential for accurate optimization. We have no equivalent.

**Chalumier references:**

### Whistle (WhistleDesigner.kt lines 90-125):
```kotlin
override fun patchInstrument(inst: Instrument): Instrument {
    val patchedInst = inst.dup()
    patchedInst.trueLength = patchedInst.length
    
    val boreDiameter = patchedInst.inner(patchedInst.length)
    patchedInst.length -= (boreDiameter * tweakBoreLess)  // tweakBoreLess = 0.3
    patchedInst.inner = patchedInst.inner.clipped(0.0, patchedInst.length)
    
    val props = getWhistleHeadProportions()
    val diameter = props.first
    val length = (props.second / 2.0) + diameter * tweakGapExtra  // tweakGapExtra = 0.6
    
    patchedInst.inner = Profile(
        ArrayList(patchedInst.inner.pos + listOf(patchedInst.length + length)),
        ArrayList(patchedInst.inner.low + listOf(diameter)),
        ArrayList(patchedInst.inner.high.slice(0 until patchedInst.inner.high.size - 1) + listOf(diameter, diameter))
    )
    patchedInst.length += length
    return patchedInst
}
```

### Flute (FluteDesigner.kt lines 103-109):
```kotlin
override fun patchInstrument(inst: Instrument): Instrument {
    val hl = inst.holeLengths.dup()
    hl[inst.holeLengths.size - 1] += (inst.holeDiameters.fromEnd(1) * embExtra)  // embExtra = 0.53
    val result = inst.dup()
    result.holeLengths = hl
    return result
}
```

### Shawm (ShawmDesigner.kt lines 66-78):
```kotlin
override fun patchInstrument(inst: Instrument): Instrument {
    val patchedInst = inst.dup()
    patchedInst.trueLength = length
    val reedLength = bore * reedVirtualLength  // reedVirtualLength = 34.0
    val reedTop = bore * reedVirtualTop  // reedVirtualTop = 1.0
    val reed = Profile.makeProfile(listOf(listOf(0.0, bore), arrayListOf(reedLength, reedTop)))
    patchedInst.inner += reed
    patchedInst.length += reedLength
    return patchedInst
}
```

**Task:** Implement `patch_instrument` function in `tmm_optimizer_sequential.py`:

```python
def patch_instrument(
    inst: TMMInstrument,
    instrument_type: str,
    bore_radius: float,
    hole_diameters: List[float],
    hole_lengths: List[float],
    **kwargs
) -> TMMInstrument:
    """Apply instrument-specific modifications before scoring.
    
    Args:
        inst: TMMInstrument to patch
        instrument_type: 'whistle', 'flute', 'shawm', 'clarinet', 'sax', etc.
        bore_radius: bore radius at the top (reed end)
        hole_diameters: list of hole diameters
        hole_lengths: list of hole lengths
        **kwargs: instrument-specific parameters
    
    Returns:
        Patched TMMInstrument
    """
    patched = inst.dup()
    
    if instrument_type == 'whistle':
        # Bore shortening
        bore_diameter = bore_radius * 2
        tweak_bore_less = kwargs.get('tweak_bore_less', 0.3)
        patched.length -= bore_diameter * tweak_bore_less
        
        # Fipple head
        tweak_gap_extra = kwargs.get('tweak_gap_extra', 0.6)
        # ... (add fipple head profile)
        
    elif instrument_type == 'flute':
        # Embouchure depth
        emb_extra = kwargs.get('emb_extra', 0.53)
        patched.hole_lengths[-1] += hole_diameters[-1] * emb_extra
        
    elif instrument_type == 'shawm':
        # Virtual reed cone
        reed_virtual_length = kwargs.get('reed_virtual_length', 34.0)
        reed_virtual_top = kwargs.get('reed_virtual_top', 1.0)
        reed_length = bore_radius * 2 * reed_virtual_length
        reed_top = bore_radius * 2 * reed_virtual_top
        # ... (append reed cone profile)
        
    return patched
```

**Integration:** Update `intonation_score` to call `patch_instrument` before computing resonances.

---

## Prompt 4: Implement Cross-Fingerings and nth Register Support

**Context:** Our current code only supports sequential fingerings (cumulative from bottom). Chalumier supports arbitrary O/X combinations (cross-fingerings) and nth register parameter for reed instruments.

**Chalumier reference (Fingering.kt lines 23-49):**
```kotlin
@Serializable
enum class Hole {
    O, X
}

@Serializable
data class Fingering(
    val noteName: String, val fingers: List<Hole>, val nth: Int? = null
) {
    fun wavelength(transpose: Int): Double {
        return wavelength(noteName, transpose)
    }
}
```

**Task:** 
1. Add `Hole` enum to `tmm_acoustics.py` (already exists, but not used consistently)
2. Update fingering handling in optimizer to support arbitrary O/X combinations
3. Add nth parameter support for reed instruments

**Implementation:**
```python
# In tmm_acoustics.py
from enum import Enum

class Hole(Enum):
    OPEN = 'O'
    CLOSED = 'X'

# In tmm_optimizer_sequential.py
def intonation_score(
    self,
    inst: TMMInstrument,
    fingerings: List[Dict],  # Each dict has 'fingers' and optional 'nth'
    transpose: int = 0,
) -> float:
    """Compute cubic mean intonation score.
    
    Args:
        inst: TMMInstrument (already patched)
        fingerings: List of dicts with keys:
            - 'fingers': List of 'O'/'X' or Hole.OPEN/Hole.CLOSED
            - 'nth': Optional register number (for reed instruments)
        transpose: Transposition in semitones
    
    Returns:
        Cubic mean of absolute cents errors
    """
    score = 0.0
    div = 0.0
    s = 1200.0 / math.log(2.0)
    
    for fingering in fingerings:
        fingers = fingering['fingers']
        nth = fingering.get('nth', None)
        
        # Get target wavelength
        note_name = fingering['noteName']
        target_wl = wavelength(note_name, transpose)  # Convert note to wavelength
        
        # Find actual wavelength
        if nth is None:
            actual_wl = inst.true_wavelength_near(target_wl, fingers)
        else:
            actual_wl = inst.true_nth_wavelength_near(target_wl, fingers, nth)
        
        # Compute cents error
        diff = abs(math.log(target_wl) - math.log(actual_wl)) * s
        score += diff ** 3
        div += 1
    
    return (score / div) ** (1.0/3.0)
```

---

## Prompt 5: Implement Constraint Scoring (Physical Feasibility)

**Context:** Chalumier uses lexicographic scoring: first check if instrument is physically feasible (constraintScore), then optimize intonation (intonationScore). We have no constraint scoring.

**Chalumier reference (InstrumentDesigner.kt lines 366-438):**
```kotlin
fun constraintScore(inst: Instrument): Double {
    val scores = ArrayList<Double>()
    scores.add(inst.length)
    val ml = maxLength
    if (ml != null) {
        scores.add(ml * scale - inst.length)
    }

    // Check hole separations
    val inners = ArrayList(listOf(0.0) + inst.innerKinks + listOf(inst.length))
    for (i in 0 until inners.size - 1) {
        val sep = inners[i + 1] - inners[i]
        scores.add(sep - minInnerFractionSep[i] * inst.length)
        scores.add(maxInnerFractionSep[i] * inst.length - sep)
    }

    // Check bottom/top clearance
    scores.add(inst.holePositions[0] - bottomClearanceFraction * inst.length)
    scores.add((1.0 - topClearanceFraction) * inst.length - inst.holePositions.last())

    // Check hole spacing
    for (idx in minHoleSpacing.indices) {
        val minSpacing = minHoleSpacing[idx]
        if (minSpacing != null) {
            scores.add((inst.holePositions[idx + 1] - inst.holePositions[idx]) - minSpacing)
        }
    }

    // Check hole diameters
    minHoleDiameters.forEachIndexed { i, value ->
        scores.add(inst.holeDiameters[i] - value)
    }
    maxHoleDiameters.forEachIndexed { i, value ->
        scores.add(value - inst.holeDiameters[i])
    }

    val negScores = scores.filter { it < -0.05 }.map { -it }
    return if (negScores.isNotEmpty()) {
        negScores.sum()
    } else {
        0.0
    }
}
```

**Task:** Implement `constraint_score` in `tmm_optimizer_sequential.py`:

```python
def constraint_score(
    bore_length: float,
    hole_positions: List[float],
    hole_diameters: List[float],
    min_hole_spacing: float = 5.0,  # mm
    bottom_clearance_fraction: float = 0.1,
    top_clearance_fraction: float = 0.1,
    min_hole_diameter: float = 2.0,  # mm
    max_hole_diameter: float = 15.0,  # mm
) -> float:
    """Compute constraint violation score.
    
    Returns:
        0.0 if all constraints satisfied, otherwise sum of violations
    """
    scores = []
    
    # Bore length
    scores.append(bore_length)  # Must be positive
    scores.append(500.0 - bore_length)  # Must be < 500mm
    
    # Hole positions
    if hole_positions:
        # Bottom clearance
        scores.append(hole_positions[0] - bottom_clearance_fraction * bore_length)
        # Top clearance
        scores.append((1.0 - top_clearance_fraction) * bore_length - hole_positions[-1])
        
        # Hole spacing
        for i in range(len(hole_positions) - 1):
            spacing = hole_positions[i + 1] - hole_positions[i]
            scores.append(spacing - min_hole_spacing)
    
    # Hole diameters
    for d in hole_diameters:
        scores.append(d - min_hole_diameter)
        scores.append(max_hole_diameter - d)
    
    # Sum of violations
    neg_scores = [abs(s) for s in scores if s < -0.05]
    return sum(neg_scores) if neg_scores else 0.0
```

**Integration:** Update optimizer to use lexicographic scoring:
```python
def full_score(params):
    inst = make_instrument(params)
    cs = constraint_score(...)
    is_ = intonation_score(inst, fingerings)
    return (cs, is_)  # Lexicographic: constraint first, then intonation
```

---

## Prompt 6: Fix Coordinate System Consistency

**Context:** Chalumier uses position 0 = bell (open end), position L = reed (closed end). Our code uses the same convention internally, but there's confusion in the optimizer about hole indexing.

**Task:**
1. Document the convention clearly in all files
2. Ensure hole indexing is consistent (index 0 = first hole from bell)
3. Fix any places where the convention is violated

**Current status:**
- `tmm_acoustics.py`: Correct (position 0 = open end, phase starts at 0.5)
- `tmm_optimizer_sequential.py`: Mostly correct, but some confusion in comments
- `benchmark_all.py`: Correct

---

## Prompt 7: Fix n_register Bug in benchmark_all.py

**Context:** `benchmark_all.py` line 237 hardcodes `n_reg = 1` for all instruments in the `sequential()` function, but open-open instruments need `n_reg = 2`.

**Current code (benchmark_all.py line 237):**
```python
n_reg = 1  # This is wrong for open-open instruments!
```

**Task:** Fix to auto-detect based on `closed_top`:
```python
n_reg = 1 if cfg["closed_top"] else 2
```

**Verification:** Run `python benchmark_all.py sequential` and verify open-open instruments now work.

---

## Prompt 8: Remove Dead Code in tmm_optimizer.py

**Context:** `tmm_optimizer.py` has dead code that was never ported to the sequential optimizer.

**Task:** Remove lines 385-394 and 434-437 in `tmm_optimizer.py` (dead code that references obsolete functions).

---

## Prompt 9: Implement Two-Phase Lexicographic Optimization

**Context:** Chalumier's optimizer first filters by constraint satisfaction, then optimizes intonation. We can do the same.

**Task:** Implement in `tmm_optimizer_sequential.py`:

```python
class LexicographicOptimizer:
    def __init__(self, constraint_weight=1e6):
        self.constraint_weight = constraint_weight
    
    def objective(self, params):
        """Two-phase objective: constraints first, then intonation."""
        inst = make_instrument(params)
        cs = constraint_score(...)
        if cs > 0:
            # Constraints violated: return large penalty
            return self.constraint_weight * cs
        else:
            # Constraints satisfied: optimize intonation
            return intonation_score(inst, fingerings)
```

---

## Prompt 10: Validate Against chalumier's Benchmark Results

**Context:** After implementing the above changes, we need to validate that our results match chalumier's.

**Task:**
1. Run `python benchmark_all.py` on all 12 instruments
2. Compare results with chalumier's expected values
3. Document any discrepancies
4. Create a validation report

**Expected results (from chalumier):**
| Instrument | Type | Expected RMS (c) |
|------------|------|------------------|
| Chalumeau C | closed-open | 0.00 |
| Bass Chalumeau Bb | closed-open | 0.00 |
| Soprano Sax Bb | open-open | 0.03 |
| Xaphoon C | open-open | 0.00 |
| Alto Sax Eb | open-open | 0.15 |
| Tin Whistle D | open-open | 0.91 |
| Recorder C | open-open | 1.41 |

---

## Prompt 11: Performance Optimization

**Context:** Some instruments take 100+ seconds to optimize. We need to speed this up.

**Task:**
1. Profile the optimizer to find bottlenecks
2. Implement parallelization for grid search (Phase 2)
3. Optimize the TMM evaluation (possibly using JAX or Numba)
4. Add early stopping when score is below threshold

---

## Prompt 12: Documentation and Examples

**Context:** The code needs better documentation for LLM assistance.

**Task:**
1. Add docstrings to all public functions
2. Create example scripts for common use cases
3. Document the coordinate system convention
4. Document the fingering convention
5. Create a troubleshooting guide for common issues

---

## Summary of Priority Changes

1. **High Priority:**
   - Fix n_register bug in benchmark_all.py
   - Implement cubic mean scoring
   - Implement nearest-resonance search

2. **Medium Priority:**
   - Implement patchInstrument for whistle/flute/shawm
   - Implement cross-fingering support
   - Implement constraint scoring

3. **Low Priority:**
   - Remove dead code
   - Performance optimization
   - Documentation

---

## Validation Checklist

After implementing changes, verify:

- [ ] `python benchmark_all.py` runs without errors
- [ ] All instruments achieve sub-1c RMS
- [ ] Results match chalumier's expected values
- [ ] Code is well-documented
- [ ] No regressions in existing functionality
