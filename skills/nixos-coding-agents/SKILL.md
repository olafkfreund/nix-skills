---
name: nixos-coding-agents
description: Choose, install and sandbox AI coding agents on NixOS with llm-agents.nix packages, agent-images containers and agent-box disposable workspaces.
---

# NixOS coding agents

Three upstream projects form one pipeline. Use as many layers as the user
needs:

| Layer | Project | Gives |
|---|---|---|
| Packages | [numtide/llm-agents.nix](https://github.com/numtide/llm-agents.nix) | About 200 agents (Claude Code, Codex, Gemini CLI, OpenCode and others) as flake packages and an overlay, with a binary cache and daily updates |
| Images | [nothingnesses/agent-images](https://github.com/nothingnesses/agent-images) | A Nix-built OCI image per agent, running as a non-root user in `/workspace` |
| Orchestration | [0xferrous/agent-box](https://github.com/0xferrous/agent-box) | `ab`, which creates a disposable Git worktree or Jujutsu workspace and runs the agent in a container |

This skill links to upstream rather than copying it; the examples were checked
against upstream on 2026-09-23. Upstream changes daily, so confirm flags and
parameters there before relying on them.

## Establish the setup first

- Find out how the system is built: a flake with `nixosConfigurations`, or
  channels. Check whether Home Manager is standalone or a NixOS module.
- Check whether the system's nixpkgs follows nixpkgs-unstable or a stable
  release. llm-agents.nix is tested only against unstable.
- The images and agent-box are Linux only. On nix-darwin and standalone Home
  Manager, offer only the packages layer.

## Decision tree

1. **Trying an agent once?** Run `nix run github:numtide/llm-agents.nix#<agent>`,
   or `nix run github:numtide/llm-agents.nix` for an interactive picker.
   Nothing is installed.
2. **Keeping it?** Add llm-agents.nix as a flake input and install the chosen
   agents declaratively. They are then pinned in `flake.lock` and rolled back
   with the generation. See [setup](references/setup.md#llm-agentsnix).
3. **Keeping it away from secrets?** An agent on the host can read everything
   the user can, including `~/.ssh`, cloud credentials and `.env` files. Run it
   from an agent-images container that mounts only the project. See
   [setup](references/setup.md#agent-images).
4. **Several agents in parallel, or throwaway branches?** Use agent-box
   worktree mode. Each session gets its own workspace with tracked files only.
   See [setup](references/setup.md#agent-box).
5. **Team standard?** Build one image with `mkAgentImage` and commit an example
   `.agent-box.toml`. See [story 5](references/user-stories.md#5-publish-one-reproducible-team-image).

## Choosing an agent

The generated package list in the
[llm-agents.nix README](https://github.com/numtide/llm-agents.nix#available-tools)
shows each agent's licence and whether it is built from source or shipped as a
binary. Compare:

- **Licence.** llm-agents.nix marks unfree agents `free = true` for
  evaluation, so `allowUnfree` neither gates nor is needed for them. Read
  `meta.license.shortName` instead.
- **Source.** A source build can be audited; a binary cannot.
- **Provider.** Which model provider it talks to, which key it needs, and what
  that costs. Some agents support several providers or local models.
- **Cache.** Using the flake's own packages hits the Numtide cache. The overlay
  builds against the user's nixpkgs and may compile locally.

Recommend a short list with the trade-offs, not a single winner.

## Rules

- Do not suggest `inputs.nixpkgs.follows` for llm-agents.nix on a stable
  release. It breaks eventually and loses cache hits.
- Never suggest `home-manager switch` to someone who uses Home Manager as a
  NixOS module; they rebuild through `nixos-rebuild`.
- Never add a secret or socket to `env_passthrough` or `-e` without saying
  what it gives the agent. Never forward `SSH_AUTH_SOCK`, cloud credentials or
  the Nix daemon socket by default.
- Do not add substituters or trusted keys, rebuild, build images, load images
  or start containers without the user's authorization. Propose the exact
  change or command instead.
- Say what the sandbox does not protect. Read [security](references/security.md)
  before advising on isolation.

## References

- [User stories](references/user-stories.md): a guide of six stories, each
  with a configuration, a check and how to undo it.
- [Setup](references/setup.md): llm-agents.nix, rootless Podman on NixOS,
  agent-images, agent-box, Portal, and nix-darwin or standalone Home Manager.
- [Security](references/security.md): what each layer protects and what it
  does not.

Report what you actually ran, and which advice you could not verify on the
user's release.
