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

> **Known discrepancy (finding C1, commit `38782b1`):** `backend/archived_optimizers/optimizer_global.py:385` comments "open from LAST index (nearest bell)", which inverts the canonical indexing above (hole index 0 = nearest the bell). The file sits in `archived_optimizers/`, declared frozen in its `__init__`; documented here, not modified.

## Units and Speed of Sound

### Units by Module

| Module | Length unit | Speed of sound |
|---|---|---|
| `tmm_acoustics.py` (core TMM) | mm | `SPEED_OF_SOUND = 346100.0` mm/s |
| `tmm_acoustics_jax.py` | mm | `346100.0` mm/s |
| `two_phase_optimizer.py` | mm | imports `SPEED_OF_SOUND` |
| `pareto_optimizer.py` | mm | via TMM |
| `modular_components.py` | mm | `343000.0` mm/s |
| `tone_hole_corrections.py` | mm | `343000.0` mm/s |
| `bore_optimizer_lbfgs.py` | m (`unit="m"`) | `331.3 + 0.606 * temperature` m/s (line 188) |
| `mouthpiece_models.py` | m | `343.0` m/s |
| `trumpet_openwind.py` (OpenWInD) | m | `343.0` m/s |

### Canonical Reference

At 20 °C, c = 331.3 + 0.606·T m/s → **343.4 m/s (343400 mm/s)**.

### Known Discrepancy (finding B1, commit `38782b1`)

The core TMM constant `346100.0` mm/s (346.1 m/s) corresponds to ≈ 24.4 °C, not 20 °C. Modules using `343000.0`/`343.0` (20 °C) differ by **~15.6 cents (0.9%)**. Unification is deferred; tests assert consistency with the temperature formula rather than a hardcoded constant.

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
