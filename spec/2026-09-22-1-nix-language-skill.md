---
status: draft
issue: 1
intent: intent/2026-09-22-1-nix-language-skill.md
---

# Spec: Reusable Nix language skill

## Design

### Scope and package

Implement one skill at `skills/nix-language/` in this repository.
Its `SKILL.md` uses standard `name` and `description` frontmatter and relative reference links, with automatic selection permitted.
It supports writing, explaining, debugging, and reviewing Nix expressions.
It distinguishes built-ins from Nixpkgs `lib`, and language attribute sets from the NixOS module system.
It does not incorporate this machine's deployment policies or perform system rebuilds.

Keep the skill entrypoint concise: establish the target Nix version and evaluation mode, inspect relevant code and callers, read the relevant reference, make the smallest correct change, and verify the affected behaviour.
When Nix execution is unavailable, state that validation was limited to inspection.
Do not imply that syntax checking proves evaluation or build success.
Evaluation can access files, fetch inputs, or trigger builds; examples used for validation must be controlled, and project validation must respect the task's permissions.

The proposed files are:

```text
skills/nix-language/
  SKILL.md
  references/
    language.md       # Selected source sections on core language semantics
    builtins.md       # Selected generated built-in documentation
  sources.json       # Exact source revision, selections, and content hashes
  COPYING            # Upstream licence text accompanying copied material
scripts/
  update.py           # Deterministic reference updater, Python standard library
  check.py            # Portable structural and reference validation
tests/
  language.nix        # Small executable semantic checks
  test_update.py      # Updater failure and reproducibility checks using unittest
.github/workflows/
  check.yml
  update.yml
README.md
```

Do not add a plugin, MCP server, model API dependency, or agent-specific runtime requirement.
Keep maintenance scripts outside the installed skill package.
Use the existing root README for installation, updating, supported scope, and maintenance commands.
Document copying or linking the whole skill folder into an agent's supported skill directory; do not claim all agents use the same discovery path.
Agents without native skill discovery can read `SKILL.md` and its references explicitly.
Pin consumers to a repository commit for reproducible installation and rollback.
No machine installation or NixOS configuration changes are included in this task.

### Reference selection and provenance

Use the upstream Nix repository as the authoritative source, starting from a stable release selected during implementation and recorded by tag and full commit SHA.
The earlier inspected development checkout is evidence for the design, not the initial release pin.

`sources.json` records the repository URL, release tag, exact source revision, reported Nix version, selected source paths and sections, selected built-in names, and SHA-256 hashes of input material and generated reference files.
Exclude timestamps and machine paths so repeated generation has identical output.
Record enough information to regenerate the references from a clean checkout.

Select focused sections from `doc/manual/source/language/` covering syntax, values, operators, scope, function arguments and defaults, evaluation and laziness, strings and string context, paths, and derivations.
Include concrete pitfalls such as lexical scope taking precedence over `with`, shallow attribute-set updates, defaults not being added to an `@` argument binding, and incomplete evaluation of lazy values.
Keep explanatory instructions separate from verbatim generated reference content.
Avoid copying the entire manual or every built-in; link to the corresponding versioned manual for material outside the selected subset.
For each included section, retain a source pointer tied to the recorded revision.

Build or obtain the Nix executable from the pinned upstream source through its existing build definition, and use that executable's `__dump-language` output.
Do not silently substitute the host's installed Nix.
Reuse upstream `doc/manual/generate-builtins.nix` and its helper dependencies for the selected built-in entries, preserving argument information and experimental/pure-evaluation notices.
Include the upstream derivation reference separately because `derivation` has separately authored documentation.

Resolve `@docroot@`, relative documentation links, and any includes in selected material using the upstream documentation conventions.
Prefer upstream preprocessing when includes require it; do not implement a general Markdown parser.
Retained links must target included content or the selected release's published manual, with the appropriate anchors and page extensions.
Source provenance links point to the full upstream revision.
Fail on unsupported include syntax, missing sections or built-ins, unresolved placeholders, or ambiguous link conversion rather than silently dropping content.

