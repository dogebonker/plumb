# Feature-Sliced Design (frontend)

ID `fsd`, row L9. Layers from the top: app, pages, widgets, features, entities, shared. A module imports only from layers strictly below, and slices on one layer do not import each other. Not every layer is needed. Sources: `docs/research/layouts-selection.md`, pattern 8; https://feature-sliced.design.

**Fits:** a frontend root with an entity or user action that two or more screens use, or a growing team. **Does not fit:** nothing shared between screens yet (`frontend-small`; moving up later is renames, not a rewrite).

## Layout lines

Relative to the frontend root, React with Vite:
1. `src/shared/`: ui kit, api client, lib and config. No business logic
2. `src/entities/<entity>/`: domain objects features share (UI-side models, not the backend's aggregates)
3. `src/features/<feature>/`: one user action each, with its `ui`, `model` and `api` segments
4. `src/widgets/<widget>/`: large blocks a page combines
5. `src/pages/<page>/`: one slice per screen, composed from widgets and features. A block never reused stays here
6. `src/app/`: providers, routing, global styles
7. `public/`: static assets served as they are
8. `index.html`: the page that loads the entry
9. `vite.config.ts`: the bundler config
10. `steiger.config.js`: the FSD linter's config

Next.js, same order: `src/shared/`, `src/entities/<entity>/`, `src/features/<feature>/`, `src/widgets/<widget>/`, `src/_pages/<page>/`, `src/_app/`, `public/`, `app/` (Next's routing, thin re-exports of `src/_pages`; `pages/` with the Pages Router), `next.config.ts`, `steiger.config.js`. steiger resolves the underscore-prefixed layers: plugin 0.8.0 depends on `@feature-sliced/filesystem` ^3.1.0, which added them (feature-sliced/steiger PR #233).

## Layers

- Vite: `["src/shared/**", "src/entities/**", "src/features/**", "src/widgets/**", "src/pages/**", "src/app/**"]`
- Next.js: `["src/shared/**", "src/entities/**", "src/features/**", "src/widgets/**", "src/_pages/**", "src/_app/**", "{app,pages}/**"]`

Sibling rule: no imports between slices of one layer.

## Check

steiger with the FSD plugin (`tools.yaml`).

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [noveogroup-amorgunov/nukeapp](https://github.com/noveogroup-amorgunov/nukeapp) | React | 414, 2026-09 | `src/{app,pages,features,entities,shared}`, steiger in `package.json` |
| [yurisldk/realworld-react-fsd](https://github.com/yurisldk/realworld-react-fsd) | React | 532, 2026-05 | FSD's minimal form: only `src/{app,pages,shared}` |
| [Snouzy/workout-cool](https://github.com/Snouzy/workout-cool) | Next.js | 8,595, 2026-09 | a real product: `src/{entities,features,widgets,shared}` beside Next's routing |
