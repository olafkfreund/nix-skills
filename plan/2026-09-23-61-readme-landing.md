---
status: approved
issue: 61
spec: spec/2026-09-23-61-readme-landing.md
---

# Plan: README as a landing page

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Correction to the intent and spec.** They say "eight" per-skill
maintenance sections. The README has **seven**:

| README heading | README line |
| --- | --- |
| devenv maintenance | 334 |
| Home Manager maintenance | 365 |
| microvm.nix maintenance | 382 |
| NixOS operations maintenance | 397 |
| nix-darwin maintenance | 417 |
| Nixpkgs maintenance | 432 |
| NixOS Wiki maintenance and lookup | 472 |

`nix-language` has no section of its own; its maintenance text sits in
"Development environment", which moves to `maintain/index.md`. The design is
otherwise unchanged.

**New README,** about 90 lines, in this order:
1. The title, the one-sentence description, and
   `**Documentation:** <https://olafkfreund.github.io/nix-skills/>`.
2. **What this is,** in 3 to 4 lines: skills for Claude Code, Codex,
   OpenCode and Antigravity, and skills, not agents.
3. **Get started,** three ways in:
   - try it: `nix run github:olafkfreund/nix-skills?dir=demo`, linking to
     the demo tutorial;
   - your NixOS machine: `nixosModules.agentic`, or `nix flake init -t
     github:olafkfreund/nix-skills#agentic-nixos`, linking to "Set up your
     own machine";
   - skills only: a snippet of the input plus `programs.nix-skills = {
     enable = true; agents = [ "claude" ]; };`, linking to "Install the
     skills".
4. **First prompt,** in a `text` block.
5. **Skills:** a table with the columns `| Skill | Purpose | Source and
   licence |`.
   - One row per `skills.json` name, linked as
     `[name](skills/name/SKILL.md)`.
   - Source and licence is the upstream name with its licence file link
     (`skills/<name>/LICENSE` or `COPYING`), or "hand-written, repository
     licence".
   - It ends with a link to the generated catalog.
6. **Documentation:** links to Tutorials, How-to guides, Reference,
   Explanation and Maintain.
7. **Contributing:** 2 lines, linking to CONTRIBUTING.md and AGENTS.md.
8. **Licence:** the repository licence, and "copied upstream material keeps
   its upstream licence and is not relicensed", linking to the sources
   section on the site.

**Where content moves.** Moved text is unchanged, with three exceptions:
- relative links become absolute `https://github.com/olafkfreund/nix-skills/blob/main/<path>`,
  or `/tree/main/<dir>` for directories;
- heading levels are adjusted;
- "this README" becomes "the README" or a link.

Code blocks move byte for byte.

| From the README | To |
| --- | --- |
| Getting started: install, table, check, prompt, examples | Already on `tutorials/getting-started.md` and `how-to/install.md`; add any sentence not yet present. |
| Getting started: user story | Appended to `tutorials/getting-started.md` as `## Next: agentic coding on NixOS`, linking to the demo and own-machine pages |
| Use, and Declarative installation on NixOS | Missing facts added to `how-to/install.md` (collision protection, rejected names and paths, per-skill package outputs and `default`, `directory` versus `agents`) and to `how-to/update-and-rollback.md` |
| Maintain intro and Development environment | `docs/src/maintain/index.md` ("Maintain the collection") |
| The seven maintenance sections | `docs/src/maintain/{devenv-project,home-manager,microvm-nix,nixos-operations,nix-darwin,nixpkgs-development,nixos-wiki}.md` |
| Automatic updates | `docs/src/maintain/automatic-updates.md`, with `explanation/updates.md` linking to it |
| Sources and licensing | `## Per-skill sources and licences` appended to `explanation/authored-and-generated.md` |

**`SUMMARY.md`** gains `# Maintain`, listing:
- Maintain the collection (`maintain/index.md`);
- Automatic updates;
- the seven skill pages in `skills.json` order.

**Skill-table check** in `scripts/check_collection.py`:
- It reads the first Markdown table in `README.md` whose header begins
  `| Skill |`.
- It collects the names from `[name](skills/name/SKILL.md)` links.
- If the table is missing, or the set differs from `skills.json`, it raises
  `ValueError("README skill table must match skills.json: missing […], extra […]")`.
- New tests in `tests/test_collection.py`: a match passes; a missing skill,
  an extra skill, and no table each fail.

**Links.**
- `CONTRIBUTING.md:143` becomes
  `https://olafkfreund.github.io/nix-skills/maintain/automatic-updates.html`.
- Any AGENTS.md or CONTRIBUTING.md mention of the README's maintenance
  sections is pointed at `docs/src/maintain/`.

## Steps

1. **Maintain pages.**
   - Create `docs/src/maintain/index.md`, the seven skill pages and
     `automatic-updates.md` by moving the README text with the link rewrite.
   - Add the `# Maintain` group to `SUMMARY.md`.
   - Link `explanation/updates.md` to the new automatic-updates page.

   → Verify: `nix build .#docs` passes. A one-off coverage script finds
   every normalised line of those README sections in the new pages.
2. **Sources and licensing, and the remaining user facts.** Append the
   per-skill section to `authored-and-generated.md`. Add the missing install
   facts, and the user-story section to `getting-started.md`.
   → Verify: `nix build .#docs` passes. The coverage script finds those
   README lines, and lists the exceptions (the hand-kept `ln -s` list, the
   `skills = [ … ]` list and the invocation line, replaced by the catalog)
   for the PR.
3. **Skill-table check and tests.**
   → Verify: the unit tests pass. The check still passes on the **current**
   README, which does have a `| Skill |` table, before the rewrite.
4. **Rewrite the README** as designed, and update the CONTRIBUTING link.
   → Verify:
   - `check_collection.py` passes, including the table check;
   - `wc -l README.md` is about 90;
   - every designed section is present;
   - no relative link in the README is broken.
5. **Full checks:**
   - unit tests;
   - `check_collection.py`;
   - `devenv shell check-fast`;
   - `nix flake check`;
   - `nix build .#docs`;
   - `actionlint`.

   Commit steps 1 to 4 separately, push, and open a PR with `Closes #61`.
   It lists the coverage check's exceptions.
   → Verify: CI is green and the PR is `CLEAN`. Do not merge without
   approval.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_collection.py
nix build .#docs
nix flake check
devenv shell check-fast
actionlint
wc -l README.md
```

The one-off coverage script (not committed) compares the old README
(`git show main:README.md`) with its new homes.

## Rollback

- **Before merge:** close the PR and delete the branch.
- **After merge:** `git revert` the commits. That restores the 605-line
  README and removes the Maintain pages, the added sections and the table
  check. There is no state outside the repository.
