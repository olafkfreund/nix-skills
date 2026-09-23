---
status: approved
issue: 26
intent: intent/2026-09-23-26-nixpkgs-contributor-docs.md
---

# Spec: Nixpkgs contributor guidance and review tools

The intent was approved without answers to its open questions, so this spec
uses its recommendations: a new `contributing` reference, the recommended
sections, and a short authored `nixpkgs-review` section. Reject any of them at
this review.

## Facts the design rests on

The pinned revision is `9c0ece3dc2086e85434c5d2477eb6bc118d20ff8`.

- **No anchors.** `CONTRIBUTING.md` (55 headings), `pkgs/README.md` (56) and
  `pkgs/by-name/README.md` (15) contain no mdBook `{#id}` anchors. Today
  `excerpt()` (`scripts/nixpkgs.py`) selects only by
  `anchor == {#id} and heading == text`, so none of their sections can be
  selected.
- **Links would fail.** Their links are GitHub-style: `#github-slug`,
  `./relative/path` and directories. `convert()` resolves fragments only
  against the manual's anchor index, and relative paths only against recorded
  manual files. It would reject these links ("Missing/ambiguous anchor",
  "Unresolved relative source link").
- **A heading collides.** `## Commit conventions` appears in both
  `CONTRIBUTING.md` and `pkgs/README.md`, so slug-derived ids would collide.
  The generator rejects duplicate packaged anchors.
- **Outputs are fixed.** They are hard-coded to `packaging`, `customization`,
  `helpers` and `library` (`GENERATED`, the `documents` construction, and
  `validate_manifest`).
- **Tool subcommands.** `nixpkgs-review` has local build subcommands (`pr`,
  `rev`, `wip`), and subcommands that act on GitHub (`post-result`, `approve`,
  `merge`, plus `pr --post-result` and `--approve-pr`).

## Design

### 1. A GitHub-Markdown section format in the provider (`scripts/nixpkgs.py`)

Selection items gain an optional `"format"`. It is `"manual"` by default,
which keeps today's behaviour for every existing item unchanged, or
`"github"`.

For `"format": "github"`:

- **Allowed paths:** `path` must be one of `CONTRIBUTING.md`,
  `pkgs/README.md` or `pkgs/by-name/README.md`. This is a constant in code, so
  widening it is a reviewed code change. `reference` must be `contributing`.
- **Matching:** the section is found by exact heading text plus level. The
  selection adds `"level": N`, and exactly one prose heading at that level
  must have that text, or generation fails. `children` keeps its meaning.
- **Anchor:** `anchor` is this collection's own output id. It is validated by
  the existing `[\w.:-]+` rule and must be unique across all selections. The
  generator writes `<a id="ANCHOR"></a>` before the excerpt, because the
  source has no `{#id}`. Ids are prefixed per file: `contributing-…`,
  `pkgs-readme-…` and `by-name-…`.
- **Links** are converted by a new `convert_github()`. It never alters fenced
  code, and fails closed like `convert()`:
  - `http` and `https` links are kept. Other schemes and protocol-relative
    links are an error.
  - A fragment link `#slug` is looked up against the GitHub slugs of the same
    file's prose headings. The slug rule is lower-case, drop punctuation other
    than `-` and `_`, spaces to `-`, and `-N` suffixes for duplicates. If that
    heading's section is bundled, the link points to its bundled anchor.
    Otherwise it points to
    `https://github.com/NixOS/nixpkgs/blob/REV/PATH#slug`. An unknown slug is
    an error.
  - A relative or root-relative (`/…`) path is normalised against the file's
    directory. It must stay inside the source tree and exist in the pinned
    source. It becomes `…/blob/REV/P` for a file or `…/tree/REV/P` for a
    directory, keeping any fragment. Escaping or missing paths are an error.
  - Reference-style definitions are resolved the same way. Duplicate
    definitions are an error, as in `convert()`.
- **Provenance:** each github-format source file's hash is recorded in
  `inputs`, like other consumed inputs.

### 2. A new `contributing` reference

- `GENERATED` includes `references/contributing.md`.
- The `documents` list, the heading (`# Contributing`) and the table of
  contents include `contributing`.
- The `reference` sets checked in `validate_manifest` include `contributing`.
  The allowed-path rule from section 1 is also enforced there, so a hand-edited
  `sources.json` cannot select other files.
- `scripts/check.py` needs no change, because it reads `generated_files` and
  the manifest. The package boundary follows `GENERATED`.
- **Size cap:** generation fails if `references/contributing.md` exceeds
  64 KiB (`helpers.md` is 53 KB today). This keeps it loadable and stops
  upstream growth from silently doubling it.

### 3. Selected sections (reviewed policy)

| File | Heading (level) | Children |
|---|---|---|
| `CONTRIBUTING.md` | Overview (2) | no |
| `CONTRIBUTING.md` | How to create pull requests (2) | yes; includes the PR template checklist and rebasing |
| `CONTRIBUTING.md` | How to review pull requests (2) | no |
| `CONTRIBUTING.md` | Branch conventions (2) | yes; master vs staging, mass rebuilds |
| `CONTRIBUTING.md` | Commit conventions (2) | yes |
| `CONTRIBUTING.md` | File naming and organisation (3) | no |
| `CONTRIBUTING.md` | Formatting (3) | no |
| `pkgs/README.md` | Quick Start to Adding a Package (2) | no |
| `pkgs/README.md` | Commit conventions (2) | no |
| `pkgs/README.md` | Package naming (2) | no |
| `pkgs/README.md` | Versioning (2) | no |
| `pkgs/README.md` | Patches (2) | yes |
| `pkgs/README.md` | Automatic package updates (2) | no |
| `pkgs/by-name/README.md` | Name-based package directories (1) | yes; the whole file |

