---
status: draft
issue: 37
author: olafkfreund
---

# Intent: NixOS coding agents skill

## Problem

New NixOS users who want an AI coding agent (Claude Code, Codex, Gemini CLI,
OpenCode and others) get no help from this collection, and face three
separate problems:

- **Choosing.** There are about 200 packaged agents. They mix free and unfree
  licences, source builds and prebuilt binaries, and each needs a different
  model provider and credentials. Nothing helps a newcomer narrow that down.
- **Installing the Nix way.** Vendor install scripts (`curl | sh`, `npm -g`)
  bypass the Nix store, do not work well on NixOS, and cannot be rolled back
  with a generation.
- **Containing the agent.** An agent running directly on the host can read
  `~/.ssh`, cloud credentials, `.env` files and the rest of the home
  directory. Most users do not know the Nix-native ways to limit that.

Three upstream projects already solve these problems as one pipeline, but
users have to discover them separately and join them up:

| Layer | Project | Licence |
|---|---|---|
| Packages | [numtide/llm-agents.nix](https://github.com/numtide/llm-agents.nix) | MIT |
| Container images | [nothingnesses/agent-images](https://github.com/nothingnesses/agent-images) | BlueOak-1.0.0 |
| Orchestration | [0xferrous/agent-box](https://github.com/0xferrous/agent-box) | MIT |

The layers work like this:

- **Packages.** llm-agents.nix provides flake packages and an overlay, with a
  binary cache. It is updated daily and tested only against
  nixpkgs-unstable.
- **Container images.** agent-images builds an OCI image for each agent. The
  image runs as a non-root user in `/workspace`. It also documents the setup
  NixOS needs for rootless Podman.
- **Orchestration.** agent-box creates disposable Git worktree or Jujutsu
  workspaces and starts each one in a container.

No skill in the collection covers AI coding agents. The routing table in
`skills/nix-workflow/SKILL.md` has no entry for them.

## Proposed outcome

- **A choice in a few questions.** A new user can ask their agent "which
  coding agent should I use on NixOS, and how do I run it safely?" and be
  walked through a short decision tree:
  1. try it once;
  2. install it declaratively;
  3. run it in a container;
  4. run several agents in parallel on disposable workspaces;
  5. build a team-standard image.
- **A guide built from user stories.** Each story has a goal, a minimal
  configuration and a check command. The stories cover:
  - trying an agent;
  - installing agents pinned and with rollback;
  - keeping an agent away from home-directory secrets;
  - running parallel disposable sessions;
  - building a team image;
  - choosing an agent by licence, cost and provider.
- **Honest security notes.** The guide states plainly what the sandbox does
  not protect:
  - environment variables passed into the container;
  - gitignored files exposed in local mode;
  - a permissive container trust policy;
  - daily-updated binaries;
  - the coupling to nixpkgs-unstable.
- **Discoverable.** The skill is found through the `nix-workflow` routing
  table and the README.

## Affected users and systems

- New and existing NixOS users who run, or want to run, AI coding agents.
- Home Manager users, including those who use Home Manager as a NixOS module.
  They rebuild through `nixos-rebuild`, never `home-manager switch`.
- Repository files: a new `skills/nixos-coding-agents/` directory,
  `skills.json`, the `skills/nix-workflow/SKILL.md` routing table, and
  `README.md`.
- No hosts are changed. Nothing is installed or activated as part of this
  work.

## Constraints

- **Authored, not copied.** The upstream documentation changes daily. The
  skill links to it rather than copying it. That means no provider, no
  updater, no `sources.json`, and no enrolment in automatic updates.
  Registering the skill must not enrol an updater.
- **Portable.** It must pass `scripts/check_collection.py`: two-line
  frontmatter, relative links that resolve, and no placeholders.
- **Verified configuration.** Every Nix snippet must use option names that
  exist in current NixOS and Home Manager, checked, not recalled from memory.
- **Safe defaults.** Security guidance must never recommend passing SSH agent
  sockets or cloud credentials into a container by default. It must present
  `insecureAcceptAnything` only as a local convenience.
- **No execution.** Validation does not run any upstream tool, build an
  image, or start a container.

## Open questions

- **Name.** The proposal is `nixos-coding-agents`. Codex suggested
  `nixos-agent-sandboxes`, but about half the scope is plain installation
  with no sandbox.
- **Scope beyond NixOS.** Should the guide also cover nix-darwin and
  standalone Home Manager? llm-agents.nix supports them, but the images are
  Linux-only.
- **Portal.** Should agent-box's host-capability broker (Portal) get only a
  pointer, or a user story of its own?
