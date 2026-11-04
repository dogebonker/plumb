---
type: Module Contract
title: Session restore
sources:
  - id: previous-plan
    resource: ../sources/proposal.md
---

# Current intended behavior

Project slugs replace slashes and dots only. Normalize Unicode to NFC.

# Responsibility

The public restore_path function delegates project encoding to code/slug.py.
When revising this contract, preserve the governing decision's exact wording
as a quotation and link to its captured source. Generated knowledge is not a
new independent authority.
