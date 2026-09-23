---
status: approved
issue: 61
intent: intent/2026-09-23-61-readme-landing.md
---

# Spec: README as a landing page

## Facts

Checked on 2026-09-23 against `main` at `4410e91`.

- **The README** is 605 lines. Its sections and approximate sizes:
  - Getting started (~144, with subsections);
  - Use (43);
  - Declarative installation on NixOS (72);
  - Maintain (9) and Development environment (59);
  - eight per-skill maintenance sections: devenv 31, Home Manager 17,
    microvm.nix 15, NixOS operations 20, nix-darwin 15, Nixpkgs 40,
    NixOS Wiki 47;
  - Automatic updates (40);
  - Sources and licensing (47).
- **Relative links** in the README point to `skills/…`, `intent/…`, `spec/…`
  and `plan/…`. Those resolve on GitHub, but not from the site, where
  `check_docs.py` requires relative links to stay inside `docs/src`.
- **Code blocks.** The maintenance sections contain 11 fenced code blocks,
  which are commands and must move unchanged.
- **Inbound links.** Only `CONTRIBUTING.md:143` links into the README, to
  `README.md#automatic-updates`.
- **The README is validated.** `check_collection.py` checks its links,
  anchors and Nix style. The site is validated by `nix build .#docs`, which
  also checks that every page is listed in `SUMMARY.md`.
- **The README's current skill table** has columns Skill, Purpose and
  "Initial reference". There is no check that it matches `skills.json`.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Maintainer detail.** It goes to a new **Maintain** section on the site.
   CONTRIBUTING stays focused on contribution rules.
2. **The skill list.** A short README table, checked against `skills.json`
   by `check_collection.py`.
3. **Sources and licensing.** A compact licence table in the README. The
   full per-skill paragraphs move to the site.

### New README (target: about 90 lines)

1. **Title and one-sentence description,** with the documentation link.
2. **"What this is"**: 3 to 4 lines on skills for AI coding agents, the
   agents supported, and "skills, not agents".
3. **"Get started"**: three ways in, one command each:
   - **try it:** `nix run github:olafkfreund/nix-skills?dir=demo`, linking
     to the demo tutorial;
   - **your NixOS machine:** `nixosModules.agentic` or
     `nix flake init -t github:olafkfreund/nix-skills#agentic-nixos`,
     linking to "Set up your own machine";
   - **skills only:** the Home Manager module snippet, with
     `programs.nix-skills = { enable = true; agents = [ "claude" ]; }`,
     linking to "Install the skills".
4. **"First prompt"**: the start prompt, in a `text` block.
5. **"Skills"**: a table with columns Skill (linked to `SKILL.md`), Purpose,
   and Source and licence. Source is the upstream name, or "hand-written";
   licence is linked to the skill's `LICENSE` or `COPYING`, or "repository
   licence". It ends with a link to the generated catalog for pins and
   details.
6. **"Documentation"**: links to the four site sections and the Maintain
   section.
7. **"Contributing"**: 2 lines, linking to CONTRIBUTING and AGENTS.
8. **"Licence"**: the repository licence, and the sentence that copied
   upstream material keeps its own licence and is not relicensed, linking
   to the site's sources page.

### Where the rest goes

| README content | New home |
| --- | --- |
| Getting started: install, agent table, check, prompt, examples | Already covered: `tutorials/getting-started.md` and `how-to/install.md` |
| Getting started: user story | Appended to `tutorials/getting-started.md` as "Next: agentic coding on NixOS". Each step links to the demo and own-machine pages where those now replace it. |
| Use (clone, pin, links, invocation, update and rollback) | Covered by `how-to/install.md` and `how-to/update-and-rollback.md`. Any sentence not yet present is added there. |
| Declarative installation on NixOS | Covered by `how-to/install.md` and the generated options page. Facts not yet present are added to `how-to/install.md`: collision protection, rejected names and paths, the data package's per-skill outputs and `default`, and custom `directory` versus `agents`. |
| Maintain intro and Development environment | New `maintain/index.md` ("Maintain the collection") |
| Each per-skill maintenance section (8) | New `maintain/<skill>.md`, one page each |
| Automatic updates | New `maintain/automatic-updates.md`, with the maintainer detail (branches, reports, token, failure behaviour). `explanation/updates.md` stays the overview and links to it. |
| Sources and licensing, per-skill paragraphs and design-history links | New "Per-skill sources and licences" section on `explanation/authored-and-generated.md` |

