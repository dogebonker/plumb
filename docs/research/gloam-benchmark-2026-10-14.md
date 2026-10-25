# Gloam: a discovery benchmark — 14 October 2026

The support-desk comparison could not show what Factory is for. Its brief froze the FR/NFR list, the HTTP contract, every accessible label and a "professional neutral" look, and the operator answered every design question with the same neutral line. Both arms built the same specification, so the run measured implementation speed, and Superpowers won it at 19× lower cost ([results](codex-fullstack-benchmark-2026-10-14.md)).

Gloam measures what that run removed: whether a workflow asks the questions that change the product, writes down the product's language, and keeps a brand voice with a clear boundary. The arm prompt is the owner's one sentence, the way real requests arrive:

> I need a chat for my roleplaying groups, so we can keep the story going between sessions.

Everything else, from who the users are to whether the X-card exists, comes only from asking the owner.

- Prompt: [evals/cases/gloam-chat/task.md](../../evals/cases/gloam-chat/task.md)
- Owner policy: [evals/operators/gloam-owner.json](../../evals/operators/gloam-owner.json)
- Test contract (adapter only, never shown to arms): [grading/contract.md](../../evals/cases/gloam-chat/grading/contract.md)
- Judge prompts: [judging.md](../../evals/cases/gloam-chat/judging.md); question-log scoring: [gloam_score.py](../../evals/gloam_score.py)

## The product

Gloam is a play-by-post chat for tabletop roleplaying troupes. A table is one campaign with a Keeper and players. People post in scenes, in character or out of character. The Keeper whispers to players. Anyone can tap the X-card.

Why this domain:

- **Real hidden rules.** X-card anonymity, whisper direction, canon locking and departed players are things a roleplayer knows and a generic chat model does not. A workflow finds them only by asking about the domain.
- **Security that is product-shaped.** Leaking who tapped the X-card or a whisper through search is an authorization bug that only exists once you know the rule.
- **A voice with a boundary.** Gloam has flavor where people wait and none where people are hurt or stuck. A neutral default loses half the brand, and flavor everywhere breaks the safety rule.
- **Vocabulary that a default gets wrong.** A model's defaults are channel, DM, GM, message and archive. Every one of those is banned.

## Owner glossary

This is the grading reference. Agents receive it only by asking about vocabulary.

| Term | Meaning | Never on screen |
| --- | --- | --- |
| Table | One campaign and its people | server, workspace, group, room |
| Keeper | Whoever runs the table | GM, DM, admin, moderator, owner, host |
| Player | A person at a table | member, user |
| Character | Who a player is in the story; one per player per table | avatar, persona |
| Scene | One stretch of story | channel, thread, room, chat |
| Post | One contribution to a scene | message, comment |
| In character / Out of character | Spoken as the character / as the player; IC and OOC only as small labels | |
| Whisper | Private post between the Keeper and one player | DM, direct message, PM |
| X-card | Anonymous pause anyone can tap | report, flag, block |
| Veiled | Hidden by the X-card, kept in the record, never shown again | removed, hidden, moderated |
| Canon | A post someone else has posted after; frozen | locked, final |
| Drawn to a close | A finished, read-only scene | archived, closed, ended |
| Departed | A player who has left; their posts remain. The Keeper's action reads "Release from the table" | removed, kicked, deleted user |

Fantasy pastiche (adventurer, quest, tavern, thou) is also banned: Gloam serves horror, noir and science fiction tables.

## Owner voice

Warm, low, a little wry, never cute. Short sentences, second person, sentence case.

| Moment | Gloam says | Not |
| --- | --- | --- |
| Empty scene | Nothing's been said here yet. Set the scene. | No messages yet |
| After posting | Posted. The table's turn. | Message sent! |
| Bad login | That email and password don't match. | Oops! Invalid credentials |
| Failed post | Your post didn't reach the table. It's still here. Send it again. | Something went wrong |
| X-card tapped | The X-card was tapped. The scene is paused. You can talk out of character, or wait for the Keeper. | Any flavor, any in-world language |

The boundary is the test: safety, consent, the X-card and departures get zero flavor. No exclamation marks, no emoji in the interface, never "user" or "content".

## What the owner knows

