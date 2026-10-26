# MVC (framework conventions)

ID `mvc`, row L2. Sources: `docs/research/layouts-selection.md`, pattern 2.

**Fits:** `crud-service` on a framework with its own convention. Django apps double as modules. **Does not fit:** a rich domain: an ActiveRecord model is a table, while a domain must not depend on its data source. Go has no MVC convention.

The framework's generator decides the tree; record what it creates. Plumb has adapters for TypeScript, Python, Go and Rust; Rails, Laravel and Loco trees are reference only.

## Layout lines

AdonisJS (TypeScript):
1. `app/models/`: persistence and model rules. May not reference controllers or views
2. `resources/views/`: rendering only. No queries beyond what the controller passes
3. `app/controllers/`: one action per request. May not hold domain rules a second controller needs
4. `start/routes.ts`: URL to action only
5. `database/migrations/`: schema changes only

Other stacks, same order and descriptions:
- Django (Python), per app: `<app>/models.py`, `<app>/templates/<app>/`, `<app>/views.py`, `<app>/urls.py`, `<app>/migrations/`
- Rails (reference): `app/models/`, `app/views/`, `app/controllers/`, `config/routes.rb`, `db/migrate/`
- Laravel (reference): `app/Models/`, `resources/views/`, `app/Http/Controllers/`, `routes/web.php`, `database/migrations/`
- Loco (Rust): `src/models/`, `src/views/`, `src/controllers/`, `src/app.rs`

## Layers

- TypeScript (AdonisJS): `["app/models/**", "resources/views/**", "app/controllers/**", "start/**"]`
- Python (Django): `["*/models.py", "*/templates/**", "*/views.py", "*/urls.py"]`
- Rust (Loco): `["src/models/**", "src/views/**", "src/controllers/**", "src/app.rs"]`

Sibling rules: when Django apps are business areas, an app imports another only through `<other>/services.py`; signals are exempt.

## Check

TypeScript: eslint-plugin-boundaries. Python: import-linter `independence` between apps. See `tools.yaml`.

## Exemplars (checked 2026-10-12)

| Repo | Stack | Stars, last push | Look at |
| --- | --- | --- | --- |
| [django/djangoproject.com](https://github.com/django/djangoproject.com) | Django | 2,021, 2026-10 | one app per area: `blog/`, `releases/`, `members/` |
| [expressjs/express](https://github.com/expressjs/express) | JavaScript | 69,624, 2026-10 | `examples/mvc/` |
| [loco-rs/loco](https://github.com/loco-rs/loco) | Rust | 9,426, 2026-09 | reference apps under `evals/tasks/*/reference/src/` |
| [rubygems/rubygems.org](https://github.com/rubygems/rubygems.org) | Rails (reference) | 2,441, 2026-10 | `app/models`, `app/controllers`, `app/views`, `app/policies`, `app/jobs` |
| [koel/koel](https://github.com/koel/koel) | Laravel (reference) | 17,277, 2026-10 | `app/Http`, `app/Models`, with `app/Services` added |
