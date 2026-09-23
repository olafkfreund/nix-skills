# Hand-written and generated references

Each skill has two kinds of content.

## Hand-written

Every `SKILL.md` is written and reviewed by hand: when to use the skill,
rules, routing, and the [Nix style rules](../reference/nix-style.md). Two
skills are hand-written throughout, `nix-workflow` and `nixos-coding-agents`;
they link to upstream documentation instead of copying it, because their
sources change too often to copy.

Hand-written text changes only through reviewed pull requests, and automated
updates never replace it.

## Generated from upstream

The other skills also carry `references/` generated from upstream sources:
the Nix manual, the NixOS manual, Nixpkgs documentation, the Home Manager
and nix-darwin repositories, microvm.nix, devenv, and a retained NixOS Wiki
dump.

Each such skill has a `sources.json` that records:

- the upstream repository or dump, and the branch, release or snapshot;
- the exact revision or snapshot hash the text was generated from;
- which upstream files were selected, with their hashes;
- the hash of every generated output file.

`scripts/check.py` recomputes these hashes offline, so any hand edit to a
generated file, or any mismatch with its recorded source, fails the check.
The [skill catalog](../reference/catalog.md) shows each skill's upstream and
pin.

## Licences

Generated text is a copy of upstream material and keeps its upstream
licence, which ships with the skill as `LICENSE` or `COPYING`: for example
LGPL-2.1 for the Nix manual, MIT for Nixpkgs, NixOS and Home Manager text,
and Apache-2.0 for devenv. The repository does not relicense copied
material. Hand-written skills are covered by the repository licence.

## Per-skill sources and licences

Each package records its upstream snapshot identity, curated selection, and
input/output hashes in its own `sources.json`. References cover selected topics,
not every upstream feature. Agents must check the project's actual versions.
The Nix skill does not supply NixOS options or replace Nixpkgs API documentation.
The portable `devenv-project` skill is distinct from a machine-specific `devenv`
policy skill and upstream's `devenv-setup`; their behavior is not interchangeable.
Each skill can be installed independently.


Home Manager references originate in [nix-community/home-manager](https://github.com/nix-community/home-manager)
and retain its accompanying [LICENSE](https://github.com/olafkfreund/nix-skills/blob/main/skills/home-manager/LICENSE). microvm.nix
references originate in [microvm-nix/microvm.nix](https://github.com/microvm-nix/microvm.nix)
and retain its accompanying [LICENSE](https://github.com/olafkfreund/nix-skills/blob/main/skills/microvm-nix/LICENSE). nix-darwin
references originate in [nix-darwin/nix-darwin](https://github.com/nix-darwin/nix-darwin)
and retain its accompanying [LICENSE](https://github.com/olafkfreund/nix-skills/blob/main/skills/nix-darwin/LICENSE). These packages
record the selected branch revision, source-file hashes, and generated-output
hashes in `sources.json`; the repository does not relicense copied upstream
material.

Design history: [intent](https://github.com/olafkfreund/nix-skills/blob/main/intent/2026-09-22-14-home-manager-microvm.md),
[spec](https://github.com/olafkfreund/nix-skills/blob/main/spec/2026-09-22-14-home-manager-microvm.md),
[implementation plan](https://github.com/olafkfreund/nix-skills/blob/main/plan/2026-09-22-14-home-manager-microvm.md).

The copied references originate in [Nix](https://github.com/NixOS/nix), whose upstream README identifies LGPL v2.1; the upstream licence accompanies the skill as [COPYING](https://github.com/olafkfreund/nix-skills/blob/main/skills/nix-language/COPYING).
Generated references identify the Nix contributors and link to original files at the recorded revision.
The repository does not relicense that material under MIT or another permissive licence.
The manifest tracks source files, generator helpers, the full language dump, and generated hashes for reproduction.

Design history: [intent](https://github.com/olafkfreund/nix-skills/blob/main/intent/2026-09-22-1-nix-language-skill.md), [spec](https://github.com/olafkfreund/nix-skills/blob/main/spec/2026-09-22-1-nix-language-skill.md), [implementation plan](https://github.com/olafkfreund/nix-skills/blob/main/plan/2026-09-22-1-nix-language-skill.md).

Devenv references originate in [cachix/devenv](https://github.com/cachix/devenv),
under its accompanying [Apache-2.0 LICENSE](https://github.com/olafkfreund/nix-skills/blob/main/skills/devenv-project/LICENSE).
The manifest hashes selected narrative pages, committed generated data,
generators/templates, the upstream setup skill, and the documentation coverage.
Modified excerpts retain source attribution. The repository does not relicense
Nix material under devenv's license.

Devenv design history: [intent](https://github.com/olafkfreund/nix-skills/blob/main/intent/2026-09-22-3-devenv-skill.md),
[spec](https://github.com/olafkfreund/nix-skills/blob/main/spec/2026-09-22-3-devenv-skill.md),
[implementation plan](https://github.com/olafkfreund/nix-skills/blob/main/plan/2026-09-22-3-devenv-skill.md).

Nixpkgs references originate in [NixOS/nixpkgs](https://github.com/NixOS/nixpkgs),
under its accompanying [MIT COPYING](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixpkgs-development/COPYING).
The license of the nixdoc generator does not replace the upstream source license.
Nixpkgs design history: [intent](https://github.com/olafkfreund/nix-skills/blob/main/intent/2026-09-22-5-nixpkgs-skill.md),
[spec](https://github.com/olafkfreund/nix-skills/blob/main/spec/2026-09-22-5-nixpkgs-skill.md),
[implementation plan](https://github.com/olafkfreund/nix-skills/blob/main/plan/2026-09-22-5-nixpkgs-skill.md).

Wiki text is from the [official NixOS Wiki](https://wiki.nixos.org/), under the
retained [MIT COPYING](https://github.com/olafkfreund/nix-skills/blob/main/skills/nixos-wiki/COPYING) from copyright-policy revision
22887. Media can have other terms and is excluded. Wiki design history:
[intent](https://github.com/olafkfreund/nix-skills/blob/main/intent/2026-09-22-8-nixos-wiki-skill.md),
[spec](https://github.com/olafkfreund/nix-skills/blob/main/spec/2026-09-22-8-nixos-wiki-skill.md),
[plan](https://github.com/olafkfreund/nix-skills/blob/main/plan/2026-09-22-8-nixos-wiki-skill.md).
