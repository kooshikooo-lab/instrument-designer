# Physics First Principles

## Core Rule
**Physics and research always take precedence over code results.**

If the code produces results that contradict established acoustics, the code is wrong - not the physics.

## Tone-Hole Fingering Convention (Verified from Chalumier + Woodwind Acoustics)

For a **closed-open pipe** (clarinet, bass clarinet):

### Coordinate System (matching chalumier)
- **Position 0.0 = bell (open end)**
- **Position = length = reed/mouthpiece (closed end)**
- Hole index 0 = nearest the **bell**
- Hole index N-1 = nearest the **reed**

### Ascending Scale = Open from Bell End First
- All holes closed = **lowest note** (longest effective tube)
- Open hole nearest bell first = **small pitch rise** (hole is near pressure node)
- Progressively open holes toward reed = **pitch rises further**
- **NEVER open from reed end first** - this creates huge pitch jumps

### Key Physics
- The bell is the **open end** (pressure node, phase = 0.5)
- The reed is the **closed end** (pressure antinode, phase = integer at resonance)
- Opening a hole near the bell creates a **small perturbation** (near pressure node)
- Opening a hole near the reed creates a **large perturbation** (near pressure antinode)
- For chromatic steps, open from bell end first

### TMM Walk Direction
- Walk from bell (open end) toward reed (closed end)
- Phase starts at 0.5 (open end = bell)
- Phase accumulates toward reed
- Resonance when phase is integer at reed (closed end)

## Verification Sources
- Chalumier (Mark C. Chu-Carroll, Paul Francis Harrison) - Apache 2.0
- Nederveen, "Acoustical Aspects of Woodwind Instruments"
- Fletcher & Rossing, "The Physics of Musical Instruments"
- Campallotto et al., "Physical modeling of wind instruments" (OpenWInD)

## When Code Results Conflict with Physics
1. Check the TMM walk direction matches chalumier
2. Check the coordinate system (position 0 = bell)
3. Check fingering direction (bell-first ascending)
4. Check phase boundary conditions (0.5 at open end, integer at closed end)
5. Do NOT trust optimizer results that require physically impossible configurations
