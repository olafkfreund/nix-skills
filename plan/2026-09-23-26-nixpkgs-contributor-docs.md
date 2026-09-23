---
status: approved
issue: 26
spec: spec/2026-09-23-26-nixpkgs-contributor-docs.md
---

# Plan: Nixpkgs contributor guidance and review tools

Branch: `feat/26-nixpkgs-contributor-docs`, based on `main` 539c8ec.
Pinned Nixpkgs revision: `9c0ece3dc2086e85434c5d2477eb6bc118d20ff8`.
Intent: `intent/2026-09-23-26-nixpkgs-contributor-docs.md`.
Spec: `spec/2026-09-23-26-nixpkgs-contributor-docs.md`.

## Approved decisions

- **D1 Section format:** selection items take an optional `format`, either
  `"manual"` (the default, today's behaviour, unchanged) or `"github"`.
  A github item:
  - requires `level` (an integer from 1 to 6) and `reference: "contributing"`;
  - its `path` must be in the code constant
    `GITHUB_SOURCES = {'CONTRIBUTING.md', 'pkgs/README.md', 'pkgs/by-name/README.md'}`;
  - is selected by exact heading text and level, and exactly one prose heading
    must match, ignoring fenced code;
  - uses `children` with its current meaning;
  - has `anchor` as our own id, matching `[\w.:-]+`, unique across the
    selection, with the prefix `contributing-`, `pkgs-readme-` or `by-name-`
    by file;
  - is emitted as `<a id="ANCHOR"></a>` before the excerpt.
- **D2 Links in github excerpts (`convert_github`):**
  - Fenced code is never altered.
  - `http` and `https` links are kept. Other schemes and `//` are an error.
  - `#slug` is resolved against the same file's GitHub heading slugs:
    lower-case, punctuation other than `-` and `_` removed, spaces to `-`, and
    `-N` added for duplicates. It points to the bundled anchor if that section
    is bundled, otherwise to `https://github.com/NixOS/nixpkgs/blob/REV/PATH#slug`.
    An unknown slug is an error.
  - A relative or root-relative path is normalised. It must stay inside the
    source and exist in the pinned source. It becomes `…/blob/REV/P` for a
    file or `…/tree/REV/P` for a directory, keeping any fragment.
  - Reference definitions resolve the same way, and duplicates are an error.
- **D3 Output:**
  - `references/contributing.md` is added to `GENERATED`, the `documents`
    list (`# Contributing`) and the table of contents.
  - `validate_manifest` accepts `contributing`, and enforces D1's schema and
    allowed paths.
  - github source files are hashed into `inputs`.
  - Generation fails if `contributing.md` is over 64 KiB (65536 bytes).
- **D4 Selection** (reviewed policy), heading (level, children):
  - `CONTRIBUTING.md`:
    1. Overview (2, no)
    2. How to create pull requests (2, yes)
    3. How to review pull requests (2, no)
    4. Branch conventions (2, yes)
    5. Commit conventions (2, yes)
    6. File naming and organisation (3, no)
    7. Formatting (3, no)
  - `pkgs/README.md`:
    1. Quick Start to Adding a Package (2, no)
    2. Commit conventions (2, no)
    3. Package naming (2, no)
    4. Versioning (2, no)
    5. Patches (2, yes)
    6. Automatic package updates (2, no)
  - `pkgs/by-name/README.md`:
    1. Name-based package directories (1, yes)

  If the cap is exceeded, remove `CONTRIBUTING.md` rows from the bottom up,
  and record them in this plan. Never raise the cap.
- **D5 Authored `SKILL.md` additions:**
  - a pointer to the contributing reference;
  - unpinned, labelled `blob/master` links to `lib/README.md` and
    `nixos/README.md`;
  - search Nixpkgs issues and PRs before a workaround, and cite the results;
  - `nixpkgs-review`: `wip`, `rev HEAD` and `pr N`; check the scale and ask
    before large runs; read the report. Never use `post-result`, `approve`,
    `merge`, `--post-result` or `--approve-pr` without explicit authorization;
  - `nixpkgs-update` / `r-ryantm` PRs, with its docs and logs URLs.
- **D6 Invariants:**
  - Manual-format output stays byte-identical: `packaging.md`,
    `customization.md`, `helpers.md` and `library.md` are unchanged.
  - Every existing fail-closed check is kept.
  - No new dependencies.
  - The automation still cannot change the selection (`immutable_policy`).
- **Stop rule:** stop, revise this plan and ask if any of these happens:
  - an upstream link form cannot be converted safely under D2;
  - a manual-format reference changes bytes;
  - dropping rows under D4 would remove any `pkgs/README.md` or `by-name` row.

## Steps

Each step is one commit, with Conventional Commits and `(#26)`, citing the
step number.

1. **Provider support (D1–D3, D6), with the selection unchanged:** in
   `scripts/nixpkgs.py`, add:
   - `GITHUB_SOURCES` and `github_slug()`;
   - `github_headings()`, `excerpt_github()` and `convert_github()`;
   - the `contributing` document, `GENERATED` entry and size cap;
   - `validate_manifest` rules;
   - dispatch on `format` in `generate`.

   Add unit tests in `tests/test_nixpkgs.py`:
   - heading and level selection, with ambiguous or missing headings failing;
   - disallowed path or reference, and a missing `level`, rejected;
   - bundled and unbundled slug links, with unknown slugs failing;
   - relative file and directory links, with escaping and missing paths
     failing;
   - duplicate anchors rejected;
   - the size cap enforced;
   - fenced code unchanged.

   With no github items selected yet, `contributing.md` contains only its
   header, which the output boundary requires once it is in `GENERATED`.
   → Verify:
   - `python3 -m unittest tests.test_nixpkgs` passes;
   - `update.py --skill nixpkgs-development --revision 9c0ece3… ` regenerates;
   - the four manual references are byte-identical (`git diff --stat` shows
     only the new `contributing.md` and `sources.json` hashes);
   - `check.py --skill nixpkgs-development` passes.
2. **Selection (D4):** add the 14 items to `selection.sections` in
   `skills/nixpkgs-development/sources.json`, then regenerate at the pinned
   revision with `--revision`.
   → Verify:
   - the four manual references are still byte-identical to `main`;
   - `contributing.md` is at most 65536 bytes and contains all 14 anchors;
   - `grep -nE '\]\((\.|/|#[a-z])' contributing.md` finds no raw relative or
     slug links;
   - `update.py --skill nixpkgs-development --check` passes.

   If the stop rule triggers, stop.
3. **SKILL.md (D5):** add the authored sections to
   `skills/nixpkgs-development/SKILL.md`, and link
   `references/contributing.md`.
   → Verify:
   - `check.py` and `check_collection.py` pass;
   - every URL returns 200;
   - the `nixpkgs-review` subcommands and flags named match
     `nixpkgs-review --help` and `nixpkgs-review pr --help`.
4. **Full verification:** run the commands under Tests below.
5. **PR:**
   - Push with `git push -u origin feat/26-nixpkgs-contributor-docs`.
   - Open a PR with `Closes #26`, following the template.
   - Link the intent, spec and plan.
   - Include the regeneration evidence (manual references byte-identical, the
     size of `contributing.md`) and any rows dropped.

   → Verify the PR `Check` workflow is green. Merge only on the maintainer's
   approval.

## Tests

```sh
python3 scripts/check_collection.py
python3 -m unittest discover -s tests -p 'test_*.py'
for s in nix-language devenv-project home-manager microvm-nix nixpkgs-development nixos-wiki; do
  python3 scripts/check.py --skill "$s"
  python3 scripts/update.py --skill "$s" --check
done
git diff main -- skills/nixpkgs-development/references/{packaging,customization,helpers,library}.md   # expect empty
wc -c skills/nixpkgs-development/references/contributing.md                                           # expect <= 65536
git diff --exit-code
```

Expected result: every command exits 0, the four manual references have no
diff against `main`, and `contributing.md` is within the cap.

Limitation: the network and Nix checks run on one x86_64-linux host. The
behaviour examples in the spec are for reviewers, and no agent run is claimed.

## Rollback

Revert the PR's merge commit, or the individual step commits. The previous
`sources.json` selection and generator are restored together, and the next
update regenerates without `contributing.md`. The provider change is
self-contained in `scripts/nixpkgs.py` and its tests. No other provider,
workflow or skill is touched.
