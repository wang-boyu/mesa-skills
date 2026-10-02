# Client integrations

The main README covers [installation](../README.md#installation),
[usage](../README.md#example-usage) and
[updating the skills](../README.md#updating-the-skills).
The [Codex notes](codex/README.md) and
[Claude Code notes](claude-code/README.md) cover client-specific discovery,
native definitions and validation limits.

## Troubleshooting

**Existing files or local edits.** The installer refuses to overwrite
unrecognized installations or locally edited files. Compare the reported
paths with the source and preserve customizations before reconciling them.
Keep `mesa-skills-install.json` in the client home; deleting it does not
resolve a conflict. Do not remove unrelated skills or configuration to make
installation succeed.

**Interrupted updates or retained locks.** Do not run installers concurrently
or edit installed files during an update. Read the installer output and
follow the reported `RECOVERY.txt`:

- If restoration is unfinished or the outcome is unknown, keep the backups,
  recovery directories and locks until the specified restoration is complete.
- If the instructions say **cleanup only**, the installed files and record
  are consistent. Do not restore old backups. After confirming no installer
  is running, remove only the leftover paths named in those instructions.

Do not blindly delete `.mesa-skills-install.lock` directories or assume an
interrupted update succeeded.
