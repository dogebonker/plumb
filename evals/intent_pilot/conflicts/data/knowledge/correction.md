---
type: Intent Source
title: correction
plumb_role: scenario_defined
sources:
  - id: original
    resource: https://github.com/tenequm/pond/commit/a218ef33cb337b2ec8c41bb9b23b02fb76231559
---

fix(adapter): correct project-slug encoding for Windows and posix

Plan §3.5, the last phase-1 delta after PR A (#152) and PR B (#155). The
plan called this "the adapters PR"; what it turned into is a correctness
fix that lands on **every** platform, not just Windows.

## The headline: this fixes a live bug on macOS and Linux

`encode_project` mapped only `/` and `.` to `-`. Claude Code's actual
rule collapses **every** non-alphanumeric character, so `_` and spaces
were surviving into the project slug — and every restore of such a
project has been writing to a directory Claude Code will not open.
Underscore-bearing project paths are common: 31 of them in a 14k-session
corpus.

The rule is no longer inferred. It is read off Claude Code's own bundle:

```js
vJ(cwd) = join(projectsDir, _b(cwd))
_b = (A) => A.replace(/[^a-zA-Z0-9]/g, "-")
```

Cross-checked against 181 real posix project directories (178 exact; the
3 misses are a worktree `cwd` drift and two `ssh-<uuid>` remote
sessions, which are not path-derived at all), then confirmed on native
Windows — see the fixture below.

Two subtleties the naive port would miss:

- **The regex is un-`u`-flagged**, so it counts UTF-16 code units: an
astral character collapses to *two* dashes. Handled with `len_utf16()`,
not one dash per `char`.
- **NFC normalization does not apply.** Claude Code normalizes the
*memory* path, not the session path. The plan said NFC; the bundle says
otherwise.

Neutralizing `\` and `:` is what makes a Windows slug a legal path
segment at all — PR B's `validate_path_id` now rejects both, so a
Windows-captured session previously failed restore outright.

## Fallback decoder

For the one path that needs it — a transcript where no row carries
`cwd`. It cannot undo a lossy collapse, but it now recovers posix,
drive-letter and UNC prefixes instead of emitting `C//Users/...`. The
lossiness is asserted outright in the tests rather than papered over.

