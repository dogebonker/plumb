fix(sync): stop reporting provably-synced or empty sessions as pending

The freshness gate's peek is now a three-way verdict (SourceWatermark:
At/Empty/Opaque) with one seam decision rule (source_in_sync):

- codex-cli rollouts with no response_item key on the session-start
  header; fully-ingested legacy rollouts gate fresh instead of re-reading
  (and showing pending) forever. Skip still requires a stored watermark.
- Workflow journal.jsonl control files leave the walk entirely
  (JsonlTree::skip_source): never a session, never read, never pending.
- Zero-byte files and claude-code transcripts with no timestamped row
  gate Empty: provably nothing to ingest, re-proven from file content on
  every run (spec 5.4 amendment). The claude-code proof is locked to real
  ingest by keyless_file_peeks_empty_and_ingests_nothing.
- Anything undeterminable stays Opaque: counts pending, re-reads.

Status and dry-run now count sessions, not sources - the wording and the
JSON field follow the unit the gate actually enumerates.
