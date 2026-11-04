---
type: Module Contract
title: Forked subagent transcript identity
sources:
  - id: upstream
    resource: https://github.com/tenequm/pond/commit/06a2d2725ede538d5016dcae4a6af178fd636e48
generated:
  by: plumb-pilot/0.1
---

# Intended behavior

A forked transcript may start with a fork-context-ref record without a sessionId. A subagent's identity comes from its path, even if no record carries sessionId; top-level sessions may obtain their id from a later record. Preserve the leading header instead of dropping the transcript.[^upstream]

# Scope

Claude Code adapter; audit this behavior only. This is a retrospective analyst-curated interpretation, pending maintainer review.

[^upstream]: Original corrective explanation: https://github.com/tenequm/pond/commit/06a2d2725ede538d5016dcae4a6af178fd636e48
