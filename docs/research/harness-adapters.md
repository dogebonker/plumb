# Harness adapters: Claude Code, Codex CLI, Cursor

What each harness supports today, and how the factory could run on all three through one adapter file per harness. Researched 2026-10-12 from official docs, source code and changelogs, read live. Versions checked: Claude Code 2.1.296 ([cc-changelog]), Codex CLI 0.162.1 of 2026-10-09 ([cx-latest]), Cursor editor 3.23 ([cu-relnotes]) and Cursor CLI 2026.10.08 ([cu-clichangelog]). Claude Code's changelog has no dates, so its entries are given by version only.

Links are reference-style and resolve in [Sources](#sources). "Source:" means the claim was read in the harness's code on `main`, not only in its docs.

## What the factory needs from a harness

Taken from `skills/README.md`, `skills/factory-shared/gates.md`, `hooks/factory_gate.py`, `runner/factory_run.py` and the skills.

| ID | Operation | Where the factory uses it today |
| --- | --- | --- |
| O1 | Load a skill by name, with an argument. Skills are user-invoked only (`disable-model-invocation: true`) and read `$ARGUMENTS` | Every `skills/factory-*/SKILL.md` (`Slug: $ARGUMENTS`) |
| O2 | Ask the user a structured question | AskUserQuestion, counted by retro metric M1 (`factory-retro/metrics.md`) |
| O3 | Start a fresh sub-agent with only the given instructions. Choose a smaller model. Run several in parallel or in the background. A read-only agent type | build's executor, interface's panel ("all at once"), review's lens reviewers ("in the background"), architecture's research and retro's candidates (smaller model, `Explore`) |
| O4 | Know the session id | `Session: ${CLAUDE_SESSION_ID}` in nine skills, written into `step_start` events |
| O5 | Block a file edit before it happens | `hooks/factory_gate.py`, a Claude Code PreToolUse hook reading `tool_input.file_path` and exiting 2 |
| O6 | Run headless from a script with a prompt, and get an exit code | `runner/factory_run.py`: `HARNESS = "claude -p --setting-sources user --strict-mcp-config"`, prompt `/{skill} {slug}` passed as the last argument, exit code checked |
| O7 | MCP servers | Pond (`pond_search`, `pond_get_session`) in triage, product, slices, retro |
| O8 | Where user and project skills and instructions live | Install symlinks into `~/.claude/skills`. Triage reads `CLAUDE.md` / `AGENTS.md` |
| O9 | Transcript storage | Retro M1 to M3 read sessions through Pond. M7 reads `~/.claude/settings.json` |

## Capability matrix

Yes: works as the factory needs it. Partial: works with a documented limit or a different shape. No: not available. Unconfirmed: the docs and code did not settle it.

| Operation | Claude Code | Codex CLI | Cursor |
| --- | --- | --- | --- |
| O1 skill by name | Yes, `/name args` ([cc-skills]) | Partial, `$name` mention or `/skills` picker. No `/name` ([cx-skills], [cx-mentions]) | Yes, `/name`, also in `-p` ([cu-skills], [cu-clichangelog]) |
| O1 `$ARGUMENTS` | Yes, plus `$0`, `$ARGUMENTS[N]` ([cc-skills]) | No substitution anywhere in the skills code ([cx-fragments]) | Unconfirmed: args after `/name` are not documented ([cu-skills]) |
| O1 user-invoked only | Yes, `disable-model-invocation` ([cc-skills]) | Partial, ignores that key. `agents/openai.yaml` `policy.allow_implicit_invocation: false` instead ([cx-skills]) | Yes, `disable-model-invocation` ([cu-skills]) |
| O2 structured question | Yes, AskUserQuestion, 1 to 4 questions of 2 to 4 options. Not in sub-agents ([cc-tools], [cc-sub]) | Partial, `request_user_input` in Plan mode only. Rejected in `codex exec` and sub-agents ([cx-modes], [cx-exec-lib]) | Yes, ask-question tool in any conversation since 2.4 ([cu-24]). Headless unconfirmed |
| O3 fresh sub-agent | Yes, Agent tool ([cc-sub]) | Yes, `spawn_agent` with `fork_context` off ([cx-ma-spec]) | Yes, Task tool, clean context ([cu-sub]) |
| O3 model per agent | Yes, `model: sonnet` ([cc-sub]) | Yes, `model` on the spawn call or in the agent file ([cx-sub]) | Yes, `model:` in the agent file ([cu-sub]) |
| O3 parallel, background | Yes, background by default since 2.1.198, up to 20 ([cc-changelog]) | Yes, parallel, `wait_agent`. Default 6 threads, depth 1 ([cx-config-mod]) | Yes, `is_background`, parallel Task calls. Two levels: a sub-agent of a sub-agent cannot launch more ([cu-sub]) |
| O3 read-only agent | Yes, built-in Explore ([cc-sub]) | Partial, agent file with `sandbox_mode = "read-only"`, but a parent's live sandbox override carries over ([cx-sub]) | Yes, `readonly: true` in the agent file ([cu-sub]) |
| O4 session id | Yes, `${CLAUDE_SESSION_ID}` in skills, `CLAUDE_CODE_SESSION_ID` in Bash ([cc-skills], [cc-env]) | Partial, `$CODEX_THREAD_ID` in shell commands only ([cx-execenv]) | Partial, hooks only (`conversation_id`, `session_id`). Nothing reaches the model ([cu-hooks]) |
| O5 pre-edit block | Yes, PreToolUse, exit 2 ([cc-hooks]) | Partial, PreToolUse fires for `apply_patch`, but its input is patch text, not a path ([cx-applypatch]). Hooks run only once trusted ([cx-hooks]) | Partial, `preToolUse` matcher `Write`, exit 2. Claude hooks imported by default. Path field unconfirmed ([cu-hooks], [cu-3p]) |
| O6 headless | Yes, `claude -p` ([cc-headless]) | Yes, `codex exec` ([cx-exec-cli]) | Yes, `cursor-agent -p --force` ([cu-params]) |
| O7 MCP | Yes ([cc-mcp]) | Yes, `[mcp_servers.<name>]` ([cx-mcp]) | Yes, `mcp.json` ([cu-mcp]) |
| O8 reads `~/.claude/skills` | Yes | No ([cx-roots]) | Yes ([cu-skills]) |
| O8 reads `~/.agents/skills` | No ([cc-memory]) | Yes ([cx-roots]) | Yes ([cu-skills]) |
| O8 reads `AGENTS.md` | Partial, only when no `CLAUDE.md` exists, since 2.1.277 ([cc-memory]) | Yes ([cx-agentsmd]) | Yes, and `CLAUDE.md` too ([cu-rules], [cu-cliusing]) |
| O9 transcripts | Yes, JSONL, Pond adapter `claude-code` | Yes, JSONL with token counts, Pond adapter `codex-cli` | Partial, path undocumented, no Pond adapter seen |

All three read the open Agent Skills format and are listed as clients on [as-clients]. The spec defines only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools` ([as-spec]). `disable-model-invocation`, `argument-hint` and `$ARGUMENTS` are Claude Code extensions that Cursor partly copies. The client guide names `.agents/skills/` as the cross-client location and `disable-model-invocation` as a common way to hide a skill from the catalog ([as-client]).

## Claude Code (baseline)

**O1 skills.** `~/.claude/skills/<name>/SKILL.md`, `.claude/skills/`, nested `.claude/skills` in subdirectories (2.1.6), plugins and `--add-dir` ([cc-skills]). Invoked as `/name args`. Substitutions: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `${CLAUDE_SESSION_ID}` (2.1.9), `${CLAUDE_SKILL_DIR}` (2.1.69) ([cc-changelog]). Arguments that no placeholder uses are appended as `ARGUMENTS: <value>` ([cc-skills]). A `disable-model-invocation` skill can still be typed by the user ([cc-skills]). Not read: anything under `.agents/` ([cc-memory]).

**O2 ask.** AskUserQuestion takes "1-4 questions with 2-4 options each", with a free-text "Other" ([cc-tools]). It is removed from every sub-agent ([cc-sub]). In `-p` it needs a permission host such as an SDK callback ([cc-hooks]).

**O3 sub-agents.** Agent tool (renamed from Task in 2.1.63, `Task` still an alias) ([cc-sub]). Agent files in `.claude/agents/` and `~/.claude/agents/` take `model: sonnet|opus|haiku|fable|inherit` and a per-call `model` since 2.1.292 ([cc-sub]). Built-in Explore is read-only ([cc-sub]). Background agents since 2.0.60, background by default since 2.1.198, 20 at once, depth 3 since 2.1.219 ([cc-changelog]).

**O4 session id.** `${CLAUDE_SESSION_ID}` in skills. The Bash variable is `CLAUDE_CODE_SESSION_ID`, not `CLAUDE_SESSION_ID`, and it "matches the `session_id` field" of hooks ([cc-env]).

**O5 hook.** PreToolUse in `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed settings, plugins, skill or agent frontmatter ([cc-hooks]). Stdin: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`, `tool_input` (`file_path` for Write and Edit), and `agent_id`/`agent_type` inside sub-agents. Exit 2 blocks and feeds stderr to Claude. Exit 1 does not block. JSON `hookSpecificOutput.permissionDecision: "deny"` also blocks. It fires for sub-agent tool calls and in `-p` ([cc-hooks]). Hooks since 1.0.38 ([cc-changelog]). MultiEdit is not in the current tools table ([cc-tools]).

**O6 headless.** `claude -p "<prompt>"` with `--output-format text|json|stream-json`, `--setting-sources`, `--strict-mcp-config` ("Only use MCP servers from `--mcp-config`"), `--mcp-config`, `--permission-mode`, `--model`, `--max-turns`, `--resume` ([cc-cli]). Without a mode, a `-p` run starts in a default that "can be `auto`" ([cc-headless]). "Include `/skill-name` in the prompt string" to run a skill ([cc-headless]). Exit 0 on success, non-zero on failure ([cc-headless]).

**O7 MCP.** `claude mcp add --scope user|project|local`, `.mcp.json` at the repository root, `~/.claude.json` ([cc-mcp]).

**O8 instructions.** `~/.claude/CLAUDE.md`, `./CLAUDE.md` or `./.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`, `@path` imports ([cc-memory]). `AGENTS.md` is read since 2.1.277, by default "only when you have no `CLAUDE.md`" in the working directory or above. `pluginConfigs."cc-plugin-agents-md@builtin".options.instructionFiles = "claude-md-and-agents-md"` reads both ([cc-memory]).

**O9 transcripts.** `~/.claude/projects/<encoded cwd>/<session-id>.jsonl`, sub-agents under `<session-id>/subagents/agent-<id>.jsonl`, kept `cleanupPeriodDays` (30) days ([cc-sessions]).

## OpenAI Codex CLI

The docs at `developers.openai.com/codex` now redirect to `learn.chatgpt.com/docs`. Some pages lag the code: the CLI reference still lists `--full-auto`, removed from `exec` in 0.147.0, and the custom-prompts page still describes prompts whose support was removed in 0.118.0 ([cx-releases], [cx-prompts]).

**O1 skills.** Since 0.65.0 (2025-12-04), on by default since 0.76.0 ([cx-releases]). Roots, from source: `~/.agents/skills` (0.95.0), deprecated `$CODEX_HOME/skills`, `.agents/skills` in every directory from the project root down to the cwd (0.94.0), the project's `.codex/skills`, `/etc/codex/skills`, and plugins ([cx-roots]). It does not read `~/.claude/skills`. The user mentions `$skill-name` or picks from `/skills` ([cx-skills], [cx-mentions]). The body is injected verbatim in a `<skill>` block with no placeholder substitution ([cx-fragments]). `disable-model-invocation` is ignored. The equivalent is `agents/openai.yaml` in the skill folder with `policy: allow_implicit_invocation: false`, which keeps explicit `$name` working (0.99.0) ([cx-skills]). The parser ignores unknown frontmatter keys ([cx-parser]). Whether a `$name` mention inside a `codex exec` prompt injects the skill is inferred from the mention parser, not documented or tested.

**O2 ask.** `request_user_input`: 1 to 3 questions, 2 to 3 options each, an "Other" added ([cx-rui]). Only Plan mode allows it ([cx-modes]). Default mode needs `features.default_mode_request_user_input`, marked under development and off ([cx-features]). `codex exec` rejects it: "request_user_input is not supported in exec mode" ([cx-exec-lib]). Sub-agents cannot call it.

**O3 sub-agents.** `features.multi_agent` is stable and on ([cx-features]). Tools `spawn_agent`, `send_input`, `wait_agent`, `close_agent`, `resume_agent` ([cx-ma-spec]). With `fork_context` off the agent "starts with only the initial prompt" ([cx-ma-spec]). Model: the spawn call's `model`, then `agents.default_subagent_model`, then the parent's ([cx-sub]). Custom agents are TOML files in `~/.codex/agents/` or `.codex/agents/` with `name`, `description`, `developer_instructions`, and optional `model`, `sandbox_mode`, `mcp_servers` ([cx-sub], [cx-roles]). Built-in roles `default`, `worker`, `explorer` ([cx-sub]). Limits: 6 concurrent threads and depth 1 by default (`agents.max_concurrent_threads_per_session`, `agents.max_depth`) ([cx-config-mod]). Live parent overrides such as `--yolo` "carry over to spawned agents" ([cx-sub]).

**O4 session id.** Shell commands get `CODEX_THREAD_ID` (0.95.0, "so scripts and skills can detect the active thread"), `CODEX_SESSION_ID` and `CODEX_VERSION` ([cx-execenv], [cx-releases]). Hooks get `session_id` on stdin ([cx-pretool]).

**O5 hooks.** `~/.codex/hooks.json`, `[hooks]` in `~/.codex/config.toml`, the project's `.codex/hooks.json` (trusted projects only), plugins and managed `requirements.toml` ([cx-hooks]). The JSON shape is Claude Code's: `{"hooks":{"PreToolUse":[{"matcher":"…","hooks":[{"type":"command","command":"…"}]}]}}`, the matcher a regex ([cx-hooks]). Shell-only PreToolUse came in 0.117.0, and `apply_patch` and MCP coverage in 0.124.0 ([cx-releases]). For edits, `tool_name` is `apply_patch`, the matchers `Edit` and `Write` are aliases for it, and `tool_input` is `{"command": "<patch text>"}` ([cx-hooknames], [cx-applypatch]). The handler accepts only the freeform patch form, so every `apply_patch` edit has a hook payload ([cx-applypatch]). File paths sit in the patch's `*** Add File: `, `*** Update File: `, `*** Delete File: ` and `*** Move to: ` lines ([cx-patchgrammar]). Blocking: exit 2 with a reason on stderr, or `permissionDecision: "deny"`. Exit 2 with empty stderr, and any other code, fail open ([cx-pretool]). New or changed non-managed hooks "are skipped until trusted" through `/hooks`. `--dangerously-bypass-hook-trust` runs them without stored trust for one call ([cx-hooks]). The docs call hooks "a useful guardrail, not a complete enforcement boundary" ([cx-hooks]).

**O6 headless.** `codex exec [PROMPT]`, reading stdin when the prompt is `-` or absent. Flags (also checked with `codex exec --help` on 0.162.0): `--json`, `-o/--output-last-message`, `-s/--sandbox read-only|workspace-write|danger-full-access`, `--dangerously-bypass-approvals-and-sandbox`, `-m`, `-c key=value`, `-p/--profile`, `--ignore-user-config`, `--ignore-rules`, `--ephemeral`, `--skip-git-repo-check`, `--dangerously-bypass-hook-trust` ([cx-exec-cli], [cx-noninteractive]). Exec forces approvals to "never", so actions that need approval fail ([cx-exec-lib]). It exits 1 when the turn fails or is interrupted. There is no documented table of exit codes ([cx-exec-lib]). Workspace-write's network switch is `sandbox_workspace_write.network_access` ([cx-configref]).

**O7 MCP.** `[mcp_servers.<name>]` with `command`, `args`, `env` or `url`. `codex mcp add <name> -- <cmd>`. The project's `.codex/config.toml` loads for trusted projects only ([cx-mcp]).

**O8 instructions.** `$CODEX_HOME/AGENTS.override.md` or `AGENTS.md`, then one file per directory from the project root to the cwd (`AGENTS.override.md`, else `AGENTS.md`, else names in `project_doc_fallback_filenames`) ([cx-agentsmd]). The total is cut at `project_doc_max_bytes`, 32768 by default, "silently truncated" ([cx-config-mod]). The project's `.codex/config.toml` needs `projects."<path>".trust_level = "trusted"` ([cx-agentsmd]).

**O9 transcripts.** `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<time>-<thread>.jsonl`, lines `{timestamp, type, payload}`, token counts persisted ([cx-recorder], [cx-rollout-payload]). The format "isn't a stable interface" ([cx-hooks]).

## Cursor

The current CLI binary is `agent`. The older name `cursor-agent` still appears in the docs, and the copy on this machine is `cursor-agent` 2025.09.12, which predates skills, CLI hooks and CLI sub-agents ([cu-clichangelog]).

**O1 skills.** Since 2.4 (2026-01-22) in the editor and CLI ([cu-24]). Roots: `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `~/.cursor/skills/`, and "for compatibility" `.claude/skills/`, `.codex/skills/` and their `~/` forms ([cu-skills]). Frontmatter: `name` (must match the folder), `description`, `paths`, `disable-model-invocation`, `icon`, `color`, `metadata` ([cu-skills]). With `disable-model-invocation`, a skill is "only included when explicitly invoked via `/skill-name`" ([cu-skills]). `/skill-name` works in `-p` since 2026-05-07 ([cu-clichangelog]). Passing arguments, and `$ARGUMENTS`, are not documented. Only `~/.cursor/skills/` syncs to cloud agents ([cu-skills]).

**O2 ask.** Since 2.4 the question tool "lets agents ask clarifying questions in any conversation" ([cu-24]). Over ACP it is `cursor/ask_question` with `questions[]` of `{id, prompt, options, allowMultiple}` ([cu-acp]). Behavior in `-p` and in cloud agents is not documented.

**O3 sub-agents.** Since 2.4, CLI in 2026-03 ([cu-24], [cu-clichangelog]). Files in `.cursor/agents/`, `.claude/agents/`, `.codex/agents/` and the `~/` forms, with frontmatter `name`, `description`, `model` (`inherit` or an id), `readonly` ("no file edits, no state-changing shell commands") and `is_background` ([cu-sub]). Several Task calls in one message run in parallel. Built-ins: Explore, which "uses a faster model by default", and Browser. A sub-agent may launch one more sub-agent, and "a subagent launched by another subagent can't launch further ones", which needs Task access in the current mode ([cu-sub]). On legacy request-based plans without Max Mode, sub-agents run on Composer whatever `model` says ([cu-sub]).

**O4 session id.** Hook stdin has `conversation_id` and `generation_id`, and `sessionStart` adds `session_id` ([cu-hooks]). `sessionStart` can return `additional_context`, which is a way to hand the id to the model (not tested). `create-chat` returns a chat id, `--resume <id>` continues it, and `--output-format json` returns `session_id` ([cu-params], [cu-output]).

**O5 hooks.** Beta since 1.7 (2025-09-29), CLI since 2026-01 ([cu-17], [cu-clichangelog]). Files: `.cursor/hooks.json` (trusted workspaces), `~/.cursor/hooks.json`, enterprise and team files, plugins ([cu-hooks]). Shape `{"version":1,"hooks":{"preToolUse":[{"command":"…","matcher":"Write","failClosed":true}]}}`. There is no before-edit event: the pre-edit block is `preToolUse` with matcher `Write`. `afterFileEdit` runs after the write ([cu-hooks]). Output `{"permission":"deny","user_message":"…","agent_message":"…"}`, or exit 2 to deny. Other non-zero exits fail open unless `failClosed: true`. Invalid JSON from a permission hook blocks ([cu-hooks]). The docs show no `preToolUse` example for Write, so whether the path arrives as `tool_input.file_path` is unconfirmed ([cu-hooks]). Cursor also loads Claude Code hooks from `.claude/settings.local.json`, `.claude/settings.json` and `~/.claude/settings.json`, mapping `Edit` and `Write` to `Write` and honouring exit 2. The setting "Include Third-Party Plugins, Skills, and Other Configs" is on by default ([cu-3p]). Cloud agents run only command hooks from the project plus team and enterprise hooks, not user hooks ([cu-hooks]).

**O6 headless.** `agent -p "<prompt>"` with `--output-format text|json|stream-json`, `-f/--force` ("Force allow commands unless explicitly denied"), `--model`, `--workspace`, `--api-key` or `CURSOR_API_KEY`, `--resume`, `--sandbox enabled|disabled`, `--approve-mcps`, `--trust` ("Trust the workspace without prompting (headless mode only)") ([cu-params]). "Without `--force`, changes are only proposed, not applied" ([cu-headless]). Failure is only "non-zero", with the error on stderr ([cu-output]). No flag ignores the project's own Cursor config ([cu-params]). A Cloud Agents API (`POST https://api.cursor.com/v1/agents`) also runs agents remotely ([cu-cloudapi]).

**O7 MCP.** `.cursor/mcp.json` and `~/.cursor/mcp.json`, key `mcpServers`, stdio `command`/`args`/`env` or `url` ([cu-mcp]). Since 2026-04 global servers load without a per-workspace prompt, and project servers still need approval ([cu-clichangelog]).

**O8 instructions.** `.cursor/rules/*.mdc` with `description`, `globs`, `alwaysApply`. `AGENTS.md` at the root and in subdirectories. A root `CLAUDE.md` is "always applied". `.cursorrules` is legacy ([cu-rules]). The CLI "also reads `AGENTS.md` and `CLAUDE.md` at the project root" ([cu-cliusing]).

**O9 transcripts.** Hooks receive `transcript_path`, also `CURSOR_TRANSCRIPT_PATH` ([cu-hooks]). Headless transcripts "write Claude Code-compatible JSONL" since 2026-02 ([cu-clichangelog]). No documented storage path or export. The Pond install here (0.19.5) lists adapters `claude-code`, `claude-desktop-app`, `codex-cli` and `opencode`, and no Cursor adapter (`pond adapters list`).

## Adapter design

### D1. One adapter file per harness

Put them at `kit/harnesses/<harness>.md`, next to `kit/adapters/<language>.md` and in the same terse style. A skill reads the one for its harness at Load. Proposed contents:

```markdown
# Harness: Claude Code

## Invoke
- `/<skill> <args>`. Arguments arrive in `$ARGUMENTS`. `${CLAUDE_SESSION_ID}` is filled in.

## Ask
- AskUserQuestion: 1 to 4 questions, 2 to 4 options each. Only the main session can ask.

## Agents
- Fresh agent: the Agent tool, `subagent_type: general-purpose`, with only the given instructions.
- Smaller model: `model: sonnet`.
- Read-only agent: `subagent_type: Explore`.
- Background: the default. Up to 20 at once.

## Gate
- `~/.claude/settings.json` PreToolUse, matcher `Edit|Write|NotebookEdit`, `python3 <factory>/hooks/factory_gate.py`.

## Headless
- `claude -p --setting-sources user --strict-mcp-config --mcp-config ~/.software-factory/mcp.json --permission-mode <mode>`, prompt `/{skill} {slug}`.

## Transcripts
- `~/.claude/projects/<encoded cwd>/<session>.jsonl`. Pond adapter `claude-code`.
```

```markdown
# Harness: Codex CLI

## Invoke
- `$<skill> <args>`. Nothing is substituted: `$ARGUMENTS` stays literal, so the argument is the text after the skill mention.
- Session id: `echo "$CODEX_THREAD_ID"`.
- Each factory skill folder holds `agents/openai.yaml` with `policy: allow_implicit_invocation: false`.

## Ask
- Plan mode: `request_user_input`, 1 to 3 questions, 2 to 3 options each.
- Otherwise: write the question with numbered options as the last message and end the turn.

## Agents
- Fresh agent: `spawn_agent` with `fork_context: false` and the instructions as `message`. Collect with `wait_agent`.
- Smaller model: `model: <id set at install>` on the spawn call.
- Read-only agent: `agent_type: factory-reader`, from `~/.codex/agents/factory-reader.toml` with `sandbox_mode = "read-only"`.
- Limits: 6 agents at once, and agents cannot spawn agents.

## Gate
- `~/.codex/hooks.json` PreToolUse, matcher `^apply_patch$`, same script. Trust it once with `/hooks`.

## Headless
- `codex exec --sandbox workspace-write -c sandbox_workspace_write.network_access=true`, prompt `${skill} {slug}`.

## Transcripts
- `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Pond adapter `codex-cli`.
```

```markdown
# Harness: Cursor

## Invoke
- `/<skill> <args>`. If `$ARGUMENTS` is still literal, the argument is the text after the skill name.
- Session id: "unknown", unless a `sessionStart` hook put it in context.

## Ask
- The ask-question tool. Headless: not used, the pull request is the conversation.

## Agents
- Fresh agent: the Task tool, one call per agent, all in one message to run them in parallel.
- Smaller model: an agent file with `model: <id set at install>`.
- Read-only agent: `~/.cursor/agents/factory-reader.md` with `readonly: true`, or the built-in Explore.
- Background: `is_background: true`. A sub-agent may launch one more level, no deeper.

## Gate
- The Claude Code hook in `~/.claude/settings.json`, imported by Cursor (Edit and Write map to Write).
- Cloud agents run no user hooks: there the runner's check is the only gate.

## Headless
- `agent -p --force --trust --output-format text`, `CURSOR_API_KEY` set, prompt `/{skill} {slug}`.

## Transcripts
- `transcript_path` in hook input. No Pond adapter.
```

### D2. Neutral phrasing in skills

Skills name the operation and the adapter supplies the mechanics. Today's Claude-specific phrases map like this:

| Today | Neutral |
| --- | --- |
| "ask the user" (meaning AskUserQuestion) | "ask the user (harness: ask)" |
| "Start one fresh sub-agent" | "Start one fresh agent (harness: fresh agent)" |
| "on the smaller model (… `model: sonnet`)" in gates.md Models | "on the smaller model (harness: smaller model)" |
| "in the background" | "in the background (harness: background)" |
| "whose tools can only read (in Claude Code, the `Explore` agent type)" | "(harness: read-only agent)" |
| `Slug: $ARGUMENTS`, `Session: ${CLAUDE_SESSION_ID}` | Keep both lines. Add to gates.md Load: "A placeholder still shown literally means the harness did not fill it. Take the argument from the text after the skill name, and the session id as the harness adapter says." |
| `/factory-<gate>` in messages to the user | "the `factory-<gate>` skill (harness: invoke)" in prose. Keep the hook's messages as they are, since Codex and Cursor users can read `/factory-x` too |

Load gains one step 0: detect the harness (D5) and read `~/.software-factory/harnesses/<harness>.md`.

### D3. The hard gate per harness

- **Claude Code.** Unchanged.
- **Codex.** Same script, registered in `~/.codex/hooks.json` with matcher `^apply_patch$`. One change to `factory_gate.py`: when `tool_name` is `apply_patch`, take the paths from the `*** Add File: `, `*** Update File: `, `*** Delete File: ` and `*** Move to: ` lines of `tool_input.command`, resolve them against `cwd`, and block when any path fails `check`. A patch can touch several files ([cx-patchgrammar]). Its stderr must not be empty, or exit 2 counts as a failed hook ([cx-pretool]). The hook is skipped until trusted, so retro M7 should also read `~/.codex/hooks.json` and `[hooks]` in `~/.codex/config.toml`.
- **Cursor.** Keep the hook in `~/.claude/settings.json`, which Cursor imports by default ([cu-3p]). Do not also add `~/.cursor/hooks.json`, or the gate runs twice. Before relying on it, run one edit with a hook that logs its stdin, to confirm Cursor's Write sends `tool_input.file_path` and that the CLI fires it. If the field is `path`, read either one. Cloud agents run no user hooks.
- **Where no pre-edit hook applies** (Cursor cloud agents, an untrusted Codex hook, shell commands that write files in any harness): two backstops that do not depend on the harness.
  - The runner checks each run: the files changed between the head the harness started from and its new head must be in `.factory/`, the root `DESIGN.md`, or the Allowed files and logged deviations of a slice the run was building. Otherwise the runner resets the run's commits as it does for untrusted heads. This needs a mode of `factory_gate.py` that applies `check` to a list of paths.
  - Interactive runs can add a git `pre-commit` hook that runs the same path check on staged files. It stops the commit, not the edit, and `--no-verify` skips it.

### D4. The runner's command per harness

`runner/factory_run.py` already takes `--harness` and `--prompt`, and passes the prompt as the last argument, which all three accept. No code change is needed for the command itself.

| Harness | `--harness` | `--prompt` | Notes |
| --- | --- | --- | --- |
| Claude Code | `claude -p --setting-sources user --strict-mcp-config --mcp-config ~/.software-factory/mcp.json --permission-mode <mode>` | `/{skill} {slug}` | Today's default, plus `--mcp-config` so Pond loads, and an explicit mode instead of a default that "can be `auto`" ([cc-headless]) |
| Codex | `codex exec --sandbox workspace-write -c sandbox_workspace_write.network_access=true` | `${skill} {slug}` | A fresh clone in a temp folder is an untrusted project, so its `.codex/` config, hooks and rules are skipped ([cx-agentsmd]). Do not pass `--ignore-user-config`: it drops the user's hooks and MCP servers. Network is on for `git push` and `gh`. `request_user_input` is rejected, which matches headless mode. If `$skill` in an exec prompt does not load the skill, use `Follow ~/.agents/skills/{skill}/SKILL.md. Argument: {slug}` |
| Cursor | `agent -p --force --trust --output-format text` with `CURSOR_API_KEY` | `/{skill} {slug}` | `--force` is required to write. `--trust` trusts the clone, so its `.cursor/` rules and hooks load and no flag turns them off ([cu-params]). Leave out `--approve-mcps`: Pond as a global server loads without approval, and the repository's own servers stay unapproved ([cu-clichangelog]) |

### D5. How triage detects its harness

Run in the shell:

```sh
if [ -n "$CODEX_THREAD_ID" ]; then echo codex
elif [ -n "$CURSOR_AGENT" ]; then echo cursor
elif [ "$CLAUDECODE" = 1 ]; then echo claude-code
else echo unknown; fi
```

- `CODEX_THREAD_ID`: set in Codex shell commands since 0.95.0 ([cx-execenv]).
- `CURSOR_AGENT`: not in Cursor's docs. A forum reply of 2025-09-02 says the CLI had dropped it and it was "re-added" ([cu-forum-agentenv]). Treat it as observed.
- `CLAUDECODE=1`: documented for Bash, hooks and MCP subprocesses. IDE extensions also set it in their terminals ([cc-env]). That is why it is checked last.
- A harness started from another's shell inherits the outer variables, so the model checks the result against its own tools (AskUserQuestion and Agent, `spawn_agent` and `apply_patch`, Task and the Cursor question tool). `unknown` asks the user.
- Every skill detects again at Load, since one change can move between harnesses (interactive triage in Cursor, headless build with Claude Code). It writes the result into its `step_start` detail ("session <id>, factory <sha>, harness <name>"), so `status.yaml` keeps its schema and retro can split metrics by harness.

### D6. Installing skills and instructions once for all three

- Symlink the skills into `~/.claude/skills` (Claude Code, Cursor) and `~/.agents/skills` (Codex, Cursor). Cursor then sees each skill twice. Its rule for duplicate names is not documented, and the client guide only asks clients to pick one deterministically ([as-client]).
- Add `agents/openai.yaml` with `policy: allow_implicit_invocation: false` to each factory skill. The other two ignore the extra folder.
- Instructions: put the factory's lines (for example the DESIGN.md line from `design-md-guide.md`) in `AGENTS.md`. Where a repository has a `CLAUDE.md`, add `@AGENTS.md` to it, since Claude Code otherwise skips `AGENTS.md` ([cc-memory]). Codex reads only `AGENTS.md` unless `project_doc_fallback_filenames` lists `CLAUDE.md` ([cx-agentsmd]).
- Pond: `claude mcp add --scope user pond -- ~/.local/bin/pond mcp`, `[mcp_servers.pond] command = "~/.local/bin/pond", args = ["mcp"]` in `~/.codex/config.toml`, and the same server under `mcpServers` in `~/.cursor/mcp.json`.

## Gaps and fallbacks

| ID | Gap | Fallback |
| --- | --- | --- |
| G1 | Codex has no `$ARGUMENTS` and no `/name`. Cursor's argument handling is undocumented | The literal-placeholder rule in D2. The argument is the text after the skill name |
| G2 | Codex ignores `disable-model-invocation` | `agents/openai.yaml` with `allow_implicit_invocation: false` per skill |
| G3 | Codex asks structured questions only in Plan mode | A numbered plain-text question as the last message, then end the turn. Retro M1 counts these as free-text turns |
| G4 | No session id in Codex skill text, none at all for Cursor's model | Codex: `$CODEX_THREAD_ID` from the shell. Cursor: a `sessionStart` hook returning `additional_context` with `session_id` (untested), else "unknown", and retro falls back to command rows |
| G5 | Codex gives the gate patch text, not a path, and skips hooks until trusted | Parse the patch headers (D3). Trust once with `/hooks`. Retro M7 checks Codex's hook files |
| G6 | Cursor's Write payload field is unconfirmed, and cloud agents run no user hooks | Probe once with a logging hook. Read `file_path` or `path`. In cloud, the runner's check is the gate |
| G7 | Shell commands that write files pass every pre-edit hook (Codex patches run through the shell match `Bash`) | The runner's changed-files check, and a pre-commit hook interactively (D3) |
| G8 | Codex: 6 agents at once, depth 1, and a parent's `--yolo` overrides a read-only agent | Raise `agents.max_concurrent_threads_per_session` if the interface panel needs more lenses. Never run the factory under `--yolo`. Depth 1 suffices: only the main session spawns agents |
| G9 | Cursor: legacy request plans run sub-agents on Composer whatever `model` says | Note the plan type in the adapter. Nesting is not a limit: two levels are allowed and the factory uses one |
| G10 | Cursor headless has no switch to ignore the repository's own config | Run it in a container or VM, as the README already requires. Leave out `--approve-mcps` |
| G11 | Cursor transcripts have no documented path and Pond has no Cursor adapter | Retro reports M1 to M3 as "not measured" for Cursor steps. M4 to M8 come from `history` and files and still work |
| G12 | AskUserQuestion and `request_user_input` are unavailable in headless runs of every harness | Already handled: headless questions go to the pull request (gates.md, Headless mode) |

## Findings about the current factory

| ID | Finding | Source |
| --- | --- | --- |
| F1 | The default runner command passes `--strict-mcp-config` without `--mcp-config`, so headless runs load no MCP server, Pond included. Skills then take their "Pond tools are not available" path, although the README asks for `pond init` on the server | `runner/factory_run.py` line 46, [cc-cli] |
| F2 | The runner sets no `--permission-mode`. A `-p` run without one starts in a default that "can be `auto`" | [cc-headless] |
| F3 | The skills' `${CLAUDE_SESSION_ID}` is a skill substitution. The Bash variable is `CLAUDE_CODE_SESSION_ID` | [cc-skills], [cc-env] |
| F4 | `MultiEdit` in the README's hook matcher is not a current Claude Code tool. It does no harm | [cc-tools] |
| F5 | The `cursor-agent` on this machine is 2025.09.12. Skills, CLI hooks and CLI sub-agents came later, so upgrade before any trial | [cu-clichangelog] |

## Could not confirm

- Q1. Whether `codex exec '$factory-build slug'` injects the skill. Inferred from the mention parser ([cx-mentions]).
- Q2. Whether Cursor passes text after `/skill-name` as an argument, or substitutes `$ARGUMENTS` ([cu-skills]).
- Q3. The `tool_input` field Cursor sends for Write in `preToolUse`, whether the CLI fires `preToolUse` and imported Claude hooks, and whether it fires for sub-agent tool calls ([cu-hooks], [cu-3p]).
- Q4. Whether Cursor's question tool works in `-p` and in cloud agents ([cu-24]).
- Q5. Cursor's precedence when the same skill name appears in `~/.claude/skills` and `~/.agents/skills` ([cu-skills]).
- Q6. Whether Codex's `--sandbox workspace-write` on the command line counts as a "live override" that carries over to a read-only agent ([cx-sub]).
- Q7. Whether `--dangerously-bypass-hook-trust` also enables an untrusted project's hooks in Codex ([cx-hooks]).
- Q8. Release dates of Claude Code versions (the changelog has none) and of Cursor 3.23.
- Q9. `CURSOR_AGENT` as a stable, documented variable ([cu-forum-agentenv]).

## What this does not cover

- No code or skill was changed. D1 to D6 are proposals, and none was run on Codex or Cursor.
- Cursor's IDE-only features (Tab, rules UI, the Agents Window), Codex's IDE extension and cloud tasks, and Claude Code's SDK and cloud sessions.
- Cost, speed and model quality of the three harnesses, and which models fill "smaller model" outside Claude Code.
- Other Agent Skills clients (Gemini CLI, OpenCode, Copilot and others on [as-clients]).
- Security review of running each harness unattended, beyond the isolation flags in D4.
- The plugin formats of each harness, as a way to ship skills, hooks and agents together.

## Sources

Agent Skills
- as-spec: <https://agentskills.io/specification>
- as-client: <https://agentskills.io/client-implementation/adding-skills-support>
- as-clients: <https://agentskills.io/clients>

Claude Code
- cc-skills: <https://code.claude.com/docs/en/skills>
- cc-sub: <https://code.claude.com/docs/en/sub-agents>
- cc-tools: <https://code.claude.com/docs/en/tools-reference>
- cc-hooks: <https://code.claude.com/docs/en/hooks>
- cc-headless: <https://code.claude.com/docs/en/headless>
- cc-cli: <https://code.claude.com/docs/en/cli-reference>
- cc-mcp: <https://code.claude.com/docs/en/mcp>
- cc-memory: <https://code.claude.com/docs/en/memory>
- cc-env: <https://code.claude.com/docs/en/env-vars>
- cc-sessions: <https://code.claude.com/docs/en/sessions>
- cc-changelog: <https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md>

Codex CLI
- cx-latest: <https://github.com/openai/codex/releases/latest>
- cx-releases: <https://github.com/openai/codex/releases>
- cx-skills: <https://learn.chatgpt.com/docs/build-skills>
- cx-prompts: <https://learn.chatgpt.com/docs/custom-prompts>
- cx-roots: <https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/host_roots.rs>
- cx-parser: <https://github.com/openai/codex/blob/main/codex-rs/skills/src/parser.rs>
- cx-mentions: <https://github.com/openai/codex/blob/main/codex-rs/skills/src/mentions.rs>
- cx-fragments: <https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/fragments.rs>
- cx-rui: <https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/request_user_input_spec.rs>
- cx-modes: <https://github.com/openai/codex/blob/main/codex-rs/protocol/src/config_types.rs>
- cx-features: <https://github.com/openai/codex/blob/main/codex-rs/features/src/lib.rs>
- cx-exec-lib: <https://github.com/openai/codex/blob/main/codex-rs/exec/src/lib.rs>
- cx-exec-cli: <https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs>
- cx-noninteractive: <https://learn.chatgpt.com/docs/non-interactive-mode>
- cx-sub: <https://learn.chatgpt.com/docs/agent-configuration/subagents>
- cx-ma-spec: <https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/multi_agents_spec.rs>
- cx-roles: <https://github.com/openai/codex/blob/main/codex-rs/agent-roles/src/discovery.rs>
- cx-config-mod: <https://github.com/openai/codex/blob/main/codex-rs/core/src/config/mod.rs>
- cx-execenv: <https://github.com/openai/codex/blob/main/codex-rs/core/src/exec_env.rs>
- cx-hooks: <https://learn.chatgpt.com/docs/hooks>
- cx-pretool: <https://github.com/openai/codex/blob/main/codex-rs/hooks/src/events/pre_tool_use.rs>
- cx-applypatch: <https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/apply_patch.rs>
- cx-hooknames: <https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/hook_names.rs>
- cx-patchgrammar: <https://github.com/openai/codex/blob/main/codex-rs/apply-patch/src/parser.rs>
- cx-mcp: <https://learn.chatgpt.com/docs/extend/mcp?surface=cli>
- cx-agentsmd: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- cx-configref: <https://learn.chatgpt.com/docs/config-file/config-reference>
- cx-recorder: <https://github.com/openai/codex/blob/main/codex-rs/rollout/src/recorder.rs>
- cx-rollout-payload: <https://github.com/openai/codex/blob/main/codex-rs/history/src/rollout_payload.rs>

Cursor
- cu-skills: <https://cursor.com/docs/context/skills>
- cu-24: <https://cursor.com/changelog/2-4>
- cu-17: <https://cursor.com/changelog/1-7>
- cu-relnotes: <https://cursor.com/docs/release-notes>
- cu-clichangelog: <https://cursor.com/docs/cli/changelog>
- cu-sub: <https://cursor.com/docs/context/subagents>
- cu-acp: <https://cursor.com/docs/cli/acp>
- cu-hooks: <https://cursor.com/docs/agent/hooks>
- cu-3p: <https://cursor.com/docs/reference/third-party-hooks>
- cu-params: <https://cursor.com/docs/cli/reference/parameters>
- cu-headless: <https://cursor.com/docs/cli/headless>
- cu-output: <https://cursor.com/docs/cli/reference/output-format>
- cu-cloudapi: <https://cursor.com/docs/cloud-agent/api/endpoints>
- cu-mcp: <https://cursor.com/docs/context/mcp>
- cu-rules: <https://cursor.com/docs/context/rules>
- cu-cliusing: <https://cursor.com/docs/cli/using>
- cu-forum-agentenv: <https://forum.cursor.com/t/cursor-cli-is-not-setting-cursor-agent-1-environment-variable-while-executing-bash-commands/132427>

[as-spec]: https://agentskills.io/specification
[as-client]: https://agentskills.io/client-implementation/adding-skills-support
[as-clients]: https://agentskills.io/clients
[cc-skills]: https://code.claude.com/docs/en/skills
[cc-sub]: https://code.claude.com/docs/en/sub-agents
[cc-tools]: https://code.claude.com/docs/en/tools-reference
[cc-hooks]: https://code.claude.com/docs/en/hooks
[cc-headless]: https://code.claude.com/docs/en/headless
[cc-cli]: https://code.claude.com/docs/en/cli-reference
[cc-mcp]: https://code.claude.com/docs/en/mcp
[cc-memory]: https://code.claude.com/docs/en/memory
[cc-env]: https://code.claude.com/docs/en/env-vars
[cc-sessions]: https://code.claude.com/docs/en/sessions
[cc-changelog]: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
[cx-latest]: https://github.com/openai/codex/releases/latest
[cx-releases]: https://github.com/openai/codex/releases
[cx-skills]: https://learn.chatgpt.com/docs/build-skills
[cx-prompts]: https://learn.chatgpt.com/docs/custom-prompts
[cx-roots]: https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/host_roots.rs
[cx-parser]: https://github.com/openai/codex/blob/main/codex-rs/skills/src/parser.rs
[cx-mentions]: https://github.com/openai/codex/blob/main/codex-rs/skills/src/mentions.rs
[cx-fragments]: https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/fragments.rs
[cx-rui]: https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/request_user_input_spec.rs
[cx-modes]: https://github.com/openai/codex/blob/main/codex-rs/protocol/src/config_types.rs
[cx-features]: https://github.com/openai/codex/blob/main/codex-rs/features/src/lib.rs
[cx-exec-lib]: https://github.com/openai/codex/blob/main/codex-rs/exec/src/lib.rs
[cx-exec-cli]: https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs
[cx-noninteractive]: https://learn.chatgpt.com/docs/non-interactive-mode
[cx-sub]: https://learn.chatgpt.com/docs/agent-configuration/subagents
[cx-ma-spec]: https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/multi_agents_spec.rs
[cx-roles]: https://github.com/openai/codex/blob/main/codex-rs/agent-roles/src/discovery.rs
[cx-config-mod]: https://github.com/openai/codex/blob/main/codex-rs/core/src/config/mod.rs
[cx-execenv]: https://github.com/openai/codex/blob/main/codex-rs/core/src/exec_env.rs
[cx-hooks]: https://learn.chatgpt.com/docs/hooks
[cx-pretool]: https://github.com/openai/codex/blob/main/codex-rs/hooks/src/events/pre_tool_use.rs
[cx-applypatch]: https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/apply_patch.rs
[cx-hooknames]: https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/hook_names.rs
[cx-patchgrammar]: https://github.com/openai/codex/blob/main/codex-rs/apply-patch/src/parser.rs
[cx-mcp]: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
[cx-agentsmd]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[cx-configref]: https://learn.chatgpt.com/docs/config-file/config-reference
[cx-recorder]: https://github.com/openai/codex/blob/main/codex-rs/rollout/src/recorder.rs
[cx-rollout-payload]: https://github.com/openai/codex/blob/main/codex-rs/history/src/rollout_payload.rs
[cu-skills]: https://cursor.com/docs/context/skills
[cu-24]: https://cursor.com/changelog/2-4
[cu-17]: https://cursor.com/changelog/1-7
[cu-relnotes]: https://cursor.com/docs/release-notes
[cu-clichangelog]: https://cursor.com/docs/cli/changelog
[cu-sub]: https://cursor.com/docs/context/subagents
[cu-acp]: https://cursor.com/docs/cli/acp
[cu-hooks]: https://cursor.com/docs/agent/hooks
[cu-3p]: https://cursor.com/docs/reference/third-party-hooks
[cu-params]: https://cursor.com/docs/cli/reference/parameters
[cu-headless]: https://cursor.com/docs/cli/headless
[cu-output]: https://cursor.com/docs/cli/reference/output-format
[cu-cloudapi]: https://cursor.com/docs/cloud-agent/api/endpoints
[cu-mcp]: https://cursor.com/docs/context/mcp
[cu-rules]: https://cursor.com/docs/context/rules
[cu-cliusing]: https://cursor.com/docs/cli/using
[cu-forum-agentenv]: https://forum.cursor.com/t/cursor-cli-is-not-setting-cursor-agent-1-environment-variable-while-executing-bash-commands/132427

## Update after decision 30

Decision 30 made the interactive autopilot a thin orchestrator that starts a step agent per slice and per milestone review. Two statements above no longer hold for the factory: G8's "depth 1 suffices: only the main session spawns agents" and G9's "the factory uses one". Step agents start their own sub-agents (the executor, polish's reviewers, lens reviewers), so the factory now needs depth 2, and 3 under factory-security's lens. Continuing a stopped agent with the user's answer is a new operation: Claude Code does it with SendMessage (used in this factory's sessions, docs/research/retro/C-signals.md); Codex and Cursor were not researched for it.
