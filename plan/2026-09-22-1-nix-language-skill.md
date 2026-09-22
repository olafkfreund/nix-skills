---
status: draft
issue: 1
spec: spec/2026-09-22-1-nix-language-skill.md
---

# Plan: Reusable Nix language skill

## Approved decisions

Deliver one portable skill at `skills/nix-language/` for writing, explaining, debugging, and reviewing Nix expressions.
Use standard `name` and `description` frontmatter, relative package links, and normal automatic skill selection.
Keep the entrypoint concise and route to focused references rather than loading the full manual.
Separate language semantics from Nixpkgs `lib` and NixOS modules; include no personal deployment policies or system rebuilds.
Establish the user's Nix version and evaluation mode, inspect affected code and callers, make the smallest correct change, and verify observable behaviour.
Distinguish syntax, evaluation, and build checks; report inspection-only validation when Nix cannot run.
Respect task permissions when evaluation could read files, fetch inputs, or build derivations.

Use a stable upstream Nix release, selected during implementation, pinned by tag and full commit SHA.
Do not use the previously inspected development checkout as the default release pin.
Build or obtain the executable through that revision's upstream build definition and generate built-in documentation with its `__dump-language` output and upstream `doc/manual/generate-builtins.nix` plus helper dependencies.
Never substitute the host's Nix executable for generation or semantic checks.

Select source sections covering syntax, values, operators, lexical scope, functions and defaults, evaluation and laziness, strings and string context, paths, and derivations.
Include the pitfalls of `with` scope precedence, shallow set updates, `@` bindings not receiving parameter defaults, and lazy values not being fully evaluated.
Keep generated excerpts separate from authored instructions; do not copy the entire manual or every built-in.
Retain argument descriptions and experimental/pure-evaluation restrictions.
Include the separately authored derivation documentation.
Resolve documentation links and includes using upstream conventions, preferring existing preprocessing when needed; do not create a general Markdown parser.
Reject unsupported directives, missing selections, unresolved placeholders, and ambiguous links.
Link unbundled material to the selected release's published manual and source provenance to the exact revision.

The package contains `SKILL.md`, `references/language.md`, `references/builtins.md`, `sources.json`, and `COPYING` with applicable upstream notices.
Do not claim a new permissive licence over copied upstream content.
The manifest records repository URL, tag, SHA, reported version, selected paths/sections/built-ins, input hashes, and generated reference hashes.
Exclude timestamps and machine paths from generated output.
Keep scripts and tests outside the installed package.
Do not add a plugin, MCP server, model API, vector index, or agent-specific runtime dependency.
Document installation and updates in the existing root README, including commit-pinned copying/linking of the complete skill folder, per-agent discovery differences, and explicit reading for agents without native discovery.
This task does not install anything into the user's agent directories or alter NixOS configuration.

Updates use Python's standard library and the existing Nix build tooling.
Support an explicit release tag and a read-only regeneration check against the existing pin.
Generate into temporary output, validate before replacement, and preserve the previous package on failure.
Run weekly and by manual dispatch, discovering the newest non-draft, non-prerelease upstream release.
Skip unchanged revisions; reject a moved existing tag and visibly fail discovery, resolution, or generation errors.
Maintain one automatic update branch and at most one open PR with concurrency control, old/new revisions, and a summary of selected and other language-source changes.
Only generated references, provenance, and necessary upstream notices may change automatically; selections, instructions, scripts, tests, and workflows remain reviewed edits.
Never automatically merge or install updates.

CI uses a Linux runner with Nix, Git, Python 3, and required network access.
Pin external Actions to full commit SHAs.
Normal PR validation is read-only and receives no write credentials.
Use repository-scoped workflow-token permissions for update publication where allowed, validate before pushing, and document a maintainer-triggered check path when token-created PRs do not trigger required checks.
Do not add a personal token if repository policy prevents PR creation; report the prerequisite.

## Steps

1. **Confirm the release and upstream interfaces.** Inspect repository status and applicable instructions. Query upstream releases, resolve a stable tag to a SHA, and inspect that revision's language sources, generator, build outputs, preprocessing, and licence notices in a temporary checkout. Obtain the matching executable through its upstream build definition and record how it was selected. Verify its reported version and language dump, and confirm published manual targets exist. Stop on version, licence, or interface ambiguity rather than guessing. This step may use build caches; it must not alter the existing upstream checkout.

2. **Implement deterministic generation in `scripts/update.py`.** Provide `--release TAG`, `--check`, and `--latest` modes, with `--check` fixed to the committed manifest pin. Keep the curated selection in `sources.json`, editable only through reviewed changes. Assemble the two focused references, reuse upstream built-in rendering, resolve links/includes, and emit exact provenance and hashes. Stage and validate the complete result before replacement, with restoration if replacement fails. Make identical inputs produce identical bytes. Verify missing source sections, unsupported syntax, moved tags, and failed generation cannot replace existing output. Do not execute untrusted repository scripts with publication credentials.

