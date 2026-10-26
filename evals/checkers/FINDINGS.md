# LAY-01 findings

What running the pinned checkers showed, 2026-10-12. Toolchains: Node 22.15.0, Python 3.12.9 (run.sh pins `uv venv --python 3.12`), uv 0.8.15, Go 1.27.1 (`GOTOOLCHAIN=local`) and cargo 1.95.0. F1 to F3 are applied to `kit/layouts/tools.yaml`. Each of O1 to O5, O7 and O8 is a `note:` on its tool there. O6 is kept only here.

## Wrong or incomplete in tools.yaml

### F1. eslint-plugin-import 2.32.0 does not install beside current ESLint

Its peer range stops at ESLint 9, and npm marks every ESLint 9 release as unsupported. A project on ESLint 10 cannot add it without `--legacy-peer-deps`.

```
$ npm install --save-dev --save-exact eslint-plugin-import@2.32.0 eslint@10.11.0
npm error ERESOLVE unable to resolve dependency tree
npm error Found: eslint@10.11.0
npm error peer eslint@"^2 || ^3 || ^4 || ^5 || ^6 || ^7.2.0 || ^8 || ^9" from eslint-plugin-import@2.32.0
$ npm view eslint@9.39.5 deprecated
This version is no longer supported. Please see https://eslint.org/version-support for other options.
```

2.32.0 (2025-06-20) is still the latest release. With eslint@9.39.5 it did enforce the rule.

**Corrected value:** `eslint-plugin-import-x@4.17.1` (2026-06-28, peer `eslint ^8.57.0 || ^9.0.0 || ^10.0.0`). The rule is `import-x/no-restricted-paths` with the same `zones`, and the resolver setting is `import-x/resolver`.

**Applied:** tools.yaml pins `eslint-plugin-import-x@4.17.1` with eslint@10.11.0, and feature-folders.md names it. The LAY-01 checker `eslint-plugin-import-x` runs on a feature-folders fixture. Feature a may not import from `./src/features` except `./a`. The planted `src/features/a/leak.ts` imports feature b and fails with `import-x/no-restricted-paths`.

### F2. steiger 0.7.0 needs Node 22.18 or later

`steiger@0.7.0` declares `engines.node >=22.18.0`, and its dependency `cosmiconfig@10.0.1` declares `^22.18 || >= 24`. On Node 22.15.0, npm warns and steiger still ran correctly on this fixture:

```
npm warn EBADENGINE   package: 'steiger@0.7.0',
npm warn EBADENGINE   required: { node: '>=22.18.0' },
npm warn EBADENGINE   current: { node: 'v22.15.0', npm: '10.9.2' }
```

**Applied:** the steiger install line says `(requires Node >= 22.18.0)`.

### F3. The TypeScript checkers need typescript 6.0.x

TypeScript 7.0.2, the `latest` tag, ships no compiler API.
- **dependency-cruiser:** with TypeScript 7 it cruises nothing and exits 0, even on the planted tree:

  ```
  $ npm install -D dependency-cruiser@18.4.0 typescript@7.0.2 && npx --no-install depcruise src   # planted tree
  ✔ no dependency violations found (0 modules, 0 dependencies cruised)
  ‼ missing-typescript-transpiler: dependency-cruiser detected a TypeScript environment,
      but not a compatible TypeScript compiler (typescript: >=2.0.0 <7.0.0).
  exit 0
  ```
- **ESLint checkers:** `@typescript-eslint/parser@8.71.0` refuses TypeScript 7:

  ```
  $ npm install -D @typescript-eslint/parser@8.71.0 typescript@7.0.2
  npm error ERESOLVE unable to resolve dependency tree
  npm error peer typescript@">=4.8.4 <6.1.0" from @typescript-eslint/parser@8.71.0
  ```

**Applied:** the dependency-cruiser, eslint-plugin-boundaries and eslint-plugin-import-x entries pin `typescript@6.0.3` in their install lines, with a note that explains why.

## Facts the Layout Decision needs when it writes a config

- **O1. On its own, the Go compiler does not enforce direction inside a module.** A nested `internal/` hides one module's parts from its siblings. Inside a module, or across a flat `internal/{domain,adapters}`, only an import cycle stops domain from importing adapters. Evidence: the go-arch-lint fixture plus its planted file, `go build ./...`, exit 0. LAY-01's go-compiler fixture tests the sibling rule: identity's domain imports billing's adapters and fails with `use of internal package ... not allowed`. modular-monolith.md now names go-arch-lint for the layers inside a module.
- **O2. go-arch-lint rejects an empty `mayDependOn: []`.** On the clean tree it exits 1 with `should have ref in 'mayDependOn'/'canUse' or at least one flag of ['anyProjectDeps', 'anyVendorDeps']`. The innermost component must have no `deps` entry, which means it may depend on no component.
- **O3. `go get -tool github.com/fe3dback/go-arch-lint@v1.19.0` rewrites go.mod.** It raised `go 1.24` to `go 1.25.0` and added about 40 indirect requires. The slice that installs it needs go.mod and go.sum in its Allowed files.
- **O4. import-linter needs the project installed.** For a `src/` layout, `lint-imports` with only import-linter installed prints `Could not find package 'shop' in your Python path.` The docs say the root package "must be importable". LAY-01 installs the project (`uv pip install -e .`, as `uv sync` would). Its output names the module (`shop.domain.leak -> shop.adapters.clock (l.2)`), not the file path.
- **O5. eslint-plugin-boundaries 7.2.0: the key is `policies`.** The jsboundaries.dev rule page lists the option as `rules`, but the 7.2.0 source says "`policies` is the current option name; `rules` is kept as a deprecated alias" (`dist/Settings/Rules.js:439`). The README uses `policies`.
- **O6. Cargo compiles a new file only when something names it.** A new `src/leak.rs` is invisible to `cargo check` until a `mod leak;` line is added. A file under `src/bin/` is built on its own, so LAY-01 plants `crates/domain/src/bin/leak.rs`. Cargo is exempt from planting in plumb-slices, so this matters only for this eval.
- **O7. Without the TypeScript resolver, both ESLint checkers pass silently.** I removed the `import/resolver` (boundaries) and `import-x/resolver` (import-x) settings. Then `npx --no-install eslint .` exited 0 on each planted tree. They need `eslint-import-resolver-typescript@4.4.5` under that key.
- **O8. tach allows every import from a module with no `depends_on` key.** I deleted `depends_on = []` from `shop.domain`. Then `tach check` on the planted tree printed `✅ All modules validated!` and exited 0. The innermost module needs `depends_on = []`, which is the opposite of go-arch-lint's rule in O2.

## Guards in run.sh

- **Signatures:** each checker has a rule signature that must appear in the planted output and not in the clean output.
- **Planted files:** every planted file must be named in the output.
- **Pins:** every pin must appear in the checker's tools.yaml entry before anything is installed.
- **Skips:** a skipped stack makes the run exit 2 unless `LAY01_ALLOW_SKIP=1`.

Negative tests, run on a temp copy:
- A wrong cargo signature gives `cargo: FAIL ... signature 'E9999': no`.
- `tach==0.35.2` in tools.yaml gives `tach: FAIL pin tach==0.35.1 is not in tools.yaml python.tach`. Together these two exit 1.
- Taking cargo off PATH gives `cargo: SKIP` and exit 2. With `LAY01_ALLOW_SKIP=1` it exits 0.
