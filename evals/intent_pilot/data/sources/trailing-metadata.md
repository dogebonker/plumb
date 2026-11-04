fix(claude-code): walk back past trailing metadata rows for the freshness watermark

Claude Code appends metadata rows (last-prompt, permission-mode,
bridge-session, agent-name, ...) with no timestamp after the
conversation, so peeking only the literal last line returned None for the
source watermark. is_session_fresh then never fired, stranding ~2,000 of
~9,800 sessions perpetually un-fresh: ~1.18M already-stored rows were
re-decoded and re-merged as no-ops every sync. The peek now walks back to
the last row that carries a timestamp - the real watermark.

Measured on the real corpus: claude-code import 20.1s -> 1.76s,
re-decoded rows 1.18M -> 10.5k, fresh-skips 7863 -> 9823.
