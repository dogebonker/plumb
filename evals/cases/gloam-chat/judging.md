# Gloam blind-judge prompts

Four self-contained prompts. Paste one into a fresh judge with the inputs it names. Never include the arm name, workflow wording, cost, tokens or timing. Return only the JSON shape given in each prompt.

## Shared reference

### Owner glossary

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

### Owner voice

Warm, low, a little wry, never cute. Short sentences, second person, sentence case.

| Moment | Gloam says | Not |
| --- | --- | --- |
| Empty scene | Nothing's been said here yet. Set the scene. | No messages yet |
| After posting | Posted. The table's turn. | Message sent! |
| Bad login | That email and password don't match. | Oops! Invalid credentials |
| Failed post | Your post didn't reach the table. It's still here. Send it again. | Something went wrong |
| X-card tapped | The X-card was tapped. The scene is paused. You can talk out of character, or wait for the Keeper. | Any flavor, any in-world language |

The boundary is the test: safety, consent, the X-card and departures get zero flavor. No exclamation marks, no emoji in the interface, never "user" or "content".

## 1. Question maturity

You judge the questions a software workflow asked its owner while building Gloam, a play-by-post chat for tabletop roleplaying troupes. You do not know which workflow asked them.

Inputs: the brief (`task.md`), and the ordered list of questions. Each question comes with the rule IDs its answer revealed (empty if none) and the earlier questions and answers.

Classify every question as exactly one of:

- Reveals: its answer revealed an owner rule (a listed rule ID that starts with L, N or V).
- Trade-off: it offered concrete options with consequences for the owner, and no rule was revealed.
- Rubber stamp: "does this look good", "shall I proceed" or similar, with no decision in it.
- Redundant: already answered by the brief or an earlier answer.

If a question fits several classes, use the first in the order above, except that Redundant wins when the answer was already available. Judge only the question text, the brief and the earlier answers. Do not reward length or politeness.

Output: `{"questions":[{"n":1,"class":"Reveals|Trade-off|Rubber stamp|Redundant","reason":"one sentence"}],"counts":{"Reveals":0,"Trade-off":0,"Rubber stamp":0,"Redundant":0}}`

## 2. Voice

You judge the product copy of Gloam against the owner's voice. You do not know which workflow built it.

Inputs: the grader's `copy.json` (`{"states":{...},"unreached":{...}}`) and the per-state screenshots `state-<key>.png`. Judge only these states: empty_scene, after_posting, bad_login, failed_post, xcard_paused, departed_player, drawn_to_a_close. Ignore login, scene_list, keeper_scene and xcard_tapped. A judged state listed under `unreached` scores 0. departed_player is the Keeper's scene view, so it includes the roster's "Release from the table" labels. Post text is not in `copy.json`; a "Departed" tag inside a post appears only in the screenshot. Use the owner voice table and glossary above, and nothing else.

Score each state 0 to 3:

- 3: matches the voice (warm, low, a little wry, never cute; short sentences, second person, sentence case), uses no banned word, and respects the safety boundary.
- 2: close; one small miss such as a stiff sentence, a missing second person or a banned word that is not on a safety screen.
- 1: generic default copy ("No messages yet", "Message sent", "Something went wrong"), or a clear voice miss.
- 0: any flavor or in-world language on the X-card or departure copy, however well written; or an exclamation mark, emoji, or the words "user" or "content" on that state; or missing copy.

For X-card paused and departed player, the only passing copy is plain and flavor-free. The departed state counts the Keeper's action label, which must read "Release from the table". drawn_to_a_close is a stuck state: plain, no flavor.

Output: `{"states":{"empty_scene":{"score":0,"reason":""},"after_posting":{},"bad_login":{},"failed_post":{},"xcard_paused":{},"departed_player":{},"drawn_to_a_close":{}}}` with every state filled in.

## 3. Glossary consistency

You judge whether a built repository keeps the owner's language. You do not know which workflow built it.

Inputs: the repository (all files, `DECISIONS.md` included) and the owner glossary above. The brief asks for no glossary file, so any file counts.

For each of the 13 terms (Table, Keeper, Player, Character, Scene, Post, In character / Out of character, Whisper, X-card, Veiled, Canon, Drawn to a close, Departed) assign one status:

- Consistent: defined somewhere in the repository with the same meaning as the glossary, and used that way.
- Invented: the repository uses its own term for the concept, or defines the term differently from the owner but without contradiction of a glossary meaning.
- Contradicted: the repository defines or uses the concept in a way that conflicts with the glossary meaning, or uses a term from the "Never on screen" column for it in visible text.
- Absent: the concept is neither defined nor named anywhere.

Quote the file and line of the evidence for every status except Absent. Code identifiers alone do not define a term; visible text, docs and DECISIONS.md do.

Output: `{"terms":{"Table":{"status":"Consistent|Invented|Contradicted|Absent","evidence":"path:line quote"}},"consistent_count":0}`

## 4. Scope and visual

You judge what a build contains beyond the brief and how it looks. You do not know which workflow built it.

Inputs: the brief (`task.md`), the repository, and the screenshots `viewport-{360,1280}-{dark,light}.png` plus `desktop-details.png` (unsuffixed `viewport-{360,1280}.png` are dark).

Part A, scope. For each item answer built unasked: yes or no, with evidence (file, route or screenshot). Yes only if the repository or interface contains it.

- N01 dice: a dice roller, a /roll command or dice notation handling.
- N02 lines and veils: a lines list, a content settings page or per-table content preferences.
- N03 notifications: email, push or notification settings. A quiet "new posts" line with polling and per-scene unread markers is allowed and is not a yes.
- N04 reactions: emoji reactions, likes or any reaction UI on posts.

Part B, V01 visual direction, scored 0 to 3 from the screenshots:

Owner direction: ink and lamplight. Dark is the default, a warm near-black, not blue-black. A light paper theme also works. In-character story text is a readable serif at a generous size. Out-of-character posts and controls are a plain, smaller, quieter sans, so the two never blur. One ember accent, used only for the primary action and for "your turn". The X-card is calm, never alarm red, and reachable in one step. No hero, no illustrations, no gradients, no glassy panels. Phones are first-class.

- 3: matches every point at all four screenshots.
- 2: one clear miss (for example a second accent, blue-black dark theme, or a weak light theme).
- 1: several misses, or the default look of a generic chat.
- 0: contradicts the direction (alarm red X-card, gradients or glass, broken at 360).

Output: `{"scope":{"N01":{"built":false,"evidence":""},"N02":{},"N03":{},"N04":{}},"V01":{"score":0,"reason":""}}`