Each row is one policy rule. **L** rows change behavior and have hidden checks; **N** rows are things the owner does not want, so building them unasked is scope creep; **V** rows are graded by blind review.

| ID | Owner rule | Hidden check |
| --- | --- | --- |
| L01 | Vocabulary above | Visible text of login, table, scene, whisper and X-card screens contains no banned word (visually hidden skip links excluded) |
| L02 | Voice above, with the safety boundary | Banned phrases absent; X-card and departure copy judged flavor-free (V) |
| L03 | Keeper whispers to any player; players whisper only to the Keeper; never player to player; no leak via scene view, search, counts or history; private forever | Player-to-player whisper refused; the whisper text is absent from every other account's scene view and search |
| L05 | X-card is anonymous even to the Keeper; pauses in-character posting, out of character allowed; only the Keeper resumes; a pointed post is veiled for everyone, author included, and never unveiled | Tapper email absent from every response any other account receives; in-character post refused while paused, out of character accepted; player resume refused; veiled body absent for all accounts |
| L07 | In character shows the character name, never the email; one character per player; the Keeper names each in-character post freely and must name it | A player's in-character post is spoken by their own character, whether a foreign `character` is refused or ignored; unnamed Keeper post refused; in-character post renders the character name without the email |
| L08 | Edit or withdraw your own post until someone else posts after it; then it is canon, nobody edits or deletes it, Keeper included | Edit before reply accepted; after reply refused with the text unchanged; nobody edits another's post |
| L09 | Only the Keeper removes a player; access ends at once; posts stay, marked departed; whispers stay private | Removed session refused; posts still present; player cannot remove another player |
| L10 | A failed post keeps the text, says so plainly, resends exactly once | Injected HTTP failure keeps the `composer` text and shows role=alert; retry creates one post |
| L11 | Damaged data refuses to start; never reseed or overwrite; unwritable storage refuses the post and keeps the draft | Malformed database fails startup and stays byte-identical; read-only storage preserves earlier posts |
| L12 | Simultaneous posts both land in arrival order; a stale edit keeps the newer text and says so | Two clients post, both stored in order. The stale-edit check is a baseline check: any edit feature should refuse a stale write without the owner asking |
| L13 | Only the Keeper draws a scene to a close; then read-only forever, no X-card, no reopening; whispers stay private | Post, edit and X-card refused on a closed scene; player close refused |
| N01 | No dice | Blind review: no roller or /roll |
| N02 | No lines and veils in v1 | Blind review: no lines list or content settings |
| N03 | No notifications or push; a quiet "new posts" line with polling is welcome; unread never counts others' whispers | Blind review; unread leak covered by L03 |
| N04 | No reactions | Blind review: no reaction UI |
| V01 | Ink and lamplight: warm dark default plus light theme, serif story text, quiet sans out of character, one ember accent, calm X-card, mobile first-class | Blind review of screenshots at 360 and 1280 in both themes |

Baseline checks are engineering basics a mature build gets right without the owner asking: login and logout, cross-table isolation in scenes and search (Neon Fathoms sees nothing of The Salt Road), anonymous 401, durable restart, `/health`, stale `version` refused with the newer text kept, 360/1280 without overflow, keyboard reachability. They carry B IDs and are reported separately from the latent checks.

## Scores

Pre-registered before any run. No combined score: each is reported per arm and repetition.

1. **Discovery.** Distinct policy rules triggered, from the question log, out of 16 (L, N and V rows). Each answer maps back to its rule IDs, combined answers included. Context answers (C rows: purpose, scale, accounts, devices, version one) are needed to sound like a real owner and are not scored. Also reported: questions per revealed rule.
2. **Question maturity.** Two blind judges classify every question, arm names and workflow wording removed:
   - *Reveals*: triggered an L, N or V rule.
   - *Trade-off*: offered concrete options with consequences for the user.
   - *Rubber stamp*: "does this look good", "shall I proceed" without a decision in it.
   - *Redundant*: already answered by the prompt or an earlier answer.
   A mature process has a high share of the first two and asks redundant questions rarely. Raw question count is not maturity: Factory asked 18 to Superpowers' 3 last time.
