---
status: draft
issue: 1
author: olafkfreund
---

# Intent: Reusable Nix language skill

## Problem

AI coding agents need consistent, source-grounded guidance when writing, explaining, and reviewing Nix expressions.
The upstream manual contains the authoritative language reference, but its source is not a ready-to-use agent skill: built-in documentation is generated, links require preprocessing, and available features vary with the Nix version.
Manual copying risks stale guidance and mixing language semantics with Nixpkgs APIs or NixOS module conventions.

## Proposed outcome

The public `olafkfreund/nix-skills` repository provides a reusable Nix language skill that Codex and other AI agents can consume.
Agents can locate relevant guidance without loading the entire manual and trace it to an identified upstream revision.
Coverage includes syntax, scope, evaluation and laziness, functions, attribute sets, strings and paths, derivations, and built-ins.
Version-specific, experimental, and pure-evaluation restrictions remain visible.
An automatic update process detects upstream changes, refreshes maintained reference material, validates the result, and presents changes for review.
Users can install a known version and update or roll back deliberately.

## Affected users and systems

- Developers using Codex or other AI coding agents for Nix language tasks.
- This repository's skill files, supporting references, validation, and update automation.
- Upstream Nix documentation and documentation generators as read-only source material.

## Constraints

- Use `doc/manual/source` from the upstream Nix repository as the documentation foundation.
- Preserve source provenance and applicable licence and attribution information for reused material.
- Keep documentation and generated built-in information aligned to the same upstream revision.
- Keep the reusable guidance independent of one user's machine, absolute checkout paths, and agent-specific tools.
- Distinguish Nix language semantics from Nixpkgs APIs and NixOS or Home Manager conventions.
- Use focused references and existing upstream generation capabilities where practical; avoid duplicating the whole manual or adding unnecessary infrastructure.
- Validate generated references and representative language examples before accepting updates.
- Automatically proposed updates must not silently replace reviewed behavioural instructions or deploy machine configuration.
- Follow separate intent, spec, and plan approvals before implementation; this document does not approve a design.

## Open questions

- None required to review the problem framing. Release tracking policy, packaging, agent discovery, and CI design will be proposed in the spec.

## Review evidence

Initial source inspection used upstream commit `ba515bd92ddc4e5ef4118d6e591b77bcc5af39aa` (checkout version file: `2.36.0`).
Relevant paths: `doc/manual/source/language/`, `doc/manual/source/language/meson.build`, `doc/manual/generate-builtins.nix`, `doc/manual/substitute.py`, and `src/nix/main.cc` (`__dump-language`).
Tracking issue: [#1](https://github.com/olafkfreund/nix-skills/issues/1).
