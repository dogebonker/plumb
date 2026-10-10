# Adapter: Go

## Stubs
- Types, interfaces and constants: exactly as written.
- Functions and methods: the frozen signature with the body `panic("stub")`.
- Imports: whatever the signatures need.

## Typecheck
`go build ./... && go vet ./...` in the module directory

## BDD
- Run one feature: the module's `go test` entry that runs godog (`go test -run <its TestXxx> ./<package>`), pointed at the feature file the way that entry reads its paths
- Step definitions: `rg -n "\.(Step|Given|When|Then)\(" <module>`

## Import graph
- `go list -f '{{.ImportPath}}: {{join .Imports " "}}' ./...` lists each package's imports; strip the module path from `go.mod` to compare them with path globs

## Dead code
- `deadcode ./...` (golang.org/x/tools/cmd/deadcode) when installed and the module has a main package, otherwise `golangci-lint run --enable-only unused`
