# Adapter: TypeScript

## Stubs
- Types and interfaces: exactly as written.
- Functions and methods: the frozen signature with the body `throw new Error("stub");` (it type-checks against any return type, async included).
- Overloads: the overload declarations as written, plus one implementation signature with the stub body.
- Imports: whatever the signatures need, from the paths the module already uses.

## Typecheck
`npx --no-install tsc --noEmit -p <the module's tsconfig.json> --noUnusedLocals false --noUnusedParameters false` (stub bodies leave parameters unused)

## BDD
- Run one feature: `npx --no-install cucumber-js <feature file>`
- Step definitions: `rg -n "(Given|When|Then|defineStep)\(" <module>`

## Import graph
- `npx --no-install depcruise --output-type json <module src>` when dependency-cruiser is installed; otherwise `rg -n "from ['\"](\.|@/)" <files>` lists each file's local imports

## Dead code
- `npx --no-install knip --reporter json` when knip is installed; keep only results in the slice's changed files
