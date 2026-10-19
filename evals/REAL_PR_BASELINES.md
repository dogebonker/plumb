# Frozen repository guides

These are the exact task-independent guides for the CLAUDE.md and Factory arms. Each task appends its verification command; that same command and environment are also supplied to the bare arm. The experiment records the full per-task instruction hashes. The guides contain no Factory routing.

## limitless

```markdown
# Limitless API

TypeScript/NestJS backend. Work within the existing feature module in src; keep transport validation, application services and persistence access in their current layers. Follow the existing DTO/auth-guard conventions for public and admin routes. Keep financial calculations in the established amount representation. Jest uses ts-jest transpile-only, so a green test is not a type check.

Keep the change focused on the requested behavior. Inspect existing callers, types, tests and neighboring implementations before editing. Reuse the repository's existing helpers and conventions. Preserve validation, authorization, error handling and unrelated behavior. Avoid new dependencies or abstractions unless the requirement needs them. Add meaningful regression tests for the behavior and edge cases; never delete assertions to obtain a pass. Use deterministic mocks for external services. Do not contact deployed services or use credentials. Run relevant tests and available type checks, inspect the final diff, and report concrete results and unresolved blockers. Ask only a product decision that the approved task cannot settle. Do not look up this task's historical implementation.
```

## goldengate

```markdown
# Goldengate API

This workspace is the Go API module. Feature packages live in internal; platform integrations are in internal/platform. Keep business operations in their existing services and storage in existing repositories. Preserve tenant/workspace authorization and context cancellation. Reuse established error mapping, mocks, transactions and domain vocabulary. Prefer typed structs to ad-hoc maps. Tests should exercise public outcomes and external failures without live infrastructure.

Keep the change focused on the requested behavior. Inspect existing callers, types, tests and neighboring implementations before editing. Reuse the repository's existing helpers and conventions. Preserve validation, authorization, error handling and unrelated behavior. Avoid new dependencies or abstractions unless the requirement needs them. Add meaningful regression tests for the behavior and edge cases; never delete assertions to obtain a pass. Use deterministic mocks for external services. Do not contact deployed services or use credentials. Run relevant tests and available type checks, inspect the final diff, and report concrete results and unresolved blockers. Ask only a product decision that the approved task cannot settle. Do not look up this task's historical implementation.
```

## bot

```markdown
# Exchange bot

TypeScript Telegram bot and Mini App. Core logic must stay independent of bot/server/database adapters; the web app uses the core model rather than importing server internals. Follow existing Grammy conversation/session handling and backend-client result types. Preserve account/chat authorization, replay safety and navigation state. Prefer local PGlite/test fakes over a live backend. Vite Plus provides test and check commands.

Keep the change focused on the requested behavior. Inspect existing callers, types, tests and neighboring implementations before editing. Reuse the repository's existing helpers and conventions. Preserve validation, authorization, error handling and unrelated behavior. Avoid new dependencies or abstractions unless the requirement needs them. Add meaningful regression tests for the behavior and edge cases; never delete assertions to obtain a pass. Use deterministic mocks for external services. Do not contact deployed services or use credentials. Run relevant tests and available type checks, inspect the final diff, and report concrete results and unresolved blockers. Ask only a product decision that the approved task cannot settle. Do not look up this task's historical implementation.
```
