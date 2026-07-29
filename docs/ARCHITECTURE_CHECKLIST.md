# Architecture Checklist

Pre-flight and pre-commit checklist for AI agents. Run this before writing code and again before finishing.

---

## Pre-Flight (before writing code)

- [ ] Read `docs/AI_CONSTITUTION.md` and identify applicable laws
- [ ] Read `docs/ARCHITECTURE.md` ÔÇö understand coordinate systems and conventions
- [ ] Read `docs/ARCHITECTURE_DECISIONS.md` ÔÇö understand why the architecture is what it is
- [ ] Identify the subsystem you are modifying
- [ ] Search existing code for what you need (function, class, utility)
- [ ] Search existing tests
- [ ] Search existing documentation
- [ ] Search existing interfaces
- [ ] Produce a short implementation plan

## Pre-Commit (before finishing)

### No duplication
- [ ] No duplicate code created
- [ ] No duplicate interfaces created
- [ ] No duplicate data structures (coordinate systems, units, fingerings)

### Architecture integrity
- [ ] No new coordinate systems introduced
- [ ] No hidden physics (physics belongs in `backend.physics`, not in optimizers or pipelines)
- [ ] No mixing of GUI concerns with backend concerns
- [ ] Module boundaries respected (one responsibility per file)
- [ ] Public APIs preserved or explicitly deprecated

### Quality
- [ ] Tests updated or added
- [ ] Documentation updated
- [ ] No hardcoded instrument-specific assumptions in general code
- [ ] All functions have type hints
- [ ] All functions have NumPy-style docstrings
- [ ] Error handling uses sentinel values (1e10) for optimization failures, not exceptions
- [ ] No bare `except:` clauses

### If a mistake was made
- [ ] Log it in `docs/AI_FAILURE_PATTERNS.md` so it is not repeated
- [ ] Fix the mistake before committing
