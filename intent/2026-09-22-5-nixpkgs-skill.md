---
status: approved
issue: 5
author: olafkfreund
---

# Intent: Source-maintained Nixpkgs skill

## Problem

AI coding agents need reusable guidance for working with Nixpkgs package
expressions and APIs. The existing Nix language skill describes language
semantics, and the proposed devenv skill describes project environments; neither
provides focused guidance for Nixpkgs packaging, build helpers, dependency roles,
overrides, overlays, or library functions.

The requested `NixOS/nixpkgs/doc` directory combines narrative documentation,
navigation, renderer-specific markup, and references generated from sources
outside that directory. For example, `doc/lib.md` is only a heading, while the
library reference is generated from selected `lib/` documentation comments.
Copying only visible Markdown pages would omit important APIs and could leave
unresolved includes, anchors, or generated content. Nixpkgs is also actively
restructuring its manual, so updates need to detect source-layout changes.

Nixpkgs revisions, Nix evaluator versions, and consumer lockfiles are separate.
An agent must not apply guidance from the newest manual as proof that an API
exists in a project's pinned package set.

## Proposed outcome

The public `olafkfreund/nix-skills` repository includes a portable Nixpkgs skill
following the established package and maintenance pattern. Codex and other AI
agents can use it to create, explain, review, and troubleshoot package
expressions, standard-environment builds, fetchers, dependencies and hooks,
overrides/overlays, and a focused selection of library and generic module-system
APIs. Relevant packaging metadata, checks, and language-specific helpers are
discoverable without bundling the entire manual or package catalogue.

References retain examples, warnings, API distinctions, and source attribution,
with exact provenance for both narrative and generated material. Agents check
the consumer's actual Nixpkgs pin and target platform before applying
version-sensitive advice. Automatic source updates produce validated review
PRs, preserve authored instructions and curated selections, and support rollback
through repository commits. Existing sibling skills and updates continue to work.

## Affected users and systems

- Developers using AI agents to maintain Nixpkgs packages or consume/customize
  a Nixpkgs package set.
- This repository's skill packages, generation/check scripts, update workflows,
  and installation/maintenance documentation.
- Upstream Nixpkgs documentation and the source/generators needed to interpret
  selected references, accessed as read-only inputs.

## Constraints

- Use the requested `https://github.com/NixOS/nixpkgs/tree/master/doc` as the
  documentation foundation and record full upstream revisions for bundled content.
- Reuse the existing skill template and applicable maintenance code. Do not
  assume Nixpkgs shares Nix's release-tag policy or devenv's source formats.
- Keep scope focused on Nixpkgs APIs and packaging. Generic module-system
  guidance does not imply an exhaustive NixOS/Home Manager option catalogue or
  authorization to deploy a host configuration.
- Distinguish `override`, `overrideAttrs`, overlays, and module option merging;
  preserve dependency/platform distinctions and build-phase hook semantics.
- Follow selected generated references to their real source and generator.
  Do not mistake navigation stubs or the function catalogue for complete API docs,
  invent defaults, or claim generated material was rebuilt when it was not.
- Preserve relevant custom anchors, cross-references, includes, admonitions,
  literal roles, and executable examples when adapting material. Unsupported or
  ambiguous conversions must fail visibly, retaining previous validated output.
- Preserve upstream's applicable MIT copyright/permission notice and any
  additional notices for selected material. Keep each sibling's license distinct.
- Respect project pins, local repository conventions, and the user's chosen
  development environment. Do not introduce personal machine policies into the
  portable skill or refresh consumer lockfiles merely to fit the references.
- Automated updates must not silently rewrite instructions, reviewed selections,
  updater code, tests, workflows, or sibling packages. Publish reviewable changes;
  do not automatically merge or install them.
- Validate provenance, conversion, relevant library/package behavior, and update
  boundaries using isolated checks and bounded builds. Do not execute arbitrary
  upstream documentation examples or rebuild a user's system for validation.
- Do not modify host configuration, agent installations, or unrelated projects.
- Devenv PR #4 is open at task creation. This intent starts from `main` and does
  not merge that PR. Coordinate shared updater changes when its reviewed work is
  available, rather than duplicating it or folding it into this task implicitly.
- Obtain separate intent, spec, and plan approvals before implementation.

## Open questions

None required for intent review. The spec will propose a package name, initial
source revision and update stream, exact reference/API selection, handling of
generated documentation, bounded validation commands, and the smallest extension
to the shared updater. In particular, it must explicitly distinguish tracking
master, a tested unstable branch, or a maintained release branch rather than
silently treating a moving branch as a release.

## Review evidence

Initial source inspection used master commit
`7561e7e3e12a06677b1525a12bcccb0b4e4c601d`.

- `doc/README.md` documents the active restructuring and renderer extensions.
- `doc/nav.json` identifies actual chapter paths; `doc/stdenv.md` and
  `doc/lib.md` are heading stubs, not the full reference material.
- `doc/using/overrides.chapter.md` and `doc/using/overlays.chapter.md` explain
  distinct package-customization mechanisms and their constraints.
- `doc/build-helpers.md` distinguishes build helpers from primitive builders
  and notes that helper interfaces differ.
- `doc/module-system/module-system.chapter.md` documents generic module APIs
  and marks its coverage as incomplete.
- `doc/doc-support/package.nix` connects narrative docs to generated library,
  configuration-option, and other reference inputs through `nixos-render-docs`.
- `doc/function-catalog.json` and `doc/doc-support/lib-function-docs.nix`
  select and generate library documentation from comments in `lib/` via `nixdoc`.
- `COPYING` contains the upstream MIT notice for the software and documentation.

Local templates reviewed: the existing Nix skill and the devenv package/updater
extensions on `docs/3-devenv-skill`. Tracking issue:
[#5](https://github.com/olafkfreund/nix-skills/issues/5).
