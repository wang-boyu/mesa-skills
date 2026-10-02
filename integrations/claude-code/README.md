# Claude Code integration notes

See the main README for [installation](../../README.md#installation),
[usage examples](../../README.md#claude-code) and
[updating the skills](../../README.md#updating-the-skills).

## Discovery

Check the selected skill and subagent paths against those printed by the
installer. Older project-local definitions can take precedence over
user-level definitions; the installer does not remove them. Check known
duplicates and restart the session if a definition is missing.

## Native definitions

The Markdown definitions use hyphenated names corresponding to the portable
roles, such as [mesa-model-worker](agents/mesa-model-worker.md) for
`mesa_model_worker`.
Keep coordinating skills in the main conversation; do not add `context: fork`
to their definitions.

Review roles can use Bash for checks. Their no-write instructions do not,
by themselves, establish operating-system-enforced read-only access.

See the official [skill](https://code.claude.com/docs/en/skills) and
[subagent](https://code.claude.com/docs/en/sub-agents) documentation
for client controls.

## Validation status

**Optional, Experimental and native-unverified.** Definition, resource and
installer checks have been performed offline. Native discovery, permissions
and end-to-end workflows remain unverified; no tested client version is claimed.

For installer conflicts or retained locks, see
[installation troubleshooting](../README.md#troubleshooting).
