# Codex integration notes

See the main README for [installation](../../README.md#installation),
[usage examples](../../README.md#codex) and
[updating the skills](../../README.md#updating-the-skills).

## Discovery

In Codex CLI or the IDE extension, use `/skills` or `$` to select a skill.
Other interfaces may use a skill picker. Confirm that the selected `SKILL.md`
and subagent paths match those printed by the installer. Older project-local
copies can compete with user-level copies; the installer does not remove them.

If a skill or role is missing, check the selected paths and restart the
session. If your client cannot delegate to a required role, that review
remains unperformed; do not substitute self-review.

## Native definitions

The TOML definitions use the same names as the roles in the portable skills;
for example, [mesa_model_worker](agents/mesa_model_worker.toml).
Codex identifies each agent by its `name` field.
See the official [skill](https://developers.openai.com/codex/skills/) and
[subagent](https://developers.openai.com/codex/subagents/) documentation
for client controls.

## Validation status

**Experimental.** Earlier native tests used project-local installation.
The current user-level route has offline checks but has not been validated
end to end in a native Codex session.

For installer conflicts or retained locks, see
[installation troubleshooting](../README.md#troubleshooting).
