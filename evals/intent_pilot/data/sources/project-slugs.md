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

## The other two adapters, both re-checked rather than assumed

- **pi**: the real divergence was not `\`/`:` — those were already
mapped — it was **UNC**. `sessionDirectoryName` strips exactly one
leading separator (`/^[/\\]/`, no `g` flag); pond used
`trim_start_matches`, which eats both, so every `\\host\share` project
encoded to a directory pi would never look in.
- **opencode**: needed nothing, contra the plan. Its encoder already
collapses everything non-alphanumeric, and the result lands in a JSON
`projectID` field, never a path segment. Now documented so it does not
get "fixed" later.

## Cowork store probe: the plan's MSIX claim was wrong

§3.5 asserted the Windows desktop app is MSIX-packaged and that the
store is **not** `%APPDATA%\Claude`. Checked against a real Windows 11
install running Claude 1.30096.1: `Get-AppxPackage *Claude*` returns
nothing, `%LOCALAPPDATA%\Packages` has no Claude entry, and the app
ships as a per-user Squirrel install under
`%LOCALAPPDATA%\AnthropicClaude` — so Electron's `userData` is never
virtualized. `%APPDATA%\Claude\local-agent-mode-sessions` exists and is
the real path.

It now leads the probe order. The MSIX glob stays as a secondary for the
Store channel, still unverified against a packaged install and written
to find nothing rather than find wrong.

## The Windows fixture gate is closed with a real capture

§3.5 held claude-code Windows ingest behind a real native-Windows
corpus. Rather than scrub a personal corpus, the fixture was
**generated** on a Windows 11 box by Claude Code 2.1.232 itself, from a
`cwd` of:

```
C:\dev\pond fixture_demo.v2
```

One path deliberately carrying a drive colon, backslashes, a space, an
underscore and a dot — every character class the rule collapses, in a
single capture. Claude Code stored it as `C--dev-pond-fixture-demo-v2`,
matching `encode_project` exactly.

Two sessions committed: a plain one, and a two-subagent one confirming
`<parent>/subagents/agent-<hash>.jsonl` + `.meta.json` is **identical to
posix**. Also settled: transcripts are **LF, not CRLF**, and the slug is
stable across Claude Code 2.0.76 and 2.1.232.

The fixture lives in its own root so the many tests ingesting the
existing corpus keep their counts. Sole edit to the capture: the
`%LOCALAPPDATA%\Temp` Task output paths had their user component
replaced with `user` — recorded in the fixture doc comment and the
commit message so nobody mistakes it for byte-verbatim.

## Every adapter's Windows path, verified rather than assumed

Prompted by the MSIX miss, each tool's own path resolution was read
rather than trusting pond's assumption:

| adapter | Windows path | evidence |
|---|---|---|
| claude-code | `%USERPROFILE%\.claude\projects` | field-verified (real
corpus) |
| claude-desktop-app | `%APPDATA%\Claude\...` | field-verified (MSIX
claim disproved) |
| oh-my-pi | `~/.omp/agent/sessions` | field-verified (#147, 331
sessions) + source |
| codex-cli | `CODEX_HOME`, else `dirs::home_dir()/.codex` | source |
| openclaw | `join(homedir(), ".openclaw")` | source |
| hermes | `HERMES_HOME`, else `Path.home()/".hermes"` | source |
| pi-coding-agent | `homedir()`-rooted | source |
| opencode | `~/.local/share/opencode` verbatim | source (xdg-basedir) |
| nanoclaw | checkout-relative `data/v2-sessions` | source |

The two libraries that would have made this a real problem are absent:
hermes uses plain `Path.home()` rather than `platformdirs`, and nothing
uses npm `env-paths`. Either would have relocated the store to
`%LOCALAPPDATA%`/`%APPDATA%`.

**On nanoclaw specifically:** its `HOME`-first line (`process.env.HOME
|| os.homedir()`) governs only `~/.config/nanoclaw/*-allowlist.json`,
which pond never reads. The session store is
`path.resolve(process.cwd(), 'data')` - relative to the checkout, not to
home - so pond's probe is an explicitly best-effort guess at where the
repo was cloned, and the configured path is the real answer. No
home-resolution divergence applies to it.

## oh-my-pi subagents were ingesting as top-level sessions

Found by installing omp on the Windows box and running a real session
with subagent fan-out. omp keeps a session's spawned children in an
artifacts directory named after its own file - `<dir>/<name>.jsonl`
beside `<dir>/<name>/<AgentId>.jsonl` - and the child header is a plain
v3 session with its own id and **no parent field at all**. pond ingested
each as an independent top-level session, so every omp subagent ranked
in default search as if it were a real conversation, against the rule
that keeps subagents out.

The path is the only link, so it is derived from the path - the same
rule claude-code's `subagents/` layout already follows, not synthesis.
The parent id is **read from the neighbouring file's own header**, never
parsed out of the directory name: omp nests unconditionally
(`leaseArtifacts` gives every subagent its own directory on spawn, and
`session-manager.ts` walks up to eight levels) and agent ids keep `_`
(omp sanitizes to `[A-Za-z0-9_-]`), so splitting on `_` invents a parent
for nested children and drops the link for the rest. Reading the header
is correct at any depth.

`source_agent` becomes the fixed `oh-my-pi/subagent`, matching
`claude-code/subagent` - the leaf name is a per-invocation
`generateTaskName()` value and would make the taxonomy unbounded.

Verified on the real corpus, not only the fixture: the two subagents
from that run link to their parent and drop out of default search, which
reports `148 nearest messages (160 searchable in scope)`.

## CI: the kache version is pinned

The action's default resolves the latest kache at run time, so an
upstream cache-key bump could invalidate the Windows build cache with no
commit here - which is exactly what 0.14.0 did, costing a 138 min run
against 9.5 min warm. Pinned to `v0.14.2`, matching how
`.github/actions/bootstrap` already pins `KACHE_VERSION` for Linux.

## Deliberately out of scope

Cowork **ingest** on Windows. The store name is the reason:
`local-agent-mode-sessions` fills only for **local** agent mode, and
Cowork runs in the cloud by default — a Cowork session launched on the
box wrote no `audit.jsonl` at all. The ingest path is
platform-independent (same reader the macOS fixture covers); only the
store location was Windows-specific, and that half is now tested.

## Verification

| gate | result |
|---|---|
| Windows native (`x86_64-pc-windows-msvc`, real hardware + CI) | green
|
| macOS | 307 lib + 41 bin + 89 integration, 0 failed |
| `clippy --locked --all-targets -D warnings` | clean |
| `cargo fmt --check` | clean |

Plan section 3.7's manual gate is also closed on real hardware: `pond
init`, first sync against a local store (6 sessions, embeddings on CPU),
`pond search`, and `pond mcp` registration into a real Claude Code
(`pond: pond mcp - Connected`). Ctrl-C inside a cliclack prompt was
driven under a Windows ConPTY - it cancels, exits 1, and writes nothing
at all.

All four adapters present on that machine were exercised end to end:
claude-code, claude-desktop-app (probe only - see below), oh-my-pi, and
codex-cli 0.147.0, each discovered with no config help and each
preserving its Windows `cwd` with backslashes intact.

Both new fixture tests pass **on Windows**, which is the meaningful run
— `relative_path.starts_with("C--dev-pond-fixture-demo-v2")` is exactly
the kind of assertion that can pass on macOS and fail on Windows.

Beyond the suite, the encoding change was checked against the live
corpus: restoring a session whose project is
`/Users/.../Library/Application Support/Claude/...` now lands in a slug
with the space collapsed; a native claude-code session still restores to
its captured `project_dir` unchanged; and a foreign codex session
restores fine.
