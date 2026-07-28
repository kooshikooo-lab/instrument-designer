# Coding Standards

## Documentation

Every function, module, and class must have a docstring describing:
- What it does (purpose)
- Parameters (name, type, meaning)
- Returns (type, meaning)
- Coordinate system convention (if applicable)

### Module docstrings

Every `.py` file starts with a docstring describing the module's purpose, usage examples, and key architecture notes.

### Function docstrings

Use NumPy-style docstrings:

```python
def my_function(param1: int, param2: str) -> bool:
    """Short description.

    Longer description if needed.

    Parameters
    ----------
    param1 : int
        Description of param1.
    param2 : str
        Description of param2.

    Returns
    -------
    bool
        Description of return value.
    """
```

### Coordinate systems

When a function bridges coordinate systems (chalumier, OpenWind, TMM), document the convention at the function entry point:

```python
def convert(input_data):
    """Convert chalumier output to OpenWind format.

    Chalumier coordinates:
    - Bore: 0=bell, L=mouthpiece
    - Holes: numbered from bell (hole1=nearest bell)

    OpenWind coordinates:
    - Bore: 0=mouthpiece, L=bell
    - Holes: numbered from mouthpiece (hole1=nearest mouthpiece)
    """
```

### Changelog in function headers

If a change might be wrong or experimental, add a note:

```python
def experimental_function():
    """Description.

    NOTE 2026-07-28: This uses cubic mean L3 instead of RMS.
    The change was made to match chalumier scoring but needs
    validation against real instrument measurements.
    """
```

## Imports

- Standard library first, then third-party, then local
- Absolute imports preferred (`from backend.tmm_acoustics import ...`)
- No relative imports outside the same subpackage

## Type Hints

All function signatures must include type hints. Use `|` for union types (Python 3.10+):

```python
def f(x: int | float) -> str | None:
```

## Code Style

- No comments in implementation code (docstrings only)
- 4-space indentation
- Line length: 100 characters preferred, 120 max
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants

## Error Handling

- Return sentinel values (e.g. `1e10`) for optimization failures
- Catch specific exceptions, not bare `except:`
- Use `traceback.print_exc()` when logging unexpected failures

## Testing

- All test files go in `tests/`
- Benchmarks and debug scripts go in `scripts/`
- Core source code never imports from tests/ or scripts/

## Architecture Rules

- `backend/` root: ONLY core source modules (no test/debug/benchmark files)
- `tests/`: ALL test files
- `scripts/`: ALL utility/debug/benchmark scripts
- `docs/`: ALL documentation, prompts, session logs
- Root: ONLY config files (pyproject.toml, README.md, etc.)
- The solver/optimizer should NOT know specific instrument types — only acoustic parameters
- Fingering charts are independent data structures from bore geometry
