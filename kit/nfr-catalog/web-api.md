# NFR catalog: web API and SaaS backend

Default promises for a service that answers HTTP requests for many users or tenants. Triage offers these rows when a project's registry is created; the user keeps the ones that apply, and they become `SYS-NFR-NN` rows. Budgets are starting points: tune them per project.

| Key | Promise | Default fit criterion | Enforced by | Question to ask |
| --- | --- | --- | --- | --- |
| latency | Pages and calls feel instant | p95 under 300 ms for reads, 800 ms for writes, per endpoint | monitor | Which endpoints are on a user's critical path, and what do they wait for today? |
| availability | The service is there when users need it | 99.9% of minutes per month answer without 5xx | monitor | What does an hour of downtime cost, and who notices first? |
| errors | Requests succeed | 5xx under 0.1% of requests per endpoint per day | monitor | Which failures are the caller's fault, and do they get 4xx with a stable error shape? |
| timeouts | A slow dependency never hangs a request | every outbound call has a timeout below the caller's budget | lint rule or test | Which outbound calls exist, and what is each one's worst observed latency? |
| retries | Transient failures recover without duplicates | only idempotent calls retry, with capped exponential backoff and jitter | test | Which calls are safe to repeat, and which change state? |
| idempotency | Repeating a request never repeats its effect | state-changing POSTs accept an idempotency key; a replay returns the first result | test | What happens today when a client retries a create after a timeout? |
| rate-limits | One client cannot starve the others | per-key and per-tenant limits; excess gets 429 with `Retry-After` | test | Who are the heaviest callers, and what limit would they hit? |
| pagination | Lists stay fast as data grows | list endpoints paginate with a maximum page size | test | Which lists can grow without bound? |
| validation | Bad input is rejected at the door | every request body and parameter is validated before any side effect; failures return 4xx | test | Where is input validated today, and what reaches storage unchecked? |
| authn-authz | Only the right people reach the right data | every non-public endpoint authenticates; every resource access checks permission | test | Which endpoints are public on purpose? |
| tenant-isolation | A tenant never sees another tenant's data | every query is scoped by tenant; a cross-tenant test fails closed | test | Where is the tenant boundary enforced: query, service, or database? |
| logging-pii | Logs never leak secrets or personal data | secrets and personal fields are redacted before logging | lint rule or test | Which fields are personal or secret? |
| audit | Privileged actions can be traced | admin and permission changes write an audit record with actor, target and time | test | Who needs to answer "who changed this", and how fast? |
| deletion | Users can leave and take their data | a deletion request completes within 30 days, backups included | human-verified | Which stores and backups hold user data? |
| backups | Data survives a disaster | RPO 24 h, RTO 4 h, restore rehearsed every quarter | human-verified | When was a restore last tested end to end? |
| migrations | Deploys never break running code | every schema change is backward compatible with the previous release (expand, then contract) | test or human-verified | Can the old and new release run against the same schema during a deploy? |
| api-compat | Integrations keep working across releases | no breaking change to a published API version; deprecations announced 90 days ahead | test | Who integrates with the API, and how do they learn about changes? |
| observability | Problems are found before users report them | structured logs with a request id, per-endpoint metrics, traces across services | monitor | How long does it take today to find the cause of a failed request? |
| degradation | One broken dependency breaks one feature, not the service | each dependency sits behind a bulkhead or circuit breaker with a fallback | test | Which dependencies are optional for the core path? |
| health | The platform can tell a broken instance from a busy one | liveness and readiness endpoints that check real dependencies | test | What should take an instance out of rotation? |
| capacity | The service holds up at peak | sustains the expected peak rps at the latency budget in a load test | human-verified | What is today's peak, and the next year's? |
| read-your-writes | Users see their own changes immediately | a read after a user's own write returns that write | test | Where do replicas or caches serve reads after writes? |
| durability | An acknowledged write is never lost | writes are acknowledged only after durable commit | test | Which writes are acknowledged before they are durable? |
