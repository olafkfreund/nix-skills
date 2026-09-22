---
status: approved
issue: 5
intent: intent/2026-09-22-5-nixpkgs-skill.md
---

# Spec: Source-maintained Nixpkgs skill

## Design

### Package and scope

Add `skills/nixpkgs-development/` with ordinary skill frontmatter and automatic
selection enabled. Keep it portable across agents, independent of installations
of the sibling skills, and free of machine-specific policy or required services.

```text
skills/nixpkgs-development/
  SKILL.md
  references/
    packaging.md
    customization.md
    helpers.md
    library.md
  sources.json
  COPYING
```

Keep `SKILL.md` concise: inspect the repository and its actual Nixpkgs pin, route
to relevant references, select the appropriate packaging/customization mechanism,
and validate the requested change. Support writing, explaining, reviewing, and
debugging package expressions and Nixpkgs APIs. Do not present the package as a
complete NixOS/Home Manager option reference or a substitute for host policy.

Distinguish the evaluator version, Nixpkgs source revision, and build/host/target
platforms. Preserve project lockfiles, overlays, package-set conventions, and the
chosen development-environment tooling. Explain `override` versus `overrideAttrs`
versus overlays and module merging; use the mechanism that matches the change.
Account for dependency roles, setup hooks, `runHook`, checks, hashes, and metadata.
Do not disable checks, sandboxing, or hardening simply to suppress an unexplained
failure. A temporary fake hash is only a discovery aid; the finished recipe must
contain a verified hash appropriate to its fetcher. Respect existing authorization
and report evaluation separately from actual builds and runtime tests.

### Source pin and update stream

Track the requested upstream **master** branch through weekly, full-SHA snapshots.
Start from reviewed commit `7561e7e3e12a06677b1525a12bcccb0b4e4c601d`.
Its `.version` is `26.11`; that is development-series metadata, not a claim that
this snapshot is a stable release or has passed channel promotion tests.
The skill must verify APIs against the consumer's pin, which may be older or on
a maintained release branch. Do not silently switch to `nixpkgs-unstable`, a
NixOS channel, a release tag, or whatever `<nixpkgs>` resolves to locally.

Provide `--skill nixpkgs-development --latest` to resolve master once to an exact
SHA, `--revision <full-sha>` for an explicit source pin, and `--check` to reproduce
the manifest pin. Keep existing Nix/devenv command semantics unchanged; reject
revision/release flags when they do not apply to the selected skill.
Verify the fetched source identity. Automatic advancement must be a descendant
of the recorded commit; a rewind, divergence, missing source, or unavailable
ancestry check fails for review. Explicit repinning is a reviewed operation.

If the branch still resolves to the recorded SHA, latest is a no-op. If the SHA
advances, regenerate and validate even if selected prose is unchanged: source
and package semantics can change independently. Reports must clearly identify
provenance-only changes rather than implying every update adds new guidance.

Record upstream, branch, full revision, source version, curated paths/anchors/API
names, consumed source and generated-data hashes, packaged output hashes, and
coverage hashes. Sort deterministically; omit timestamps, temporary paths, and
credentials. Branch/selection/toolchain policies are immutable to automatic PRs.

### Focused reference selection

Record exact selections in the manifest, normally using upstream explicit anchor
IDs plus expected headings. Missing, duplicated, or renamed selections fail;
never guess a replacement section from a similar name. Large chapters are read
as sources but only useful sections are bundled, with contents lists and pinned
source citations. Implementation must validate the actual anchor/API inventory.

| Reference | Initial selection |
| --- | --- |
| `packaging.md` | `doc/stdenv/stdenv.chapter.md`: using stdenv, dependency overview, fixed-point arguments, phase control, check/install phases, `runHook`, and selected substitution/setup-hook guidance. `doc/stdenv/meta.chapter.md`: description, license, maintainers, main program, and platforms. `doc/stdenv/passthru.chapter.md`: package tests. |
| `customization.md` | `doc/using/overrides.chapter.md`: `override`, `overrideAttrs`, and the limitations of `overrideDerivation`. `doc/using/overlays.chapter.md`: defining overlays and explicit application. `doc/module-system/module-system.chapter.md`: generic module-system introduction and focused `lib.evalModules` arguments/results, retaining the chapter's incompleteness notice. |
| `helpers.md` | `doc/build-helpers.md`; selected caveats/hash guidance and `fetchurl`, `fetchzip`, `fetchFromGitHub` sections from `doc/build-helpers/fetchers.chapter.md`; selected `runCommand`, `writeText`, `writeShellApplication` sections from `doc/build-helpers/trivial-build-helpers.chapter.md`; `doc/build-helpers/special/mkshell.section.md`. Include short entry sections for Python package/application builders, JavaScript `buildNpmPackage`, Go `buildGoModule`, and Rust `buildRustPackage` from their `doc/languages-frameworks/` pages. |
| `library.md` | Generated descriptions, arguments, types, and examples for `lib.attrsets.attrByPath`, `mapAttrs`, `mapAttrsToList`, `optionalAttrs`, `recursiveUpdate`; `lib.lists.optionals`, `unique`; `lib.strings.escapeShellArg`, `concatMapStringsSep`; `lib.customisation.callPackageWith`; `lib.fixedPoints.composeExtensions`; and `lib.fileset.toSource`. Use fully qualified identities from the actual generator output, with aliases recorded explicitly if necessary. |

