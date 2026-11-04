# OKF: Account closure
Only an actor with can_close_account for their own account may close it. The account service guards the command.
Account service emits account.closed.v1; audit consumer archives the account ID for 30 days.
Sources: sources/confluence-retention.md and sources/notion-event.md.
Historical incident fix: consumers once rejected missing email; v1 no longer carries email.
Planned: move to account.closed.v2 with 90-day archive; not approved.
