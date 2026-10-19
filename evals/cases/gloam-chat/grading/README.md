The 23 checks split into brief-level checks (B01-B09), which any implementation of the
brief should pass, and latent checks (L01-L13), which follow rules that only the owner's
answers reveal. case.json reports them as separate outcomes: one `brief` outcome and one
outcome per latent rule. The reusable [QA contract](contract.md) defines the adapter surface and mapping-review boundary.

Arms get one line from the owner and an empty repository, so nothing tells them a seed, a
launch script, an HTTP shape or a test hook. After an arm finishes, the benchmark runs a fresh
adapter agent on a copy of the delivered product: same harness, model and effort as the arm,
no workflow skills, and the fixed prompt in adapter-prompt.md, identical for both arms. It reads
contract.md and writes only `benchmark.sh` and `qa/**`: a seed through the product's own
mechanisms, `qa/mapping.py` for the `/qa` test API, and `qa/ui.json` with CSS selectors for the
product's real controls (null when the product lacks one). A change to any other graded file or to
`node_modules`/`.venv`, a nonzero exit, a timeout or a response other than complete records
`adapter_failed`: that grade is not attributable to the arm and the trial stops without a product
verdict. The exception is `qa/report.json` saying `product_starts: false` with evidence: then the
arm delivered a product that does not start, every check fails, and that result is the arm's. The adapter's diff and cost are kept apart from the arm's.

At grade time `benchmark.sh start` runs only the product. The runtime snapshots `qa/mapping.py`
and `qa/ui.json` before any product code runs, then launches the trusted qa_proxy.py from this
directory in its own sandbox: it reads only that snapshot and writes only the raw log, which the
product's sandbox can neither read nor write. The proxy sends `/qa/...` to the mapping and relays
everything else byte for byte to the product, so the browser checks see the product's own UI and
API. The mapping imports nothing and may not touch names or attributes starting with `_`, classes,
`format` or frame attributes; it reaches the product only through the proxy's client, which logs
every raw product response with the account the grader named in `X-QA-Account`.

The leak checks (B03 cross-table, L03 and departed or closed whispers, L05 tapper email and
veiled text) scan both the adapter's answer and the raw product responses
behind it, so an adapter that filters cannot hide a leak, and each such answer must come from at
least one logged product call made during that request, other than the routes the adapter uses
for /qa/health. Each /qa request runs the mapping in a fresh worker, so no state carries over. The refusal tripwire requires the returned 4xx in a non-health product response, and for a QA
write requires a mutating product method (POST/PUT/PATCH/DELETE). It rejects fabricated write denials
backed by unrelated successful or failing reads; it does not prove semantic correspondence to
an arbitrary backend. A same-status unrelated failing write can still pass, as can an unrelated
failure behind a QA read. Manual mapping review against the product and raw trace is required
before a comparison is valid; an unreviewed grade is diagnostic. See the [contract](contract.md).
The raw log is kept as qa-raw.jsonl in the grade artifact, retaining QA method/path/query/body
and product method/path/request body/status/response body, labelled with the grader's caller.
The caller label does not prove the product's authenticated identity.

API checks use `/qa/api/...`. Seeded scenes are found through GET /qa/api/tables/:table/scenes
with the table from /qa/api/me. Whispers use their own routes, so a product with scene-scoped
whispers and one with a thread per Keeper and player map alike. A route answered 404 "not built"
fails the checks for that feature; where it is only one part of another check (anonymous access
to edits in B02, a per-scene read in B03 and L09, the whisper parts of L09 and L13, edits and the X-card
after a close in L13), that part is skipped and listed in the check's `skipped`, and the rest still
counts. B02 still needs at least one built read and one built write refused. Success is any 2xx and a refusal any 4xx with state unchanged on
re-read, because the adapter passes the product's own codes through. A foreign
`character` from a player may be refused or ignored, as long as the stored speaker is the
player's own character. X-card anonymity compares how often the tapper's email appears in every
other account's answers and raw responses before and after the tap, so a roster that always
lists emails is not a leak. The failed-post check fails the first write request the page sends
after Send, whatever route the product uses; a product that posts over a WebSocket fails it.

B08 covers keyboard login, opening a scene, composing and sending; reaching the X-card by
keyboard is a separate L05 check. Screen scans read visible text only, on every fixed state the
browser reached; login and the Keeper's scene view are required, and a latent state the product
cannot reach is listed under unreached in copy.json instead of failing the scan. Text inside the `post` selector, textareas and visually
hidden helpers such as skip links is excluded; placeholders and visible select options are
included. L01 bans the glossary's "never on screen" words and the fantasy pastiche words, whole
words, case-insensitive, with clock times such as "9:30 PM" removed first. L02 bans the voice
table's phrases, the word "content", exclamation marks and emoji. Voice quality, the
flavor-free X-card and departure copy, scope (N rows) and the visual direction (V01) need the
blind judges.

For those judges the grader writes copy.json (visible non-post text per fixed state: login,
bad login, scene list, Keeper scene with the whisper control, empty scene, failed post,
after posting, X-card paused, X-card tapped, departed player, drawn to a close) with a
state-*.png screenshot each, viewport-360/1280 screenshots in dark and light color schemes
(the unsuffixed names are dark), and desktop-details.png. Requests to any host other than
the loopback server are aborted and fail B09.

The trusted runtime then restarts the server and compares every scene and post (contract
fields only) as the Keeper through `/qa` (B05), makes storage read-only and requires a 5xx
error for a named in-character post (or a 5xx error refusing the sign-in itself, for a product that
stores sessions) with nothing kept and an exact single retry afterwards (L11), and corrupts the database to require refused startup with the bytes untouched (L11).
Sandboxing, dependency copying and process ownership are shared with support-fullstack; see
its README.
