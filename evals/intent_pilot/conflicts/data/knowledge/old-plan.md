---
type: Intent Source
title: old-plan
plumb_role: scenario_defined
sources:
  - id: original
    resource: https://github.com/tenequm/pond/blob/95e8ce4d88a1e9f210811ce8546e9b95503d3ce1/docs/plans/2608-13-windows-support-plan.md
---

  2. **Slug decode for the fallback path**, from the evidence model (issues #33140, #14088, third-party implementations): drive-letter colon -> `-`, each `\` -> `-` (giving `C--Users-foo-bar`), dots/spaces/underscores -> `-`, UNC -> `--host-share-...`, drive-letter case NOT normalized (match case-insensitively), NFC-normalized, and mapped network drives can produce two slugs for one project. One encode/decode function pair handling posix and Windows forms.