**`SUMMARY.md`** gains a fifth group, "Maintain": the overview, "Automatic
updates", then the eight skill pages in `skills.json` order.

### Moving without rewriting

- **Moved text** stays as it is. Only these change:
  - relative links, which become
    `https://github.com/olafkfreund/nix-skills/blob/main/<path>` (or
    `/tree/main/` for directories);
  - heading levels, adjusted for the new page;
  - references to "this README", changed to "the README" or a link.
- **Code blocks** move byte for byte.
- **A one-off coverage check** during implementation, not committed:
  1. split the old README's moved sections into normalised lines
     (whitespace collapsed, link targets reduced to their repository path);
  2. assert that each line appears in its new home;
  3. list the exceptions, such as intentionally replaced hand-kept lists,
     in the PR.

### README skill-table check (`scripts/check_collection.py`)

- It reads the README's first table whose header starts with `| Skill |`.
- It takes the linked names (`[name](skills/name/SKILL.md)`).
- It raises `ValueError` unless that set equals `skills.json` exactly,
  naming any that are missing or extra.
- `tests/test_collection.py` covers:
  - a matching table;
  - a missing skill;
  - an extra skill;
  - a README without the table, which also fails, so the check cannot be
    skipped silently.

### Link updates

- `CONTRIBUTING.md:143` →
  `https://olafkfreund.github.io/nix-skills/maintain/automatic-updates.html`.
  Alternatively a relative repository link to `docs/src/maintain/…`; the
  public site link is the one readers use.
- AGENTS.md and CONTRIBUTING.md mentions of "README maintenance sections",
  if any, are pointed at `docs/src/maintain/`.

## Alternatives rejected

- **Maintainer detail in CONTRIBUTING.** It would grow from 150 to about
  450 lines, mixing contribution rules with provider runbooks, and could not
  be searched on the site.
- **Generating the maintenance pages from provider code.** The text is
  hand-written guidance, not data. Generating it would mean rewriting it,
  which the intent forbids.
- **Only a link to the catalog, with no README skill table.** Visitors on
  GitHub would see no skills without clicking. A checked table gives both.
- **Deleting the user story** as superseded by the demo and own-machine
  pages. It is kept on the site, with links, so nothing is lost.
- **A separate `docs/maintainers.md` file outside the site.** It would
  duplicate the site's purpose, with no navigation or search.

## Risks

- **Text lost in the move.** Mitigated by the coverage check and by
  section-by-section commits.
- **A broken link after rewriting.** Caught by `check_docs.py` (relative
  links) and review; absolute GitHub links are not fetched. The rewrite is
  mechanical, applied only to `skills/`, `intent/`, `spec/`, `plan/`,
  `scripts/`, `tests/`, `nix/` and `.github/` targets.
- **Bookmarks to old README anchors break.** The only in-repository one is
  updated. External bookmarks land on a README whose "Documentation" section
  points to the new places.
- **Skill-table check false negatives:** a table format the parser does not
  expect. It fails loudly rather than passing, and its tests fix the format.

## Verification

- The one-off coverage check passes, and its exceptions are listed in the
  PR.
- `python3 scripts/check_collection.py` passes, including the new
  skill-table check. Unit tests pass, including the new cases.
- `nix build .#docs` passes: the new pages and links are valid, and every
  page is in `SUMMARY.md`.
- `nix flake check`, `devenv shell check-fast` and `actionlint` pass.
- The new README is about 90 lines, and every section in the design is
  present.
- After merge: the site deploys, and the Maintain pages return 200.
