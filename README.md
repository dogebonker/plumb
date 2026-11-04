# Plumb

Spec-driven development for the coding agent you already use.

Plumb is a skill that helps your agent understand a module's existing rules,
work from the original requirements, make a change, and check what actually
happened. Lasting module knowledge lives in OKF bundles. Substantial changes
get requirements, a design, and tasks. Small edits stay small.

<img src="assets/plumb-hero.png" alt="Intricate folded paper structures connected by a red thread, with a brass plumb bob suspended over a reference mark." width="1200">

**Experimental.** The skill and supporting CLI are implemented. General accuracy,
maintainer time savings, and the cost of keeping bundles current remain unproven.

## Use it

Point your coding agent at the skill in this checkout:

```text
Read /path/to/plumb/skills/plumb/SKILL.md and use Plumb to implement this change:
reject batches above five items before writing anything to storage.
Preserve the existing behavior for batches of zero through five.
```

To make it discoverable for repeated use, copy the entire
[`skills/plumb`](skills/plumb) directory into your agent's skill directory.
For Codex, that is `~/.codex/skills/plumb/`; for Claude Code, it is
`~/.claude/skills/plumb/`. Keep the `references/` directory beside `SKILL.md`.
Use a new destination so an existing installation's edits are preserved.

Once your agent discovers the skill, invoke it with your request:

```text
$plumb Add cancellation to the orders module using the linked issue and its module bundle.
```

Hosts with slash-command skill invocation can use `/plumb`. You can also locate
or read the skill from the repository without installing anything:

```sh
python3 -m plumb skill --path
python3 -m plumb skill
```

The skill uses the current host agent. It does not launch another model CLI or
install a workflow runtime. These two commands only print local documentation.

## What the agent does

1. Reads the affected module's knowledge, original source material, code, and
   relevant dependencies. Missing context stays explicit.
2. Separates current commitments, observed behavior, and the requested change.
   A genuine conflict produces a concrete question about which rule governs.
3. Keeps a bounded change in one brief note. Substantial behavior changes,
   cross-module contracts, or consequential uncertainty get requirements,
   a design, and tasks.
4. Implements through the host's normal tools, runs targeted checks, and reviews
   the diff against requirements and preserved behavior.
5. Updates affected module knowledge with sources and observed results. It reports
   failed or unrun checks instead of treating them as success.

Existing authorization carries through ordinary reversible work. A source saying
"approved" does not grant authority, and an imported requirement does not become
agreed intent because an agent summarized it.

## What lives in the project

Use the project's existing documentation locations. A possible arrangement is:

```text
knowledge/
  index.md
  orders/
    index.md
    module.md           Purpose, scope, code paths, and contracts
    cancellation.md     Current rule, rationale, sources, and unknowns
changes/
  cancel-order/
    requirements.md     Requested delta and acceptance examples
    design.md           Affected contracts and implementation approach
    tasks.md            Work linked to requirements and actual check results
```

A module's bundle survives individual changes. Its concepts link to original
sources and related modules. An in-progress change spec describes proposed work;
it does not assert that the behavior is already implemented.

Start with a service or module and refine the knowledge gradually. Inspect
imports, API callers, events, and shared data where relevant. Plumb does not
claim an exhaustive dependency graph from a list of imports.

The format is [OKF](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md):
Markdown concepts with YAML metadata and links. The module and change layouts
above are conventions, not additional requirements of the format.

## Where requirements come from

Repository documents, Confluence pages, Notion pages, Linear tickets, GitHub
issues, and local exports can supply requirements. The agent uses available,
authorized connectors or reads the exported files. It records source locators,
passages, available revisions, and uncertainty.

Plumb ships a local Git capture helper. It does not ship live SaaS connectors.
A captured page with no upstream access cannot establish live freshness. Read the
[four walkthroughs](skills/plumb/references/examples.md) for direct edits, new
behavior, conflicting sources, and changes to a source during unfinished work.

## Optional source and reconciliation tools

The Python CLI supports bounded, isolated review workspaces. Run it from this
repository with Python 3.10 or later and Git. It has no extra Python dependencies.

| Command | What it does | Extra model inference |
| --- | --- | --- |
| `skill` | Prints the reusable skill or its path | No |
| `init` | Copies selected committed code and a source into a new draft workspace | No |
| `status` | Compares the capture with its selected local Git ref | No |
| `refresh` | Updates the source capture, preserving code and knowledge | No |
| `check` | Produces a cited reconciliation report | Yes, through Claude CLI |
| `propose` | Produces a scoped correction after an explicit choice | Yes, through Claude CLI |
| `apply` | Applies one correction after input/version checks | No |

For a draft bundle from a local checkout:

```sh
python3 -m plumb init /path/to/new-workspace \
  --repo /path/to/project --module 'Orders' --code src/orders \
  --source docs/orders.md --section 'Cancellation'

python3 -m plumb status /path/to/new-workspace --source-repo /path/to/project
```

The workspace's parent must exist. Init reads committed blobs and leaves the
original repository and dirty files untouched. Check the
[prepared Pond bundle](examples/pond-claude-code/knowledge/index.md) for a real import.

The skill can do semantic work in its current host session. Optional `check` and
`propose` calls consume additional provider allowance and require an available
allocation. An exhausted budget stays exhausted. [Command and budget guide](plumb/README.md).

## What stays lightweight

There is no required IDE, background service, index, local model, or GPU workload.
The skill selects relevant context rather than loading every bundle. Tests and
model work run serially unless the task and available resources justify more.

The optional CLI bounds a text workspace to 256 files, 2 MiB total, and 256 KiB
per file. Its guards apply to operations routed through those commands. Skill
instructions are not a sandbox for the host agent.

Source refresh tracks a selected local Git ref without fetching origin. It does
not resync code or push corrections upstream. Apply changes one file in an
isolated workspace; concurrent edits can race its final check and write.

OpenProse remains an optional future way to package a workflow once plain skill
instructions show a concrete limitation. No OpenProse or Reactor dependency is
required. [Architecture and direction](docs/ARCHITECTURE.md).

## Evidence and development

The [skill forward test](evals/skill_pilot/RESULTS.md) exercised an isolated code
change and a conflicting-source case, and exposed overhead we reduced. It is a
controlled native-agent trial, not evidence of general effectiveness.

The [historical Pond pilot](evals/intent_pilot/RESULTS.md) established no detection
advantage for curated bundles over the original source material. Controlled
[correction workflows](evals/intent_pilot/hillclimb/RESULTS.md) and
[adversarial exercises](evals/intent_pilot/adversarial/RESULTS.md) test selected
behaviors. The [Git-source milestone](evals/intent_pilot/module_source_milestone/RESULTS.md)
verifies imports and stale-correction rejection. These do not establish general
semantic accuracy or everyday adoption.

Run the local command tests without model usage:

```sh
python3 -m unittest discover -s plumb -p 'test_*.py'
```

The [hero artwork](assets/plumb-hero.png) was created with image generation.
Its [generation prompt](assets/plumb-hero.prompt.md) is kept with the asset.

Earlier factory skills and experiments remain in the repository for reference.
The standalone [Plumb skill](skills/plumb/SKILL.md) has no dependency on their
installers, hooks, or approval files.

[MIT](LICENSE). Bundled book rubrics retain their [upstream notice](kit/packs/LICENSE.agent-rules-books).
