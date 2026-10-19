# Gloam QA contract

Independent tests drive a delivered Gloam product through a thin adapter. This contract fixes what the adapter provides. It does not say who may do what: those rules belong to the product, and the tests judge the product's own behavior.

You write `benchmark.sh` in the repository root, `qa/mapping.py`, `qa/ui.json`, and `qa/report.json` saying whether the product starts (`{"product_starts": true|false, "evidence": "..."}`). `qa/qa_proxy.py` is provided so you can test locally; the grader runs its own copy, so never edit it.

## Seed

Password for every account: `benchmark-pass`.

| Table | Keeper | Players (character) |
| --- | --- | --- |
| The Salt Road | `keeper@saltroad.test` | `ash@saltroad.test` (Marrow), `bryn@saltroad.test` (Sister Vey), `cato@saltroad.test` (Old Tam) |
| Neon Fathoms | `keeper@fathoms.test` | `dana@fathoms.test` (Kestrel) |

Each table starts with one open scene: `The Drowned Mile` (Salt Road) and `Pressure Drop` (Neon Fathoms), each with one in-character post by its first player.

Create the seed only through the product's own mechanisms: its API, its command line or its own seed code path. Never write the product's storage directly. Something the product cannot represent stays out of the seed, and the checks that need it fail.

## Launch

Executable `benchmark.sh setup|reset|start` in portable `/bin/sh`. The grader supplies `HOST=127.0.0.1`, `PRODUCT_PORT` (also passed as `PORT`) and an absolute `DATABASE_PATH`.

- `setup` prepares already-present local dependencies without starting a server. Install nothing.
- `reset` recreates the seeded data at `DATABASE_PATH`. It may start the product on `PRODUCT_PORT` to seed through its API, and must stop it before exiting.
- `start` runs only the product, in the foreground, on `127.0.0.1:PRODUCT_PORT`. It never resets data. The grader starts a separate QA proxy on another port; `GET /qa/health` through that proxy must return 200 within 15 seconds. Browser checks use the product's native origin, preserving its Host and Origin protections.

To test locally, start the product, then run `PORT=<free port> PRODUCT_PORT=<product port> QA_RAW_LOG=.tmp/raw.jsonl python3 qa/qa_proxy.py` and call `http://127.0.0.1:<free port>/qa/...`.

Point the product at `PRODUCT_PORT` and `DATABASE_PATH` through its own configuration: environment variables, flags, or a config file under `qa/`. `DATABASE_PATH` is a file or directory that holds all durable data; the grader restarts the product, makes that path read-only and corrupts it. Never bind publicly.

## The proxy

The proxy listens on `PORT`. Requests under `/qa` go to `handle(request, product)` in `qa/mapping.py`. Its other connections are relayed byte for byte; independent browser checks navigate directly to the product's native origin for its real pages, assets and API.

