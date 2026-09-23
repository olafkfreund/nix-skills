# Contributing

Contribute through an issue and pull request. GitHub Actions validates the PR;
a reviewed merge adds the skill to the collection and its Nix packages.
Consumers choose when to update their pinned revision. PR checks do not install,
publish or automatically merge contributions.

## Propose and approve the work

Open a skill proposal (or a normal issue for a fix), then create a branch such as
`feat/123-example-skill`. Use Conventional Commits and `Closes #123` in the PR.
Follow [AGENTS.md](AGENTS.md) for the artifact gates:

1. Commit `intent/YYYY-MM-DD-123-example-skill.md` as draft: problem, observable
   outcome, affected users, constraints, open questions. Stop for approval.
2. Record approval alone (`docs(intent): approve ... (#123)`). Commit a draft
   `spec/` with design, alternatives, risks and verification; link the intent.
   Stop for approval.
3. Record spec approval alone. Commit a draft `plan/` with all approved
   decisions, ordered steps/checkpoints, tests and rollback; link the spec.
   Stop for approval, then record approval alone before implementation.

Every artifact has `status: draft` or `status: approved` and `issue: 123`
frontmatter. Humans approve; contributors and agents never self-approve.
Keep all three files. Implementation deviations update the plan in the same
commit as code. Typos, lock-only bumps and one-line configuration changes are
exempt. Routine generated-source PRs use the existing approved provider contract;
this exception does not authorize new policies, generators or privileges.

## Add a skill

Create `skills/<name>/SKILL.md` and insert its name into the sorted `skills.json`
list. Names are lowercase letters/digits separated by single hyphens, at most
64 characters. `default` and `nix-skills` are reserved collection output names.
The directory and frontmatter name must match. Frontmatter contains exactly the
two fields shown below; put other descriptive information in the body or linked
resources. Use a nonempty, single-line
plain-text description starting with a letter that says when the skill should
trigger. Avoid YAML quoting, block scalars, `: ` and ` #` in this field; this
repository deliberately uses a small metadata convention without a YAML runtime.

```markdown
---
name: example-skill
description: Explain and review example configurations when a user asks about their syntax or behavior.
---

# Example configurations

Read the project's version and existing configuration before editing.
Use the bundled [reference](references/configuration.md) for supported syntax.
Validate changes with the project's documented command and report its result.
```

Replace the example with useful, finished instructions and provide every linked
resource. Relative links must stay inside the skill package. Do not include
symlinks, scratch files, credentials or unresolved template placeholders.
The checker rejects unfinished TODO/FIXME/TBD markers in entrypoint prose;
copied reference material can retain upstream comments. Review referenced prose
for completeness too. Use simple inline Markdown resource links or explicit
reference definitions; code fences are examples and are not checked as links.
Authored code examples must not quote attribute names that are valid Nix identifiers
(`pkgs.foo-bar`, not `pkgs."foo-bar"`) or search or hard-code `/nix/store`;
`check_collection.py` enforces this outside generated references, and a deliberate
counterexample needs `<!-- nix-style: counterexample -->` on the line before its fence.
Keep the entrypoint short and put detailed material in linked references.

The documentation site lives in `docs/src/`; list every page in `docs/src/SUMMARY.md`.
`nix build .#docs` (also a flake check) generates the skill catalog, module options and
update schedule from repository data and fails on broken links, missing anchors or Nix
style findings. Never edit the generated reference pages by hand.

Document source URLs, exact versions/revisions, modifications, attribution and
redistribution rights for copied material; include required license files.
Do not imply the repository grants rights to third-party sources. Authored-only
skills need no invented `sources.json`. Reviewers assess licensing and usefulness;
the metadata validator cannot establish either.

Prefer instructions over helpers. If a helper is needed, document its runtime,
dependencies, arguments, network use and side effects in SKILL.md. Include a
meaningful runnable behavioral test under `tests/`. Metadata checks inspect
helper source as package data without running it. Exercise trigger and non-trigger
prompts; describe the agent/version tested. For prose-only skills, supply reviewer
examples and limitations rather than tests that merely repeat the prose.

## Develop and validate

Use an installed Devenv CLI with the committed root environment:

```sh
devenv info
devenv shell check-fast
nix flake check
nix build .#nix-skills --no-link
nix eval .#packages.aarch64-linux.nix-skills.drvPath --raw
devenv shell check-providers
```

The equivalent fast checks are:

```sh
python3 scripts/check_collection.py
python3 -m unittest discover -s tests -p 'test_*.py'
actionlint
```

Provider checks use `python3 scripts/check.py --skill <name>` and
`python3 scripts/update.py --skill <name> --check` for each of nix-language,
devenv-project, nixpkgs-development and nixos-wiki. The first three regeneration
checks use upstream network/cache access; the wiki check uses retained local
data. Keep their failures distinct from offline metadata/build failures.

Git flakes omit untracked files: stage new files before Nix evaluation. Builds
fetch locked dependencies when absent, but package builders never acquire or
regenerate upstream references. Module checks build a disposable test home;
they never activate it. An aarch64 evaluation is not an aarch64 build or a native
agent-discovery test. Do not grant project trust or change your host to run tests.

`devenv.lock` pins contributor tools/modules. `flake.lock` pins distribution and
module-test inputs. Review each lock update separately; do not delete either to
work around a failure. `tests/devenv/devenv.lock` belongs to upstream skill tests.
Entering the project shell does not regenerate sources, install skills or start
services. Personal environment overrides belong in ignored `devenv.local.nix`.

## Maintained sources and automation

Generic registration requires no updater implementation. Existing maintained
skills additionally pass explicit source/hash/reproduction checks. A new source
updater is a separate design review touching trusted generator, validator,
artifact allowlist and workflow code. Registration cannot select commands or
expand scheduled publication. Keep authored instructions out of generated PRs.

PR validation uses read-only GitHub Actions with checkout credentials disabled.
Fork contributions use GitHub's normal approval model. Never run submitted code
in a write-enabled job or privileged artifact consumer. Scheduled publication
retains its existing trusted validation, stale-base rejection and per-provider
branches/artifacts. Bot PRs may require a manual Check dispatch as documented in
[README.md](README.md#automatic-updates).

Maintainers should configure branch protection/rulesets to require
`collection-check`, current PR checks, review and code-owner review, and prevent
direct changes to main. CODEOWNERS only routes/enforces review when repository
settings enable it. These files do not change those settings. The aggregate check
fails on failed, cancelled or skipped required jobs; network checks remain visible
as individual provider jobs. Do not bypass a failure because the aggregate exists.

## Review checklist

- Scope and trigger are useful; existing skills are not unnecessarily duplicated.
- Issue and approved artifacts match the final diff; PR closes the issue.
- Complete resources, provenance, redistribution rights and helper prerequisites
  are present; existing maintained packages have no incidental edits.
- Fast checks, package/module checks and relevant provider checks pass.
- Behavioral/manual evidence states versions, actual results and untested limits.
- No new updater permissions, automatic installation or unreviewed merge behavior.
