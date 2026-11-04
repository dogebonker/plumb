---
type: Module Contract
title: Project directory encoding
sources:
  - id: upstream
    resource: https://github.com/tenequm/pond/commit/a218ef33cb337b2ec8c41bb9b23b02fb76231559
generated:
  by: plumb-pilot/0.1
---

# Intended behavior

Restore must use Claude Code's project slug: each character outside ASCII a-z, A-Z and 0-9 becomes a dash for each UTF-16 code unit. Underscores, spaces, slashes, dots, colons and backslashes must not survive. An astral character becomes two dashes. Do not apply NFC normalization.[^upstream]

# Scope

Claude Code adapter; audit this behavior only. This is a retrospective analyst-curated interpretation, pending maintainer review.

[^upstream]: Original corrective explanation: https://github.com/tenequm/pond/commit/a218ef33cb337b2ec8c41bb9b23b02fb76231559
