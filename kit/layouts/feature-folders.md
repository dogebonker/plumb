# Feature folders (bulletproof-react)

ID `feature-folders`, an explicit alternative in row L9 to the FDA default. One layer of features between shared code and the app, without FSD's entities and widgets. Code flows from shared to features to app. Sources: `docs/research/layouts-selection.md`, pattern 10.

**Fits:** an existing feature-folder convention, or a team explicitly choosing feature isolation without FSD's six layers. Record the reason for choosing it over `fda`. **Does not fit:** many entities shared across features, which FSD's entities layer exists for.

## Layout lines

Relative to the frontend root, React with Vite:
1. `src/components/`: shared components. No feature imports
2. `src/hooks/`: shared hooks. No feature imports
3. `src/lib/`: API client and preconfigured libraries. No feature imports
4. `src/stores/`: global state. No feature imports
5. `src/types/`: shared types
6. `src/utils/`: shared helpers
7. `src/config/`: configuration and environment
8. `src/features/<feature>/`: one feature's components, hooks, api and state
9. `src/app/`: routes, providers, the app shell
10. `public/`: static assets served as they are
11. `index.html`: the page that loads the entry
12. `vite.config.ts`: the bundler config

## Layers

`["src/{components,hooks,lib,stores,types,utils,config}/**", "src/features/**", "src/app/**"]` (the first layer is seven folders; gates.md, Layout, allows `{a,b}`).

Sibling rule: features may not import each other.

## Check

eslint-plugin-import-x `import-x/no-restricted-paths` zones (`tools.yaml`).

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [alan2207/bulletproof-react](https://github.com/alan2207/bulletproof-react) | React | 35,967, 2026-05 | `apps/react-vite/src/` and `docs/project-structure.md`; the only exemplar the research found |
