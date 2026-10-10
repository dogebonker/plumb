# Adapter: Rust

## Stubs
- Structs, enums, traits and type aliases: exactly as written.
- Functions and methods: the frozen signature with the body `todo!()`.
- `use` lines: whatever the signatures need; new modules get their `mod` line in the parent.

## Typecheck
`cargo check --all-targets -p <crate>` (in a single-crate repository, without `-p`)

## BDD
- Run one feature: the module's cucumber harness, `cargo test --test <harness> -- --input <feature file>`
- Step definitions: `rg -n "#\[(given|when|then)" <module>`

## Import graph
- `rg -n "^\s*(pub(\([^)]*\))? )?use " <files>` lists each file's imports, crate-local and from workspace crates

## Dead code
- `cargo check --all-targets -p <crate> --message-format short 2>&1 | rg "never (used|read|constructed)"`
