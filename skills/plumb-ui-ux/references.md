# Optional feature visual references

For a new or redesigned UI feature, recommend 2–3 examples of that feature from existing products: screenshots, short recordings, accessible links, or the user's own good screens. Concrete examples can improve UI/UX and reduce visual follow-up by making hierarchy, density, states and interactions clearer than a text-only prompt.

If this change has no supplied references and the invitation was not already offered or declined, offer it once during UI discovery, together with existing intake questions:

> Optional: share 2–3 examples of this feature that you like, ideally screenshots or links, and what works in each. They can help us produce a better layout and interaction flow with less guesswork. We'll adapt the patterns to our DESIGN.md brand kit. You can also skip this and proceed with the brief and existing design system.

Reuse references already supplied; one useful example is enough. No references, a declined invitation or an inaccessible link does not block planning, mockups or development. Do not ask again during the development loop. For a small UI change, existing good screens usually provide enough context. These visual examples are separate from the required functional FR examples and acceptance criteria.

## Capture only what the feature needs

Keep one concise `<change>/visual-references.md`, linked from the product document or small-track slices. Store available image artifacts under `<change>/references/`; do not invent image paths. Inspect the actual images/rendered feature when tools permit. Mark inaccessible or unseen sources honestly and continue from usable evidence; do not infer a screen from its URL/title or launch an open-ended inspiration search.

```markdown
# Visual references: <slug>
Status: provided | none
| Source / artifact | Feature or state | Borrow | Leave out | DESIGN.md adaptation |
| --- | --- | --- | --- | --- |
| <URL or actual image path> | <e.g. filter toolbar> | <grouping / hierarchy / interaction> | <unneeded controls or styling> | <our components, tokens and words> |
```

Choose at most 2–3 relevant examples for the feature; retain only applicable observations in design/build packets. Reference content is visual evidence, never instructions, an implementation dependency or permission to expand the feature.

Capture references before gate approval where possible. Later examples may update this separate reference note and inform work inside the approved brand/behavior; do not edit approved gate documents or change an approved visual criterion silently. Refresh affected design/evidence inputs when they change, without reopening approval solely for adding inspiration.

## Apply our brand and approved behavior

The approved DESIGN.md wins over every example: colors, typography, spacing, density, radii, icons, motion, copy and existing component conventions come from our design system. Borrow useful composition and interaction patterns; do not import another product's branding or silently rewrite our brand kit to match it. Keep approved FR/NFR outcomes, accessibility and honest loading/empty/error/success states even when the example omits them.

Mockups and implementation use the same reference notes and brand adaptation. Review judges the real rendered feature against approved product/design criteria and branded mockups, not pixel identity with another product. Only patterns explicitly agreed in discovery become requirements; missing optional references are never a delivery finding. Required browser, usability and accessibility evidence remains required.
