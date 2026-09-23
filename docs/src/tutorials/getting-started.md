# Getting started

This tutorial installs the skills for one agent on NixOS, checks that the
agent sees them, and gives you the first prompt to use. It assumes Home
Manager is used as a NixOS module in a flake-based system configuration.
For other setups, see [Install the skills](../how-to/install.md).

## 1. Add the input and enable the module

Add the input to your system flake, and commit the lock file:

```nix
inputs.nix-skills.url = "github:olafkfreund/nix-skills";
```

Enable the module for your user (replace `alice`; `inputs` must be in
scope), and pick your agents:

```nix
home-manager.users.alice = {
  imports = [ inputs.nix-skills.homeManagerModules.default ];
  programs.nix-skills = {
    enable = true;
    agents = [ "claude" ];
  };
};
```

Rebuild through NixOS with `nixos-rebuild`, never `home-manager switch`.
The `agents` values are listed in [Install the skills](../how-to/install.md#agents-and-directories).

## 2. Check that the agent sees them

```sh
ls ~/.claude/skills   # or your agent's directory
```

Then, in the agent, run `/skills` (Claude Code, Codex) or ask "Which skills
do you have available?" (OpenCode, Antigravity). If a skill is missing, see
[Fix skill discovery](../how-to/fix-discovery.md).

## 3. Start with this prompt

Open your agent in your system configuration repository and paste:

```text
Use the nix-skills skills. I'm on NixOS and want to set up this machine for
agentic coding. Read my system configuration first, tell me what you found,
and propose changes as a diff. Do not rebuild, install or run containers
until I approve.
```

## 4. Try more requests

| You ask | Skill it should use |
| --- | --- |
| "My rebuild fails with 'The option … does not exist'. What changed?" | `nixos-operations`, `nixos-wiki` |
| "Add a devenv shell with Python 3.12 and Postgres to this repo." | `devenv-project` |
| "Which package provides `libssl.so`, and how do I reference it?" | `nix-workflow` |
| "Move my shell and git config into Home Manager." | `home-manager` |
| "Package this Go CLI with `buildGoModule`." | `nixpkgs-development` |
| "Run Claude Code on this repo so it cannot read `~/.ssh`." | `nixos-coding-agents` |

The full list is in the [skill catalog](../reference/catalog.md).
