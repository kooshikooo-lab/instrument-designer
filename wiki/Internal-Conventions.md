# Code Conventions

## Python

- **Version:** 3.12+
- **Style:** PEP 8, 4-space indentation
- **Type hints:** Required on function signatures
- **Docstrings:** Google style
- **Imports:** stdlib → third-party → local (alphabetical within groups)

## File Naming

- `snake_case.py` for Python files
- `CamelCase.tsx` for React components
- `kebab-case.css` for stylesheets

## Testing

- Test file: `tests/test_*.py`
- Run: `python -m pytest tests/`
- Property tests: `tests/test_properties.py` (4 tests, all must pass)

## Git

### Commit Messages
- Format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Scope: module name (e.g., `tmm`, `optimizer`, `ui`)
- Example: `feat(tmm): add KeefeLoss viscothermal model`

### Branch Naming
- `laptop` — active development
- `main` — stable shared
- `option-a-*` — Tauri UI features
- `experiment/*` — research branches
- `fix/*` — bug fixes
- `refactor/*` — architecture changes
- `ui/*` — UI experiments

## Coordinate Convention

**Position 0 = bell, Position L = reed.** Non-negotiable. Matches chalumier.

## Metric Convention

**Absolute RMS** is the primary metric. Report additional metrics (MAD, SD, max) alongside it. Never use median-corrected RMS as the primary metric.

## Documentation

- Wiki: User-facing (installation, library) + Internal (architecture, research)
- `ROADMAP.md`: Master roadmap with phases
- `WIKI.md`: Comprehensive technical reference
- `chat-logs/`: Session logs with research findings
