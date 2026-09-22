---
status: draft
issue: 9
spec: spec/2026-09-22-9-contributor-workflow.md
---

# Plan: Contributor workflow and declarative distribution

## Approved decisions

Use native GitHub Actions for contribution checks, with reviewed merges adding
skills to the collection. No hosted engine, webhook daemon, auto-merge, privileged
PR execution, automatic consumer installation or repository-setting changes.
Integrate against the merged and tested wiki task #8; do not copy its unfinished
implementation or merge it without authorization. Independent documentation and
packaging work can proceed while that dependency is pending.

Add a data-only root `skills.json`: a sorted, unique list of names matching
`[a-z0-9]+(?:-[a-z0-9]+)*`, each at most 64 characters, mapped to `skills/<name>`.
Require exact agreement with skill directories. Initially register nix-language,
devenv-project, nixpkgs-development and nixos-wiki after #8 integrates. The registry
contains no commands, updater selection, secrets or permission settings.

A generic contribution consists of a complete skill directory plus registration.
Validate matching SKILL.md name/description, portable relative resource links,
package containment, no symlinks/traversal and no unfinished placeholders. Do not
interpret code examples as links/instructions or fetch arbitrary contributor URLs.
Allow reviewed executable helpers as source without executing them in metadata
validation. Require documentation of prerequisites and redistributed-source
attribution/licensing. Generic skills need not invent sources.json or an updater.
Use meaningful tests for behavioral helpers and reviewer evidence for prose-only
skills; metadata validation alone does not establish behavioral quality.

Existing maintained skills retain provider-specific regeneration, exact generated
allowlists and immutable policy checks. A new updater requires separately reviewed
trusted code/CI changes. Generic registration never expands scheduled publication
or write permissions. Keep explicit maintained-provider jobs and preserve all
existing package bytes while adding collection-level validation.

Add `scripts/check_collection.py` using existing metadata/link logic where its
contract matches, without weakening provider checks or creating a plugin framework.
Add a stable aggregate check such as `collection-check`, depending on all required
collection, unit/lint, package/module and provider jobs. Fail if any required job
fails, is cancelled or is unexpectedly skipped. Keep upstream-network checks
identifiable separately from offline failures.

Use read-only `pull_request` validation, no secrets and checkout credentials
disabled. Respect GitHub's normal fork-PR approval model. Never run submitted code
through pull_request_target, a write-enabled job or a privileged artifact consumer.
Do not publish/install from PR jobs. Keep existing scheduled read-only generation,
scoped write publication, stale-base validation, per-skill concurrency/artifacts/
branches and manual Check dispatch for bot PRs. Registry data does not control
those privileged boundaries.

Document required checks/review and protection of trusted maintenance files as
maintainer repository-setting steps. Workflows alone cannot enforce merge policy.
Add CODEOWNERS entries for `@olafkfreund` covering workflows, updater/validator code,
registry, flake/modules/locks and root AGENTS.md; do not change repository settings
or enable auto-merge. State that CODEOWNERS enforcement depends on settings.

Add concise root AGENTS.md and human CONTRIBUTING.md. Cover layout, canonical
commands, registration versus updater implementation, licensing/provenance, resource
and helper requirements, evidence/limits, issue-driven branches, Conventional
Commits and intent → spec → plan gates with separate approval commits. Preserve
small-change exemptions and explain that recurring generated-only maintenance
follows the already-approved provider contract, not permission to change it.
CONTRIBUTING includes a minimal SKILL.md example and review checklist; no scaffolding
framework. Add a PR template and skill-proposal issue template collecting scope,
issue/artifact links, source/license information, helper requirements and validation.

Add ordinary `devenv.nix`, `devenv.yaml`, tracked `devenv.lock`, and appropriate
scratch/local-override ignores. Include Python, Git, GitHub CLI, Zstandard,
actionlint and only further tools actually used by documented checks. No services,
virtualenv, pip setup, global installation or trust grant. Provide simple fast
collection/unit/lint and explicit full-provider commands. Entering the environment
does not acquire upstream content, regenerate snapshots, install skills or start
services. Validate against a pinned Devenv CLI/module set.

Add a small flake and committed flake.lock with explicit pinned imports, no IFD,
bare URLs, ambient registry lookups or secrets. Environment and distribution locks
have separate ownership; do not silently refresh both as a troubleshooting step.
Export for x86_64-linux and aarch64-linux:

- Per-skill packages containing the whole directory under
  `$out/share/nix-skills/<name>`.
- `packages.<system>.nix-skills` and default containing the full registered collection.
- Offline checks for registry/metadata, exact package contents and installation
  module evaluation; no source acquisition/regeneration during builds.
- `homeManagerModules.default`, opt-in, building data with the consumer's package
  set instead of forcing the host to use our nixpkgs pin.

The Home Manager module exposes `programs.nix-skills.enable`, a validated list of
registered skill names (default all when enabled), and relative `directory`
(default `.agents/skills`). Reject unknown/duplicate selections, absolute or
traversing destinations. Use `home.file` links to complete immutable skill folders,
with normal collision handling and no forced overwrite. Disabled emits no links
or installation effects. Do not install agents/services or change user trust.

Document the module inside the consumer's existing Home Manager-as-NixOS setup;
module-managed users apply through their NixOS workflow, not home-manager switch.
Without Home Manager, adding the data package to systemPackages is supported, but
agent discovery links remain explicit consumer configuration. No extra NixOS adapter
module. Verify the documented default agent path while writing examples; other
agents can use a relative directory override if supported by their actual discovery
mechanism. Do not claim native discovery tests from evaluating links. Consumers pin
flake inputs and can roll back locks/generations. No host configuration edits or
activation are part of repository development.

