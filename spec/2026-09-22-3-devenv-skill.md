---
status: approved
issue: 3
intent: intent/2026-09-22-3-devenv-skill.md
---

# Spec: Source-maintained devenv skill

## Design

### Package and scope

Add `skills/devenv-project/` beside `skills/nix-language/` in this repository.
Use `name: devenv-project` to distinguish the portable package from the owner's installed machine-specific `devenv` skill and upstream's `devenv-setup` skill.
Use ordinary skill frontmatter and relative links, with automatic selection permitted.
No plugin, MCP server, model API, or agent-specific runtime is required.

The package contains:

```text
skills/devenv-project/
  SKILL.md
  references/
    configuration.md
    workflows.md
    options.md
  sources.json
  LICENSE
```

Keep `SKILL.md` short and route to only the relevant reference sections.
Support creating, explaining, editing, reviewing, and debugging project environments: packages/languages, configuration and inputs, imports and profiles, lockfiles, scripts/tasks/tests, services/processes, and activation.
Use upstream `docs/public/.well-known/agent-skills/devenv-setup/SKILL.md` as a reviewed source for practical setup guidance, not as an automatically replaced instruction file.
Retain attribution for adapted upstream material.

Read the project's existing configuration and lockfile before editing.
Distinguish the installed devenv CLI, the project's pinned devenv modules, and its nixpkgs input; a release-pinned reference does not establish that all three match the user's project.
Check `require_version` where present and verify version-sensitive options against the actual target.
Preserve local overrides and existing project conventions.
Use project commands for project dependencies; host installation follows the user's platform and repository policies.
Do not copy Nixarchy commands, system rebuild rules, or personal paths into this portable skill.

Treat `devenv update` as an intentional input change, and preserve/commit the resulting lockfile when appropriate.
Do not delete a lockfile to disguise an evaluation failure.
Distinguish `devenv hook` from direnv integration, and explain their different activation and trust mechanisms.
Do not silently grant directory trust, edit shell startup files, start services, or run unknown hooks merely to inspect a project.
Respect already granted task authorization; do not require repeated consent for actions that are already authorized.
Explain that evaluation, shell activation, task execution, and `devenv test` have different side effects, including process startup when configured.
Keep secrets out of committed configuration and references.

### Source pin and update policy

Begin with release `v2.3.1`, resolved to commit `2418e1b43797c44de5166176622c8d8fa0149871` during review.
Verify the tag and release metadata again before implementation; a moved tag must fail rather than silently changing the agreed source.
Use the latest non-draft, non-prerelease GitHub Release for subsequent automatic updates, resolving its tag to a full commit SHA.
Unlike Nix, devenv publishes GitHub Release objects; do not reuse Nix's numeric-tag-only discovery assumption.
Support an explicit release selection and regeneration from the existing manifest pin.
Do not automatically track unreleased `main` documentation.

Record upstream URL, release tag, full revision, reported version, curated paths/headings/option names, consumed input hashes, generated output hashes, and source hashes used to report coverage changes.
Use deterministic ordering and omit timestamps, machine paths, and credentials.
Missing or ambiguous inputs, renamed selected files, moved tags, and unavailable required sources must fail without replacing the previous package.
Changes such as `.md` to `.mdx` renames require a reviewed selection update; do not silently select a similarly named page.

### Focused references

Use `docs/src/content/docs` as the main source, with exact paths from the pinned release.
At `v2.3.1`, several pages are `.md` although their current-main counterparts are `.mdx`.
The selection must therefore record actual release paths rather than filenames inferred from `main`.

| Reference | Initial source topics |
| --- | --- |
| `configuration.md` | `basics.md`, `files-and-variables.md`, `inputs.md`, `pinning.md`, `packages.md`, `composing-using-imports.md`, `profiles.md`, and selected `reference/yaml-options.md` sections |
| `workflows.md` | `auto-activation.mdx`, `integrations/direnv.mdx`, `scripts.md`, `tasks.md`, `processes.md`, `tests.md`, and focused git-hook guidance |
| `options.md` | Selected records from `docs/src/data/options.json`, with relevant language/service examples from the pinned generated documentation |

Select useful sections rather than entire long pages, blog history, or all options.
Include compact examples for common Python, JavaScript, Rust, and Go configuration and a local service, but do not promise exhaustive language/service coverage.
Option selection should support those examples and the core workflow: environment variables, packages, shell/test hooks, script/task/process execution, and selected language/service enablement.
Choose exact keys after inspecting the release data; validate every selected key rather than inventing option names or defaults.
Add a contents list to substantial reference files and link each excerpt to its source at the full revision.

