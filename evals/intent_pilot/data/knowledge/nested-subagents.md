---
type: Module Contract
title: Nested workflow subagent identity
sources:
  - id: upstream
    resource: https://github.com/tenequm/pond/commit/94b9beeff58d4badc96017b66df32071e01daf1f
generated:
  by: plumb-pilot/0.1
---

# Intended behavior

A transcript beneath <parent>/subagents/workflows/<workflow>/agent-<hash>.jsonl must have its own path-derived child identity, preserving the workflow segments. Do not merge it under the parent's content sessionId. Native restore must preserve the nested path. Unrecognized subagent layouts must fail visibly rather than borrowing the parent's identity.[^upstream]

# Scope

Claude Code adapter; audit this behavior only. This is a retrospective analyst-curated interpretation, pending maintainer review.

[^upstream]: Original corrective explanation: https://github.com/tenequm/pond/commit/94b9beeff58d4badc96017b66df32071e01daf1f
