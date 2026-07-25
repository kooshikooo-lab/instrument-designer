# AcousticElement Hierarchy — Experimental Design

## Goal
Replace woodwind-specific `Port`/`Tonehole`/`RegisterVent` with general `AcousticElement` hierarchy that supports all wind instrument types.

## Current (Woodwind-Specific)
```
Port (base)
├── Tonehole (length_control)
├── RegisterVent (mode_selection, harmonic=3)
└── BrassValve
```

## Proposed (General)
```
AcousticElement
├── Waveguide (was Segment) — cylindrical/conical bore sections
├── Junction — connections between waveguides
├── SideBranch (was Tonehole, RegisterVent, BrassValve)
│   ├── OpenHole (standard tonehole)
│   ├── RegisterHole (suppresses fundamental, promotes harmonic N)
│   ├── BrassValve (piston/rotor)
│   ├── TuningSlide
│   ├── Leak (pad leak, crack)
│   └── HelmholtzResonator
├── Radiation (bell, open end)
├── Excitation (reed, lip, air jet)
└── LossModel (viscothermal, pad compliance)
```

## Key Design Principles

1. **No instrument knowledge in solver** — elements carry their own type metadata
2. **Unified interface** — all elements implement `transfer_matrix(wavelength)` or `shunt_impedance(wavelength)`
3. **Optimization metadata** — separate from physics:
   ```python
   class SideBranch(AcousticElement):
       role = "length_control" | "mode_selection" | "tuning"
       optimize_for = "effective_length" | "harmonic_suppression" | "pitch_correction"
   ```

## Benefits
- Supports reeds, lips, air jets without special cases
- Brass valves become first-class elements
- Tuning slides, leaks, resonators naturally fit
- Future: non-cylindrical side branches, pad compliance, cork resonance

## Migration Path
1. Add `AcousticElement` base class alongside `Port`
2. Implement `Waveguide`, `SideBranch` subclasses
3. Update `AcousticNetwork` to store `elements: List[AcousticElement]`
4. Add adapter: `Port.to_element()` for backward compatibility
5. Update solvers to iterate over elements

## ChatGPT Reference
From 2026-07-24 architecture review: "Removes woodwind-specific terminology, supports reeds, valves, piston ports, rotor valves, tuning slides, leaks, pad compliance, Helmholtz resonators."