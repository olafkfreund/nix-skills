---
status: draft
issue: 58
author: olafkfreund
---

# Intent: move from the demo to your own machine

## Problem

The demo VM (#57) lets users try agents and skills without changing their
system. When they want the same setup on their own NixOS machine, they are
on their own:

- **The only real-machine path is manual.** The [Getting started] tutorial
  shows how to add the skills. Installing an agent from llm-agents.nix, its
  binary cache, Podman and devenv is described only in the
  `nixos-coding-agents` skill, as separate snippets the user must assemble.
- **The demo's configuration cannot be reused as it is.** `demo/demo.nix`
  mixes parts that belong on any machine (agents, skills for each agent,
  Podman, devenv, flakes and the Numtide cache) with parts that must never
  reach a real system:
  - a `demo` user with the fixed password `demo`;
  - console automatic login;
  - SSH enabled for that account;
  - VM sizing (`virtualisation.vmVariant`).

  `nixosConfigurations.demo` cannot even be built for real hardware, since
  it has no disks or bootloader. Copying it would be unsafe.
- **Two kinds of user need different things:**
  - **someone starting a new flake configuration**, for example on a fresh
    install, wants a complete, working starting point;
  - **someone with an existing NixOS flake**, the common case, cannot use a
    template, because `nix flake init` refuses to overwrite existing files.
    They need something to import into the configuration they already
    have.
- **Choosing agents stays scattered.** The duplicate-directory rule
  (OpenCode sees the Claude and Codex directories), the agent-to-directory
  mapping and the unfree label all live in the demo module or the docs. A
  user wiring things by hand has to get each right.

[Getting started]: https://olafkfreund.github.io/nix-skills/tutorials/getting-started.html

## Proposed outcome

- **Existing configurations:** one import and one option list. A user adds
  a module to their system and sets which agents they want. They get the
  agents, the skills for each agent, the Numtide cache, and optionally
  Podman and devenv, with the duplicate-directory rule handled for them.
- **New configurations:** `nix flake init -t
  github:olafkfreund/nix-skills#agentic-nixos` produces a small, commented
  flake that uses that same module, for a user to adapt to their hardware.
  The welcome text after `init` lists the next steps and ends with the
  start prompt.
- **The demo uses the same shared part,** so the demo, the template and a
  real machine cannot drift apart. The demo keeps only its demo-only
  additions.
- **Documented** with a how-to page on the site, "Set up your own machine",
  with the demo as the recommended first step.
- **Tested.** The shared part is checked by the existing demo VM test. The
  template is checked to evaluate, so it cannot silently break.

## Affected users and systems

- NixOS users moving from the demo to their own machine, and new NixOS
  users starting a configuration.
- Likely files:
  - a shared module, split out of `demo/demo.nix`, with the demo module
    importing it;
  - a template directory;
  - a `templates` output;
  - possibly a new module output;
  - a docs page, `SUMMARY.md`, and AGENTS.md and CONTRIBUTING.md.
- Users' machines only when they choose to import or init. Nothing changes
  for people who only install skills.
- No change to the skills or to the Home Manager skill module's behaviour.

## Constraints

- **Skill users unaffected.** The main flake must not gain llm-agents.nix as
  an input, because skill users would then lock it. Anything that needs
  llm-agents.nix lives where the demo does, or takes the agent packages as
  an argument.
- **Safe on real hardware.** The shared part adds no users, passwords,
  automatic login, SSH, firewall changes or boot settings. It only adds
  what is listed above. Demo-only settings stay in the demo.
- **Fits into existing configurations.** It works with Home Manager as a
  NixOS module, which the documentation assumes, for a user the importer
  names. It never runs `home-manager switch`, and never overrides the
  user's own nixpkgs `config`.
- **Nothing hidden.** The binary cache and any unfree agents are opt-in or
  clearly stated. Choosing agents stays with the user.
- **The template is a starting point, not a system.** It cannot know the
  user's disks, bootloader or hardware. It must say so and point to
  `nixos-generate-config`, never pretend to be bootable as it is.
- **Tested in CI.** The template's flake must at least evaluate there,
  against the current commit. The shared module keeps passing the demo VM
  test.
- **Existing rules still apply:** the Nix style rules, the documentation
  checks, and the intent → spec → plan gates.

## Open questions

- **Where does the shared module live?** In the `demo/` flake, which
  already has llm-agents.nix, as `nixosModules.agentic`, or in the main
  flake taking agent packages as an argument, so it needs no new input?
- **Home Manager user.** Should the module configure skills for one named
  user (an option such as `user = "alice"`), or leave the Home Manager part
  to the user and only provide the system part?
- **Podman and devenv.** On by default, or opt-in options?
- **The template's shape.** A complete minimal `flake.nix` plus a
  `configuration.nix` with placeholders for hardware, or only a flake
  fragment and a README for merging into an existing flake?
