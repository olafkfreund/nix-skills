---
status: approved
issue: 27
author: olafkfreund
---

# Intent: darwin Home Manager and NixOS system operations

## Problem

User feedback identified three typical entry points into Nix: developers
(devShells), Home Manager users (often on darwin), and NixOS administrators
(mostly rebuilding the system). The collection now serves developers through
`nix-workflow`, `devenv-project` and `nix-language`. The other two groups are
poorly served:

- **Home Manager on darwin.** The `home-manager` skill bundles five upstream
  files: NixOS module integration, configuration, dotfiles, modular services
  and writing modules. None covers darwin. Upstream Home Manager has pages for
  exactly this gap: `installation/nix-darwin.md`, `nix-flakes/nix-darwin.md`,
  standalone installation (`nix-flakes/standalone.md`), `usage/rollbacks.md`
  and `usage/updating.md`. An agent on a Mac cannot tell whether the user runs
  Home Manager standalone or as a nix-darwin module, and so applies NixOS-only
  advice.
- **nix-darwin itself.** No skill covers it: `darwin-rebuild`, its
  configuration and its relation to Home Manager. nix-darwin is MIT licensed;
  its main documentation is `README.md` plus a generated options manual.
- **NixOS system operations.** No skill covers:
  - the rebuild modes (`switch`, `boot`, `test`, `build`);
  - generations and rollback;
  - upgrading channels or flake inputs;
  - cleaning the store;
  - boot problems and service management.

  `nixos-wiki` has 17 curated wiki topics, but not the NixOS manual's
  authoritative chapters. These chapters are small: changing the
  configuration 3.6 KB, upgrading 5.3 KB, rollback 1.3 KB, cleaning the store
  1.9 KB, boot problems 3.3 KB, service management 6.9 KB.

## Proposed outcome

- **Home Manager:** an agent working on a user's Home Manager setup first
  finds out how it is installed: NixOS module, nix-darwin module or
  standalone. It then follows the matching pinned upstream instructions for
  configuring, applying, updating and rolling back, including on darwin.
- **nix-darwin:** an agent working on a nix-darwin system can explain and
  change its configuration, and knows how `darwin-rebuild` applies it and how
  Home Manager fits in, from pinned upstream text.
- **NixOS administration:** an agent helping an administrator can explain and
  choose between rebuild modes, list and roll back generations, upgrade
  deliberately, clean the store safely and diagnose boot problems, from pinned
  NixOS manual text. It presents every state-changing action as a proposal
  that needs the user's authorization.
- The `nix-workflow` routing table then points darwin and NixOS
  administrators at real content.

## Affected users and systems

- Home Manager users on darwin and Linux, nix-darwin users, and NixOS
  administrators, through the collection's agents.
- `scripts/home_manager.py` (the reviewed selection), and possibly a new
  provider config for nix-darwin and one for the NixOS manual.
- `skills/home-manager/`, a new skill or skills, `skills.json`, the README,
  and the `nix-workflow` routing text.
- The weekly update workflow, if new providers are enrolled. That needs its
  own reviewed matrix entry.

## Constraints

- **Maintained upstream excerpts, not authored rewrites,** consistent with the
  collection. Pinned revisions, recorded hashes, licences and attribution.
  Home Manager and nix-darwin are MIT; Nixpkgs, including the NixOS manual, is
  MIT.
- **Reuse the existing providers.** `github_docs` copies whole files and is
  already used by `home-manager` and `microvm-nix`. The `nixpkgs` updater's
  manual format already converts NixOS manual markup: `{#id}` anchors,
  admonitions and roles. Any new capability goes through review, and keeps
  every fail-closed check.
- **The NixOS manual links to option anchors** such as
  `#opt-systemd.user.services`. The `nixpkgs` updater indexes anchors only
  under `doc/`, so these links fail closed today. The design must resolve
  them safely, for example to search.nixos.org or the pinned option
  declaration, not drop them silently.
- **No state changes without authorization.** Skill text must not tell an
  agent to rebuild, switch, roll back, collect garbage or change boot entries
  on its own initiative.
- **Keep packages loadable,** with excerpts rather than whole manuals.
- **Weekly automation cannot change selections.** Only reviewed edits can.

## Open questions

- **Split this task?** The darwin work only extends the reviewed Home Manager
  file list, plus possibly a small nix-darwin README source. NixOS operations
  needs a decision on option-anchor links and possibly a new skill. The
  recommendation is two tasks and two PRs: finish darwin under #27 first, and
  open a separate issue for NixOS operations.
- **Where nix-darwin lives:** inside `home-manager` as a darwin reference, or
  as its own `nix-darwin` skill? The recommendation is its own small skill,
  because nix-darwin is a system manager and not a Home Manager feature.
- **Where NixOS operations lives:** a new `nixos-operations` skill sourced
  from the NixOS manual (recommended), or new sections in `nixos-wiki`, which
  is wiki-sourced and a poor fit for manual text.
