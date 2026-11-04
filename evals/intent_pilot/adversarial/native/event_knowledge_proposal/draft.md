---
type: Module Contract
title: Account closure and audit
generated:
  by: plumb-native-simulation/1
sources:
  - id: retention-current
    resource: ../sources/linear-legal.md
  - id: retention-prior
    resource: ../sources/confluence-retention.md
  - id: event-current
    resource: ../sources/notion-event.md
  - id: v2-proposal
    resource: ../sources/linear-v2.md
---

# Current intended behavior

The separately supplied simulated legal-owner decision selects LEGAL-203 for
retention of current v1 records:

> All account closure audit records must be retained for exactly 7 days, including account.closed.v1 records.[^retention-current]

> No migration to v2 is required to apply this policy.[^retention-current]

The account command checks both account ownership and `can_close_account` before
closing the account and publishing. The audit consumer does not repeat that
command authorization check.[^retention-prior]

> account.closed.v1 carries account_id only and is consumed by the audit service.[^event-current]

# Implementation links

`code/accounts/close.py` invokes `code/events/publisher.py`. The publisher emits
`account.closed.v1` with `account_id`; `code/audit/consumer.py` subscribes to that
topic and archives the account ID with `retention_days=7`.

# Superseded and planned knowledge

The old 30-day Confluence retention clause is superseded for this simulated
resolution. Its authorization-boundary statement remains unchanged. The old
missing-email incident is historical. The v2 proposal to add email, duplicate
consumer authorization and 90-day retention has not been adopted.[^v2-proposal]

No actual human verification event is asserted: this is a controlled simulation.
Captured source documents remain unchanged.

[^retention-current]: Captured Linear LEGAL-203 revision 8.
[^retention-prior]: Captured Confluence account audit revision 22.
[^event-current]: Captured Notion event contract revision 11.
[^v2-proposal]: Captured Linear EVENTS-421 revision 2, backlog proposal.
