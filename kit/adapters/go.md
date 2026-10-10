# Adapter: Go

## Stubs
- Types, interfaces and constants: exactly as written.
- Functions and methods: the frozen signature with the body `panic("stub")`.
- Imports: whatever the signatures need.

## Typecheck
`go build ./... && go vet ./...` in the module directory
