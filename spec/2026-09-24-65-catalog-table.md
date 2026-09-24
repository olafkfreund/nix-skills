---
status: approved
issue: 65
intent: intent/2026-09-24-65-catalog-table.md
---

# Spec: a readable skill catalog

## Facts

Checked on 2026-09-24.

- **Measurements.** In the browser, mdBook's content column (`main`) is
  750 px wide. The catalog table is 1007 px wide, with all 10 description
  cells under 160 px wide. The install page's agent table is 751 px. The
  remaining six tables are at most 750 px.
- **The generator.** `scripts/docs_catalog.py` renders one six-column
  table. Its fields come from `sources.json`: `upstream`, `release` or
  `branch`, and `revision` or `snapshot_sha256`. The licence file is
  `LICENSE`, `COPYING` or absent.
- **Upstreams.** Seven skills have `https://github.com/<owner>/<repo>`
  upstreams. `nixos-wiki` has `https://wiki.nixos.org/wikidump.xml.zst`
  with `snapshot_sha256`, which is not a revision.
- **Licence file headers:**

  | Header text | Skill |
  | --- | --- |
  | `Apache License` | devenv-project |
  | `GNU LESSER GENERAL PUBLIC LICENSE` | nix-language |
  | `Permission is hereby granted, free of charge`, the MIT text | home-manager, microvm-nix, nix-darwin, nixos-operations, nixos-wiki, nixpkgs-development |

  `nix-workflow` and `nixos-coding-agents` have no licence file.
- **Anchors.** `check_docs.py` validates links and anchors on generated
  pages too, because it runs after generation.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Layout.** A compact three-column overview table, followed by one
   section per skill.
2. **Licence names** are detected from licence file text. An unrecognised
   licence file fails the build.
3. **Guard.** A table-shape rule in `check_docs.py` for every site page,
   plus generator tests. No browser in the build.

### `reference/catalog.md` (generated)

```markdown
# Skill catalog

Generated from `skills.json`, each skill's `SKILL.md` and `sources.json` when this site was built.

| Skill | Source | Licence |
| --- | --- | --- |
| [devenv-project](#devenv-project) | [cachix/devenv](https://github.com/cachix/devenv) | [Apache-2.0](…/skills/devenv-project/LICENSE) |
| [nix-workflow](#nix-workflow) | Hand-written | Repository licence (MIT) |
…

## devenv-project

Create, explain, review, and debug devenv project environments, … (the full description).

- **Source:** [cachix/devenv](https://github.com/cachix/devenv), release v2.3.1 at
  [`2418e1b43797`](https://github.com/cachix/devenv/tree/2418e1b43797c44de5166176622c8d8fa0149871)
- **Licence:** [Apache-2.0](…/skills/devenv-project/LICENSE)
- **Instructions:** [SKILL.md](…/skills/devenv-project/SKILL.md)
```

- **Source name:**
  - a GitHub upstream is shown as `owner/repo`, linked;
  - any other upstream is shown by host, linked (`wiki.nixos.org` dump);
  - hand-written skills say "Hand-written".
- **The pin line:**
  - `release <r>` or `branch <b>`, then `at` followed by the 12-character
    revision linked to `<upstream>/tree/<revision>`. The link is made only
    for GitHub upstreams, and only when `revision` is present;
  - for `snapshot_sha256`, "dump snapshot `sha256:<first 12>`", with no link;
  - a hand-written skill has no pin line;
  - missing fields render as "—".
- **Licence detection** (`licence_name(path)`), on the file text:
  - `Apache License` together with `Version 2.0` → `Apache-2.0`;
  - `GNU LESSER GENERAL PUBLIC LICENSE` together with `Version 2.1` →
    `LGPL-2.1`;
  - `Permission is hereby granted, free of charge` → `MIT`;
  - anything else raises `ValueError`;
  - no licence file → "Repository licence (MIT)". The repository's own
    `LICENSE` is detected the same way, so the parenthesis is not
    hard-coded.
- **The overview table** has three columns, and every cell is under 60
  characters.
- **Anchors.** The overview links to each section's anchor, which
  `check_docs.py` validates.

`update-schedule.md` is unchanged.

### "Install the skills": the agent table

- The five-column table (Agent, `agents` value, Skill directory, Call a
  skill, List skills) loses the **List skills** column. It becomes four
  columns.
- The column's information moves to one sentence under the table: "List
  the installed skills with `/skills` in Claude Code and Codex; in OpenCode
  and Antigravity, ask the agent which skills it has."
- The same table on Getting started, if present, is not affected. It
  already has fewer columns.

### Guard: table shape in `scripts/check_docs.py`

For every page, each Markdown table must:
- have **at most 4 columns**;
- have visible cell text (links and code markers stripped) of **at most
  120 characters**.

Otherwise it fails with `Table too wide in <page>: …`. The limits fit all
current tables once this change is made: the longest cell is 102
characters, and the widest table after the fix has 4 columns.
`tests/test_docs.py` covers a 5-column table and a 121-character cell
failing, and the limits passing.

### Tests

`tests/test_docs.py`:
- **Catalog rendering** from the fixture:
  - a three-column overview, with section anchors;
  - a GitHub pin link;
  - no link for a snapshot hash;
  - "Hand-written" for a skill without `sources.json`.
- **Licence detection:** each of the three known texts; an unknown text
  raises.
- **Real repository:**
  - 10 overview rows and 10 sections;
  - licences Apache-2.0 ×1, LGPL-2.1 ×1 and MIT ×6, plus 2 repository
    licence rows;
  - the wiki row has no revision link.

## Alternatives rejected

- **Widening mdBook's content column** (`.content main { max-width }`). It
  would hurt readability on every page, and the intent rules it out.
- **Keeping one table and letting it scroll horizontally.** Hidden columns
  are the reported problem.
- **A licence-name mapping hard-coded per skill.** It drifts. Detecting
  from the shipped file text keeps the site tied to what is actually
  distributed.
- **A browser-based width check in CI.** It needs a headless browser in an
  offline Nix build. The shape rule catches the causes (too many columns,
  long cells) cheaply.
- **Putting descriptions in `<details>` blocks inside the table.** Still a
  cramped cell, and raw HTML in generated Markdown is harder to check.

## Risks

- **A new upstream licence text** (for example BSD) makes the build fail
  until the detector learns it. That is intended: it forces a reviewed
  label.
- **The shape rule rejects a future legitimate table.** The limits are
  documented in CONTRIBUTING, and a page can use a list or sections
  instead.
- **Heuristic limits don't guarantee pixel width.** Four columns with long
  code spans could still overflow. Mitigated by the 120-character cell
  limit, and by the post-deploy browser measurement in Verification.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*.py'` passes, including
  the new tests.
- `nix build .#docs` passes. The shape rule holds on all pages, and the
  anchors from the overview to the sections resolve.
- **Local browser measurement.** Serve the built site locally
  (`python3 -m http.server`) and re-run the table-width measurement. The
  catalog and install tables must be at most 750 px, with no scrolling
  wrapper and no cramped cells.
- `check_collection.py`, `devenv shell check-fast` and `nix flake check`
  pass.
- **After merge:** the same measurement on the live site.
