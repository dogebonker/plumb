# Adapter: Python

## Stubs
- Classes, protocols, dataclasses and type aliases: exactly as written, with full type hints.
- Functions and methods: the frozen signature with the body `raise NotImplementedError`.
- Imports: whatever the signatures need.

## Typecheck
The module's type checker (`uv run pyright <files>` or `uv run mypy <files>`); without one, `python -m py_compile <files>`
