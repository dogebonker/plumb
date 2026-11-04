---
type: Intent Source
title: corrected-plan
plumb_role: scenario_defined
sources:
  - id: original
    resource: https://github.com/tenequm/pond/blob/a218ef33cb337b2ec8c41bb9b23b02fb76231559/docs/plans/2608-13-windows-support-plan.md
---

     - **The claude-code slug rule is no longer a model - it is read off Claude Code's own bundle.** `vJ(cwd) = join(projectsDir, _b(cwd))` with `_b = A.replace(/[^a-zA-Z0-9]/g, "-")`: every non-alphanumeric character becomes `-`. Cross-checked against 181 real project directories (178 exact; the 3 misses are a worktree `cwd` drift and two `ssh-<uuid>` remote sessions, which are not path-derived at all) and against the 14k-session corpus, which contains 31 underscore-bearing project paths and zero with a space.


     - **`\` counts in UTF-16, not chars.** The JS regex is un-`u`-flagged, so an astral character collapses to *two* dashes. `len_utf16()` per character, not one dash per `char`.


     - **NFC normalization does not apply.** Claude Code normalizes the *memory* path (`I_1`), not the session path (`vJ`) - so pond must not normalize either. 3.5's bullet said NFC; the bundle says otherwise, and the bundle wins.


> Status: shipped in PR C, fixture gate included. The corrections the implementation forced - the slug rule read off Claude Code's bundle, the posix underscore bug it exposed, pi's UNC divergence, and opencode/oh-my-pi needing nothing - are recorded under PR C in section 2.1; read that before trusting the bullets below.


  2. **Slug decode for the fallback path**, from the evidence model (issues #33140, #14088, third-party implementations): drive-letter colon -> `-`, each `\` -> `-` (giving `C--Users-foo-bar`), dots/spaces/underscores -> `-`, UNC -> `--host-share-...`, drive-letter case NOT normalized (match case-insensitively), NFC-normalized, and mapped network drives can produce two slugs for one project. One encode/decode function pair handling posix and Windows forms.
