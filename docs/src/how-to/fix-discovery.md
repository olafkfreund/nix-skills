# Fix skill discovery

## Check the files first

```sh
ls -l ~/.claude/skills           # or your agent's directory
ls ~/.claude/skills/nix-workflow  # SKILL.md must be present
```

If the directory is empty, the module is not enabled for this user, or the
system was not rebuilt. With Home Manager as a NixOS module, rebuild with
`nixos-rebuild`, not `home-manager switch`.

## Then check the agent

- **Claude Code, Codex:** run `/skills`. Both document support for
  symlinked skill directories.
- **OpenCode, Antigravity:** ask "Which skills do you have available?".
  Neither documents whether it follows symlinked skill directories, and the
  module installs each skill as a link into `/nix/store`. If a skill is
  missing here, please [open an issue](https://github.com/olafkfreund/nix-skills/issues)
  with the agent version.

## Common causes

| Symptom | Cause | Fix |
| --- | --- | --- |
| OpenCode shows each skill twice | OpenCode also reads `~/.claude/skills` and `~/.agents/skills` | Remove `"opencode"` from `agents` when `"claude"` or `"codex"` is selected |
| Home Manager refuses to create a link | A file or folder already exists at the destination | Move the existing item away; links are never forced |
| A skill is present but never used | Its description did not match the request | Call it explicitly, see [Install the skills](install.md#agents-and-directories) |
| Old guidance after an update | The agent session started before the rebuild | Start a new agent session |
