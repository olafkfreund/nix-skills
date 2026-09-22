---
name: nixpkgs-development
description: Write, explain, review, and debug Nixpkgs package expressions, build helpers, overrides, overlays, and library APIs against the project's pinned package set.
---

# Nixpkgs development

Read the repository instructions, existing package expressions, and actual Nixpkgs
input/lock before editing. Keep its package layout, overlays, and development
environment conventions. Distinguish the Nix evaluator version, Nixpkgs revision,
and build/host/target platforms. The bundled references describe the master
snapshot in [sources.json](sources.json); they are not a stable-release claim or
proof that an API exists in an older consumer pin.

Read only the relevant reference:

- [Packaging](references/packaging.md): stdenv, dependency roles, phases/hooks,
  metadata, and package tests.
- [Customization](references/customization.md): argument overrides, attribute
  overrides, overlays, and generic module composition.
- [Helpers](references/helpers.md): fetchers/hashes, small builders, mkShell,
  and entry points for Python, JavaScript, Go, and Rust packaging.
- [Library](references/library.md): selected generated API descriptions, types,
  arguments, and examples with pinned declarations.

Choose the mechanism that matches the change: `override` changes recipe arguments;
`overrideAttrs` changes mkDerivation inputs; overlays compose package sets;
module options merge configuration. In overlays, use the previous package for
its original recipe and the final set for dependencies; inspect self-reference
when diagnosing recursion. Inspect the target recipe before assuming every
language helper has the same override behavior.

Prefer an existing appropriate build helper. Preserve pre/post hooks when replacing
phases, keep native build tools distinct from host dependencies, and inspect
platform assumptions. A temporary fake hash is a discovery aid: finish with the
verified hash for the selected fetcher/source. Preserve upstream lockfiles and
update consumer inputs deliberately, not merely to match these references.
Do not disable checks, sandboxing, or hardening to hide an unexplained failure.

Start validation with the target package set and bounded checks for the change.
Report evaluation, actual builds, and runtime tests separately. Documentation
examples can use historical versions or illustrative values; inspect them before
adapting or running them. Do not execute arbitrary snippets merely to read docs.
Respect existing task authorization and keep secrets out of the Nix store.

This skill does not supply a complete package/API catalogue or NixOS/Home Manager
option reference. Host installation and deployment follow local policy. Public
manual links can move; packaged excerpts and source citations are revision-pinned.
Modified upstream material is covered by [COPYING](COPYING).
