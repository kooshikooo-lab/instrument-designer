# Register Vent Architecture — ChatGPT Clarification (2026-07-24)

## Key Insight
**Physically, the register vent is a tonehole. Functionally, it is not.**

## Decisions Made

### 1. Behavior
- Register vent suppresses fundamental resonance, allows 3rd harmonic to dominate
- Clarinet is stopped cylindrical pipe: supports f, 3f, 5f, ...
- Chalumeau: register vent closed. Clarion: register vent open. Altissimo: varies.
- Benade (1976): register vent is a "resonance selector, not a pitch generator"

### 2. Position: 80mm from reed — GOOD
- Nondimensional: x/L ≈ 0.05-0.08 for soprano clarinet
- Scaled to bass clarinet (1.2-1.3m): 70-95mm
- 80mm is excellent starting point

### 3. Diameter: 3.5mm (NOT 5mm)
- Measured professional clarinets: 2.5-4mm
- Bass clarinet often 3-4mm
- 5mm vents aggressively — flattens upper notes, reduces first-register stability
- Start at 3.5mm, optimize from there

### 4. Optimization Strategy — STAGED
- Stage 1: Optimize bore + toneholes (register vent closed)
- Stage 2: Optimize register vent (bore+toneholes fixed)
- Stage 3: Joint optimization (all variables)
- Reason: too many coupled variables for joint optimization from scratch

### 5. Does it affect all fingerings equally? NO
- First mode: register vent near pressure antinode → opening greatly weakens fundamental
- Third mode: register vent near pressure node → opening has little effect
- This is WHY one small hole can change register without changing pitch

### 6. NodeType: Separate from TONEHOLE
- Both use same TMM class (same shunt impedance physics)
- Distinction valuable for optimization, UI, CAD export, fingering logic

### 7. Fingering: Register state SEPARATE from tonehole states
```python
Fingering(
    toneholes=[False, False, True, ...],
    register=False
)
```
- Future-proofs: automatic register vents, saxophone octave vents, double vents, harmonic vents

### 8. Follow chalumier closely
- Chalumier changes resonance search during overblowing
- Register vent is BOTH a side hole AND a change in which resonance solver seeks
- Preserve that distinction in our code

### 9. Recommended class hierarchy
```python
class Vent(Port):
    acoustic_model = "side_hole"

class Tonehole(Vent):
    role = "length_control"

class RegisterVent(Vent):
    role = "mode_selection"
    preferred_harmonic = 3
```
- Solver only sees Vent (generic physics)
- Optimizer sees RegisterVent (specialized metadata)

### 10. References
- Benade (1976), Ch. 21-23: register vent placement, standing-wave diagrams
- Nederveen (1998), Ch. 6-8: register-hole sizing, placement, side-branch modeling
- Keefe (1982): shunt-impedance model (applies equally to toneholes and register vents)
- Dalmont, Kergomard et al.: TMM/FEM studies model register vents with same physics, optimize separately