## Steps

1. **Inspect the integration baseline.** Check branch/worktree and available
   approved artifacts. Verify #8's merge state/checks; when separately authorized
   and merged, incorporate its reviewed base. Record sibling package hashes and
   existing provider interfaces/CI permissions. Read actual module/flake/devenv
   conventions and verify prerequisite tool availability before editing.
   Verify: known clean/understood state, explicit dependency status, passing
   existing unit/offline checks and recorded comparison base.

2. **Add the collection registry and validator.** Create skills.json with reviewed
   membership. Implement check_collection.py and minimal shared validation changes
   only where needed. Require exact directory/registry agreement and enforce name,
   metadata, resource, symlink and path constraints. Keep providers and privileged
   update allowlists explicit; no registry command fields or generic provider loader.
   Verify with disposable generic skills and negative name/path/resource cases;
   existing provider checks and automated-write boundary tests continue passing.

3. **Add data packaging and the installation module.** Write flake.nix, its small
   packaging/module files as needed and flake.lock. Derive package membership from
   the registry; copy complete skill contents, excluding repository-only data and
   build scratch. Expose per-skill and collection outputs for both Linux systems.
   Add the opt-in Home Manager module with selection/path validation and declarative
   full-directory links. Use pinned test Home Manager input for module checks;
   do not evaluate or edit the real user's configuration.
   Verify x86_64 builds, aarch64 evaluation, exact resources/licenses, disabled/
   default/subset/invalid module cases and a built test home without activation.

4. **Add project Devenv tooling.** Write root devenv.nix/devenv.yaml and generate
   the committed lock deliberately with the pinned CLI. Preserve test fixtures
   under tests/devenv as separate upstream tests. Add fast and full check commands
   and ignores for generated local state. Avoid activation hooks with side effects.
   Verify devenv info and actual shell/check commands in a disposable project copy;
   confirm entering it does not regenerate files, start services or alter trust.

5. **Write contributor and agent guidance.** Add AGENTS.md, CONTRIBUTING.md,
   CODEOWNERS, PR template and skill-proposal issue template. Document all approved
   gates and small-change exceptions; distinguish generic additions from provider
   code/policy changes. Include exact canonical commands, a minimal metadata example,
   license/source guidance and validation limits. Update README with flake/module
   installation, data-only systemPackages alternative, independent locks, development
   entrypoints and rollback. Verify default agent discovery location against its
   documented source and label untested alternatives accurately.
   Verify links/commands and walk through a new generic skill proposal end to end.

6. **Integrate PR checks without widening write authority.** Update Check workflow
   with collection and flake/module checks and a stable aggregate job. Preserve
   explicit maintained-provider checks and isolated failure reporting. Ensure the
   aggregate fails on required-job failure/cancellation/unexpected skipping. Keep
   fork-safe read-only permissions, no secrets and checkout credentials disabled.
   Inspect scheduled updater workflows to confirm registry additions cannot enroll
   providers or widen publication allowlists. Document required-check/review settings
   as manual maintainer configuration; do not mutate them.
   Verify actionlint, aggregate-condition fixtures/review and CI on the actual PR.

7. **Review, validate and open the implementation PR.** Run the checks below and
   inspect the final diff against this plan. Exercise a temporary generic skill
   through registration, validation, packaging and module links; remove the fixture
   afterward and confirm no new updater or publication job appears. Compare all
   four existing package trees against the recorded integration base. Report actual
   x86_64 builds separately from aarch64 evaluation and native discovery claims.
   Push the task branch and open a PR linking intent/spec/plan with `Closes #9`.
   Wait for clean-runner checks; merge only through the authorized process. Record
   necessary deviations in this plan in the same commit as implementation.

## Tests

Run from the repository root after implementation (task command names should
match these documented entrypoints):

```sh
python3 scripts/check_collection.py
python3 -m unittest discover -s tests -p 'test_*.py'
actionlint
nix flake check
nix build .#nix-skills --no-link
nix eval .#packages.aarch64-linux.nix-skills.drvPath --raw
devenv info
devenv shell check-fast
```

Run each maintained skill's `scripts/check.py --skill <name>` and
`scripts/update.py --skill <name> --check`, including offline wiki checks, once
shared changes are stable. Run environment validation in an isolated copy where
needed; never invoke devenv allow. Stage new Nix files before flake evaluation,
since Git-based flakes omit untracked files. Do not run host/home activation.

Tests cover sorted/unique registry names; invalid names, directory mismatch,
missing frontmatter/resources, placeholders, escaping links and symlinks; generic
helper handling; exact skill/resource/license packaging; unknown/duplicate module
selections; invalid target paths; disabled/default/subset links; fixture home build;
unchanged provider update permissions; aggregate failure/skipping semantics; and
a temporary generic contribution round-trip. Verify committed-lock reproducibility
without updating inputs implicitly. Inspect final Git status and whitespace.

Confirm existing package trees are byte-identical to the integration base:

```sh
git diff --exit-code <integration-base> -- skills/nix-language skills/devenv-project skills/nixpkgs-development skills/nixos-wiki
git diff --check
```

## Rollback

Before merge, revert implementation commits on this task branch while retaining
approval history and rerun existing checks. After merge, use a reviewed revert PR
for registry/tooling/distribution changes; preserve skill content and provider
maintenance. Consumers restore their previous flake lock or disable the opt-in
module through their own configuration workflow. No host activation, user trust,
repository settings or remote service needs restoration because none is changed
by this development task.
