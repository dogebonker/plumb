---
type: Module Contract
status: draft
---

Unreviewed verbatim source import; no agreed intent is inferred from code.

Source: https://github.com/tenequm/pond/blob/b049b2e8ba3a418ad54eebe738c9d8fbe8a8d1c3/docs/spec.md

### 6.6 Ingest order and integrity

#### `adapter-integrity`

The parse face's contract on output:

##### `adapter-integrity-event-ordering`

For each session: the Session first, then each Message immediately followed by its Parts in order, before the next Message. pond core computes a message's indexed text at the message boundary without buffering across messages - the transition off a Part stream is the signal the message is complete. Core MAY flush a completed prefix of a large in-flight session to keep ingest memory bounded, but MUST write the session row only after the substream closes so the freshness signal cannot outrun its message and part rows.

##### `adapter-integrity-no-silent-drops`

Malformed source input MUST surface as a typed error carrying the adapter and the location of the fault; never silently skipped. A silent drop is invisible data loss, a surfaced one is a fixable report.

##### `adapter-integrity-opaque-ids`

Identifiers on canonical objects are opaque strings. An adapter decodes any structure a source encodes into a path or name once, at ingest, and stores the decoded value; readers never re-parse.

##### `adapter-integrity-additive-sync`

A write MUST NOT overwrite a row already present under its primary key - matched rows are no-ops. Adapter output is monotone across versions: a newer adapter produces a superset of the rows a prior version produced. The source is not authoritative against pond's stored copy - a re-parse from a since-corrupted source must not be able to overwrite good data. Changing or removing an already-stored row is a deliberate migration, never a side effect of re-ingest.

##### `adapter-integrity-dedup`

An adapter SHOULD detect duplicate primary keys in its own output using the source format's own mechanism; the write path drops duplicates as a floor regardless. Catching them in the adapter keeps the count visible in the ingest summary, while the write-path floor keeps storage correct when an adapter misses one. A duplicate is two records that agree on primary key and content; two records sharing a source-supplied id but differing in content are not duplicates - dropping one is invisible data loss (`adapter-integrity-no-silent-drops`). An adapter that dedups on a source id alone MUST confirm content-identity before dropping, or distinguish the records by deriving a content-keyed primary key; a collision it cannot resolve surfaces as a visible drop, never a silent one.

