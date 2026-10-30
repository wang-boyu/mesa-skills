# Scoped quality checks for evaluation work

Inspect and use the model project's existing quality configuration first.
Preserve useful checks, settings and spelling exceptions. When authoring
evaluation Python code and suitable tooling is absent, adapt this skill's
[pre-commit configuration](../assets/quality/.pre-commit-config.yaml),
[empty spelling word allowlist](../assets/quality/.codespellignore) and
[minimal Ruff configuration](../assets/quality/ruff.toml) within authorized
project setup. These resources work without the development skill.

Do not overwrite existing configuration or add a competing Ruff configuration.
If the project uses `pyproject.toml`, merge needed settings into its existing
`[tool.ruff]` and `[tool.ruff.lint]` sections only where setup is authorized.
Planning or report-only work uses applicable document checks without adding
Python tooling unnecessarily. Audit-only adds no configuration and runs no
auto-fixers against protected targets.

## Adapt the baseline to owned and protected paths

The baseline pins pre-commit hooks for Ruff lint/import sorting and formatting,
codespell, whitespace, end-of-file, YAML and TOML checks. Retain useful existing
versions; do not upgrade pins merely to copy the template. Python hooks select
Python and stub files. Set a Python target only after checking the project's
supported version. `.codespellignore` is a word allowlist: add only justified
words, one per line. File exclusions belong in tool configuration.

Adapt the pre-commit exclusions and Ruff `extend-exclude` to actual protected
inputs, production code, accepted results, generated figures and third-party
material. The templates cover common data/output directories, not every
project's protected paths. Ruff `force-exclude` also excludes explicitly passed
paths; `extend-exclude` retains its built-in exclusions. Exclusions complement
assigned-file scope, not replace it.

Before running existing hooks, inspect their behavior and commands. Passing
`--files` does not authorize hooks that ignore filenames, change protected
files or launch simulations; inspect such settings as `pass_filenames: false`
and `always_run`, and the invoked script itself. Use safe scoped checks instead
and disclose any unavailable coverage. Formatting never authorizes experiments.

Use authorized project-local setup for tool installation and hook downloads,
including required network access and caches. Do not modify global Python or
personal client configuration. The baseline is compatible with pre-commit
4.7.0; record chosen versions in the project's existing dependency convention
when useful. Running checks is separate from installing automatic Git hooks:
do not run `pre-commit install` automatically. The skill installer installs none
of these tools. Disclose unavailable checks rather than treating copied
configuration as validation.

## Author checks and independent review

Authors run modifying checks only on assigned evaluation code, tests,
documentation and configuration. Run lint fixes before formatting, inspect all
modifications, correct spelling or format defects, rerun affected tests or
plotting checks and obtain a clean final pass. A hook that rewrites files has
made edits needing review, not completed validation.

From the model project root, an illustrative scoped run is:

```sh
pre-commit run --files evaluation/analysis.py evaluation/plot_results.py docs/evaluation_results.md
```

Replace these example paths with every actual owned file, including authored
untracked files and any new configuration. Do not stage unrelated user work to
make hooks see it. Do not default to a modifying `--all-files` run over the model
repository; it also misses untracked files. Inspect changes and repeat applicable
checks until clean.

Reviewers apply no fixes. Where appropriate, use check-only commands such as
`ruff check --no-fix --no-cache <owned paths>` and
`ruff format --check --no-cache <owned paths>`; also inspect configuration for
other write behavior. A pre-commit run is not inherently read-only. Route
accepted findings to the author through the existing workflow, then recheck
affected artifacts. Audit checks must also satisfy the workflow's protected
target and cache restrictions.

Primary references: [pre-commit execution and hooks](https://pre-commit.com/),
[Ruff ordering and integration](https://docs.astral.sh/ruff/integrations/),
[Ruff configuration](https://docs.astral.sh/ruff/configuration/) and
[codespell allowlists](https://github.com/codespell-project/codespell).