Do not include whole language-framework chapters, all library APIs, or generated
configuration-option catalogues. Keep inherited caveats when extracting a narrow
subsection. Link to further upstream material for advanced/cross-compilation
topics rather than promising exhaustive coverage. Selecting an introductory
section must not implicitly pull all its child sections into the package.

### Generated library material and toolchain

Build upstream's `nixpkgs-manual.lib-docs` derivation from the same pinned Nixpkgs
source. `doc/doc-support/lib-function-docs.nix` uses the pinned package set's
`nixdoc` with `doc/function-catalog.json` and `lib/` to produce
`lib-functions.json`. Inspect and validate that actual schema, then select the
reviewed APIs; do not write a regex parser for Nix documentation comments or use
an unrelated host-installed nixdoc. Missing/ambiguous API identities or changed
output schemas fail for review.

Record the generated JSON hash, relevant `lib/` source hashes, catalogue and
generator hashes, and the pinned nixdoc package definition. The generated text
describes source comments, not evaluated types/defaults; report separate semantic
checks as such. Verify declaration paths against the pinned checkout and cite
them at its SHA. Do not misattribute dependency/tool licenses to the generated
Nixpkgs prose: retain applicable notices for the content actually distributed.

Use an explicit, independently recorded Nix evaluator pin for generation and
semantic checks. Initially reuse Nix 2.35.2 at
`2c73b59da29606068c0c98db015dd3a66955525d` through the existing pinned-tool helper.
Keep this tool pin fixed during Nixpkgs-only automatic updates; do not infer the
evaluator version from `.version` or silently follow the sibling manifest.
The host Nix may bootstrap the pinned tool. Source imports use the exact checkout,
explicit system/config/overlays, and no ambient registry or `NIX_PATH` selection.
Build required generators as separate derivations rather than adding new
import-from-derivation expressions. A full manual/site build is not required.

### Documentation conversion and links

Implement only forms needed by the selected material, using standard-library
Python and existing helpers where their semantics match. Treat
`doc/README.md`, `doc/nav.json`, `doc/manpage-urls.json`, and upstream renderer
sources as format evidence; do not assume the Nix or devenv converter applies.

- Preserve heading and inline anchor identities in portable Markdown, with
  unique local targets and an explicit mapping back to upstream sections.
- Resolve empty-label links from actual section titles. Resolve cross-chapter
  references against a source-derived anchor index, including generated library
  records; reject duplicate or unresolved identities.
- Prefer bundled targets when present. Otherwise use a verified upstream manual
  target or a pinned source-file citation with the section identified in prose;
  do not invent GitHub fragments for custom manual anchors. Public unstable
  manual links are supplementary and moving, never evidence of the snapshot.
- Retain admonition labels, nesting, example titles, inherited warnings, and
  compatibility context. Convert literal roles to readable inline literals;
  resolve manpage roles using the pinned mapping when selected.
- Preserve fenced Nix/shell examples, interpolation, and meaningful indentation.
  Documentation include fences are distinct from executable examples: resolve
  only supported, selected includes inside the pinned checkout, track their
  hashes, and reject cycles, traversal, ambiguous scope, or unknown directives.
- Support definition lists used by selected API records without dropping their
  argument names/descriptions. Unsupported placeholders, generated inserts,
  links, roles, or syntax must fail before replacing existing output.

The converter does not execute documentation snippets. Scope any generated
substitutions actually needed by selected excerpts; do not rebuild unrelated
tables or silently remove unresolved content from a broad selection.

### Shared maintenance and publication

Extend the reviewed multi-skill plumbing introduced by devenv PR #4 after it is
available on the integration base. Do not merge #4 without authorization, copy
its commits into this task implicitly, or implement a competing updater. If it
is still open when implementation reaches shared tooling, finish independent
work and report that concrete integration dependency.

