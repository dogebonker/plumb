# Adapter: Rust

## Stubs
- Structs, enums, traits and type aliases: exactly as written.
- Functions and methods: the frozen signature with the body `todo!()`.
- `use` lines: whatever the signatures need; new modules get their `mod` line in the parent.

## Typecheck
`cargo check --all-targets -p <crate>` (in a single-crate repository, without `-p`)
