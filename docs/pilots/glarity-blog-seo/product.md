# Blog and network guides

Give visitors useful explanations of crypto transfer terminology and network
selection, with an educational next step. This is an initial editorial site, not
a trading or deposit integration. The repository's existing Bitxchange name stays.

Publish two blog articles and two curated guides from `apps/frontend/content/editorial.json`:

| Route | Reader's question |
| --- | --- |
| `/blog/swap-quotes-and-transaction-status` | Does a displayed quote mean a transaction completed? |
| `/blog/deposit-address-network-check` | What does a deposit address leave unspecified? |
| `/guides/usdt-ethereum-vs-tron` | What should I verify about USDT's network? |
| `/guides/usdc-network-selection` | How do issuer information and recipient acceptance differ? |

Home, `/blog` and `/guides` provide navigation. Each detail page contains the full
approved prose, its sources and a related blog link. Unknown and unpublished slugs
return 404. The unpublished fixture never appears in indexes or the sitemap.

```text
Bitxchange                         Blog    Network guides
Skip to content
-------------------------------------------------------
One clear page title
A short explanation of what the reader will learn

Section heading
Readable paragraphs

Sources                            Read next
```

Use responsive, readable pages with one main landmark, one H1, a working skip link,
descriptive links, visible focus and sufficient contrast. Keep the existing Next
foundation and dependencies. No CMS, MDX engine, account feature or backend change.

Preview pages are crawlable with `noindex`, no inferred public canonical, and an
empty sitemap. Public indexing requires BOTH an explicit HTTPS origin and
`BITX_MARKETING_INDEXING_ENABLED=true`. Invalid origin configuration stays in preview.
The tests use `https://publication.example`; it is a test value, never a deployment.

In public mode, each of the seven published routes has its own title, description
and absolute canonical. The sitemap lists exactly those seven URLs and robots.txt
references it. No invented lastmod dates, author names, publication dates, rates,
fees, supported swap pairs or completion promises. Blog Article and detail-page
Breadcrumb structured data reflect visible content.

The source links establish issuer/blockchain facts. They do not establish what
Bitxchange currently accepts or executes. No catalogue API is required to render
these pages. This avoids generating thin asset-pair permutations from a catalogue.

Success means all frozen scenarios pass against actual production HTML, merged
links resolve, and architecture/scope/export gates pass. Ranking and indexing are
not promised. No production routing or deployment is included in this approval.

Official technical references, checked 2026-10-19:

- https://developers.google.com/search/docs/essentials/technical
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.google.com/search/docs/essentials/spam-policies#scaled-content
- https://developers.google.com/search/docs/appearance/structured-data/article
- https://developers.google.com/search/docs/appearance/structured-data/breadcrumb
