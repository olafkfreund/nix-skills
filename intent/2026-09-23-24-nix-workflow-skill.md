---
status: approved
issue: 24
author: olafkfreund
---

# Intent: Authored skill for everyday Nix practice

## Problem

The collection teaches agents the Nix language, Nixpkgs packaging, devenv, Home
Manager, microvm.nix and selected wiki pages, all quoted from upstream. A user
who will rely on the collection reported that agents still do harmful or
wasteful things that no skill addresses, because these are habits and
ecosystem knowledge rather than reference material:

- Agents search the store by brute force, for example
  `find /nix/store/*something-* -iname libsomething.so`. This is slow, depends
  on whatever happens to be in the local store, and ignores the dependency
  graph. Tools such as nix-index (`nix-locate`) and Nix's own store queries
  answer the question directly.
- Agents do not understand `devShells`: when to use `nix develop` rather than
  `nix shell` or `nix run`, or how a project's shell differs from host
  packages.
- When packaging or builds fail, agents invent workarounds instead of
  searching Nixpkgs issues and pull requests, where the same failure has often
  already been diagnosed.
- Agents reach for Python for simple text or JSON processing that `jq` or
  `awk` handles in one line.
- The ecosystem is hard to navigate:
  - helper tools such as nh, nix-output-monitor and nix-eval-jobs;
  - flakes, flake alternatives such as npins and niv, and flake frameworks;
  - many fast-changing lang2nix tools;
  - configuration that differs between the Nix client, the daemon and remote
    builders.

People also arrive in different roles, and the right entry point differs:
developers (mostly devShells), Home Manager users (often on darwin), and NixOS
administrators (mostly rebuilding the system). No skill routes an agent to the
right place by role.

## Proposed outcome

A new authored skill in the collection. An agent doing general Nix
command-line work, debugging or ecosystem choices would:

- locate files, libraries and packages with the proper tools, and never by
  scanning `/nix/store`;
- choose correctly between a project devShell, an ad-hoc shell and a one-off
  run, and explain the difference;
- search Nixpkgs issues and PRs before proposing a workaround for a packaging
  or build failure, and cite what it found;
- prefer existing command-line tools (`jq`, `awk`, `nix` subcommands) over
  new Python scripts for simple processing;
- identify whether a setting belongs to the client, the daemon or a remote
  builder, and who is allowed to change it;
- recognise the common helper tools and flake approaches, and check a tool's
  current upstream status before recommending it, instead of relying on
  memory;
- send developers, Home Manager users and NixOS administrators to the
  collection skill that fits their task.

The reviewer who gave the feedback can read the skill and confirm it addresses
the reported behaviours.

## Affected users and systems

- Agents and users who install the collection, through the flake and Home
  Manager module for all supported agents.
- `skills/` and `skills.json` (registration). The Home Manager module and
  package pick up registered skills automatically.
- No existing skill's content changes, and no maintained provider or updater
  is added or changed.

## Constraints

- Authored guidance only. No copied upstream material, so no `sources.json`
  and no updater, as CONTRIBUTING.md allows for authored skills.
- Must pass `scripts/check_collection.py`: frontmatter convention, links inside
  the package, no unfinished markers.
- Keep `SKILL.md` short, with detail in linked references, per CONTRIBUTING.md.
- No executable helpers. Prefer instructions.
- Do not duplicate the language, Nixpkgs, devenv, Home Manager or microvm
  skills; link to them instead.
- Do not present fast-moving ecosystem facts (tool status, lang2nix
  maintenance) as permanent truth. Tell the agent how to check them.
- Guidance must respect local policy and authorization. It must not tell
  agents to rebuild systems, change trust settings or install software on
  their own initiative.
- Validation for a prose-only skill is reviewer examples, not tests that
  repeat the prose (CONTRIBUTING.md).

## Open questions

- **Skill name.** Proposed: `nix-workflow`. Alternatives: `nix-practices`,
  `nix-ecosystem`.
- **Persona routing.** Should it live in this skill, as proposed, or in a
  separate small `nix-start` entry skill?
- **External review.** Should the reviewer who gave the feedback be asked to
  review the draft skill before merge, as proposed?
