# Public contract

One focused APoSD mini lens informed this boundary. No full book or automatic panel
was loaded. The shared modules hide publication parsing and route inventory; route
components consume those decisions rather than duplicating configuration rules.

`lib/content.ts` exports only:

```typescript
type ContentEntry = {
  slug: string;
  title: string;
  description: string;
  sections: readonly { heading: string; body: string }[];
  sources: readonly { label: string; url: string }[];
  published: boolean;
};
const articles: readonly ContentEntry[];
const guides: readonly ContentEntry[];
const routes: readonly string[];
```

The lists load the frozen JSON; routes contain home, both indexes and published
details only. Route handlers select published entries and reject unknown/draft
slugs. The content source has no side effects or network access.

`lib/publishing.ts` exports only:

```typescript
const publication: { origin: string | null; indexable: boolean };
function pageMetadata(path: string, title: string, description: string):
  import("next").Metadata;
```

`publication` accepts an explicit HTTPS origin without credentials, path, query or
fragment. Missing, malformed or insecure configuration stays preview. Indexing
also requires the exact `true` flag. `pageMetadata` produces the correct robots
directive and, only in public mode, the absolute canonical for its supplied route.

Root layout exports `metadata` and its default React component; home exports its
default component. Feature indexes export their default component and `metadata`.
Detail routes export the default async component, `generateMetadata` and
`generateStaticParams`. Next route params are promises. Discovery files export
only their default Next metadata-route functions. Concrete type expressions and
exclusive file ownership are in the slice YAMLs.

Implementations may have private helpers. Additional public exports or changed
interfaces require a revised contract. Frozen tests verify rendering and behavior;
the compiler checks assignability, not whether code fulfills the prose intent.
