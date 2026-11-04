---
type: Module Contract
title: Provably empty sessions and workflow journals
sources:
  - id: upstream
    resource: https://github.com/tenequm/pond/commit/6a05cd17f0869967d149df42f0b4b961b3d3c0ee
generated:
  by: plumb-pilot/0.1
---

# Intended behavior

Workflow journal.jsonl control files must be excluded from discovery and must not count as pending sessions. A full-file scan proving there are no timestamped records may classify the file Empty; a tail-only scan without a timestamp cannot prove emptiness and must remain Opaque.[^upstream]

# Scope

Claude Code adapter; audit this behavior only. This is a retrospective analyst-curated interpretation, pending maintainer review.

[^upstream]: Original corrective explanation: https://github.com/tenequm/pond/commit/6a05cd17f0869967d149df42f0b4b961b3d3c0ee
