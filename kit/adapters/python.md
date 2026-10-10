# Adapter: Python

## Stubs
- Classes, protocols, dataclasses and type aliases: exactly as written, with full type hints.
- Functions and methods: the frozen signature with the body `raise NotImplementedError`.
- Imports: whatever the signatures need.

## Typecheck
The module's type checker: `uv run pyright <files>` or `uv run mypy <files>`. Without a type checker the module stays unchecked.

## BDD
- Run one feature: `uv run behave <feature file>` (behave) or `uv run pytest <test file binding the feature>` (pytest-bdd)
- Step definitions: `rg -n "@(given|when|then|step)\(" <module>`

## Import graph
- `rg -n "^\s*(from|import) " <files>` lists each file's imports

## Dead code
- `uv run vulture <module path>` when vulture is installed
