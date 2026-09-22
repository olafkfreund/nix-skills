---
status: approved
issue: 14
author: olafkfreund
---

# Intent: Home Manager and microvm.nix skills

## Problem

The collection does not yet provide portable skills for Home Manager or
microvm.nix, even though both are central to declarative NixOS work. The
upstream projects publish useful documentation, but the collection currently
has no curated packages, provenance records, or maintained-source update
providers for them.

## Proposed outcome

The collection provides two independently selectable skills:

- `home-manager`, sourced from the Home Manager documentation tree.
- `microvm-nix`, sourced from the microvm.nix documentation tree.

Each skill contains focused instructions and curated references with pinned
upstream provenance, the applicable upstream license, and reproducible hashes.
The existing scheduled update workflow can regenerate each skill in isolation,
open a scoped PR when upstream changes, and fail closed when source structure,
links, licensing, or selected coverage require review.

## Affected users and systems

- NixOS and Home Manager users configuring declarative user environments.
- Users defining, deploying, networking, and troubleshooting microVMs.
- Collection maintainers and contributors reviewing source updates.
- The skills registry, package outputs, maintained-source providers, tests,
  scheduled update workflow, and collection documentation.

## Constraints

- Follow the collection's issue, branch, intent, spec, plan, approval, and PR
  workflow. This draft does not authorize implementation or self-approval.
- Add two separate skill packages; do not combine unrelated domains or install
  files directly into a user's agent directory.
- Preserve authored `SKILL.md` instructions while generating only approved
  reference, provenance, and license files from upstream sources.
- Pin full upstream commit revisions and record source/output hashes. Do not
  treat moving `master`/`main` URLs as reproducible input without resolution.
- Reuse the existing provider, artifact, CI, and scheduled-PR boundaries. Do
  not add updater permissions, privileged PR execution, or automatic installs.
- Keep curated references bounded and preserve source attribution and required
  redistribution notices. Unsupported documentation formats or license changes
  must fail for human review.
- Do not alter this machine's NixOS configuration, rebuild the host, or install
  collection skills as part of development.

## Open questions

- Which Home Manager topics and option references should the first curated
  snapshot cover?
- Which microvm.nix topics are essential for the first snapshot?
- Should both providers track their default development branches, or should
  Home Manager use a stable release/tag policy where upstream supports it?
- Does the existing provider architecture need a shared Markdown/source helper,
  or are two small provider modules safer and clearer?