Preserve applicable upstream copyright, attribution, and licence notices alongside copied material.
Do not label the combined package as permissively licensed by default.
Resolve any conflicting or unclear source notices before copying the affected material; documenting the upstream licence is not a relicensing decision.

### Automatic updates

Provide an explicit updater invocation for a supplied release tag and a check mode that regenerates from the existing manifest without changing committed files.
Use temporary output, validate it, and only then replace generated references and the manifest.
A failed update leaves the previous package intact.

Run `.github/workflows/update.yml` weekly and via manual dispatch.
Discover the newest non-draft, non-prerelease upstream release and compare its resolved revision with `sources.json`.
Skip when unchanged; reject a moved existing tag for manual investigation.
Release discovery, source resolution, and generation failures must fail visibly.
Use a fixed update branch with concurrency control to maintain at most one open automated update PR.
The PR identifies old and new revisions and summarises changed selected sources.
No automatic merge or installation is enabled.

Automatic updates may change only generated reference content, provenance, and necessary upstream notices.
Changes to `SKILL.md`, curated selections, updater logic, tests, and CI require ordinary reviewed edits.
New upstream concepts outside the selected subset are not automatically taught by the skill; the update PR must flag changes to other language source files for review.

The update job needs a Linux runner with Nix, Git, Python 3, network access to upstream sources/build substitutes, and repository-scoped permission to push its update branch and open PRs.
Use the workflow token where repository settings permit, and pin external Actions to full commit SHAs.
Keep normal validation read-only; do not expose write credentials to checks on untrusted PRs.
Run validation explicitly before pushing because PRs created with the default workflow token may not trigger further workflows.
Do not assume such PRs satisfy required status checks; document the maintainer-triggered validation path if needed.
If repository settings prohibit automated PR creation, report the prerequisite rather than adding a personal token automatically.

### Verification

`scripts/check.py` validates required skill metadata, relative package links, reference provenance and hashes, unresolved source directives, and the permitted generated-file set.
Validate linked headings in bundled references; check selected external manual targets during update generation and report unavailable targets as failures.
Use the skill-creator validator during implementation as an additional check when available, without making a personal skill installation a CI dependency.

`tests/language.nix` contains a compact set of assertions covering scope precedence, shallow set updates, function argument defaults, laziness, and string interpolation.
Evaluate it using the same pinned Nix used for documentation generation, with no network fetches or derivation builds in the expressions.
Use Python's standard-library test runner for deterministic generation, missing-source rejection, unresolved-link rejection, and preservation of existing output on failure.
Regenerating twice from the same pin must produce no diff.

Manually exercise representative writing, explanation, and review prompts against the completed skill.
Verify that it routes to the relevant references, distinguishes Nixpkgs APIs from built-ins, respects version restrictions, and reports actual validation limits.
Record the observed results in the implementation PR; do not claim cross-agent behaviour was tested on agents that were not run.

## Alternatives rejected

- Copy the whole manual: unnecessary context and maintenance volume, with generated pages still requiring a build.
- Scrape the latest website: moving provenance and potential mismatch with users' Nix versions.
- Parse built-in documentation directly from C++ with regular expressions: duplicates the upstream generator and risks losing availability metadata.
- Generate skill instructions with an LLM on every release: unnecessary cost and semantic drift in otherwise deterministic updates.
- Require an MCP server or vector index: plain files and targeted references meet the current need.
- Follow upstream master automatically: development features would become the default guidance for release users.
- Automatically merge updates: source changes and new language features need review.

## Risks

- Upstream generator interfaces, section headings, release metadata, or documentation URLs may change. Fail visibly and retain the last validated package.
- Building the matching Nix executable can be expensive when substitutes are unavailable. Reuse existing Nix build caching; do not use a mismatched executable to save time.
- A user's evaluator may differ from the documented release. The skill must identify the mismatch and verify version-sensitive behaviour against the user's target.
- Automatic refresh of a selected subset does not guarantee coverage of new features. Surface other language-documentation changes in update PRs.
- Native skill discovery varies between agents. Keep package contents portable and verify discovery only for documented, tested installations.
- This task affects repository files and CI only; it does not deploy to any NixOS host.
