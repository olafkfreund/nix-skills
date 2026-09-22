---
status: approved
issue: 3
author: olafkfreund
---

# Intent: Source-maintained devenv skill

## Problem

AI coding agents need reusable guidance for creating, editing, explaining, and troubleshooting devenv project environments.
The existing Nix language skill supplies language semantics but not devenv's configuration, inputs, lockfiles, lifecycle commands, or option APIs.
The requested upstream documentation at `docs/src/content/docs` mixes Markdown and MDX, contains version-specific notices and generated pages, and links to option data outside that folder.
Copying it without understanding those relationships could omit compatibility requirements or present stale or incomplete option information.

Upstream already provides a concise `devenv-setup` skill, but the user wants the same provenance, focused references, and source-update maintenance provided by this repository's Nix skill.
The installed local `devenv` skill contains machine-specific Nixarchy policies that must not become universal guidance in a portable package.

## Proposed outcome

The public `olafkfreund/nix-skills` repository includes a portable devenv skill alongside `nix-language`, following the established package and maintenance pattern.
Codex and other AI agents can use it to work with project configuration, inputs and lockfiles, packages and language support, local services and processes, tasks and tests, and environment activation.
Agents can locate focused, source-grounded references and distinguish the documented upstream version from the user's installed CLI and pinned project modules.
Examples retain their meaning, platform or shell labels, and version requirements when converted to agent-readable references.
Automatic source updates produce validated, reviewable changes with exact upstream provenance and rollback through repository commits.
The existing Nix language skill and its updater continue to work.

## Affected users and systems

- Developers using Codex or other AI agents with devenv projects.
- This repository's skills, reference generation, checks, update automation, and installation documentation.
- The upstream devenv documentation, generated option material, and existing skill as read-only reference sources.

## Constraints

- Use `https://github.com/cachix/devenv/tree/main/docs/src/content/docs` as the requested documentation foundation; record exact source revisions for bundled material.
- Follow the established Nix skill template and reuse applicable maintenance code without assuming devenv uses Nix's documentation syntax, release publishing, or option generation.
- Inspect upstream's existing `devenv-setup` skill before duplicating guidance.
- Keep references focused; do not bundle the entire documentation site, blog archive, or exhaustive option catalogue by default.
- Preserve relevant version notices, MDX tab labels, code examples, source relationships, and applicable Apache-2.0 licence/attribution notices.
- Account for generated options and configuration references; do not invent option names or mistake documentation prose for executable configuration.
- Keep the skill portable and distinguish project configuration from host installation and machine-specific Nixarchy policy.
- Distinguish native devenv activation from direnv integration, preserve lockfile reproducibility, and respect project trust and command side effects.
- Automatically refreshed references must not silently rewrite reviewed behavioural instructions or curated selections.
- Validate source conversion, provenance, representative configuration behaviour, and update boundaries; retain previous validated output on update failure.
- Do not change agent installations, trust databases, host configuration, or unrelated projects as part of creating this skill.
- Follow separate intent, spec, and plan approvals before implementation.

## Open questions

None required for intent review. The spec will propose the package name, release tracking policy, reference selection, treatment of MDX/generated data, validation commands, and the smallest necessary extension to the current updater.

## Review evidence

Initial inspection used upstream main commit `1c57b5dea0d400af97053fdd1a536fca17378f73`.
GitHub reports `v2.3.1` as the latest non-prerelease release; the requested documentation folder exists at that tag.
Relevant upstream paths include:

- `docs/src/content/docs/`: narrative Markdown/MDX, language/service pages, and YAML configuration reference.
- `docs/src/data/options.json` and `docs/src/pages/reference/options.astro`: the full option data and its web presentation.
- `docs/gen/devenv.nix` and `docs/gen/scripts/`: generation of options and individual documentation pages.
- `docs/src/individual-docs/`: source templates for generated language and service pages.
- `docs/public/.well-known/agent-skills/devenv-setup/SKILL.md`: existing upstream setup skill.
- `LICENSE`: upstream Apache-2.0 licence text.

Local template reviewed: `skills/nix-language/`, `scripts/update.py`, `scripts/check.py`, and the existing source-update workflow.
Tracking issue: [#3](https://github.com/olafkfreund/nix-skills/issues/3).
