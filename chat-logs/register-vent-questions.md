# Register Vent Modeling Questions

## Context
We're building a TMM-based acoustic model for bass clarinet design. The model uses a bell-first coordinate system where position 0 = bell (open end), position L = reed (closed end).

The register vent is currently modeled as a Port with `is_open` state, like toneholes. But the register vent has fundamentally different behavior than toneholes.

## Questions

### 1. Register Vent Behavior
- In chalumeau register: register vent is CLOSED (covered by player's thumb)
- In clarion register: register vent is OPEN
- Is this correct? Or does the register vent have a different role?

### 2. Register Vent Size
- Current: position 80mm from reed, radius 2.5mm (5mm diameter)
- Research shows: 0.1mm error in register hole radius → ~0.3-0.4 cents intonation error
- Is 5mm diameter optimal? Or should we optimize this?

### 3. Register Vent Position
- Current: 80mm from reed
- Research shows: 0.3mm error in register hole position → ~0-1.8 cents error
- Is 80mm optimal? Or should we optimize this?

### 4. Register Vent in TMM
- Currently: register vent is a Port like toneholes
- Should register vent be treated differently in the TMM model?
- Does the register vent affect all fingerings equally?

### 5. Register Vent vs Toneholes
- Toneholes: open/close to change effective bore length
- Register vent: open/close to change register (fundamental vs overtone)
- Are these fundamentally different mechanisms? Or just different applications of the same physics?

### 6. Register Vent Optimization
- Should we optimize register vent position and size jointly with tonehole positions?
- Or should we optimize register vent separately (after tonehole optimization)?

### 7. Register Vent in AcousticNetwork
- Should register vent be a separate Port type (NodeType.REGISTER_VENT)?
- Or should it be a Port like toneholes (NodeType.TONEHOLE)?

### 8. Register Vent in Fingering
- Currently: register vent state is in Fingering.port_states
- Should register vent state be separate from tonehole states?
- Example: Fingering(name="D3", toneholes=[0,0,0,0,0,0,0], register=True)

## Current Architecture
- Port: physical hole (position, radius, length, node_type)
- Fingering: musical state (name, port_states)
- NodeType: TONEHOLE, REGISTER_VENT, BELL, REED

## Recommendation
Please advise on:
1. How to model register vent in TMM
2. How to separate register vent from toneholes in Fingering
3. Whether to optimize register vent jointly or separately
4. Optimal register vent size and position for bass clarinet
