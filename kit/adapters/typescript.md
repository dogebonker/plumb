# Adapter: TypeScript

## Stubs
- Types and interfaces: exactly as written.
- Functions and methods: the frozen signature with the body `throw new Error("stub");` (it type-checks against any return type).
- Imports: whatever the signatures need, from the paths the module already uses.

## Typecheck
`npx --no-install tsc --noEmit -p <the module's tsconfig.json>`
