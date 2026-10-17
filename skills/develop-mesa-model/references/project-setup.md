# Project setup, outputs and run instructions

## Quality checks

For a new model project, adapt the bundled
[pre-commit configuration](../assets/quality/.pre-commit-config.yaml),
[empty spelling word allowlist](../assets/quality/.codespellignore) and
[minimal Ruff configuration](../assets/quality/ruff.toml) into the project root.
These are development resources, not a requirement to alter an existing
project's tooling. Preserve useful existing configuration; add or merge checks
only when development setup is in scope. Do not copy a second conflicting Ruff
configuration beside an existing one. In `pyproject.toml`, the equivalent
sections are `[tool.ruff]` and `[tool.ruff.lint]`.

The baseline pins Ruff lint/import sorting and formatting, codespell, whitespace,
end-of-file, YAML and TOML hooks. Ruff lint fixes run before formatting. Python
hooks explicitly select Python and stub files. Set a Python target only after
checking the model's minimum supported version; the template does not inherit
another project's target or spelling exceptions. Add only justified domain
words to `.codespellignore`, one word per line. File exclusions belong in the
tool configuration, not that word allowlist.

Review protected paths before running mutating tools. The templates exclude
common data, third-party and generated-output directories at any depth; adapt
both the pre-commit exclusions and Ruff `extend-exclude` to the actual project.
Source inputs may live elsewhere. Ruff `force-exclude` also protects explicitly
passed paths, and `extend-exclude` retains its normal built-in exclusions.
Do not format source datasets, third-party material, or generated results.

Use the authorized project environment for tool installation and hook downloads,
including any required network access. Do not change global Python or personal
client settings. The pinned hooks work with pre-commit 4.7.0; record the selected
tool versions in the project's existing dependency convention when useful.
Installing automatic commit hooks with `pre-commit install` is optional and
separate from executing checks.

Authors run fixes only on their assigned files. Inspect the diff after lint
fixes and formatting, correct genuine spelling or data-format findings, then
rerun affected behavior checks and obtain a clean final quality run. A hook
that rewrites a file has made an edit, not completed a successful check. Reviewers
and non-authoring verifiers do not run formatters or auto-fixes; route findings
to the appropriate owner. Where installed, `ruff check` without `--fix` and
`ruff format --check` provide check-only lint/format invocations.

In a normal Git project, run from the model root:

```sh
pre-commit run --all-files
# Repeat after inspecting and resolving changes until the run is clean.
```

`--all-files` covers tracked files only. Explicitly pass every intended authored
untracked file as well, for example:

```sh
pre-commit run --files woodland/agents.py woodland/model.py tests/test_model.py
```

Replace those example paths with the actual owned files, including new
configuration and documentation. Do not stage unrelated user files merely to
make them visible to hooks. When tracked files include other owners' changes,
limit mutating runs to the assigned paths and arrange broader checks through
the parent. Copying the templates or checking only the previously tracked files
does not verify the newly authored work.

Upstream references explain [Ruff hook ordering and integration](https://docs.astral.sh/ruff/integrations/),
[Ruff configuration and exclusions](https://docs.astral.sh/ruff/configuration/),
[pre-commit execution](https://pre-commit.com/) and
[codespell word allowlists](https://github.com/codespell-project/codespell).
Recheck compatibility when updating pins; installation is not a compatibility test.

## Fresh result destinations

For a newly generated model, allocate one unused directory for each run or UI
export, such as `outputs/run-0001/` and `outputs/run-0002/`. Keep stable filenames
inside it and report the destination. Adapt the small
[allocation helper](../assets/run_output.py) into the model's appropriate output
module, or use the same exclusive-directory operation in an existing helper.
It claims a directory with `mkdir()` and retries only a name collision; a
permission or other I/O error must surface. Checking existence before creating
the directory is insufficient when two callers allocate concurrently.

Allocate at the start of each run or export action, not once when the UI starts.
Keep existing and partial runs, including directories left by a failed export.
Preserve a sensible existing output convention with the same non-overwrite
principle. Overwriting previous results requires explicit authorization; normal
execution needs no overwrite-policy question. This is a small filesystem
convention, not a run database or backup system.

Output allocation must not draw from model RNGs. Optional metadata timestamps
also must not affect simulation behavior. Replay checks compare scientific
states, events and observations, not destination names or incidental timestamps.
Ordinary source, README and ODD edits still update the intended document rather
than creating numbered document copies.

## Portable model documentation

Write the README for someone starting from the cloned model's project root.
Document compatible Python and dependency setup, the actual relative headless
entry point and parameters, output locations, and normal verification commands.
When a Solara UI is requested, show `solara run app.py` from that root. Make the
command match the delivered entry point; a layout illustration does not create
an executable command. Use relative project paths, not a developer's username,
absolute checkout path or personal pyenv installation.

Keep scientific assumptions, rationale, units and input provenance accessible in
the model documentation. Keep machine-specific environment records, permission
history, failed tool calls, runtime ledgers and agent-by-agent work narration
out of the ordinary quick start. Use an existing verification record for useful
operational detail; no new reporting system is required. State verification
limits plainly, including any unverified requested-scale run.
