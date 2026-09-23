# nix-skills

Portable skills that give AI coding agents current, source-backed knowledge of Nix, NixOS and their ecosystem.

**Documentation:** <https://olafkfreund.github.io/nix-skills/>

## What this is

AI coding agents often give Nix advice that is out of date, meant for another distribution, or imperative.
These skills give Claude Code, Codex, OpenCode and Antigravity pinned, version-checked guidance for Nix,
NixOS, Home Manager, nix-darwin, devenv, Nixpkgs and running coding agents on NixOS, so they propose
declarative, reversible changes. The collection installs **skills, not agents**.

## Get started

**Try it without changing your system**, in a disposable NixOS VM with agents and skills ready
([guide](https://olafkfreund.github.io/nix-skills/tutorials/demo-vm.html)):

```sh
nix run github:olafkfreund/nix-skills?dir=demo
```

**Set up your own NixOS machine** with agents and skills, by importing `nixosModules.agentic` or starting
from the template ([guide](https://olafkfreund.github.io/nix-skills/how-to/own-machine.html)):

```sh
nix flake init -t github:olafkfreund/nix-skills#agentic-nixos
```

**Install only the skills** for the agents you already have, with the Home Manager module
([guide](https://olafkfreund.github.io/nix-skills/how-to/install.html)):

```nix
inputs.nix-skills.url = "github:olafkfreund/nix-skills";
# in home-manager.users.<you>:
imports = [ inputs.nix-skills.homeManagerModules.default ];
programs.nix-skills = { enable = true; agents = [ "claude" ]; };
```

## First prompt

Open your agent in your system configuration repository and paste:

```text
Use the nix-skills skills. I'm on NixOS and want to set up this machine for
agentic coding. Read my system configuration first, tell me what you found,
and propose changes as a diff. Do not rebuild, install or run containers
until I approve.
```

## Skills

| Skill | Purpose | Source and licence |
| --- | --- | --- |
| [devenv-project](skills/devenv-project/SKILL.md) | Configure and troubleshoot devenv project environments | devenv, [Apache-2.0](skills/devenv-project/LICENSE) |
| [home-manager](skills/home-manager/SKILL.md) | Configure Home Manager user environments and NixOS integration | Home Manager, [MIT](skills/home-manager/LICENSE) |
| [microvm-nix](skills/microvm-nix/SKILL.md) | Configure declarative microVMs with microvm.nix | microvm.nix, [MIT](skills/microvm-nix/LICENSE) |
| [nix-darwin](skills/nix-darwin/SKILL.md) | Configure nix-darwin macOS systems and darwin-rebuild generations | nix-darwin, [MIT](skills/nix-darwin/LICENSE) |
| [nix-language](skills/nix-language/SKILL.md) | Write, explain, debug, and review Nix expressions | Nix manual, [LGPL-2.1](skills/nix-language/COPYING) |
| [nix-workflow](skills/nix-workflow/SKILL.md) | Choose Nix commands, find packages and files, use dev shells, debug builds, and navigate the ecosystem | Hand-written, repository licence |
| [nixos-coding-agents](skills/nixos-coding-agents/SKILL.md) | Choose, install and sandbox AI coding agents with llm-agents.nix, agent-images and agent-box | Hand-written, repository licence |
| [nixos-operations](skills/nixos-operations/SKILL.md) | Operate NixOS: rebuild modes, generations and rollback, upgrades, store cleaning, boot and services | NixOS manual, [MIT](skills/nixos-operations/COPYING) |
| [nixpkgs-development](skills/nixpkgs-development/SKILL.md) | Package software and use Nixpkgs helpers, overlays, and library APIs | Nixpkgs manual, [MIT](skills/nixpkgs-development/COPYING) |
| [nixos-wiki](skills/nixos-wiki/SKILL.md) | Find retained NixOS configuration and troubleshooting guidance | NixOS Wiki, [MIT](skills/nixos-wiki/COPYING) |

Pinned upstream revisions, update schedule and details are in the generated
[skill catalog](https://olafkfreund.github.io/nix-skills/reference/catalog.html).

## Documentation

- [Tutorials](https://olafkfreund.github.io/nix-skills/tutorials/getting-started.html): getting started, the demo VM
- [How-to guides](https://olafkfreund.github.io/nix-skills/how-to/install.html): install, your own machine, update and roll back, fix discovery, contribute
- [Reference](https://olafkfreund.github.io/nix-skills/reference/catalog.html): skill catalog, module options, update schedule, Nix style rules
- [Explanation](https://olafkfreund.github.io/nix-skills/explanation/why-skills.html): why skills, sources and licences, how updates work, security model
- [Maintain](https://olafkfreund.github.io/nix-skills/maintain/index.html): development environment, automatic updates, per-skill maintenance

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md): every change goes through an issue,
reviewed intent, spec and plan documents, and a pull request that passes the checks.

## Licence

The repository is [MIT](LICENSE) licensed. Copied upstream material keeps its upstream licence, shipped with
each skill, and is not relicensed; see
[per-skill sources and licences](https://olafkfreund.github.io/nix-skills/explanation/authored-and-generated.html#per-skill-sources-and-licences).
