---
status: approved
issue: 65
spec: spec/2026-09-24-65-catalog-table.md
---

# Plan: a readable skill catalog

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Catalog (`scripts/docs_catalog.py` → `reference/catalog.md`).**
- **Intro line:** "Generated from `skills.json`, each skill's `SKILL.md`
  and `sources.json` when this site was built."
- **Overview table** `| Skill | Source | Licence |`, one row per
  `skills.json` name:
  - Skill: `[name](#name)`, linking to that skill's section;
  - Source: `[owner/repo](url)` for GitHub upstreams,
    `[host](url)` for others, or "Hand-written" without `sources.json`;
  - Licence: `[<name>](<REPO>/skills/<skill>/<file>)`, or
    `Repository licence (<name of root LICENSE>)` without a licence file.
- **One `## <skill>` section per skill:**
  - the frontmatter description as a paragraph;
  - `- **Source:** <source link>, <pin>`, only when `sources.json`
    exists;
  - `- **Licence:** <licence>`;
  - `- **Instructions:** [SKILL.md](<REPO>/skills/<skill>/SKILL.md)`.
- **Pin:**
  - `release <r>` if present, else `branch <b>`;
  - then ` at [`<rev[:12]>`](<upstream>/tree/<rev>)` for a GitHub upstream
    with `revision`;
  - with `snapshot_sha256`, `dump snapshot `sha256:<first 12>``, no link;
  - missing parts render as `—`.
- **`licence_name(path)`:**
  - `Apache License` together with `Version 2.0` → `Apache-2.0`;
  - `GNU LESSER GENERAL PUBLIC LICENSE` together with `Version 2.1` →
    `LGPL-2.1`;
  - `Permission is hereby granted, free of charge` → `MIT`;
  - anything else raises `ValueError(f"Unrecognised licence text: {path}")`.

  The root `LICENSE` uses the same function.
- `update-schedule.md` is unchanged.

**Install page.**
- `docs/src/how-to/install.md` drops the "List skills" column from its
  agent table, leaving four columns.
- After the table, it adds: "List the installed skills with `/skills` in
  Claude Code and Codex; in OpenCode and Antigravity, ask the agent which
  skills it has."

**Shape rule (`scripts/check_docs.py`),** applied to every page's Markdown
tables:
- at most 4 columns;
- each cell's visible text at most 120 characters, measured after
  stripping `[text](url)` to `text` and removing backticks.

Otherwise it raises `ValueError(f"Table too wide in {page}: …")`, naming
the column count or the long cell.

**CONTRIBUTING.md:** one sentence in the site paragraph stating the table
limits, and that a list or sections should be used for longer content.

**Tests (`tests/test_docs.py`).**
- **Fixture rendering:**
  - a 3-column overview;
  - section anchors;
  - a GitHub pin link;
  - a snapshot hash with no link;
  - "Hand-written" for a skill with no `sources.json`.
- **`licence_name`:** each of the three known texts; an unknown text
  raises.
- **Shape rule:** a 5-column table and a 121-character cell each fail; a
  4-column table with 120-character cells passes.
- **Real repository:**
  - 10 overview rows and 10 `## ` sections;
  - licence counts Apache-2.0 ×1, LGPL-2.1 ×1, MIT ×6 and repository ×2;
  - no `/tree/` link on the `nixos-wiki` row.

### Deviation during implementation

- **The docs build needs the root `LICENSE`.** "Repository licence
  (<name>)" is detected from the repository's own `LICENSE`, but
  `nix/docs.nix` only copies a chosen set of files into the build, and
  `LICENSE` was not among them. The first build failed with
  `FileNotFoundError: LICENSE`. `../LICENSE` is added to that `fileset`;
  nothing else changes.

## Steps

1. **The generator rewrite, with its tests.**
   → Verify: the unit tests pass, including the real-repository
   assertions.
2. **The shape rule in `check_docs.py`,** with its tests, and the install
   table change.
   → Verify: the unit tests pass, and `nix build .#docs` passes. The rule
   holds on every page, and the overview anchors resolve.
3. **The CONTRIBUTING sentence.**
   → Verify: `check_collection.py` passes.
4. **Local browser measurement.**
   - Serve the built site: `python3 -m http.server --directory <result>
     8765` in the background.
   - Measure the catalog and install tables at the default window width
     with the Chrome tools.
   - Stop the server.

   → Verify: both tables are at most 750 px, with no scrolling wrapper and
   no cramped cells. Save a screenshot of the new catalog for the PR.
5. **Full checks:** unit tests, `check_collection.py`, `devenv shell
   check-fast`, `nix flake check`, `actionlint`. Commit steps 1 to 3
   separately, push, and open a PR with `Closes #65`.
   → Verify: CI is green, and the PR is `CLEAN`.
6. **Merge,** with the owner's prior go-ahead ("merge when done").
   → Verify: `main` CI and the Pages deploy succeed, and the live
   measurement matches step 4.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
nix build .#docs
python3 scripts/check_collection.py
devenv shell check-fast
nix flake check
actionlint
```

The browser measurement, locally in step 4 and live in step 6, uses the
same script as the review.

## Rollback

- Before merge: close the PR and delete the branch.
- After merge: `git revert` the commits. That restores the six-column
  table and removes the shape rule. Pages redeploys the previous layout.
