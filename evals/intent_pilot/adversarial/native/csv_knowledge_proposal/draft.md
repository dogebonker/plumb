---
type: Module Contract
title: Billing CSV export
generated:
  by: plumb-native-simulation/1
sources:
  - id: privacy-current
    resource: ../sources/linear-privacy.md
  - id: billing-prior
    resource: ../sources/notion-export.md
  - id: finance-proposal
    resource: ../sources/confluence-roadmap.md
---

# Current intended behavior

Under the separately supplied simulated privacy-owner decision, PRIV-88 governs
the email column for every invoice export:

> All invoice CSV exports must omit customer_email, including billing support exports.[^privacy-current]

> No exception for can_export_billing actors is approved.[^privacy-current]

Only actors with `can_export_billing` may export. The public API owns that guard;
the internal serializer receives authorized records.[^billing-prior]

# Implementation links

`code/api/export.py` checks permission before invoking
`code/billing/csv_writer.py`. The serializer emits `invoice_id,total_cents` in
the header and corresponding values in every row. It does not emit email.

# Superseded and planned knowledge

The prior Notion requirement to include email is superseded for this simulated
resolution. Its unchanged permission-boundary statement remains relevant.
The 2025 serializer-owned permission check is historical. The second-finance-
reviewer requirement remains an unapproved future proposal.[^finance-proposal]

No actual human verification event is asserted: this document records a
controlled simulation, and the external captures remain unchanged.

[^privacy-current]: Captured Linear PRIV-88 revision l6.
[^billing-prior]: Captured Notion billing export revision n17.
[^finance-proposal]: Captured Confluence roadmap revision c3, not approved.
