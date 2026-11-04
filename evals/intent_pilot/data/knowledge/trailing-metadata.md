---
type: Module Contract
title: Freshness watermark after metadata
sources:
  - id: upstream
    resource: https://github.com/tenequm/pond/commit/dba35944d9d3e3f9ad09e225a15600a8b6953528
generated:
  by: plumb-pilot/0.1
---

# Intended behavior

Trailing metadata records may have no timestamp. The freshness watermark must come from the last timestamped record, walking backward past those metadata records instead of inspecting only the literal final line.[^upstream]

# Scope

Claude Code adapter; audit this behavior only. This is a retrospective analyst-curated interpretation, pending maintainer review.

[^upstream]: Original corrective explanation: https://github.com/tenequm/pond/commit/dba35944d9d3e3f9ad09e225a15600a8b6953528