`request` has `method`, `path` (after `/qa`, for example `/api/login`), `query` (the raw query string), `body` (raw bytes), `json` (the parsed body or `None`) and `cookie` (the caller's `Cookie` header).

`product.call(method, path, body=None, headers=None)` is the only way to reach the product. It sends the caller's cookies unless `headers` sets `Cookie`, defaults `Origin` to the product's actual first-party origin unless `headers` overrides it, sends a dict or list body as JSON, and returns an object with `status`, `headers` (use `headers.get_all('Set-Cookie')`), `body` (bytes), `text` and `json()`. Every raw product response is logged with the grader's account label, the originating QA method/path/query/body, and the product method/path/request body/status/response body. The account label records the grader's caller, not proof of the identity actually authenticated by the product. The tests scan that log as well as your answers.

`handle` returns `(status, body, headers)`: `body` is bytes, a string or a JSON-serializable value; `headers` is a list of `(name, value)` pairs, normally the product's `Set-Cookie` headers.

`qa/mapping.py` is plain functions over data. It imports nothing; `json` (`loads`, `dumps`, `JSONDecodeError`), `re` (`match`, `search`, `fullmatch`, `sub`, `split`, `findall`, `compile`, `escape`, `IGNORECASE`) and `parse` (`quote`, `unquote`, `urlencode`, `parse_qs`, `parse_qsl`, `urlsplit` from `urllib.parse`) are provided, with basic builtins such as `len`, `str`, `int`, `dict`, `list`, `isinstance`, `sorted` and `ValueError`. Classes, `global`, names or attributes starting with `_`, and `format` are refused, and the proxy will not start.

Mapping rules:

- Answer each `/qa/api` request from product calls made during that request. Keep no state between requests and never invent data the product did not return.
- Rename fields and reshape envelopes only. Never drop items, redact values or apply a rule the product does not apply: whatever the product sends an account, that account receives.
- Return the product's own status code from the equivalent operation under the caller's identity. A refusal must come from that operation, never an unrelated request. The automated tripwire requires a logged non-health product response with the returned 4xx; for a QA write, that response must come from POST, PUT, PATCH or DELETE. Method translation such as GraphQL/RPC POST for reads or edits is allowed. For a route the product has no equivalent for, return 404 `{"error": "not built"}`; an adapter-only 404 does not prove the product refused an operation. A QA read composed from other product reads (a scene picked out of its table's snapshot, say) has no status of its own: when those reads do not contain what was asked for, answer 404 `{"error": "not built"}`, never a success with nothing in it.
- Return the product's own session cookies unchanged when it uses cookies. If it uses tokens, carry the token in a cookie of your own.

## Mapping review and validity boundary

The tripwire rejects an invented denial backed only by a successful read, and a write denial backed by an unrelated failing read. It does not establish semantic correspondence: an unrelated failing write, an unrelated failure behind a QA read, altered credentials, or substituted request data may still satisfy the mechanical check. Raw trace provenance records what happened; it cannot identify arbitrary backend operations automatically. Privacy scans still inspect unfiltered raw responses.

A comparison requires manual review of `qa/mapping.py` against the delivered product and `qa-raw.jsonl`: each QA operation must reach its actual product equivalent, with the intended caller and inputs, and return that operation's status without implementing product authorization in the adapter. Until that review is recorded by the harness, automated grades are diagnostic and the comparison is invalid. Passing all 23 fixed checks alone is insufficient. The grader does not execute receipt commands or infer review from adapter claims.

## QA API

JSON in and out, errors `{ "error": "..." }`, cookie sessions.

- `GET /qa/health` -> 200 once the product answers.

The codes below are the usual ones; any code in the same class passes.
- `POST /qa/api/login {email,password}` -> 200 `{user:{email,role,table}}`; `POST /qa/api/logout`; `GET /qa/api/me`.
- `GET /qa/api/tables/:table/scenes` -> `{scenes:[{id,title,state}]}`; `POST /qa/api/tables/:table/scenes {title}` -> 201 `{scene}`.
- `GET /qa/api/scenes/:id` -> `{scene:{id,title,state,posts:[...]}}`.
- `POST /qa/api/scenes/:id/posts {body, in_character, character?}` -> 201 `{post}`. `character` is a speaker name.
- `PATCH /qa/api/posts/:id {version, body}` -> 200 `{post}`.
- `POST /qa/api/scenes/:id/xcard {post?}`, `POST /qa/api/scenes/:id/resume`, `POST /qa/api/scenes/:id/close` -> 200 `{scene}`.
- `DELETE /qa/api/tables/:table/players/:email` -> 200.
- `GET /qa/api/tables/:table/search?q=` -> `{posts:[...]}`.
- `POST /qa/api/tables/:table/whispers {to, body, scene, in_character?}` -> 201 `{whisper}`: the caller whispers `body` to the account with email `to`. `scene` is the scene it is sent from; a product whose whispers belong to the table or to a Keeper-player thread rather than a scene ignores it. `in_character` defaults to false.
- `GET /qa/api/tables/:table/whispers?with=<email>&scene=<id>` -> `{whispers:[...]}`: the whispers between the caller and `with` as the product shows them to the caller. A product that keeps whispers as scene posts may answer with the posts of `scene` the caller receives.

Whispers can live anywhere the product puts them: scene posts with a recipient, a thread per Keeper and player, or something else. Map both whisper routes to the product's own whisper operations under the caller's session. When the product addresses people by its own identifier, the mapping may resolve an email to it from what the product returns: a roster the caller's session can read, or logging in as that seeded account with the seed password and `headers={"Cookie": ""}` so the caller's session is untouched.

Post: `{id, scene, body, in_character, speaker, version, created_at}`. Whisper: `{id, body, from, to, created_at}`, with `from` and `to` as the product identifies the two people. Extra fields may pass through. `role` is `keeper` or `player`; `table` is the product's identifier for the account's table.

## UI map

`qa/ui.json` maps each key to a CSS selector that `document.querySelectorAll` accepts and that matches the product's real UI, or to `null` when the product has no such control. The tests use the first match unless noted.

| Key | What it selects |
| --- | --- |
| `email`, `password`, `log-in` | The login form's email field, password field and submit control |
| `alert` | Where the product tells a person something failed: a bad login or a post that did not send |
| `scene-link` | Each scene in a table's list; clicking one opens it |
| `table-link` | Optional. Each table in the account's list of tables, when an account can belong to several and the product shows one at a time; clicking one shows its scenes |
| `navigation` | Optional. The control that reveals the table and scene lists when a narrow layout hides them behind a menu |
| `composer` | The text field for a new post |
| `in-character` | The in-character toggle or choice |
| `send` | The control that sends a post |
| `post` | Each post shown in a scene (all matches) |
| `whisper-to` | The whisper recipient choice |
| `xcard` | The X-card control in a scene |
| `resume` | The control that resumes a paused scene |
| `close-scene` | The control that draws a scene to a close |
| `search` | The search field |
