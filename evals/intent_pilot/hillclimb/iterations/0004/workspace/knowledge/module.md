---
type: Module Contract
title: Session restore
sources:
  - id: governing-decision
    resource: ../sources/decision.md
---

# Current intended behavior

Quoted from ../sources/decision.md (the governing current agreement):

> Claude Code's actual rule collapses every non-alphanumeric character.
> The regex counts UTF-16 code units: an astral character collapses to two dashes.
> NFC normalization does not apply. Claude Code normalizes the memory path,
> not the session path. Restore must preserve the native session-path convention.
>
> For this replay, alphanumeric means ASCII a-z, A-Z and 0-9. Each other UTF-16
> code unit becomes one dash. Preserve ASCII letters and digits as given.

The earlier statement ("replace slashes and dots only", "Normalize Unicode to
NFC") came from ../sources/proposal.md, an unapproved future proposal that
states it does not change the current agreement.

# Responsibility

The public restore_path function delegates project encoding to code/slug.py.
When revising this contract, preserve the governing decision's exact wording
as a quotation and link to its captured source. Generated knowledge is not a
new independent authority.
