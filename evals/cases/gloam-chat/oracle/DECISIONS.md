# Reference decisions

This is the calibration reference the graders and judges compare against, not a contestant.
It implements the owner's answers in evals/operators/gloam-owner.json as written.

## Stack

Python standard-library HTTP server, SQLite at DATABASE_PATH, one vanilla HTML file with
inline CSS and JavaScript. No dependencies and no external assets. Rejected: a Node or
Python web framework, which adds installation work without changing the contract.

## Agreed rules

- Vocabulary: table, Keeper, player, character, scene, post, in character / out of character,
  whisper, X-card, veiled, canon, drawn to a close, departed, "Release from the table".
  None of the glossary's banned words appear on screen.
- Voice: the five owner lines verbatim. Flavor only where people wait or arrive (login,
  empty scene, after posting); plain where people are stuck; none on the X-card,
  departures or closing. No exclamation marks or emoji.
- Whispers: Keeper to any player, player only to the Keeper. Others never see them in
  scene views, search or canon status. They stay private after a close or a departure.
- X-card: anyone taps, with or without a post. The tapper is never stored. It pauses
  in-character posting; out of character stays open; only the Keeper resumes. A pointed
  post is veiled for everyone, kept in the database, never unveiled.
- Characters: a player speaks only as their own character (a foreign name is refused).
  The Keeper names every in-character post; an unnamed one is refused.
- Canon: the author edits or withdraws a post until someone else posts after it in a way
  the author can see. Then nobody changes it.
- Departure: only the Keeper releases a player. Their sessions end at once, their posts stay
  and are marked departed, their whispers stay with the Keeper.
- Failed post: the composer keeps the text, says "Your post didn't reach the table. It's
  still here. Send it again." Each draft carries a key, so a resend is kept once.
- Damaged data: startup runs an integrity check and refuses on a missing or damaged
  database, changing nothing. Only `benchmark.sh reset` seeds. Unwritable storage answers
  503 and the composer keeps the draft.
- Order: one lock serializes storage, so posts land in arrival order. A stale edit gets 409
  with the newer post; the editor keeps the user's text and shows the newer text.
- Closing: only the Keeper draws a scene to a close; then no posts, edits, X-card or resume.
- Look: ink and lamplight. Warm near-black by default, paper theme when the system asks for
  light, serif for in-character text, smaller quieter sans for everything else, one ember
  accent on the primary action, a calm X-card one step from every scene.

## Assumptions

- Only the Keeper starts scenes. Rejected: players starting scenes, which the owner never
  mentioned.
- Out-of-character posts show the player's email, or "Keeper". Rejected: display names,
  which the brief does not seed.
- Dark is the theme unless the system prefers light. Rejected: a stored theme toggle.
- Excluded: dice, lines and veils, notifications, reactions, the optional "new posts" line,
  unread markers and the "your turn" accent, all left out to keep the reference small.
