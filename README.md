# Mesa Skills

Agent skills for developing, documenting and evaluating agent-based models
with Mesa in Python.

| Skill | Purpose | Output |
|---|---|---|
| [develop-mesa-model](skills/develop-mesa-model/SKILL.md) | build or refactor models, with implementation checks and independent QA | readable model, focused tests and a concise model specification |
| [document-abm-with-odd](skills/document-abm-with-odd/SKILL.md) | write, update or audit model descriptions using the ODD protocol | seven-element ODD creation/update, or located audit findings; optional summary |
| [evaluate-mesa-model](skills/evaluate-mesa-model/SKILL.md) | plan evaluations, analyze model outputs and assess uncertainty and supporting evidence | purpose-specific plan, analysis or report with reproducible calculations and limits |

Each skill uses a main agent to coordinate subagents with different
responsibilities: implementation and independent QA for development,
writing and auditing for ODD, and experiment design and analysis for
evaluation. Other subagents help clarify model specifications or review
geographic details when needed.

The workflows use an **inner loop** for producing work, reviewing it
independently and correcting agreed issues. An **outer loop** then brings
in a new reviewer who was not involved in either producing the work or
its initial review. Accepted findings return to the responsible subagent
for correction and independent review. Audit-only tasks use separate
reviewers without changing their targets. See the
[development](skills/develop-mesa-model/references/workflow.md),
[ODD](skills/document-abm-with-odd/references/workflow.md) and
[evaluation](skills/evaluate-mesa-model/references/workflow.md) workflows
for details.

## Installation

With Python 3.12 or newer available, clone the repository:

```sh
git clone https://github.com/wang-boyu/mesa-skills.git
cd mesa-skills
```

You may preview the installation with `--dry-run`. This shows destination
paths and proposed changes without writing files:

```sh
python3 integrations/install.py --client codex --dry-run
```

Install the skills for Codex:

```sh
python3 integrations/install.py --client codex
```

For Claude Code, replace `--client codex` with `--client claude-code` in
either installer command.

This installs all three skills and ten native roles **once per user on this
machine**. Unrelated skills, roles and configuration are preserved.

### Installation locations

| Application | Skills | Native roles |
|---|---|---|
| Codex | `~/.agents/skills/` | `~/.codex/agents/` |
| Claude Code | `~/.claude/skills/` | `~/.claude/agents/` |

These are the default locations. For a custom configuration directory,
set `CODEX_HOME` or `CLAUDE_CONFIG_DIR` to an absolute directory before
installation. `CODEX_HOME` changes the Codex role and installation-record
locations, but its skills stay under `~/.agents/skills/`.
`CLAUDE_CONFIG_DIR` changes both Claude locations and its record. Changing
these settings does not migrate an existing installation.

## Example Usage

Open **your model project**, not this `mesa-skills` directory, in a local Codex or Claude Code session - for example, in the desktop app, CLI or IDE extension - and use prompts like the following to invoke the skills.

> [!WARNING]
> These skills use multiple subagents and review rounds, which can consume a substantial amount of time and tokens.

### Codex

```text
Use $develop-mesa-model to build a seeded Mesa model of households
sharing a finite resource. Verify that total resources are conserved.
```

```text
Use $document-abm-with-odd to audit docs/ODD.md against the model code.
Report discrepancies without changing the document or code.
```

```text
Use $evaluate-mesa-model to run a sensitivity analysis of this model.
Propose parameter ranges, output measures and a run budget for approval.
Then run the agreed experiments and report how the parameters affect
model outputs. For a stochastic model, use repeated runs to assess
uncertainty.
```

### Claude Code

```text
/develop-mesa-model Build a seeded Mesa model of households sharing
a finite resource. Verify that total resources are conserved.
```

```text
/document-abm-with-odd Audit docs/ODD.md against the model code.
Report discrepancies without changing the document or code.
```

```text
/evaluate-mesa-model Run a sensitivity analysis of this model.
Propose parameter ranges, output measures and a run budget for approval.
Then run the agreed experiments and report how the parameters affect
model outputs. For a stochastic model, use repeated runs to assess
uncertainty.
```

## Updating the skills

From your mesa-skills source checkout, fetch the latest changes, preview the
update, then apply it:

```sh
git pull --ff-only
python3 integrations/install.py --client codex --dry-run
python3 integrations/install.py --client codex
```

To update the Claude Code installation, use `--client claude-code`.
The installer updates your installed copies; it does not fetch updates
automatically or alter your model's Python environment. An unchanged rerun
leaves installed files unchanged.

For existing-file conflicts or interrupted updates, see
[installation troubleshooting](integrations/README.md#troubleshooting).


## License

Apache License 2.0