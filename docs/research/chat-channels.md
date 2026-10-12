# Chat channels: chat-native agents as the factory's conversation channel

What the chat-native agent products do today, and how the factory could use a chat thread next to the pull request it uses now. Researched 2026-10-12 from vendor docs, read live. Where a vendor page refused the fetch (HTTP 403), the claim cites the page that was read instead, and says so.

Links are reference-style and resolve in [Sources](#sources).

## What the factory needs from a channel

Taken from `skills/factory-shared/gates.md` (Headless mode) and `runner/factory_run.py`.

| ID | Need | Today, on the pull request |
| --- | --- | --- |
| N1 | Post a question and know when it was asked | The skill posts one PR comment and sets `waiting_since` to its `created_at` |
| N2 | Collect the approvers' replies after that time | `pull_request()` reads PR comments and review bodies. `pass_change()` keeps approvers' notes after `waiting_since` and appends them to the prompt, capped at `MAX_REPLY_BYTES` |
| N3 | An approval by a verified person | `approver_reviews()`: APPROVED reviews by logins in `--approvers`. The runner's own login is removed from that set in `main()` |
| N4 | An approval bound to exact content | `verify()`: `approve <gate>` counts only when the document's blob hash at the review's `commit` equals the current hash. `sign off slice NN` needs the review's commit to contain the slice's `head_commit` |
| N5 | Revocation | A later CHANGES_REQUESTED review by the same approver revokes their earlier approvals |
| N6 | A trigger for the next pass | Cron or CI runs `factory_run.py`, which takes a lock and passes over every `factory/*` branch |

## What each named product is

| Name used | What it refers to | Evidence |
| --- | --- | --- |
| Claude Tag | Anthropic's Slack integration that runs `@Claude` in team channels as the organization's shared identity. Public beta, Team and Enterprise only | [ct-overview], [cc-tag] |
| Claude in Slack | Two things. The earlier "Claude Code in Slack" runs each session under one user's own Claude account, Pro and Max only, in workspaces not connected to Claude Tag. In connected workspaces it is "retired effective October 5, 2026" | [cc-slack] |
| `/install-slack-app` | A Claude Code command: "Install the Claude Slack app. Opens a browser to complete the OAuth flow" | [cc-commands] |
| OpenClaw | A self-hosted, MIT-licensed gateway that connects Slack, Telegram, Discord, WhatsApp and 20+ more chat apps to an agent, and can spawn Claude Code, Codex, Cursor, Gemini CLI and others over ACP into a chat thread. Created by Peter Steinberger, formerly Clawdbot and Moltbot | [oc-gh], [oc-wiki], [oc-acp] |
| OpenClaw in Pond | A Pond source adapter that reads `~/.openclaw`. Pond also has adapters for `grok-build` and the Devin CLI | [pond] |
| dots | Most likely OpenAI's "dots": always-on agents in ChatGPT, each with its own cloud computer, reachable from ChatGPT, Slack and Teams, that delegate coding to Codex. Announced 2026-09-29. The only other "dots" found in AI is rednote-hilab's `dots.llm1` model (June 2025), which is a model, not an agent product, so the name is not ambiguous in this sense | [dots-docs], [dots-date], [dots-llm1] |
| Grok bot | xAI's Grok Bot: "AI teammates" on a persistent cloud computer, launched in beta 2026-08-11, with shared Team Bots that get their own Slack handle. Its docs say it "runs only on Cursor-hosted cloud computers" and is included with Cursor plans | [grok-wiki], [grok-team], [grok-sec], [grok-faq] |
| Grok coding agent | Grok Build, xAI's coding CLI. It runs headless (`grok -p`) and as an ACP agent. Released under Apache 2.0 on 2026-07-16. Community bridges drive it from Telegram | [grok-build], [grok-wiki], [grok-tg] |
| Grok in X or Telegram | Chat assistants. I found no primary source that either spawns coding sessions. The Telegram partnership is known only from press coverage of a 2025-05-28 announcement that Musk disputed | [grok-tgdeal] |

## Capability tables

Short answers. Details per product follow the tables.

### A. Spawn, harness, repository, reporting, identity

| Platform | Chat spawns a session by | Harness or model | Repository access | Reports and asks | Requester identity exposed |
| --- | --- | --- | --- | --- | --- |
| P1 Claude Tag | `@Claude` in a channel, thread or DM. A task gets a working session in the thread. Replies continue it, and anyone in the channel can steer ([ct-how]) | "the same engine that powers Claude Code on the web". No model named ([ct-how]) | Clones GitHub repositories granted to the Claude GitHub App. Usually ends in a draft PR authored by the app ([ct-how], [ct-id]) | Checklist edited in place in the thread, replies, files, artifacts ([ct-how]) | In channels it acts as service accounts, not as the requester. In 1:1 DMs it runs on the requester's account ([ct-id]) |
| P2 Claude Code in Slack (earlier) | `@Claude` in a channel. Routes coding intent to a cloud session ([cc-slack]) | Claude Code cloud session ([cc-slack]) | Repositories the user connected at claude.ai/code. PRs under the user's GitHub ([cc-slack], [ct-id]) | Status updates in the thread, @mentions the user at the end with View Session and Create PR ([cc-slack]) | The user's own linked Claude account ([cc-slack]) |
| P3 Claude Code channels | An MCP server pushes a chat message into an already running local session. Telegram, Discord, iMessage plugins, or your own ([cc-channels]) | The local Claude Code session ([cc-channels]) | Whatever the local session has ([cc-channels]) | A `reply` tool the server exposes. Tool permission prompts can be relayed to chat ([cc-chref]) | Whatever the channel server puts in `meta`. The server must gate on the sender ID ([cc-chref]) |
| P4 Claude Code routines | Not chat. A schedule, a `POST .../fire` with a bearer token, or a GitHub `pull_request` or `release` event ([cc-routines]) | Claude Code cloud session, model chosen per routine ([cc-routines]) | Selected GitHub repositories, pushes to `claude/` branches ([cc-routines]) | A new session per run, with a URL ([cc-routines]) | None. Runs as the routine's owner ([cc-routines]) |
| P5 OpenClaw | `/acp spawn <harness> --thread auto` or a plain request routed to ACP. Follow-ups in the bound thread go to the session ([oc-acp]) | Claude Code, Codex, Cursor, Copilot, Gemini CLI and others over ACP, or OpenClaw's own runtime ([oc-acp], [oc-gh]) | The host machine's files and credentials, per `cwd`. "Tools run on the host for the main session unless you configure sandboxing" ([oc-gh], [oc-acp]) | Output delivered back to the bound thread ([oc-acp]) | Verified native Slack user IDs when signature checks pass. Display names never establish identity ([oc-slack-ac]) |
| P6 OpenAI dots | Slack DM, or a mention in a channel thread. "Only the owner can direct their dot" ([dots-admin], [dots-channels]) | "Powered by GPT-6 Astra". Delegates coding to Codex cloud tasks ([dots-docs]) | Through a Codex cloud environment and connected plugins such as GitHub ([dots-docs]) | Activity view, notifications, questions in ChatGPT or Slack ([dots-tasks], [dots-channels]) | The dot's owner only. Others' messages do not start work ([dots-admin]) |
| P7 Grok Team Bots | DM or @mention of the bot's Slack app. It follows the thread afterwards ([grok-team]) | Not named. Can start "Cloud Agents" from Slack ([grok-team], [grok-faq]) | Not documented for Team Bots ([grok-team]) | Thread replies. Approval cards for actions ([grok-team]) | Answers only Slack users linked to a Cursor account on the bot's team ([grok-team]) |
| P8 Grok Build | No chat surface of its own. Community Telegram bridges run one `grok` process per chat over ACP ([grok-tg]) | Grok Build CLI, Grok 4.7 or a custom model ([grok-build]) | Local checkout ([grok-build]) | Through the bridge ([grok-tg]) | Whatever the bridge checks ([grok-tg]) |
| P9 GitHub Copilot cloud agent | An issue, the agents panel, a PR, the REST API, `gh`, or `@GitHub` in Slack, Teams, Jira, Linear ([gh-start], [gh-slack]) | Copilot in an ephemeral cloud environment. Model depends on the entry point ([gh-about]) | The one repository named at start. One branch, one PR per task ([gh-about]) | Session logs, a PR, a summary back in Slack ([gh-about], [gh-slack]) | Linked GitHub account. Needs write access ([gh-slack], [gh-risks]) |
| P10 Cursor cloud agents | `@cursor` in Slack starts a Cloud Agent. A mention in its thread adds follow-ups ([cu-slack]) | Cursor Cloud Agent, model inline (`model=opus`) or default ([cu-slack]) | Repository detected from the message, rules, channel or user default ([cu-slack]) | Plan and updates in the thread, a PR link at the end ([cu-slack]) | Slack users matched to Cursor accounts ([cu-slack]) |
| P11 Devin | `@Devin` in Slack, `/ask-devin`, or a message shortcut ([dv-slack]) | Devin ([dv-slack]) | Not described for Slack sessions ([dv-slack]) | Replies in the thread with updates and questions ([dv-slack]) | Slack user matched to a Devin account by email ([dv-slack]) |
| P12 Codex via ChatGPT in Slack, `@codex` on GitHub | `@ChatGPT` in Slack delegates repository work to a Codex Cloud task. `@codex <task>` on a PR starts a cloud chat ([cx-slack], [cx-gh]) | Codex Cloud ([cx-slack]) | Workspace-shared Cloud environments ([cx-slack]) | Result returned to the Slack thread. Allow and Deny on a private card ([cx-slack]) | The requester's linked account ([cx-slack]) |

### B. Approvals, API, hosting, price, untrusted input

| Platform | Approval tied to a verified user and to a commit or hash | API or webhook a runner could use | Self-host or open source | Price tier | Untrusted chat input |
| --- | --- | --- | --- | --- | --- |
| P1 Claude Tag | No. No approval primitive beyond "Approve and post" and connector consent cards ([ct-how], [ct-pc]) | No public API or outbound webhook described ([ct-how]). It can subscribe to one PR's activity ([ct-pro]) | Hosted. Sessions can run on a self-hosted environment's runners ([ct-sec]) | Team and Enterprise. Channel work bills by usage under a spend limit ([ct-overview]) | Reads every channel message. Bot posts are context only, a reply needs `@Claude`. With personal connectors it takes direction from the owner and treats others' posts "as information" ([ct-when], [ct-id]) |
| P2 Claude Code in Slack | No ([cc-slack]) | None documented ([cc-slack]) | Hosted ([cc-slack]) | Pro and Max ([cc-slack]) | "Claude may follow directions from other messages in the context" ([cc-slack]) |
| P3 Claude Code channels | Partly. Permission relay binds a 5-letter `request_id` to one tool call, and only allowlisted senders can answer. Nothing binds to a document hash ([cc-chref]) | The channel contract is the API: `notifications/claude/channel`, a reply tool, `permission_request` ([cc-chref]) | Runs locally. Plugin source is public ([cc-channels]) | Any plan. Team and Enterprise must enable `channelsEnabled` ([cc-channels]) | "An ungated channel is a prompt injection vector". Gate on sender ID, not room ID ([cc-chref]) |
| P4 Claude Code routines | No. The bearer token proves the caller holds the token, not who they are ([cc-routines]) | `POST /v1/claude_code/routines/<id>/fire`, returns a session URL ([cc-routines]) | Hosted, or a self-hosted environment ([cc-routines]) | Pro, Max, Team, Enterprise. 100 API fires an hour per account ([cc-routines]) | Fire `text` arrives in a `<routine-fire-payload>` block labeled untrusted ([cc-routines]) |
| P5 OpenClaw | Partly. Exec approvals come from configured approver IDs and bind "cwd, exact argv, env". Not a document or commit ([oc-slack-rich], [oc-exec]) | `POST /hooks/agent` and `/hooks/wake` with a bearer token ([oc-hooks]) | MIT, self-hosted ([oc-gh]) | No paid tier ([oc-gh]) | "Treat inbound messages as untrusted input". One trust boundary per gateway, not multi-tenant ([oc-gh], [oc-sec]) |
| P6 OpenAI dots | No. Actions pass an automatic review that may ask the owner ([dots-controls]) | None documented ([dots-docs], [dots-channels]) | Hosted ([dots-docs]) | Pro 100, 200, 500, Business Premium, Enterprise (off by default) ([dots-docs]) | "Built-in safeguards help defend against malicious instructions" ([dots-admin]) |
| P7 Grok Team Bots | No. Approval cards are answered by the person whose connector is used ([grok-team]) | None documented ([grok-faq]) | Hosted on Cursor computers only ([grok-sec]) | Cursor plans or SuperGrok ([grok-faq]) | Outside content is labeled untrusted, which "reduces but does not eliminate" the risk. A Bot is not a security boundary ([grok-sec]) |
| P8 Grok Build | No ([grok-build]) | `grok -p` and `grok agent stdio` (ACP) ([grok-build]) | Apache 2.0 ([grok-wiki]) | SuperGrok, $30 a month ([grok-wiki]) | Reported in July 2026 to upload whole repositories including secrets, fixed server-side the same day ([grok-wiki]) |
| P9 Copilot | Partly, inside GitHub. Comments from users without write access "are never presented to the agent", and the requester cannot approve the PR ([gh-risks]) | REST API, `gh`, events ([gh-start]) | Hosted ([gh-about]) | Depends on plan ([gh-about]) | Hidden characters filtered. Captures the whole Slack thread as context ([gh-risks], [gh-slack]) |
| P10 Cursor | No ([cu-slack]) | `POST /v1/agents`, follow-ups, SSE stream. v1 webhooks "coming soon" ([cu-cloudapi]) | Hosted. Self-hosted Team Pools on Enterprise ([cu-slack]) | Usage-based pricing must be on ([cu-slack]) | Not addressed on the Slack page ([cu-slack]) |
| P11 Devin | No ([dv-slack]) | `POST /v3/organizations/<org>/sessions`. Automations with a webhook trigger and secret ([dv-api], [dv-auto]) | Hosted ([dv-slack]) | Not checked | Reads thread history when launched in a thread ([dv-slack]) |
| P12 Codex | No. Allow and Deny cards approve agent actions ([cx-slack]) | Codex SDK and app-server exist. Slack flow has none documented ([cx-slack]) | Hosted ([cx-slack]) | Enterprise shared environments. Tiers not listed ([cx-slack]) | Does not discuss prompt injection on the Slack page ([cx-slack]) |

## Notes by platform

Only what the tables leave out and the design needs.

- **P1 Claude Tag.** Each thread gets its own sandbox, released when the session ends its turn. Edits reach Claude as old and new text, and deleted replies are not reported ([ct-how]). Credentials stay out of the sandbox and are injected by Agent Proxy, which is default-deny for egress ([ct-id], [ct-sec]). By default anyone in the paired workspace can use it, and Owners can narrow that to organization members or roles ([ct-sec]). Its PR subscription is the one way it reacts to GitHub, and it cannot fire on other repository events ([ct-pro]).
- **P3 Claude Code channels.** Research preview. Events arrive only while the session is open. In `-p`, tools that need terminal input are disabled. A custom channel needs `--dangerously-load-development-channels`, which `-p` ignores ([cc-channels], [cc-chref]). Relay covers tool approvals such as Bash and Write, not project trust dialogs ([cc-chref]).
- **P4 Routines.** GitHub triggers cover pull requests and releases only, so a routine cannot wake on a review ([cc-routines]). Runs need no approval, and pushes are checked against the GitHub access you connected ([cc-routines]).
- **P5 OpenClaw.** DM senders are paired by default (`dmPolicy: pairing`). Channel allowlists use stable Slack channel IDs. Relay-mode events are only "asserted", since the gateway authenticates the relay, not the Slack sender ([oc-slack-ac]). For the `claude-cli` backend, OpenClaw checks Bash against its exec allowlist, but Claude Code still owns execution and gets no OpenClaw sandbox ([oc-exec]). The Register's review of 2.0 noted no sandbox by default and secrets not encrypted at rest ([oc-wiki]).
- **P6 dots.** In workspaces, both "Use dots" and "Add dots to Slack" must be enabled per member ([dots-admin]). "A completed run doesn't by itself confirm that the requested result was achieved" ([dots-tasks]).
- **P7 Grok Team Bots.** Slack channels, group DMs and threads share one computer, and every teammate's conversation can use every secret ([grok-team]).
- **P9 Copilot.** Actions workflows on its PRs wait for approval by someone with write access. It cannot approve or merge its own PR ([gh-risks]). Sessions stop at 59 minutes ([gh-about]).

## Findings

| ID | Finding | Source |
| --- | --- | --- |
| F1 | No chat-native product offers an approval bound to a verified person and to a commit or document hash. Each one ends in a pull request, and the code review happens there | Tables A and B |
| F2 | The hosted agents (P1, P2, P6, P7, P9 to P12) run their own harness in the vendor's sandbox. The runner's protections do not apply there: the throwaway clone, the trusted-head check, and approvals re-derived from reviews | [ct-how], [dots-docs], [grok-sec], [gh-about], `runner/factory_run.py` |
| F3 | Slack lets a runner re-read who wrote what from Slack itself. `conversations.replies` returns each message's `user` and works with a bot token, and an edited message carries an `edited` property | [sl-replies], [sl-msg] |
| F4 | Telegram's Bot API keeps undelivered updates for at most 24 hours. I found no method for a bot to re-read group history, so a Telegram approval could be checked only once, when it arrives | [tg-api] |
| F5 | Socket Mode receives Slack events without a public URL, but events can be lost while the socket is down | [sl-socket] |
| F6 | GitHub sends `pull_request_review` and `issue_comment` webhooks, which can wake the runner without cron | [gh-webhooks] |
| F7 | Two vendor patterns match the factory's: Copilot drops comments from users without write access, and Claude Code channels gate on sender ID, not room ID | [gh-risks], [cc-chref] |

The user's premise holds for the conversation: chat is becoming where agent work starts and where questions go. It does not hold for approvals. Every product in this list still uses a PR review as the record that a person accepted the code (F1).

## Channel adapter design

### D1. Scope: questions and replies first, approvals stay on the pull request

The PR channel stays the record of every approval. A chat adapter adds three things: it mirrors questions, collects replies, and wakes the runner. Gate approvals can move to Slack later (D3), but only on Slack. `start` and slice sign-offs stay on the PR. `start` authorizes the runner to run a harness, and a sign-off says the approver read the diff, which the PR shows at that commit.

### D2. Questions and replies map to one thread per change

- When an approver's `start` review first appears, the runner posts one root message in a configured Slack channel: the slug, the branch and the PR link. It keeps `branch -> (channel, thread_ts)` in a runner-local file next to `factory-runner-heads.json`, so `status.yaml` keeps its schema.
- Skills do not change. They still post the question as a PR comment and set `waiting_since`. On its next pass the runner copies each PR comment by the harness's login (the login `main()` removes from the approvers) that is newer than the last one it mirrored into the thread, with the PR comment link.
- Replies: in `pass_change()`, the runner adds thread messages after `waiting_since` to `notes`, in the same `{login, body, at}` shape, before the existing filter. A message counts only when its Slack `user` maps to an approver login, it has no `bot_id` or `subtype`, and it has no `edited` property ([sl-msg]). The runner converts Slack's `ts` to the same UTC format as GitHub times before comparing.
- Identity mapping: `--chat-approvers alice=U123ABC,bob=U456DEF`. Every key must already be in `--approvers`, so revocation works across channels: a CHANGES_REQUESTED review on GitHub also revokes Alice's Slack approvals.

### D3. Gate approvals in Slack (second step, Slack only)

An approval message in the thread, by a mapped approver:

```text
approve architecture
<full 40-hex commit sha>
```

The adapter turns it into the same record `approver_reviews()` returns: `{login, state: "APPROVED", body, commit: <line 2>, at}`. `command()` reads line 1 as it does now, and `verify()` hashes the document at that commit as it does for a review. `verify()` needs no change. A message `revoke` becomes a CHANGES_REQUESTED record. The adapter drops `start` and `sign off slice` messages, since D1 keeps both on the PR. A Slack approval at the branch head also makes that head trusted in `pass_change()`, the same as a review at the head does today. To keep the approver from approving blind, the runner's request in the thread links the document at that commit (`.../blob/<sha>/<path>`) and prints its sha256.

Comparison with a PR review:

| Property | PR review | Slack message (D3) |
| --- | --- | --- |
| Who | GitHub login, from GitHub's API | Slack user ID, from `conversations.replies`, mapped to a login ([sl-replies]) |
| What | The review's `commit` | The commit typed in the message, hashed by `verify()` |
| Re-derived every pass | Yes | Yes, from Slack history (F3) |
| Can the agent forge it | No. The runner's login is excluded | No. Bot messages carry `bot_id` and are dropped. The harness never gets a Slack token (D5) |
| Lost if deleted | Reviews are rarely deleted | Slack retention or a deleted message removes it. The gate falls back to pending, which is safe |

Platforms where D3 does not apply: Telegram (F4), and every hosted agent (F2). There, approvals stay on the PR.

### D4. Event-triggered runner passes replace cron

- One listener process holds a Slack Socket Mode connection ([sl-socket]) and, optionally, a GitHub webhook endpoint for `pull_request_review` and `issue_comment` ([gh-webhooks]). On an event for a known thread or `factory/*` PR, it runs one runner pass for that branch. The pass already takes the lock and re-reads everything from git, GitHub and Slack.
- The event is only a signal to run a pass. The runner ignores its contents, so a forged or replayed event can at most cause an extra pass.
- Keep an hourly cron as a backstop, since Socket Mode can drop events while disconnected (F5).
- Not chosen: Claude Code routines can't wake on reviews and run outside the runner's checks (P4). Claude Tag's PR subscription posts into Slack and has no outbound hook (P1). OpenClaw `/hooks/agent` would make OpenClaw, not the runner, the writer (P5).

### D5. Chat text stays untrusted data

- Only messages from mapped approver IDs in the change's own thread get through. The runner gates on the sender, not the channel ([cc-chref]). It does not read the rest of the channel or thread history, unlike P2 and P9, which take the whole thread as context ([cc-slack], [gh-slack]).
- Replies reach the harness only inside the existing "Replies from the pull request, by approvers" block, renamed to name both channels, and capped by `MAX_REPLY_BYTES`. Skills already treat only that block as the user's answers (gates.md, Headless mode).
- The Slack bot token lives only in the runner and listener. The harness runs in its throwaway clone without it, as it runs without the runner's state today, so a prompt-injected harness cannot post as the bot or approve anything.
- Edited messages are dropped, so a reply or approval cannot change after it was posted.

### D6. Which platforms first

1. **Slack, through a runner-owned Slack app in Socket Mode.** It is the only common chat surface where the runner can re-read who approved what from the platform (F3), and every hosted product in this list already lives there. Ship D2 and D4 first, then D3.
2. **Telegram, for notifications only.** It suits a solo user without Slack, but approvals cannot be checked again later (F4).
3. **Hosted agents as spawn surfaces, not as the channel.** Claude Tag, Copilot or Cursor can open a PR from a chat thread. The factory can then pick that PR up only through a normal headless `start` review, and the trusted-head rule already blocks pushes it did not make.

For interactive mode, Claude Code channels (P3) already relay tool approvals to Telegram or Discord with sender allowlists. That covers the user being away from the terminal during `/factory-build`, with no factory code.

## Gaps and fallbacks

| ID | Gap | Fallback |
| --- | --- | --- |
| G1 | No platform binds an approval to a hash (F1) | D3 puts the commit in the approver's own message, and `verify()` hashes it |
| G2 | Telegram history cannot be read again (F4) | Questions and notifications only. Approvals on the PR |
| G3 | Socket Mode can lose events (F5) | Hourly cron backstop. Every pass re-reads all state |
| G4 | `conversations.replies` is limited to 1 request a minute for new commercially distributed non-Marketplace apps ([sl-replies]) | An internal app installed in one workspace is not in that class. One call per waiting change per pass |
| G5 | Slack retention can delete approval messages | The gate falls back to pending and the approver approves again. Approvals that must be kept long-term go on the PR |
| G6 | Hosted agents run outside the runner's checks (F2) | Use them only to open PRs. The factory applies its gates to the PR |
| G7 | Typing a 40-hex sha in Slack is awkward | The runner's request message contains the exact two-line approval text to copy |

## Could not confirm

- Q1. Whether Claude Code relays AskUserQuestion through a channel. The docs name only tool approvals such as Bash, Write and Edit ([cc-chref]).
- Q2. Whether a Telegram bot can read past group messages. `getUserPersonalChatMessages` is listed in the Bot API changelog, but the part of the page I read did not describe it ([tg-api]).
- Q3. openai.com's dots announcement, the help center's dots FAQ and x.ai's Grok Bot pages returned HTTP 403. The dots launch date comes from press coverage ([dots-date]), and the Grok Bot launch date from Wikipedia ([grok-wiki]).
- Q4. Who may post `@codex <task>` on a PR, and which identity that cloud chat runs under ([cx-gh]).

## What this does not cover

- Claude Code GitHub Actions (`@claude` in PR comments), Linear agents, Microsoft Teams bots and Discord history APIs.
- Pricing beyond the tier names on the pages read. Devin's pricing was not checked.
- Building or testing any adapter. Nothing here was run.
- Slack Enterprise Grid admin powers over user accounts, which decide how far a Slack user ID can be trusted in a given workspace.
- Changes to `status.yaml`, skills or the runner. D2 and D3 are designs to approve first.

## Sources

[cc-tag]: https://code.claude.com/docs/en/claude-tag
[cc-slack]: https://code.claude.com/docs/en/slack
[cc-commands]: https://code.claude.com/docs/en/commands
[cc-channels]: https://code.claude.com/docs/en/channels
[cc-chref]: https://code.claude.com/docs/en/channels-reference
[cc-routines]: https://code.claude.com/docs/en/routines
[ct-overview]: https://claude.com/docs/claude-tag
[ct-how]: https://claude.com/docs/claude-tag/concepts/how-it-works
[ct-id]: https://claude.com/docs/claude-tag/concepts/agent-identity
[ct-pc]: https://claude.com/docs/claude-tag/concepts/agent-identity#personal-connectors-in-a-channel
[ct-sec]: https://claude.com/docs/claude-tag/concepts/security-and-data
[ct-pro]: https://claude.com/docs/claude-tag/users/proactivity
[ct-when]: https://claude.com/docs/claude-tag/users/when-claude-responds
[oc-gh]: https://github.com/openclaw/openclaw
[oc-wiki]: https://en.wikipedia.org/wiki/OpenClaw
[oc-acp]: https://docs.openclaw.ai/tools/acp-agents
[oc-sec]: https://docs.openclaw.ai/gateway/security
[oc-slack-ac]: https://docs.openclaw.ai/channels/slack/access-control
[oc-slack-rich]: https://docs.openclaw.ai/channels/slack/rich-messages
[oc-exec]: https://docs.openclaw.ai/tools/exec-approvals
[oc-hooks]: https://docs.openclaw.ai/automation/cron-jobs/webhooks
[pond]: https://github.com/tenequm/pond
[dots-docs]: https://learn.chatgpt.com/docs/dots
[dots-channels]: https://learn.chatgpt.com/docs/dots/channels
[dots-tasks]: https://learn.chatgpt.com/docs/dots/tasks-and-memory
[dots-controls]: https://learn.chatgpt.com/docs/dots/controls
[dots-admin]: https://learn.chatgpt.com/docs/enterprise/dots-admin-guide
[dots-date]: https://www.forbes.com/sites/fionariley/2026/09/29/openai-unveils-new-ai-assistant-dots-heres-what-it-does/
[dots-llm1]: https://huggingface.co/docs/transformers/v5.14.0/model_doc/dots1
[grok-wiki]: https://en.wikipedia.org/wiki/Grok_(chatbot)#Grok_Build
[grok-build]: https://docs.x.ai/build/overview
[grok-team]: https://docs.x.ai/grok-bot/team-bots
[grok-sec]: https://docs.x.ai/grok-bot/security
[grok-faq]: https://docs.x.ai/grok-bot/faq
[grok-tg]: https://github.com/artickc/grok-telegram-bot
[grok-tgdeal]: https://www.yahoo.com/news/durov-announces-telegrams-partnership-musks-065148709.html
[gh-about]: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent
[gh-start]: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/start-copilot-sessions
[gh-risks]: https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations
[gh-slack]: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/integrate-cloud-agent-with-slack
[gh-webhooks]: https://docs.github.com/en/webhooks/webhook-events-and-payloads
[cu-slack]: https://cursor.com/docs/integrations/slack
[cu-cloudapi]: https://cursor.com/docs/cloud-agent/api/endpoints
[dv-slack]: https://docs.devin.ai/integrations/slack
[dv-auto]: https://docs.devin.ai/product-guides/automations
[dv-api]: https://docs.devin.ai/use-cases/gallery/api-webhook-custom-ticketing
[cx-slack]: https://learn.chatgpt.com/docs/third-party/slack
[cx-gh]: https://learn.chatgpt.com/docs/third-party/github
[sl-replies]: https://docs.slack.dev/reference/methods/conversations.replies
[sl-msg]: https://docs.slack.dev/reference/events/message
[sl-socket]: https://docs.slack.dev/apis/events-api/using-socket-mode
[tg-api]: https://core.telegram.org/bots/api