3. **Glossary.** Each of the 13 owner terms is defined consistently with the table anywhere in the repository, `DECISIONS.md` included; no particular glossary file is required, since the prompt asks for none. The L01 screen scan counts here too. Invented terms score zero on consistency.
4. **Voice.** Mechanical banned-phrase scan, plus three blind judges scoring fixed states (empty scene, after posting, bad login, failed post, X-card tapped, departed player, scene drawn to a close) 0 to 3 against the owner voice table. A 3 matches the voice and respects the safety boundary. Flavor on the X-card scores 0 regardless of how good it reads.
5. **Hidden acceptance.** Baseline and latent checks, reported separately.
6. **Scope.** N rows built unasked, from blind review.
7. **Cost and time.** Tokens by class, API-rate estimate, wall time, questions, child threads. Reported next to every other score, never hidden.

Factory wins Gloam if, over at least three alternating repetitions, it beats Superpowers on discovery, latent acceptance and voice by a margin larger than its own variance. Whether that is worth its cost is a separate decision the cost row informs. Superpowers' brainstorming also asks one question at a time and may find these rules: this benchmark tests Factory's claim, it does not guarantee it.

## Fairness controls

- One prompt, one owner policy, hashed before the first run and never edited mid-run. Both arms receive identical answers to identical questions. No coaching: the discovery prompt wrapper drops the DECISIONS.md and FR/NFR instructions other cases inject.
- Hidden-test failures never reach an arm. Repair rounds are forced to zero for discovery cases, because failure feedback would reveal the latent rules.
- Grading goes through a post-delivery adapter. After an arm delivers, a fresh agent with the arm's harness, model and effort, a fixed prompt and no workflow skills reads the test contract and writes `qa/mapping.py`, `qa/ui.json` and `benchmark.sh`. A mechanical diff check rejects any change outside those paths. The mapping reaches the product only through the trusted proxy's client, which logs every raw response, and leak checks scan that raw log, so an adapter cannot hide a leak. A feature the product lacks maps to null or 404 and fails its check. Adapter cost and time are reported separately.
- Arms are pinned: the Factory commit and the Superpowers version are recorded next to the policy hash. The Factory author wrote this policy, so any Factory change made after it, H12 included, must land and be recorded before the first run. A later change to either arm voids the run.
- The owner answers only what is asked. The default answer reveals nothing and tells both arms the same thing: decide, record the assumption, and ask directly about anything a player sees.
- Approval is the last rule before the default, so an approval question that names a topic still gets that topic's answer. Gate-style summaries are not penalised. The approval answer approves only what was asked: anything else in a proposal stays the agent's assumption.
- Routing was calibrated offline: 50 sample questions, including an independent critic's misroutes and collisions such as "random UUIDs", "code layout", "roll back a scene", "scene list page" and "push to remote", all reach the intended rule or the default.
- Graders, judges and the glossary key stay outside the workspaces. Judges see anonymous sources and screenshots, not arm names, cost or time.
- Run with `--comparison-mode discovery --operator-policy evals/operators/gloam-owner.json --max-questions 60`. The default cap of 12 would cut off a process that starts from one sentence and asks about 21 topics one at a time.
- `--operator human` with this file as Wren's sheet is the stronger variant: a person answers bundled or oddly phrased questions the regex cannot.

## Known limits

- The policy runs in combine mode: a question that bundles three topics gets all three answers, so bundling is neither penalised nor rewarded.
- Regex routing rewards naming the topic, not understanding it. An agent that sprays keywords triggers rules cheaply; the maturity judges see that, the discovery count does not.
- `ui-hard-gate` rule H12 requires "a neutral, factual tone". If Factory applies it, Factory flattens Gloam's voice and loses L02 to its own gate. That rule is wrong for any branded product, not only this one, but changing it is a Factory change and falls under the pinning rule above.
- An agent that re-asks the same approval summary gets the same topic answer each time; `--max-questions` bounds that loop.
- One domain. A win here shows Factory's discovery is worth something on a product with real rules and a real voice; it says nothing about brownfield changes or cost-sensitive work.

## Status

Runnable: `check_cases.py` proves the starting repository fails and the oracle passes all 23 checks, and calibration mutants (including an adapter that strips a leak and one that refuses on the product's behalf) each fail only their target check. No arm has run yet.
