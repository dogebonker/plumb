# Reference decisions and agreement

This is a calibration reference, not either benchmark contestant.

Chosen frontend: semantic vanilla HTML/JavaScript, native dialog, same-origin fetch.
Chosen backend: Python standard-library HTTP server. Chosen database: SQLite at
DATABASE_PATH. No third-party dependencies; the reference prioritizes repeatable
local grading over production deployment. A framework would add installation work
without changing this calibration's contract.

Agreed scope: FR-01 login/logout; FR-02 combined ticket search/filter; FR-03 ticket
creation and operator-only editing/assignment; FR-04 comments and activity history.
NFR-01 server-enforced session/tenant/role boundaries; NFR-02 restart durability and
malformed-data preservation; NFR-03 validation, failed-write acknowledgment and UI
draft/retry; NFR-04 versioned conflict rejection; NFR-05 semantic keyboard/mobile
interaction at 360/600/601/1280; NFR-06 local response/startup budgets. Acceptance
procedures and budgets are exactly those in the supplied task.

Unknowns/exclusions: no remote deployment, production load claim, distributed
replication, account registration, password recovery, durable sessions, or atomic
cross-device UI sync. Both contested apps retain freedom to choose other stacks.
These agreements are claims; the trusted grader independently records evidence.
