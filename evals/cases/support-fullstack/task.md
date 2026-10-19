# Support desk

Build a complete local full-stack support desk. Choose and justify your frontend, backend, framework and durable database. Use project-pinned dependencies; no global installations, remote services or external assets. The test-facing HTTP contract below is an interoperability boundary, not a prescribed architecture or file layout.

Before implementation, record `DECISIONS.md`: stack choices and alternatives, FR/NFR agreement (IDs below, measurable acceptance and explicit exclusions), unresolved assumptions and major changes. A claimed agreement is not independently verified acceptance. Keep the same agreed scope; do not trade away requirements for extra features.

Professional neutral product direction: a calm, readable support operations tool, clear ticket hierarchy, restrained color and familiar controls. No marketing hero. Desktop and mobile should feel like the same product.

## Agreement and acceptance

- FR-01: Login/logout. Four seeded accounts: `operator@acme.test`, `customer@acme.test`, `operator@north.test`, `customer@north.test`; password `benchmark-pass`. Roles are operator/customer and tenants acme/north. Operators see all tickets in their tenant. Customers see only their own tickets. Seed each tenant with T001/T002 (Acme) or T101/T102 (North), titles `Password reset expired` and `Export stalls`; first open/high, second pending/low. Both tickets belong to that tenant's seeded customer. IDs are globally unique.
- FR-02: List tickets with ID/title/status/priority; case-insensitive substring search of title/description, status and priority filters combine with AND; matching count/empty state; Reset filters.
- FR-03: Both roles create tickets with trimmed nonempty Title/Description (max 120/4000 characters), initial open/medium, unique ID. Operator edits Title, Description, Status (open/pending/resolved), Priority (low/medium/high), Assignee (unassigned or their tenant operator email). Customers can read/create/comment; ticket editing and assignment are operator-only.
- FR-04: Both roles can add trimmed nonempty comments (max 2000 chars) to visible tickets. Details show comments and ordered persistent history of creation, edits and comments, including actor and event type.
- NFR-01: Tenant/role rules are enforced by the server for listing, individual reads, writes and comments. Anonymous requests return 401. Invisible resources return 404 without leaking contents. Customer privilege escalation returns 403. Reject arbitrary tenant/customer/actor fields in writes (400); derive ownership from authenticated session. Logout invalidates that session.
- NFR-02: Committed tickets/comments/history survive server process restart using DATABASE_PATH. A malformed database is a startup error; never replace it with seeds. Seed/reset is an explicit benchmark command only, never implicit recovery.
- NFR-03: Validate every write on the server; invalid requests return 400 with JSON error and leave data unchanged. A real write/storage failure returns 5xx. The UI acknowledges only successful commits; on HTTP failure retain dialog/draft with visible role=alert error, and retry creates exactly once after recovery. The grader injects a failed HTTP response to verify this UI contract; server storage failure is tested separately by restarting with the disposable database tree read-only. Refusing readiness while durable storage is unwritable is acceptable; restoring permissions must preserve prior records and allow retry.
- NFR-04: Each ticket has integer version. Edits/comments submit the last observed version. Stale writes return 409 and preserve newer data; UI retains its draft and shows a conflict. Sequential two-client creations and unrelated-ticket edits retain all data. Simultaneous stress and distributed replication are excluded.
- NFR-05: Semantic labeled inputs/buttons/dialogs, visible keyboard focus, modal focus containment, Escape/cancel returns focus to opener. No page overflow/clipped controls or unreadable character-wide ticket titles at widths 360, 600, 601 and 1280. All product actions keyboard reachable.
- NFR-06: Local workload: 30 sequential authenticated list requests over the two seeds plus at most 20 small acceptance-created tickets; each response below 2 seconds, whole batch below 15 seconds. Empty-cache initial UI ready below 10 seconds. No remote network requests. These are conservative local acceptance budgets, not a production capacity claim.

Stable accessible interface: login fields `Email`, `Password`, action `Log in`; `Log out`, `Search tickets`, `Status filter`, `Priority filter`, `Reset filters`, `New ticket`. Ticket button/link name includes ID and title. Dialog names `New ticket` and `Ticket details`; fields `Title`, `Description`, `Status`, `Priority`, `Assignee`, `Comment`; actions `Create ticket`, `Save changes`, `Add comment`, `Cancel`. Result count role=status; errors role=alert. Customers need not be shown forbidden editing controls.

## Launch boundary

Executable `benchmark.sh setup|reset|start` in repository root. setup installs/builds pinned local dependencies without starting a server. reset recreates deterministic seeded database at DATABASE_PATH (explicitly authorized disposable test DB). start runs the server in the foreground; no daemon/detached processes. HOST=127.0.0.1, PORT supplied by harness, DATABASE_PATH absolute and supplied; UI and API share http://HOST:PORT. Never bind publicly. Start does not reset existing data. GET /health returns 200 when ready, within 15 seconds after start (dependency installation/build belongs in setup). Use portable `/bin/sh`; no host credentials. Grader supplies an installed Playwright runtime.

## HTTP boundary

API JSON requests/responses. Errors `{ "error": "human readable reason" }`. Cookie-based authenticated sessions, HttpOnly and SameSite=Lax or stricter. Endpoint success statuses below are fixed for interoperable tests.

- POST /api/login `{email,password}` -> 200 `{user:{email,role,tenant}}`, session cookie. Bad credentials 401. POST /api/logout -> 200, invalidates session. GET /api/me -> 200 same user.
- GET /api/tickets?q=&status=&priority= -> 200 `{tickets:[...]}`; empty filter or `all` means all. GET /api/tickets/:id -> 200 `{ticket:...}`.
- POST /api/tickets `{title,description}` -> 201 `{ticket:...}`.
- PATCH /api/tickets/:id `{version,title?,description?,status?,priority?,assignee?}` -> 200 `{ticket:...}`. Reject unknown fields.
- POST /api/tickets/:id/comments `{version,text}` -> 201 `{ticket:...}`. Reject unknown fields.

Ticket: `{id,title,description,status,priority,assignee,customer,tenant,version,comments,history}`. assignee is null or operator email; customer is creator email. comments: `[{text,actor}]`; history: `[{type,actor}]`, type=create/edit/comment. Server may add fields but retain this boundary. Seed history contains creation. Sessions need not survive server restart; tickets must.

The starter is a launch-contract scaffold, not an implementation. Public smoke: `sh benchmark.sh setup`. Implement your own useful tests and run them; hidden acceptance is independent. Record dependency setup failure rather than silently changing scope.
