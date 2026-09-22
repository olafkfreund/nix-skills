---
status: draft
issue: 9
intent: intent/2026-09-22-9-contributor-workflow.md
---

# Spec: Contributor workflow and declarative distribution

## Design

### Integration and contribution contract

Base implementation on the merged, checked wiki task (#8), including its final
package/helper and updater boundaries. Do not merge #8 or copy its unfinished
implementation without authorization. Complete independent documentation/design
work while that dependency is pending.

Add a root `skills.json` containing a sorted list of skill names. Names must match
`[a-z0-9]+(?:-[a-z0-9]+)*`, be at most 64 characters and map to `skills/<name>`.
Require unique names and exact agreement with packaged skill directories. Seed it
with the four reviewed skills after #8 integrates. This file registers collection
membership only: it cannot select commands, alter permissions, grant an upstream
updater or supply shell expressions.

A contributor adds a complete skill directory, registers its name and opens a PR.
GitHub Actions validates the proposal. After an explicitly reviewed merge, the
flake's collection automatically includes the newly registered skill. No daemon,
webhook service, auto-merge or automatic consumer installation is introduced.

Generic skills require valid SKILL.md metadata, matching names, useful description,
portable relative resource links, no symlinks/traversal and no unfinished template
placeholders. Validate supported Markdown resource references without interpreting
code examples as instructions or fetching arbitrary contributor URLs. Executable
helpers are allowed as reviewed source files, not executed by the metadata check.
Documentation must identify helper prerequisites, attribution and licensing for
redistributed material; generic skills are not forced to invent an upstream
manifest or updater. Behavioral tests belong in repository tests when meaningful;
review evidence covers guidance-only skills where automated assertions add little.

The existing source-maintained skills retain their stricter provider validation,
exact generated-file lists and immutable policies. A new source-maintained updater
is a separate reviewed code change to trusted provider/CI code, never enabled by
adding a registry entry. Preserve all existing sibling package bytes.

### Native PR validation

Use `.github/workflows/check.yml` and the existing Python tests. Add collection
validation covering every registered skill, including new generic submissions,
and registry/directory consistency. Keep the existing explicit per-provider
regeneration checks; do not turn arbitrary registry fields into a CI command or
privileged job matrix. A small `scripts/check_collection.py` entrypoint can reuse
metadata/link validation where contracts match without weakening provider checks.

Add an aggregate, stable required-check candidate (for example `collection-check`)
that reports failure if any required job fails or is cancelled. Do not report green
merely because dependent jobs were skipped. Include offline collection/unit/lint
checks and flake build/module checks; keep networked provider checks distinct so
failures remain understandable.

Use `pull_request` with read-only contents permissions, no secrets and checkout
credentials disabled. Never use pull_request_target to execute submitted code or
privileged follow-up runs consuming arbitrary PR artifacts. Fork PRs use GitHub's
normal approval model; do not bypass it. GitHub runner isolation is not a claim
that contributors' tests are trusted. Do not publish artifacts/releases, install
skills or change repository settings from PR validation.

Scheduled source update jobs remain an explicit maintained-provider allowlist.
They do not discover providers from untrusted registry content. Preserve their
read-only generation, narrowly scoped write publication, stale-base checks,
per-skill branches/artifacts/concurrency and manual Check dispatch for bot PRs.
Generic registration changes must not widen any automatic-write boundary.

Document branch protection/rulesets as a maintainer setup step: require the stable
aggregate check and review before merging, and protect trusted maintenance/workflow
code. Workflow YAML alone does not enforce merge policy. Do not change repository
settings or enable auto-merge as part of this implementation. A CODEOWNERS file
will identify `@olafkfreund` for workflows, updater/validator code, registry,
flake/modules/locks and root agent instructions; enforcement still depends on
repository settings.

### Human and agent contribution guidance

Add root `AGENTS.md` with concise repo-specific instructions: repository layout,
canonical local commands, skill registration versus maintained-provider changes,
source/provenance/license requirements, safe PR/update boundaries, and validation
expectations. Document issue/branch/Conventional Commit conventions and the
intent → spec → plan gates, including separate approval commits. Preserve the
existing small-change exemptions. Recurring generated-only updates follow their
already-approved provider design; this is not permission to change that design.

Add `CONTRIBUTING.md` explaining setup, the review workflow, a minimal SKILL.md
frontmatter example, complete package layout, resource/helper guidance, tests,
source-maintained provider requirements and a pre-PR checklist. Cover both human
and AI-assisted contributions without assuming Codex access. Favor instructions
and one small template over a new scaffolding framework.

Add a PR template requiring issue/artifact links, skill/registration scope,
validation evidence, source/license information and material limits. Add a skill
proposal issue template for intended users/use cases, source and licensing,
helper requirements and proposed validation. These collect information; they do
not grant execution or publication permission.

### Project environment

Add `devenv.nix`, `devenv.yaml` and committed `devenv.lock`, retaining independent
root `flake.lock` for consumer packaging. Pin their inputs deliberately and explain
which lock controls which use. Use ordinary devenv options, not Nixarchy-specific
helpers or machine policy. Include Python, Git, GitHub CLI, Zstandard and actionlint,
plus only formatting/testing tools actually used by documented checks. No service,
virtualenv, pip environment, database or global installation is needed.

Provide simple named commands/tasks for fast offline collection/unit/lint checks
and explicit full provider checks. Entering the environment must not download wiki
dumps, regenerate skill content, install skills, start services or change trust.
Validate the environment with the pinned Devenv CLI/module set. Update .gitignore
for project scratch/local override files while tracking both lockfiles. Do not run
devenv allow or create an automatic trust grant.

### Flake packaging and declarative installation

Add a small `flake.nix` and committed `flake.lock`, using explicit nixpkgs imports,
no bare URLs, ambient registry lookup, IFD or secret reads. Export for
`x86_64-linux` and `aarch64-linux`:

- `packages.<system>.<skill-name>`: copy the complete registered skill to
  `$out/share/nix-skills/<skill-name>`; no acquisition or regeneration at build time.
- `packages.<system>.nix-skills` and `packages.<system>.default`: a collection of
  those complete skill directories, preserving per-skill license files.
- `checks.<system>`: offline package-content, registry/metadata and installation
  module evaluation checks. Do not require networked upstream refreshes in builds.
- `homeManagerModules.default`: an opt-in installation module using the consumer's
  package set to build the data bundle, without forcing the host onto our nixpkgs pin.

The Home Manager module exposes `programs.nix-skills.enable`, a validated list of
registered skill names (default all when enabled), and a relative installation
`directory` defaulting to `.agents/skills`. Reject unknown/duplicate selections and
absolute/traversing targets. Use declarative `home.file` links to whole immutable
skill directories. Leave collision handling enabled; never force-overwrite an
existing user-managed directory. Disabled means no links or installation effects.
Do not install an agent executable or service.

Document importing the module through the user's existing Home Manager-as-NixOS
setup and enabling it in the selected user's Home Manager configuration. Apply
through the user's normal NixOS rebuild workflow; do not recommend home-manager
switch for module-managed users. NixOS users without Home Manager can add the data
package to systemPackages, but must explicitly configure their agent's discovery
links; putting data in the system profile alone does not establish discovery.
No additional NixOS adapter module is needed for those two routes.

Use the existing documented `.agents/skills` location as the default; verify that
reference while implementing examples. Other agents or older directory conventions
can set `directory`, with documentation that path support depends on their actual
agent. Do not claim native-agent discovery testing from package/module evaluation.
Consumers pin this flake and roll back through their input lock/system generation.
No consumer configuration is changed during repository development.

### Tests and documentation

Test collection registration errors, invalid names/paths, missing frontmatter and
resources, symlinks, duplicate/unknown selection, authored helper handling and
source-maintained boundary preservation. Exercise a temporary new generic skill
from registration through package contents and module links, without merging or
installing a real sample skill. Show that registering a generic skill does not add
an updater or alter publication permissions.

Build bundle and per-skill outputs on x86_64-linux; evaluate supported outputs for
aarch64-linux and state clearly if native builds were not performed. Evaluate
Home Manager module disabled/default/subset/invalid-selection behavior using a
pinned test input, and build a small test home configuration without activation.
Verify all linked resources and license files survive packaging. Test environment
commands and committed lock reproducibility. Run actionlint, unit/collection and
all existing provider checks on clean CI before merge.

Update README to point to CONTRIBUTING, declarative installation examples, flake
outputs, development commands, independent locks and rollback. State which checks
ran and which require external access. Do not conflate building skill data with
verifying every piece of advice a skill may contain.

## Alternatives rejected

- A hosted PR engine or bot with write credentials: GitHub Actions already provides
  event handling and checks; a new service adds operational and trust boundaries.
- Automatically installing/merging submitted skills: checks cannot grant trust or
  replace review of agent instructions and helper code.
- Registry-defined arbitrary CI commands/providers: expands privileges and makes
  the distribution catalogue a command-execution policy language.
- Hardcoded package lists in both CI and the flake: a small data-only registry makes
  collection membership consistent without creating a plugin framework.
- Imperative installers/global tool changes: incompatible with declarative consumer
  configuration and reproducible project tooling.
- One universal agent installer: discovery paths differ; default to the verified
  location and an explicit relative override, preserving local ownership.

## Risks

- PR code is untrusted even with successful checks. Keep credentials out of runs
  and distinguish workflow validation from enforced repository merge settings.
- Installation can conflict with managed files. Module evaluation must reject
  invalid paths/selections and preserve Home Manager's collision behavior.
- Registration and shared validation changes can affect sibling providers. Keep
  provider policies explicit, test boundaries and compare package bytes.
- Separate environment and consumer locks can confuse contributors. Document
  ownership/update commands and avoid silently refreshing both during a fix.

## Verification

Run bounded offline/unit/flake/environment checks, a temporary contribution
round-trip, malicious registration/path cases, provider-boundary regressions,
workflow lint and all integrated provider checks. Inspect PR permissions, aggregate
failure behavior, CODEOWNERS paths and exact package contents. Open an implementation
PR linking approved intent/spec/plan with `Closes #9`. No host rebuild, installation,
trust grant, auto-merge or repository-settings mutation is part of verification.