### Markdown and MDX conversion

Convert only the limited forms present in selected upstream material, using Python's standard library and targeted fixtures.
Do not execute imported JavaScript, Astro components, or arbitrary MDX expressions to obtain documentation.
No full website build or general-purpose MDX parser is required.

- Remove document frontmatter while retaining its title as reference context.
- Convert known `Tabs`/`TabItem` wrappers to ordinary headings that retain every selected shell/platform label and its associated content.
- Convert known version notices to explicit prose. Handle the release's `:::tip[New in version …]` and `<small class="added-in">` forms, plus tested `VersionCompatibility` forms when selected sources use them.
- Preserve admonition meaning and nesting; warnings must remain visibly warnings.
- When extracting a subsection, retain compatibility notices that apply from the enclosing page or section.
- Preserve executable code text, including Nix interpolation, shell syntax, and indentation that affects examples. Remove common MDX wrapper indentation only where necessary to produce the same fenced example; retain file-title metadata as readable labels.
- Convert documentation-relative and site-root links to bundled targets where appropriate or `https://devenv.sh/` pages. Source citations always point to the recorded commit.
- Treat the public site as a moving supplementary reference, not proof of the pinned release's behaviour. Validate links used by the package and disclose this distinction.
- Reject unknown components, unresolved imports/expressions/directives, malformed wrappers, missing sections, and ambiguous link transformations. Preserve previous validated output for review instead of dropping content.

Keep conversion rules separate from authored instructions and recorded curated selections.
Content snippets may contain commands with side effects; copying documentation never authorizes executing those examples.

### Generated options and attribution

Read the committed `docs/src/data/options.json` at the same source revision as the narrative docs.
Render selected option names, descriptions, types, defaults, examples, and declaration references as documentation, preserving literal Nix expressions rather than evaluating them as prose.
The committed artifact is the source of the packaged option reference; do not claim it was freshly rebuilt.
Record its hash and relevant upstream generator/template provenance, including `docs/gen/devenv.nix` and selected `docs/src/individual-docs` templates.
Treat committed generated language/service pages and the generated YAML reference consistently with that provenance.

For declaration links into `cachix/devenv`, use the recorded source revision after verifying the target path exists there.
Do not rewrite declarations from external inputs as if they belonged to devenv; retain their distinct origin and describe any moving-link limitation.
Runtime validation of representative options provides a separate check against the actual pinned modules; if data and evaluation disagree, fail and investigate.
Rebuilding the entire upstream documentation catalogue is out of scope unless a demonstrated inconsistency makes it necessary and the plan is revised accordingly.

Ship upstream's Apache-2.0 `LICENSE` in the new package, preserve applicable notices, and mark adapted/generated excerpts as modified from upstream.
Keep devenv's licensing distinct from the Nix package's existing `COPYING`.
Do not overwrite the owner's installed skill or require the Nix language package to be installed for basic devenv use.

### Extend the existing maintenance code

Extend `scripts/update.py` and `scripts/check.py` with an explicit `--skill` choice between `nix-language` and `devenv-project`.
Omitting the flag must preserve the current Nix behaviour and command interface.
Keep the existing Nix package's generated bytes unchanged as part of this change.

Put devenv-specific release discovery, selection, MDX conversion, and generation in a focused helper module such as `scripts/devenv.py`.
Reuse proven hashing, deterministic JSON, subprocess, link-checking, staging/restoration, and boundary-checking logic where semantics match.
Extract small common helpers only where both implementations actually need them; do not create a plugin framework or duplicate the entire Nix updater.
Keep skill identities, allowed files, upstream origins, and publication branches explicit and trusted, not supplied by downloaded metadata.

Stage all generated outputs and validate the complete package before replacement.
Restore original bytes on ordinary replacement failures; document that multi-file replacement is not a power-loss transaction.
Automatic updates may change only the selected skill's references, provenance, and necessary upstream notices.
They must not change either skill's instructions, curated selections, scripts, tests, or workflows, nor touch the sibling skill.