If the cap in section 2 is exceeded at the pinned revision, the plan removes
the lowest-priority rows, from the bottom of the `CONTRIBUTING.md` rows first,
and records which. It does not raise the cap.

### 4. Authored `SKILL.md` additions (`skills/nixpkgs-development/SKILL.md`)

- **Contributing:** a pointer to the `contributing` reference, for changes
  intended for Nixpkgs itself: commit format, `pkgs/by-name` placement, naming,
  target branch, and review expectations. Links to `lib/README.md` and
  `nixos/README.md` point to the branch path
  (`https://github.com/NixOS/nixpkgs/blob/master/…`) and are labelled as
  unpinned. `SKILL.md` is authored and never rewritten by the generator, so a
  pinned link there would go stale.
- **Before a workaround:** read the build log, then search NixOS/nixpkgs
  issues and pull requests for the error and the package, and cite what you
  found.
- **`nixpkgs-review`**, a short section:
  - `nixpkgs-review wip` for uncommitted changes, `nixpkgs-review rev HEAD`
    for a commit, and `nixpkgs-review pr N` for a pull request.
  - It builds every affected package, which can be many and slow, so check
    the scale and ask before running it on a large change.
  - Read its report of failed, broken and skipped packages before stating a
    result.
  - Never use `post-result`, `approve`, `merge`, `--post-result` or
    `--approve-pr` without the user's explicit authorization, because they act
    on GitHub under the user's identity.
- **`nixpkgs-update`:** version-bump PRs from `r-ryantm` come from
  nixpkgs-update. Review them like any update: check the changelog, run
  `nixpkgs-review pr N`, and check the linked build logs. Point to its
  documentation (`https://nix-community.github.io/nixpkgs-update/`) and logs
  (`https://nixpkgs-update-logs.nix-community.org/`).

### 5. Automation boundary

The selection change and the new `format` and `level` fields are part of the
reviewed policy that `immutable_policy` protects. Weekly updates regenerate
the new reference but cannot change what is selected. A future upstream edit
that renames a selected heading, or breaks a link, makes the weekly update
fail closed, as today.

## Alternatives rejected

- **Put the excerpts in `packaging`.** That mixes contributor process with
  build mechanics, and makes an already large reference larger.
- **Bundle the files whole.** They total over 120 KB, mostly irrelevant
  detail such as the staging mechanics and long syntax lists.
- **Anchor by GitHub slug alone.** It collides on `Commit conventions`, and
  its meaning changes silently when upstream renames a heading. Heading, level
  and our own id fail closed instead.
- **Rewrite all links to plain upstream URLs without validation.** That would
  accept broken or escaping links. Validating against the pinned source keeps
  the provider's guarantee.
- **Authored summaries instead of excerpts.** They would drift from upstream.
  Excerpts regenerate with the pin.
- **Pinned `lib/README.md` and `nixos/README.md` links in `SKILL.md`.**
  `SKILL.md` is authored and not regenerated, so a pinned link would go stale
  every week.

## Risks

- **Link edge cases in the upstream files** (HTML anchors, image links, badge
  links) could make generation fail. They are found at the pinned revision
  during implementation. A form that can't be supported safely leads to a
  revised plan, not a looser rule.
- **Weekly update fragility grows:** more headings can be renamed upstream.
  This is accepted. It fails closed and shows up as a failed update run, as
  for the manual sections.
- **Existing output must not change:** the `manual` path must stay
  byte-identical. The existing four references are regenerated and compared.
- **Hosts:** CI runners only, and local maintainer runs. Consumers get a new
  reference file.

## Verification

- **Unit tests** in `tests/test_nixpkgs.py`:
  - github-format selection by heading and level, with ambiguous or missing
    headings failing;
  - disallowed path or reference rejected by `validate_manifest`;
  - slug links resolved to bundled or pinned URLs, with unknown slugs failing;
  - relative file and directory links, with escaping and missing paths
    failing;
  - duplicate anchor ids rejected;
  - the size cap enforced;
  - fenced code left unchanged.
- **Regression:** with the new selection, `update.py --skill
  nixpkgs-development --revision <pinned>` must leave `packaging.md`,
  `customization.md`, `helpers.md` and `library.md` byte-identical to `main`,
  and add only `contributing.md`. Then
  `update.py --skill nixpkgs-development --check` passes.
- **Offline checks:** `check.py --skill nixpkgs-development`,
  `check_collection.py`, the full unit test suite, and the six-skill
  `update.py --check` list from #19.
- **Content checks:**
  - `contributing.md` is at most 64 KiB;
  - every selected heading is present;
  - a manual scan of converted links finds no raw relative or `#slug` links.
- **Behaviour (for review, no automated agent run claimed):**
  - "Add package foo to Nixpkgs" should lead to `pkgs/by-name`, the naming and
    commit conventions, and `nixpkgs-review wip`.
  - "Review PR 12345" should lead to `nixpkgs-review pr 12345`, reading the
    report, and no posting without authorization.
