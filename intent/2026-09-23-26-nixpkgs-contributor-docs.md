---
status: draft
issue: 26
author: olafkfreund
---

# Intent: Nixpkgs contributor guidance and review tools

## Problem

The `nixpkgs-development` skill quotes selected chapters of the Nixpkgs manual:
stdenv, overrides, build helpers and library APIs. A user who will rely on the
collection reported that it lacks the guidance contributors actually follow
when changing Nixpkgs:

- The repository's own contributor documents are not bundled or pointed to.
  These are `CONTRIBUTING.md`, `pkgs/README.md` (package conventions, reviewing
  and updating), `pkgs/by-name/README.md` (the directory layout new packages
  must use), `lib/README.md` and `nixos/README.md`. They describe commit
  message format, package naming and placement, how to update and review
  packages, and what reviewers expect. The manual does not cover this.
- Agents do not know the standard contributor tools:
  - `nixpkgs-review`, which builds the packages a pull request affects;
  - `nixpkgs-update`, the bot behind most automated version-bump pull requests.

  So they build and review changes by hand, or misread bot pull requests.
- When a package fails, the skill does not send agents to search Nixpkgs issues
  and pull requests first. The new `nix-workflow` skill (#24) covers this in
  general, but the packaging skill should say it where packaging happens.

The two upstream files that matter most, `CONTRIBUTING.md` and
`pkgs/README.md`, are each around 55 KB, too large to bundle whole.

## Proposed outcome

An agent using `nixpkgs-development` on a change intended for Nixpkgs itself:

- follows the repository's conventions for commit messages, package placement
  (`pkgs/by-name`), naming, and updating and reviewing packages, from pinned
  excerpts of the contributor documents;
- knows when and how to use `nixpkgs-review` (for a local change or a pull
  request) and what `nixpkgs-update` pull requests are, and reads its own
  results before reporting;
- searches Nixpkgs issues and pull requests for a failure before proposing a
  workaround.

Excerpts stay revision-pinned and regenerate automatically with the rest of
the skill, like today's references.

## Affected users and systems

- Users and agents of `nixpkgs-development`, both people contributing to
  Nixpkgs and people packaging in their own flakes.
- `scripts/nixpkgs.py` and its tests, if the provider has to learn to excerpt
  these files.
- `skills/nixpkgs-development/` (references, `SKILL.md`, `sources.json`) and
  the weekly Nixpkgs update PRs, whose content grows.

## Constraints

- **The selection is reviewed policy.** Automation cannot change it
  (`immutable_policy`), so adding sources goes through this task's review.
- **The provider hard-codes its outputs.** It has four output references and
  requires an mdBook-style anchor for every section
  (`scripts/nixpkgs.py:14,460`). The contributor documents are plain GitHub
  Markdown, so the spec must decide how to select from them. The change must
  keep every existing fail-closed check.
- **Excerpt, don't copy whole files.** Keep only sections relevant to agents,
  and keep the references loadable.
- **Licence:** Nixpkgs is MIT, and the existing COPYING and attribution
  continue to apply.
- **Authored text** (tool pointers and the search instruction) belongs only in
  `SKILL.md`, the one authored file a maintained package allows.
- **The tools are guidance only.** `nixpkgs-review` builds many packages and
  can post comments to GitHub. The skill must not tell an agent to run it,
  post a review or comment on a pull request without the user's authorization.
- **Regeneration stays reproducible:** `update.py --skill nixpkgs-development
  --check` must pass at the pinned revision.

## Open questions

- **Where the excerpts go:** a new `contributing` reference, or the existing
  `packaging` reference? The recommendation is a new reference, so contributor
  process stays separate from build mechanics.
- **Which sections:** the recommendation is commit conventions and PR
  expectations from `CONTRIBUTING.md`, conventions, update and review
  guidance from `pkgs/README.md`, and all of `pkgs/by-name/README.md`. Point to
  `lib/README.md` and `nixos/README.md` by link only, since they matter to
  fewer users.
- **Tool depth:** should `nixpkgs-review` get a short authored usage section in
  `SKILL.md`, or only a pointer to its upstream README? The recommendation is a
  short section: `pr`, `wip` and reading its report.