Add focused Nixpkgs logic in `scripts/nixpkgs.py`; extend the existing update,
check, and artifact tools with the explicit third skill identity. Reuse hashing,
JSON, process execution, package staging/restoration, links, and artifact checks
where applicable. Keep explicit trusted upstreams, branches, selections, and
file allowlists; no generic plugin framework is needed.

Automatic changes may affect only this skill's four references, `sources.json`,
and `COPYING`. A new required upstream notice requires reviewed package/allowlist
changes. Stage and validate the complete candidate before replacement and
restore old bytes on ordinary partial failures; do not claim power-loss atomicity.
Keep both sibling packages byte-identical and their command interfaces intact.

Extend the weekly Monday 06:17 UTC and manual update workflow with a separate
Nixpkgs artifact, concurrency boundary, and `automation/nixpkgs-reference-update`
branch. Maintain at most one update PR for this skill. Reports show old/new SHAs,
source versions, selected-source/API changes, generator changes, and other
documentation/library coverage changes that may warrant selection review.
Coverage hashing must exclude unrelated binary/package payloads.

Use read-only generation and a separate narrowly scoped write job. Recheck the
current base, package hashes, immutable source/selection/toolchain policy, and
exact artifact allowlist; reject symlinks, traversal, cross-skill changes, stale
bases, or disallowed files. Retain full-SHA Action pins and existing token
permissions, with no new personal credentials, automatic merge, or installation.
Preserve manual check dispatch for token-created PRs and independent sibling jobs.
Update README with the third skill, snapshot semantics, commands, attribution,
commit-pinned installation/rollback, and generation/build costs.

## Alternatives rejected

- Mirror `doc/` wholesale: too much context and incomplete generated references.
- Treat master as a stable release: its development-series version does not
  imply stability, channel promotion, or compatibility with consumer pins.
- Track a stable/unstable channel silently: differs from the requested master
  source; any later change of stream requires review.
- Scrape the live manual or copy function names from the catalogue as API docs:
  neither reproduces the selected source comments at the recorded revision.
- Parse Nix comments with a new custom extractor: upstream already provides the
  catalogue, pinned nixdoc, and a dedicated library-doc derivation.
- Build the entire manual or evaluate every package: unnecessary for the curated
  scope and costly for routine updates.
- Merge or duplicate the pending devenv work just to obtain shared tools: bypasses
  its separate review and introduces avoidable maintenance divergence.

## Risks

Master may contain temporary build failures, changing APIs, or doc restructuring.
Fail updates visibly and keep the previous validated package. Generator/schema
changes need reviewed adaptation. Nixdoc or pinned toolchain substitutes may be
unavailable, requiring builds; do not fall back to unrelated installed tools.
Moving public links can differ from pinned docs. Cross-platform behavior cannot
be established by a Linux CI run. Shared-tool changes could regress sibling
updates or widen publication permissions. PR #4 remains an integration dependency.

## Verification

- Run existing sibling tests, validators, and exact regeneration before and after
  shared changes; verify both sibling packages remain byte-identical.
- Validate skill metadata, references/anchors, selected source/declaration paths,
  source and output hashes, notices, schema, and exact file membership. Use the
  skill-creator validator locally without making a personal path a CI dependency.
- Test converter behavior with real selected syntax: anchors/empty labels,
  cross-chapter references, admonitions/examples, inherited caveats, roles,
  definition lists, includes, and executable code preservation. Test ambiguous,
  missing, cyclic, escaping, malformed, or unsupported input rejection.
- Test generated-API selection, schema changes, absent identities, stable
  serialization, and repeated generation from the same pin with identical bytes.
- Evaluate a controlled fixture against the pinned source and evaluator:
  `callPackage` argument overrides, `overrideAttrs`, overlay final/previous
  behavior, selected library results, fileset inclusion, and a small `evalModules`
  composition. Assert results, not just parseability.
- Build a bounded local-source `stdenvNoCC` fixture that proves pre/post hooks,
  checks, and installed output, plus a small shell-application helper. Avoid
  fetching application sources, starting services, or compiling every selected
  language ecosystem. Distinguish evaluated language-helper availability from
  actually built examples; do not claim cross-platform builds were tested.
- Exercise changed and unchanged updates in temporary repositories, ancestry
  failures, unavailable sources, staging/partial-write restoration, immutable
  selections/toolchain, sibling isolation, and malicious/stale artifacts.
- Run `actionlint` and clean-runner CI for all integrated skills. Walk through
  package creation, overriding a dependency, overlay recursion troubleshooting,
  and an older consumer pin; record actual observations and execution limits.
- Open an implementation PR linking all three approved artifacts and closing #5.
  After an authorized merge, validate the first live update, distinguishing a
  no-op from a genuinely exercised changed-source publication path.
