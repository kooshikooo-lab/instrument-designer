# Coding Standards

## Python

- **Version:** 3.12+
- **Style:** PEP 8, 4-space indentation
- **Type hints:** Required on all function signatures
- **Docstrings:** NumPy/Google style
- **Imports:** stdlib → third-party → local (alphabetical within groups)
- **Line length:** 100 characters max (soft), 120 hard

## File Naming

- `snake_case.py` for Python files
- `CamelCase.tsx` for React components
- `kebab-case.css` for stylesheets

## Testing

- Test files go in `tests/` — NOT `test_output/` or any other directory
- Test file pattern: `tests/test_*.py`
- Run: `python -m pytest tests/`
- Property tests: `tests/test_properties.py` (4 tests, all must pass)

## Git

### Commit Messages
- Format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Scope: module name (e.g., `tmm`, `optimizer`, `ui`, `api`)
- Example: `feat(tmm): add KeefeLoss viscothermal model`

### Branch Naming
- `laptop` — active development
- `main` — stable shared
- `option-a-*` — Tauri UI features
- `experiment/*` — research branches
- `fix/*` — bug fixes
- `refactor/*` — architecture changes
- `ui/*` — UI experiments

## Module Structure

- Every `.py` file has exactly one responsibility (Law 8)
- If a module exceeds ~500 lines, split it
- Pipeline modules must be thin orchestrators (Law 5)
- GUI never contains physics (Law 6)

## Error Handling

- Optimization failures use sentinel values (1e10), not exceptions
- No bare `except:` clauses
- Validate inputs at function boundaries

## Imports

- No unused imports — run static analysis after every refactoring
- When extracting functions to new modules, verify which imports are consumed

## Documentation

- All functions have type hints
- All functions have NumPy-style docstrings
- Architecture changes need an ADR in `docs/ARCHITECTURE_DECISIONS.md`
- Coordinate conventions documented at function entry points
