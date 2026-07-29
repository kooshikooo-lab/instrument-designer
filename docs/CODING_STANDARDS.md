# Coding Standards

## Type Hints
- All function signatures must have type hints for parameters and return values
- Use `from __future__ import annotations` for forward references
- Use `Sequence[T]` over `List[T]` for function parameters
- Use `| None` syntax (Python 3.10+) over `Optional[T]`

## Docstrings
- All public functions and methods must have NumPy-style docstrings
- Required sections: Parameters, Returns
- Optional sections: Raises, Notes, Examples, See Also

## Error Handling
- Optimization failures use sentinel values (1e10), not exceptions
- No bare `except:` clauses — always specify exception type
- Use `try/except` around known-failure operations only
- Validation errors raise `ValueError` with descriptive messages

## Imports
- Standard library first, third-party second, project modules third
- One import per line for standard library; group imports by origin
- Avoid `from module import *`
- Local imports inside functions for optional dependencies

## Testing
- All test files go in `tests/`, not `test_output/`
- Test function names: `test_<function_name>_<scenario>`
- Use pytest fixtures for shared setup
- Each test tests exactly one behavior

## Code Style
- 100 character line limit
- Descriptive variable names over abbreviations (except physics constants)
- Class names: PascalCase; functions/variables: snake_case; constants: UPPER_CASE
- No trailing whitespace; one blank line at end of file

## Module Structure
- One responsibility per module (~500 line limit)
- Public API at top of file, implementation details below
- `__all__` defined for public exports