3. **Add `scripts/check.py` and focused tests.** Check required metadata, package-relative links and linked headings, source provenance and hashes, unresolved directives, and generated-file allowlists. Check external manual targets during generation, failing visibly when unavailable. Add `tests/test_update.py` using `unittest` for reproducibility, missing inputs, unresolved links, preservation on failure, and protection of curated selections. Add `tests/language.nix` with assertions for scope precedence, shallow updates, argument defaults and `@` bindings, laziness, and interpolation; its successful result is `true`. Verify tests exercise actual output and failures rather than mirroring implementation text.

4. **Author and generate the skill.** Create `skills/nix-language/SKILL.md` with the approved scope, workflow, version awareness, validation limits, and reference routing. Generate `references/language.md`, `references/builtins.md`, `sources.json`, and `COPYING` from the selected pin. Resolve applicable attribution/licence notices before copying source material. Run structural checks, semantic assertions with the matching executable, and the available skill-creator validator. Regenerate twice and confirm no changes. Inspect reference size and relevance so the result remains a focused skill, not a manual mirror.

5. **Add `.github/workflows/check.yml` and `.github/workflows/update.yml`.** Run structural and Python checks on PRs and pushes, plus reproducibility and semantic checks using the recorded source pin. The weekly/manual updater checks stable releases, generates and validates without write credentials, and uses a separate publication phase with narrowly scoped permissions to update the fixed branch and PR. Publication must accept only validated allowed-file changes and reject changes to curated selection fields even though those share a manifest with generated metadata. Include diffs of selected and unselected language sources in the update report. Support a manual validation dispatch for a specified revision without write credentials. Verify unchanged updates are no-ops, changed updates do not create duplicate PRs, and failures do not publish partial results. Do not enable auto-merge or introduce a personal token.

6. **Document usage in `README.md`.** Explain supported scope, version provenance, package installation by commit, the distinction between portable content and per-agent discovery, how to read the skill explicitly, and exact maintenance commands. Explain Nix build/network prerequisites, workflow permissions, update-review policy, failure handling, and the manual check path for token-created PRs. Explain how to update and revert a consumer's pinned commit. Check current official documentation before naming agent discovery paths and report only installations actually tested.

7. **Validate behaviour and open the implementation PR.** Run the tests below and manually exercise writing, explanation, and review prompts using the skill. Check reference routing, built-ins versus `lib`, version restrictions, and honest reporting when execution is unavailable. Record outcomes and any untested agents or workflow limitations. Verify only intended files changed, commit on the task branch, and open a PR with `Closes #1` linking the intent, spec, and plan. Cite the plan step during implementation; any necessary deviation updates this plan in the same commit as its code. Do not merge untested changes.

## Tests

These commands are the planned interface, to be implemented before they are run.
Run from the repository root, sequentially, investigating failures before proceeding.

```bash
python3 scripts/check.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/update.py --check
python3 scripts/update.py --check
git diff --check
```

Expected results: checks exit zero, unit tests pass, repeated regeneration matches committed generated files byte-for-byte, and no whitespace errors occur.
`--check` must obtain the executable from the manifest's exact upstream pin, run `tests/language.nix` using that executable, validate external reference targets, and leave the worktree untouched.
The underlying semantic check is equivalent to the following command, with `PINNED_NIX` explicitly set to the executable obtained from the recorded revision:

```bash
"$PINNED_NIX" --extra-experimental-features nix-command eval --json --file tests/language.nix
```

Expected result: `true`; expressions require no network fetches or derivation builds.
The initial acquisition of the pinned executable and external link checks may need network access.
Also run the available skill-creator `quick_validate.py` against `skills/nix-language`; keep this local supplementary check out of CI dependencies.

Before publishing automation, exercise an unchanged release, a changed-release candidate in a temporary worktree, and a simulated generation failure.
Verify the update report identifies old/new revisions and other language changes, only allowed generated data changes, no duplicate update PR is created, and failure preserves the previous package.
If live publication cannot be exercised before the workflow reaches the default branch, record that limitation in the PR and validate the first manual run after merge; do not claim it has already passed.

Manual behavioural prompts:

- Explain lexical scope versus `with`, citing the relevant packaged reference.
- Review a shallow nested-set update and an `@` argument binding with defaults; identify the semantic errors and propose minimal fixes.
- Write a small Nix-only expression and evaluate it with the matching executable; distinguish available built-ins from Nixpkgs `lib` functions.
- Handle a requested version-sensitive feature on a different Nix version and an environment without execution; describe the compatibility check and validation limits accurately.

Record actual observations; do not claim testing on other agents merely because the file format is portable.

## Rollback

- Before merge, abandon or revise the task branch without changing `main` or the upstream Nix checkout.
- After merge, revert the relevant implementation commits through a reviewed PR and run the remaining applicable checks.
- If update automation misbehaves, disable its workflow and close the automated PR; retain the last reviewed skill package.
- Revert a bad reference update as a unit: references, manifest, and notices must continue to describe the same source revision.
- Consumers restore their previous repository commit and reinstall/copy that complete skill directory.
- No system rebuild, credential rotation, or machine configuration rollback should be needed because this task does not deploy machine changes or add credentials.
