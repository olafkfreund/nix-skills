# nix-skills

nix-skills is a collection of portable skills that give AI coding agents
(Claude Code, Codex, OpenCode, Antigravity and others) current,
source-backed knowledge of Nix, NixOS, Home Manager, nix-darwin, devenv,
Nixpkgs, and running coding agents on NixOS.

Agents often give Nix advice that is out of date, meant for another
distribution, or imperative: `nix-env -i`, editing generated files,
`curl | sh`. A skill is a folder of instructions and references that the
agent loads when a request matches. With these skills installed, the agent
proposes declarative, reversible changes based on the versions you actually
run.

The collection installs **skills, not agents**. To install an agent itself on
NixOS, see the [`nixos-coding-agents` skill](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-coding-agents/SKILL.md).

## Where to start

| You want to | Go to |
| --- | --- |
| Install the skills and try them | [Getting started](tutorials/getting-started.md) |
| Install for a specific agent, or without Home Manager | [Install the skills](how-to/install.md) |
| See which skills exist and where their content comes from | [Skill catalog](reference/catalog.md) |
| Understand how the references stay current | [How updates work](explanation/updates.md) |
| Add or improve a skill | [Contribute a skill](how-to/contribute.md) |

The source is on [GitHub](https://github.com/olafkfreund/nix-skills). The
catalog, the update schedule and the module options on this site are
generated from the repository when the site is built, so they match the
published commit.
