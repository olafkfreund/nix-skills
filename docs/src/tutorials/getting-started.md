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

## Next: agentic coding on NixOS

As a NixOS user with no AI agent yet, I want a coding agent set up
declaratively, and optionally sandboxed, so that I can start agentic coding
without breaking my system or exposing my secrets.

1. **Run an agent once, without installing it.**

   ```sh
   nix run github:numtide/llm-agents.nix#claude-code   # or #codex, #opencode, #antigravity-cli
   ```

   **Check:** it starts, and nothing is installed.
2. **Install the skills** for that agent, as in step 1 above, and rebuild.
   **Check:** as in step 2 above.
3. **Give the start prompt** from your system configuration repository.
   **Check:** the agent reads your configuration and proposes a diff without
   applying it. Typically the diff adds the llm-agents.nix input and your
   agent, the Numtide binary cache, and optionally
   `virtualisation.podman.enable` for sandboxing.
4. **Review the diff, then build and switch yourself:** `nixos-rebuild build`,
   then `nixos-rebuild switch`. **Check:** the agent is on your `PATH` without
   `nix run`. **Undo:** roll back to the previous generation.
5. **Per project.** In a code repository, ask for a devenv shell
   (`devenv-project`). For repositories you do not trust, ask to run the agent
   in a container or an agent-box worktree (`nixos-coding-agents`).
   **Check:** the devenv shell activates, and the sandbox check from
   [`nixos-coding-agents` stories 3 and 4](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-coding-agents/references/user-stories.md)
   passes.

| Skill | Purpose | Initial reference |
| --- | --- | --- |
| [devenv-project](https://github.com/olafkfreund/nix-skills/blob/main/skills/devenv-project/SKILL.md) | Configure and troubleshoot devenv project environments | devenv v2.3.1 |
| [home-manager](https://github.com/olafkfreund/nix-skills/blob/main/skills/home-manager/SKILL.md) | Configure Home Manager user environments and NixOS integration | Home Manager master snapshot |
| [microvm-nix](https://github.com/olafkfreund/nix-skills/blob/main/skills/microvm-nix/SKILL.md) | Configure declarative microVMs with microvm.nix | microvm.nix main snapshot |
| [nix-darwin](https://github.com/olafkfreund/nix-skills/blob/main/skills/nix-darwin/SKILL.md) | Configure nix-darwin macOS systems and darwin-rebuild generations | nix-darwin master snapshot |
| [nix-language](https://github.com/olafkfreund/nix-skills/blob/main/skills/nix-language/SKILL.md) | Write, explain, debug, and review Nix expressions | Nix 2.35.2 |
| [nix-workflow](https://github.com/olafkfreund/nix-skills/blob/main/skills/nix-workflow/SKILL.md) | Choose Nix commands, find packages and files, use dev shells, debug builds, and navigate the ecosystem | Authored guidance; ecosystem status checked 2026-09-23 |
| [nixos-coding-agents](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-coding-agents/SKILL.md) | Choose, install and sandbox AI coding agents with llm-agents.nix, agent-images and agent-box | Authored guidance linking upstream; checked 2026-09-23 |
| [nixos-operations](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-operations/SKILL.md) | Operate NixOS: rebuild modes, generations and rollback, upgrades, store cleaning, boot and services | NixOS manual chapters from the Nixpkgs master snapshot |
| [nixpkgs-development](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixpkgs-development/SKILL.md) | Package software and use Nixpkgs helpers, overlays, and library APIs | master snapshot; development series 26.11 |
| [nixos-wiki](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-wiki/SKILL.md) | Find retained NixOS configuration and troubleshooting guidance | 17 curated topics from the 2026-09-22 dump |

Each package records its upstream snapshot identity, curated selection, and
input/output hashes in its own `sources.json`. References cover selected topics,
not every upstream feature. Agents must check the project's actual versions.
The Nix skill does not supply NixOS options or replace Nixpkgs API documentation.
The portable `devenv-project` skill is distinct from a machine-specific `devenv`
policy skill and upstream's `devenv-setup`; their behavior is not interchangeable.
Each skill can be installed independently.


The [demo VM](demo-vm.md) and [Set up your own machine](../how-to/own-machine.md) now cover
steps 1 to 4 in a single command or import.