Extend the existing CI and weekly/manual update workflow to cover both skills using the same validated generation and separate publication model.
Use distinct artifacts, update branches, PRs, and concurrency boundaries per skill, including `automation/devenv-reference-update` for devenv.
Keep the existing Nix update branch and schedule working.
Detect unchanged upstream sources as a no-op; maintain at most one open update PR per skill.
Reports identify old/new versions and revisions, changed selected inputs/options, and other documentation changes relevant to coverage review.
Changes to upstream's setup skill are review signals, not permission to overwrite `SKILL.md`.

Normal validation has read-only permissions. Only the publication phase receives narrowly scoped write permission and uses trusted scripts to validate the artifact allowlist and immutable selection fields.
Reject an artifact generated against a different current base, symlinks/path traversal, and cross-skill mutations.
Pin external Actions to full commit SHAs and reuse the repository's existing workflow-token permission; do not add secrets or personal tokens.
Preserve manual check dispatch for token-created PRs, no automatic merge, and no automatic installation.

Update the existing root README to list both skills, explain per-skill commands and provenance, and document commit-pinned installation and rollback.
Call out the name distinction from the local `devenv` and upstream `devenv-setup` skills without claiming their behaviour is interchangeable.

## Alternatives rejected

- Mirror all upstream docs or all 1,882 option records observed at `v2.3.1`: unnecessary context and maintenance cost.
- Use the upstream setup skill unchanged: useful guidance, but it lacks this repository's requested versioned reference and update controls.
- Copy the owner's installed skill: includes Nixarchy-specific policy and commands unsuitable for a portable package.
- Strip MDX tags generically: loses tab labels, scope of compatibility notices, and warning semantics.
- Scrape the live website as the source of truth: cannot guarantee correspondence to a release commit.
- Rebuild the whole Astro site and options catalogue on each update: the pinned repository already includes the necessary generated documentation/data.
- Reuse Nix's parser, release discovery, or package assumptions without adaptation: upstream formats and generated inputs differ.
- Build a general registry/plugin abstraction: there are two known skill packages with explicit requirements.

## Risks

- Source layout and MDX components can change between releases; conversion must fail visibly until reviewed rules/selections are updated.
- Committed generated data may lag implementation; compare representative options through the pinned evaluator and report inconsistencies.
- devenv's CLI and project modules can differ independently; skill guidance must account for both and the project's lockfile.
- Fetching/building a matching CLI and pinned test inputs may cost time/storage; use existing substitutes where available without silently falling back to another version.
- Public site links can move independently of release sources; exact provenance is carried by commit links and content hashes.
- Shared script changes could break Nix regeneration or widen update permissions; regression and cross-skill boundary checks are required.
- Evaluation and tests may activate hooks or processes; use an isolated controlled fixture and do not evaluate the user's working projects as a test harness.

## Verification

- Run existing Nix structural/unit checks and byte-for-byte regeneration before and after shared-code changes; the original generated package must remain identical.
- Validate both skill entrypoints, relative links/anchors, provenance and content hashes, notices, and package file allowlists. Run the available skill-creator validator as a supplementary local check, without making a personal installation a CI dependency.
- Add focused conversion tests for labelled tabs, each supported version/admonition form, inherited notices, source frontmatter, code preservation, and unknown/malformed MDX rejection.
- Test missing options/sections, deterministic option rendering, moved tags, staging failures, restoration after a partial replacement, and rejection of selection or sibling-package changes.
- Regenerate the devenv package twice from its recorded pin with no diff; validate selected public documentation links and pinned source/declaration targets.
- Obtain the matching devenv CLI through the pinned upstream build definition; pin the fixture's devenv modules to that same source and its other inputs to recorded revisions. Do not rely on the host CLI or moving default module inputs.
- In a disposable test project, evaluate representative configuration attributes and run a small controlled shell/task/test check using that CLI. Use harmless environment variables, a simple script/task, and `enterTest`; evaluate language/service options without launching real services. Verify expected values and command output, not merely Nix syntax. Track the fixture and reproducible input pins with the tests; never run `devenv allow` or alter user trust for testing.
- Exercise unchanged and changed-release updates in a temporary checkout and verify the per-skill diff boundary and report. Run `actionlint` and clean-runner CI for both skills before presenting the implementation PR.
- Walk through realistic setup, lockfile-update, activation-troubleshooting, and version-mismatch requests with the completed skill; record actual results and distinguish inspection from executed validation. Do not claim native discovery or behaviour was tested in agents that were not run.
- Validate the first live scheduled/manual update after merge; if no newer source exists, identify a successful no-op separately from an exercised publication path.
