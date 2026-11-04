fix(claude-code): ingest forked subagent transcripts

A forked subagent transcript (Claude Code >= 2.1.117 `/fork`, default-on
from 2.1.161) opens with a `fork-context-ref` header row that carries no
`sessionId`; the id first appears on the following message row. The
adapter required `sessionId` on record 0, so it dropped the entire
transcript as "line 1 missing sessionId" - silently losing every forked
subagent's conversation (spec.md#adapter-integrity-no-silent-drops).

Scan the rows for the first `sessionId` instead of demanding it on
record 0. Subagents derive their id from the path regardless, so they
tolerate the id being absent entirely; only a top-level session still
requires one. The headerless first row now flows through the existing
non-message path and is preserved as a System message, so the whole
transcript - header included - round-trips native restore.

Adds a sanitized real fork transcript to the fixture corpus (covered by
native restore + plan) and a focused regression test that fails on main.
