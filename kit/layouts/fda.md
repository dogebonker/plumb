# Fractal Domain Architecture (frontend)

ID `fda`, row L10. The strong default for a **new frontend application root**, including a full-stack root's frontend. Existing conventions take precedence. A tiny prototype, static site or component library may choose `frontend-small`; a team may explicitly choose `fsd` or `feature-folders`. Record the reason in the Layout Decision, without another approval round solely for accepting the default.

FDA groups code by business domain, repeats that structure in subdomains when useful, and keeps UI, state, transport and persistence responsibilities explicit. Sources: [FDA documentation](https://fda-docs.vercel.app), [upstream README and examples at the reviewed revision](https://github.com/chord-ts/fda/tree/29ce5852cf1cf3a5fa487767e493776d0d24aaa4), and `docs/research/layouts-selection.md`, pattern 11.

**Plumb adaptation:** upstream recommends FDA for medium-sized, long-lived applications and considers it excessive for landing pages and prototypes. Our stronger default is a lightweight policy: keep domain colocation and browser/server boundaries, but create only files with a present responsibility. No empty layers, mandatory repository wrappers or speculative subdomains. This chooses a layout, not React, Python, an ORM or a framework.

## Layout lines

Relative to the frontend root, React with Vite and an existing separate backend:
1. `src/shared/`: genuinely shared UI primitives, types, tokens and platform helpers; no domain imports
2. `src/domains/<domain>/types.ts`: browser-safe wire contracts, when needed
3. `src/domains/<domain>/constants.ts`: browser-safe domain constants, when needed
4. `src/domains/<domain>/client.ts`: the domain's HTTP or RPC client; no database or server imports
5. `src/domains/<domain>/controller.ts`: state and user actions, calling the client; no rendering or database access
6. `src/domains/<domain>/ui/`: domain components and styles, calling the controller
7. `src/domains/<domain>/index.ts`: explicit browser-safe exports only
8. `src/app/`: route composition, providers and shell; no business rules
9. `src/main.tsx`: entry
10. `public/`: static assets
11. `index.html`: entry document
12. `vite.config.ts`: build configuration

The backend keeps its separately selected layout and owns model/repository code. A browser-only app may omit `client.ts` when it has no transport. Local state belongs in the controller; it does not justify a server model. Tests stay beside the responsibility they verify. A subdomain repeats only the parts it needs inside its parent domain, and is not a router path unless the framework says it is.

SvelteKit, in place of the Vite tree:
1. `src/lib/shared/`: shared primitives and contracts
2. `src/routes/<domain>/types.ts`, `constants.ts`: browser-safe contracts, when needed
3. `src/routes/<domain>/repo.server.ts`: persistence adapter, only when a distinct adapter is needed
4. `src/routes/<domain>/model.server.ts`: server operations and domain rules
5. `src/routes/<domain>/+page.server.ts`, `+server.ts`: server load/actions or HTTP boundary with authentication and validation
6. `src/routes/<domain>/client.ts`: browser transport, when needed; never imports `.server` files
7. `src/routes/<domain>/stores.ts`: controller/state; request-specific state is created per request/component, never in a shared server singleton
8. `src/routes/<domain>/+page.svelte`, `ui/`: UI and domain components
9. `src/routes/<domain>/index.ts`: explicit browser-safe exports only, when another domain needs them
10. `src/routes/+layout.svelte`: shell and composition
11. `static/`: static assets
12. `svelte.config.js`, `vite.config.ts`: framework/build configuration

Use SvelteKit's [routing filenames](https://svelte.dev/docs/kit/routing), [server-only modules](https://svelte.dev/docs/kit/server-only-modules) and [request state guidance](https://svelte.dev/docs/kit/state-management). Keep server dependencies behind `.server` files or `$lib/server`; load/actions invoke the model rather than placing domain rules in UI or route glue.

Next.js App Router, in place of the Vite tree:
1. `src/shared/`: shared primitives and contracts
2. `src/domains/<domain>/types.ts`, `constants.ts`: browser-safe contracts
3. `src/domains/<domain>/repo.server.ts`: persistence adapter when needed; imports `server-only`
4. `src/domains/<domain>/model.server.ts`: server operations; imports `server-only`
5. `src/domains/<domain>/server.ts`: explicit server entry exposing authorized operations; imports `server-only`
6. `src/domains/<domain>/client.ts`: browser HTTP/RPC transport, never importing the server entry
7. `src/domains/<domain>/controller.ts`: client state and actions
8. `src/domains/<domain>/ui/`: domain UI; client boundaries use `'use client'` only where needed
9. `src/domains/<domain>/index.ts`: browser-safe public exports only
10. `app/<route>/page.tsx`, `app/<route>/route.ts`: actual Next route entries composing domain UI or invoking server operations; do not mix `page.tsx` and `route.ts` at the same route segment
11. `app/layout.tsx`: shell
12. `public/`: assets
13. `next.config.ts`: framework configuration

Use [Next.js colocation/private folders](https://nextjs.org/docs/app/getting-started/project-structure), [route handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route) and [server/client boundaries](https://nextjs.org/docs/app/getting-started/server-and-client-components). `page.tsx` is a Server Component by default; `page.server.tsx` is not a Next route convention. Place an API handler at a distinct segment such as `app/api/<domain>/route.ts`. Do not use process-wide mutable state for an SSR user's session or controller. The Next mapping is Plumb's adaptation; upstream's Next example is marked unfinished.

## Layers

Lists run from lower dependencies to composition, as in `lenses.yaml`. Omit absent paths when recording the actual layout.

- Vite: `["src/shared/**", "src/domains/*/{types,constants}.ts", "src/domains/*/client.ts", "src/domains/*/controller.ts", "src/domains/*/ui/**", "src/app/**", "src/main.tsx"]`
- SvelteKit: `["src/lib/shared/**", "src/routes/*/{types,constants}.ts", "src/routes/*/repo.server.ts", "src/routes/*/model.server.ts", "src/routes/*/{+page.server,+server}.ts", "src/routes/*/client.ts", "src/routes/*/stores.ts", "src/routes/*/{+page.svelte,ui/**}", "src/routes/+layout.svelte"]`
- Next.js: `["src/shared/**", "src/domains/*/{types,constants}.ts", "src/domains/*/repo.server.ts", "src/domains/*/model.server.ts", "src/domains/*/client.ts", "src/domains/*/controller.ts", "src/domains/*/ui/**", "app/**"]`

Expand paths for actual nested domains/routes in the Layout Decision; `*` describes one segment, not every route depth. These coarse layer lists do not enforce browser/server separation or domain privacy by themselves. Public `index.ts` barrels and explicit `server.ts` entries stay outside the linear lists: a permitted cross-domain public import must not become an outward-layer violation. Their imports/re-exports and caller permissions are enforced by the domain graph rules below; omitting a barrel from linear layers is not an exemption from those checks.

## Contracts and sibling rules

- Dependency direction inside a domain: UI → controller → client/transport → model → repository. The arrow from browser client to server is a **wire call**, never a source import. Contracts/constants may be used throughout; repositories do not depend on controllers or UI.
- Browser modules and their entire import/re-export graph must never reach server entries, models, repositories, credentials or database clients. Browser `index.ts` exposes only safe types, constants, UI and controllers; do not re-export the model/repository for convenience. Server callers use the separate server entry. In SvelteKit, `.server` is enforced by the framework; Next also needs `server-only` rather than relying on a filename suffix.
- A domain may use another domain's public API, never its internal paths. Browser callers use its safe index or transport; server callers use its explicit server entry. Reject cycles, including parent/subdomain cycles. Extract a shared contract only when both sides actually need it.
- Shared code imports no domain. Route glue composes and validates; domain operations retain authorization and tenant scoping, including calls originating outside a route.

## Check

Use the repository's existing dependency-cruiser or eslint-plugin-boundaries configuration (`tools.yaml`), with explicit rules for the recorded domain paths, public entries, cycles and browser-to-server forbidden imports/re-exports. Retain type-only edges in the graph. Include server credentials/DB entry paths as well as `.server` filenames; a public barrel does not waive the prohibition. Do not select the FSD-only Steiger checker for FDA.

The first implementation slice proves the chosen configuration catches a planted browser → model/repository import, a server re-export through a browser index, and a cross-domain internal import. First prove that a permitted cross-domain browser-safe public import passes; on server stacks also prove a permitted server-to-server public entry call passes. Retain these positive cases alongside the planted violations so a checker that rejects every cross-domain import cannot pass calibration. Also run the framework build to validate server/client boundaries. If the existing checker cannot parse the framework's source files, record the coverage gap and use its framework build plus focused boundary checks; do not claim that a TypeScript-only scan covers Svelte components.

## Reference examples (checked 2026-10-14)

- [Upstream SvelteKit cart domain](https://github.com/chord-ts/fda/tree/29ce5852cf1cf3a5fa487767e493776d0d24aaa4/apps/example-sveltekit): the implemented reference example.
- [Upstream documentation source](https://github.com/chord-ts/fda/tree/29ce5852cf1cf3a5fa487767e493776d0d24aaa4/apps/docs/src/content/docs): file contracts, route colocation and domain interactions. Next.js/Nuxt examples are marked in progress, not production evidence.

These are two reference views of one upstream project, not independent adoption evidence. No two mature independent FDA exemplar repositories were verified; the default is our policy choice, not a claim of broad adoption or measured superiority.
