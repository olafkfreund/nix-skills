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
