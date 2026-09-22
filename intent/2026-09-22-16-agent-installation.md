---
status: approved
issue: 16
author: olafkfreund
---

# Intent: Declarative installation for multiple coding agents

## Problem

The collection can currently be installed through the Home Manager module into
one skill directory. Users who run Claude, Codex, OpenCode, and Antigravity
need a single declarative installation path that places the same maintained
skills where each agent discovers them. Requiring separate manual links or
duplicated package content is easy to get out of sync.

## Proposed outcome

The flake and its Home Manager module provide one documented interface that
installs selected or all registered skills for one agent or all supported
agents. The installed directories contain the complete portable skill bundles,
including references, source metadata, and licenses, and existing files retain
Home Manager's collision protection.

## Affected users and systems

- NixOS users who import the existing Home Manager module.
- Users of Claude, Codex, OpenCode, and Antigravity.
- The flake package and Home Manager module exported by this repository.
- Collection documentation and module tests.

## Constraints

- Keep `skills/<name>/` as the canonical package format; do not duplicate skill
  content for each agent.
- Keep installation declarative through the flake/Home Manager path.
- Do not silently overwrite user-managed agent files.
- Do not install, activate, or modify an agent during repository checks.
- Do not add a universal plugin abstraction unless a supported agent requires
  capabilities that plain skill bundles cannot provide.
- Preserve the repository's existing issue, artifact, validation, and NixOS
  Home Manager workflow.

## Open questions

- Should the default be a shared `.agents/skills` destination, explicit native
  destinations, or both with an `all` selector?
- Which global and project-level destinations should be supported for each
  agent, and should project-level installation be included in this change?
