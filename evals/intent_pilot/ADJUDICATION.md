# Static adjudication of the initial intent pilot

## Verdict

**PARTIAL — execution and quotation results are reproducible; superiority and the disputed false-positive label are not established.** Ground truth remains analyst-provisional. This review used frozen `data/cases.json`, not the Pond working tree, and executed no Rust, model calls, builds, browser or network operations.

## Confirmed evidence

For case `638da979433c`, answer-key revision is `6a05cd17f0869967d149df42f0b4b961b3d3c0ee`. The following line numbers refer to production strings inside that case:

- `src/adapter/claude_code.rs:336–348`: an ordinary top-level file gets a freshness identity only from its first nonempty row's `sessionId`.
- `src/adapter/jsonl.rs:303–321`: a nonempty file without that identity bypasses `peek_watermark` and becomes `Opaque`. The zero-byte exception does not cover it.
- `src/adapter/mod.rs:231–242,183–188`: `Opaque` is not in sync and counts pending. `jsonl.rs:173–193` sends it to the reader on each sync. Assume a nonempty oracle; first-sync planning deliberately marks everything pending (`jsonl.rs:220–221,260–268`).
- For a small, readable JSONL file containing only an id-less, timestamp-free summary row, `claude_code.rs:522–535` rejects session anchoring; `jsonl.rs:519–528` emits an Empty skip before any Session event. The raw response's reachable path and no-ingestion consequence are therefore supported statically.
- The driver's whole-file/no-timestamp proof exists (`claude_code.rs:351–374`) but is never reached on that path. Journal exclusion is independently supported by `claude_code.rs:417–419,457–459` and `jsonl.rs:140–145,253–255`.

## Disputed contract and labels

`data/sources/empty-freshness.md:11–14` says timestamp-free Claude transcripts “gate Empty”; line 15 also preserves undeterminable inputs as Opaque. Literal unrestricted wording supports the raw mismatch. However, whether an id-less summary-only file qualifies as an intended transcript, versus an intentionally unextractable source, is unknown. The seam explicitly preserves id-less failures (`jsonl.rs:318–320`). A reproducible path is not sufficient proof of a maintainer-contract violation.

`data/knowledge/empty-freshness.md:13` changes this to “may classify” after a full-file proof and explicitly preserves tail-only uncertainty. This qualifies the original's overbroad wording and weakens its obligation. The bundle's consistent answer is defensible against that narrower contract, but is not proof that the original claim was a false alarm. The original also omits the size and first-sync qualifications.

`pilot.py:169` labels each corrective commit consistent automatically; correction provenance does not establish exhaustive satisfaction of every phrase. No maintainer adjudication or human curation timing exists.

## Measurement and scoring

All 20 receipts match current protocol and reconstructed prompt hashes, their raw stdout matches their stored provider envelope, and all report successful execution using only the pinned model. Exact quotations independently reproduce 10/10 valid bundle responses and 5/10 valid raw responses. The five raw invalids all fail the source-quotation check; their stored semantic verdicts nevertheless match the provisional labels. Quote compliance must remain separate from semantic detection. `pilot.py:449–464,498` counts only valid responses toward recall, so raw 2/5 means successful target reviews, not three demonstrated reasoning misses.

Keep frozen prompts, labels and primary counts unchanged: bundle 10/10 successful label matches; raw 4/10, five quote-invalid and one disputed mismatch. Mark that mismatch disputed; offer a clearly post-hoc sensitivity view excluding it. Do not relabel, soften contracts or rerun selected failures after seeing outcomes. Future maintainer labels should be independent of arm results and versioned before fresh evaluation.

No “10/10 superiority” claim is defensible: five correlated retrospective pairs, unequal contract wording and an unresolved label support only this run's quotation/label-agreement observation. Human effort and adoption benefits remain unmeasured.

Skipped: Rust execution and source-format validation against real fixtures. Risk: the disputed input's intended contract remains unresolved.
