# Install the skills

Every skill is a complete, self-contained folder. Install whole folders:
`SKILL.md` needs its `references/`, `sources.json` and licence file.

## Declaratively with Home Manager (recommended)

Add `inputs.nix-skills.url = "github:olafkfreund/nix-skills";` to your
flake, import `inputs.nix-skills.homeManagerModules.default` for your user,
and set `programs.nix-skills`:

```nix
programs.nix-skills = {
  enable = true;
  agents = [ "claude" "codex" ];
  # skills = [ "nix-language" "nixos-operations" ];  # omit for all skills
};
```

The module links each selected skill directory, read-only from the Nix
store, into each agent's skill directory. Existing files keep Home Manager's
normal collision protection. All options are listed in
[Home Manager module options](../reference/options.md).

When Home Manager is a NixOS module, rebuild with `nixos-rebuild`. Never run
`home-manager switch` in that setup.

## Agents and directories

| Agent | `agents` value | Skill directory | Call a skill | List skills |
| --- | --- | --- | --- | --- |
| [Claude Code](https://code.claude.com/docs/en/skills) | `"claude"` | `~/.claude/skills` | `/nixos-coding-agents` | `/skills` |
| [Codex](https://learn.chatgpt.com/docs/build-skills) | `"codex"` | `~/.agents/skills` | `$nixos-coding-agents` | `/skills` |
| [OpenCode](https://opencode.ai/docs/skills) | `"opencode"` | `~/.config/opencode/skills` | Name the skill in your prompt | Ask the agent |
| [Antigravity](https://www.antigravity.google/docs/migration/workflows-to-skills/) | `"antigravity"` | `~/.gemini/config/skills` | `/nixos-coding-agents` | Ask the agent |

All four also pick a skill automatically when a request matches its
description. OpenCode also reads `~/.claude/skills` and `~/.agents/skills`
and needs unique skill names: if you already selected `"claude"` or
`"codex"`, do not add `"opencode"`.

For one shared or custom location, set `directory` instead of `agents`, for
example `directory = ".agents/skills";`. Do not combine the two.

## Without Home Manager

The collection is also a data package. It exposes `share/nix-skills/<name>`
but creates no links:

```nix
environment.systemPackages = [
  inputs.nix-skills.packages.${pkgs.stdenv.hostPlatform.system}.nix-skills
];
```

Or clone a reviewed commit and link folders by hand:

```sh
git clone https://github.com/olafkfreund/nix-skills.git
cd nix-skills
git checkout --detach <reviewed-commit-sha>
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/nix-workflow" ~/.agents/skills/nix-workflow
```

Repeat the link for each skill you want, using your agent's directory from
the table. For an agent without native skill discovery, ask it to read the
chosen `SKILL.md` and its linked references before the task.
