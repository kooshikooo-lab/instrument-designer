# AI Constitution

Non-negotiable principles of the Instrument Designer project. These rules override implementation convenience.

---

### Law 1 — Architecture over features

Never damage the architecture to implement a feature. If a feature cannot be added without violating an existing architectural separation, stop and document the conflict before proceeding.

### Law 2 — No architectural invention

If an abstraction is missing, do not invent one. Stop, document what is needed, and request approval. New abstractions must be approved through an Architecture Decision Record (ADR).

### Law 3 — Never duplicate code

Search first. Reuse first. Refactor second. Write new code last. Every function, class, and module in this project exists in exactly one place.

### Law 4 — Geometry is separate from acoustics

`InstrumentGeometry` (`geometry.py`) describes shape and dimensions only. It knows nothing about solvers, impedance, or optimization. Acoustic evaluation is a conversion step (`InstrumentGeometry.to_tmm()`).

### Law 5 — Optimization chooses variables, physics computes results

Pipeline modules (`design_from_wav.py`, `design_from_unconventional.py`) are thin orchestrators. They call shared optimizers (`pareto_optimizer.py`) for search and evaluation. They never re-implement NSGA-II, CMA-ES, or any optimization algorithm.

### Law 6 — The GUI never contains physics

`woodwind_designer/` and `web/` are presentation layers. They import from `backend/` but never implement acoustic computation, optimization, or geometry generation. The physics engine never depends on the GUI.

### Law 7 — One source of truth for every physical quantity

Coordinate systems, units, reference frequencies, and fingerings must never be duplicated. When a quantity exists in multiple representations, one is canonical and all others convert to it. Document the conversion at the function entry point.

### Law 8 — One responsibility per module

Every `.py` file has exactly one responsibility. If a module exceeds ~500 lines or mixes concerns (e.g., sound analysis + optimization), split it by responsibility.

### Law 9 — Document architectural decisions

Every significant decision that affects architecture, interfaces, or data flow must be recorded in `docs/ARCHITECTURE_DECISIONS.md` as an ADR. Silent architectural changes are forbidden.

### Law 10 — When uncertain, stop and ask

Never guess about architecture, coordinate systems, or physical assumptions. Stop, document the uncertainty, and request clarification.
