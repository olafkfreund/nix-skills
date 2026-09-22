---
status: draft
issue: 9
author: olafkfreund
---

# Intent: Contributor workflow and declarative distribution

## Problem

The repository now maintains several reusable skills, but contributors have no
root AGENTS.md, contribution guide or reproducible project development environment.
Its workflows enumerate existing skill identities, so proposing a new skill does
not yet have a documented registration, validation and publication path. Consumers
must manually copy/link skill folders rather than consume declarative flake outputs.

The user requested Devenv tooling, a flake for NixOS installation, contributor
instructions and an engine that checks PRs and incorporates approved skills.
The repository already has GitHub Actions checks, reviewed update PRs and strict
generated-file boundaries. Extend those capabilities instead of creating a second
hosted service or granting a PR authority to publish its own contents.

## Proposed outcome

A contributor can obtain pinned development tools, follow clear repository and
agent instructions, propose a skill or maintenance change on a branch, and receive
useful PR validation results. A reviewed merge adds the skill to the distributable
collection through an explicit, tested registration mechanism.

Repository AGENTS.md explains layout, commands, skill quality/provenance/licensing
requirements, the contributor workflow and update boundaries. Human contribution
guidance covers the same workflow without assuming a particular AI assistant.
PR/issue guidance makes the expected evidence and review process discoverable.

A flake exposes reproducible skill bundles and a documented declarative integration
for NixOS users, including Home Manager used as a NixOS module. Installation keeps
whole skill packages together and supports selecting skills and rolling back pins.
A Devenv environment supplies project tools and checks without changing the host.

## Affected users and systems

- External contributors, maintainers and agents developing new skills.
- NixOS/Home Manager consumers installing selected skills declaratively.
- Repository tooling, flake/environment files and locks, contributor documentation,
  skill registration, CI workflows and package checks.
- Existing skills and their reviewed automatic-update contracts.

## Constraints

- Follow the user's intent → spec → plan gates. This intent does not authorize
  implementation or approval of its own later design stages.
- Keep approved wiki work (#8) progressing separately; coordinate integration
  against its final interfaces rather than copying unfinished code implicitly.
- Prefer native GitHub pull_request workflows and existing helpers over a hosted
  engine. No new daemon, credentials service or unsolicited dependency framework.
- PR validation runs with minimal permissions on isolated runners. Never execute
  untrusted PR code through pull_request_target or a privileged publication job;
  do not expose write tokens/secrets to submitted code. Fork PRs must be supported
  within GitHub's normal approval and permission model.
- Validate skill structure, declared resources, licensing/provenance, relevant
  behavior and registration. Generic submissions need not implement an upstream
  updater; reviewed source-maintained providers must preserve stronger guarantees.
- Incorporation means reviewed merge into the collection, not automatic trust,
  auto-merge, deployment or installation of arbitrary submissions.
- Preserve existing per-skill update allowlists, immutable policy, independent
  schedules/artifacts and sibling isolation. New registrations must not silently
  broaden privileged publication permissions.
- AGENTS.md must be concise, repo-specific and actionable, accurately documenting
  the workflow rather than pretending local tools can bypass review gates.
- Use a project-local devenv.nix/devenv.yaml and committed lock; no global package
  installation, devenv allow or automatic trust changes.
- Use a flake with committed locks and explicit, tested outputs. Feature-gate
  installation modules; no bare URLs, IFD, secret evaluation or unrequested services.
  Do not run home-manager switch; module-managed users apply changes through their
  NixOS configuration workflow after separate host authorization.
- Do not edit this machine's flake, rebuild, overwrite user-managed agent files,
  modify repository access/branch-protection settings or install skills during
  development. Any repository-setting changes proposed later must be explicit.
- Preserve complete resource trees, distinct licenses and skill identities in
  distributable outputs. Detect invalid selections and installation-path conflicts.
- Include bounded evaluation/build tests, flake/environment validation and CI.
  Do not claim discovery support for agents whose actual lookup paths were not
  verified; document supported locations and manual alternatives.

## Open questions

None needed for intent review. The spec will choose the smallest registration
format and PR check matrix; exact flake/module outputs and installation targets;
Devenv inputs/tools; AGENTS.md and human contribution guidance; and the evidence
required for new skills versus changes to trusted maintenance code. It will also
state which required-check/review protections are workflow-level and which would
need explicit repository-setting configuration.

## Review evidence

At base `48d754c67a522f8ab0bc056bfbdf187eb93b7fce`, there is no root AGENTS.md,
CONTRIBUTING guide, flake or Devenv environment. `tests/devenv/` is an isolated
upstream-skill test fixture, not a project-wide environment.

`.github/workflows/check.yml` already validates three named skills on PRs/pushes
with read-only permissions. `.github/workflows/update.yml` separates generation
from scoped artifact publication. `scripts/check.py`, `scripts/artifact.py` and
`scripts/update.py` contain trusted per-skill identity and policy boundaries.
GitHub reports repository auto-merge disabled; this task does not enable it.

Tracking issue: [#9](https://github.com/olafkfreund/nix-skills/issues/9).
