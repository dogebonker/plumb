# Checks: slice 03, new-ticket

Range: 7f02116..4b66b4a (recovered checkpoints, not the original commit identities)
- Allowed files: pass (7f02116..4b66b4a changes only store.js, app.js, index.html; all are in the packet's Allowed files; no deviation entries)
- Frozen contract: pass (`TicketRepo.create(input)` present in store.js and returns `{ticket}` or `{errors}` as in 03-interface.md; the five create tests and 12 browser tests exercise it)
- Red tests unchanged: pass (no test file differs between 7f02116 and 4b66b4a)
- Red: 7f02116 (recovered RED, not the original red commit 2acf68a) failed on the 5 new create tests in `node --test test_store.cjs` (12 pass, 5 fail: tests 13 to 17). Green: 4b66b4a passes; branch head 8bc1ee5 has no code change since 4b66b4a (only .factory/ files). At head `node --test test_store.cjs` gives 17 of 17 and `/private/tmp/fb-neamoi0s/browser-check/browser-check` gives 35 pass, 0 fail (17 dashboard browser tests, test_existing.cjs, and the store tests it runs), exit output ending `# pass 35 # fail 0`.
- Lint: skipped (no check_command)

Provenance (honest record): the original temporary repository was deleted. The original slice 03 commits (RED 2acf68a, GREEN 03c6d91) and the historical slice 01/02 git objects are unavailable. 7f02116 and 4b66b4a are recovery checkpoints made by replaying recorded edits, as recovery.md states. The red proof above is a fresh checkout of the recovered RED, not the original. These checks are fresh verification of the recovered tree. The browser-check output was read from the run's tool result, not saved to a file (the tool cannot be redirected in this sandbox).
