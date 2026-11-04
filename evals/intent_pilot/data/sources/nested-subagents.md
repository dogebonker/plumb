fix(adapter): recognize nested workflow-subagent transcripts

Claude Code's workflow runner nests a subagent transcript one level deeper
than the historical flat layout:

  <parent_uuid>/subagents/workflows/<wf-id>/agent-<hash>.jsonl

The claude-code adapter only matched the flat `subagents/agent-<hash>.jsonl`
shape, so a nested file fell through to its content `sessionId` (the
parent's) and either tripped the immutable-project reject (cwd-shifted) or
silently merged into the parent (same cwd).

The child id is now derived from the file's full path under the `subagents/`
ancestor at any depth (`<parent>/workflows/<wf-id>/agent-<hash>`), normalized
to `/` so it stays canonical on every platform and round-trips on native
restore. An unrecognized `subagents/` layout fails visibly as a counted
Unsupported skip and is kept out of the freshness gate, so it is never merged
under a borrowed id and re-surfaces on every sync until pond is updated.

Also mirror the test layout under tests/integration/adapter/ and add
nested-workflow fixtures plus regression coverage.
