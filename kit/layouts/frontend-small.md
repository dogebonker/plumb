# Small frontend tree

ID `frontend-small`, row L8. FSD's minimal form (shared, pages, app) under plain names; it grows into `fsd` by renaming `components/` to `shared/ui/`, `lib/` to `shared/api/` and `shared/lib/`, and the entry files to `app/`. Sources: `docs/research/layouts-selection.md`, pattern 9.

**Fits:** a frontend root where no entity or user action is used by two or more screens. **Does not fit:** past that point, or a growing team (`fsd`).

## Layout lines

Relative to the frontend root, React with Vite:
1. `src/styles/`: design tokens and global CSS
2. `src/lib/`: API client, platform bindings and helpers. No JSX
3. `src/components/`: components two or more pages use. No data fetching
4. `src/pages/<page>/`: one folder per screen, with the parts only that screen uses
5. `src/main.tsx`: the entry
6. `src/app.tsx`: the app shell with routing
7. `public/`: static assets served as they are
8. `index.html`: the page that loads the entry
9. `vite.config.ts`: the bundler config

Next.js App Router, in place of lines 1 to 9: `src/styles/` (imported by `app/layout.tsx`), `src/lib/`, `src/components/`, `app/<route>/` (its `page.tsx` and private `_components/`), `app/layout.tsx` (entry and shell), `public/`, `next.config.ts`.

## Layers

- Vite: `["src/styles/**", "src/lib/**", "src/components/**", "src/pages/**", "src/main.tsx", "src/app.tsx"]`
- Next.js: `["src/styles/**", "src/lib/**", "src/components/**", "app/**"]`

Sibling rule: pages (Next.js: routes) may not import each other.

## Check

eslint-plugin-boundaries or dependency-cruiser (`tools.yaml`).

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | React (Vite) | 45,946, 2026-10 | `frontend/src/{routes,components,hooks,lib,client}` |
| [vitejs/vite](https://github.com/vitejs/vite) | React (Vite) | 83,312, 2026-10 | `packages/create-vite/template-react-ts/`: where this tree starts |
