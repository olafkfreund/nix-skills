---
status: draft
issue: 61
author: olafkfreund
---

# Intent: README as a landing page

## Problem

The documentation site is live (#56, #60) and covers onboarding, the demo
VM (#57), your own machine (#58), reference and explanation. The README has
not changed and still carries almost everything, 605 lines:

| Section | Lines | Also on the site? |
| --- | --- | --- |
| Getting started, including the per-agent table, examples and the user story | ~144 | Yes: Getting started, Install the skills, Fix skill discovery |
| Use (clone, pin, `ln -s` list, invocation) | 43 | Yes: Install the skills, Update and roll back |
| Declarative installation on NixOS | 72 | Mostly: Install the skills, plus the generated options page |
| Maintain → Development environment | 59 | Partly: Contribute (summary only) |
| Maintain → eight per-skill maintenance sections | ~200 | No |
| Automatic updates | 40 | Yes: How updates work, Update schedule, Narrow the update token |
| Sources and licensing | 47 | Partly: Hand-written and generated references, Skill catalog |

The problems:

- **Too long for its purpose.** Visitors to the GitHub page see a
  605-line document. The four things they need are buried: what this is,
  how to try it, how to install it, and where the documentation is.
- **Duplicated content drifts.** The site's version and the README's
  version of the same instructions are already maintained twice. Earlier
  tasks (#37, #41, #48, #54, #57, #58) each had to update both, or chose
  one and left the other stale. The README still has no mention of the demo
  VM or the starter template, the two easiest ways in.
- **Hand-kept lists.** The README keeps its own `ln -s` list, its own Home
  Manager `skills = [ … ]` example and its own invocation line, each of
  which must list every skill. The site's catalog is generated from
  `skills.json`.
- **Maintainer detail sits in the user entry point.** About 260 lines are
  for maintainers: the development environment and the eight per-skill
  maintenance sections, covering provider commands, selection rules,
  regeneration and review signals. Users rarely need them, and they have no
  other home: neither the site nor CONTRIBUTING has them.
- **Licensing detail matters but is scattered.** The per-skill source and
  licence paragraphs, with design-history links, are important for
  provenance, but only the README has them in full.

## Proposed outcome

- **A short landing page.** It says:
  - what nix-skills is and who it is for;
  - the three ways in, with one command each: try the demo VM, set up your
    own machine (module or template), or install only the skills;
  - the start prompt;
  - a skill list;
  - clear links into the site for everything else;
  - where to contribute, and the licence.
- **Nothing is lost.** Every fact currently in the README either stays,
  already exists on the site, or moves to a maintained home:
  - maintainer and per-skill maintenance detail goes to CONTRIBUTING or to
    maintainer pages on the site;
  - per-skill sources and licensing go to the site or CONTRIBUTING, next to
    the catalog.
- **No hand-kept lists of every skill** in the README, where the site's
  generated catalog can serve instead, or the list is checked.
- **Links keep working.** CONTRIBUTING's `README.md#automatic-updates` link
  and any other inbound anchors are updated.

## Affected users and systems

- Everyone who lands on the GitHub repository page.
- Maintainers, who look for maintenance instructions in their new place.
- Files: `README.md`; the new homes for moved content (`CONTRIBUTING.md`,
  or new pages under `docs/src/` such as a Maintain section); and
  `docs/src/SUMMARY.md` if pages are added.
- No change to skills, modules, packages, providers, updaters, templates or
  CI behaviour.

## Constraints

- **Keep provenance and licensing statements.** The per-skill statements
  that the repository does not relicense upstream material, with licence
  links, must remain easy to find from the README, even if moved.
- **Links and anchors stay valid.** `check_collection.py` validates the
  README, including the Nix style rules. `nix build .#docs` validates the
  site. Links from CONTRIBUTING into the README are updated.
- **Maintainer instructions stay accurate.** Moving the per-skill
  maintenance sections must not change their commands or meaning. Moving
  is not rewriting.
- **One task, reviewable.** The move is split into logical commits, so a
  reviewer can compare old and new text section by section.
- **Existing rules still apply:** the intent → spec → plan gates, and
  checks green before merge.

## Open questions

- **Where does maintainer detail go?** A "Maintain" section on the site
  (a page per provider skill, generated or hand-written), or
  CONTRIBUTING.md, which already holds contributor rules?
- **Skill list on the landing page.** A short hand-kept table with a
  consistency check against `skills.json`, or only a link to the generated
  catalog on the site?
- **Sources and licensing.** Move the per-skill paragraphs to the site's
  "Hand-written and generated references" page, or keep a compact licence
  table in the README with the detail on the site?
