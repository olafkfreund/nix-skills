---
status: draft
issue: 19
author: olafkfreund
---

# Intent: Harden automated reference updates against review findings

## Problem

A code review of `main` (8660959) found six defects in the update and check
tooling. None can publish incorrect content: each one fails closed. Three of
them can still break or intermittently fail the weekly reference updates for
reasons unrelated to the change being published:

1. The NixOS Wiki update's self-check (`scripts/wiki.py` `lookup_check`) requires
   that the live wiki page `Garbage Collection` redirects to
   `Storage optimization`. If wiki editors change that redirect, every
   automatic wiki update fails.
2. `section()` in `scripts/update.py` switches fence state on any fence line,
   while `prose()` matches the fence character and length. A four-backtick
   block that contains a three-backtick line hides the headings after it, so a
   Nix manual update aborts with "Missing or ambiguous section".
3. `scripts/devenv.py` and `scripts/nixpkgs.py` call the GitHub API without
   authentication. Shared runners are limited to 60 requests per hour per IP,
   so updates can fail intermittently.

Three are minor:

4. A wiki `<redirect>` element with no `title` attribute raises
   `AttributeError` instead of the `ValueError` that all other malformed input
   raises.
5. Each of the six skill jobs in `check.yml` reruns the whole unit test suite.
6. A downloaded wiki dump is hashed three times.

## Proposed outcome

- A wiki edit to any one redirect cannot by itself block the automatic wiki
  update. Redirect-following is still tested, against fixtures.
- Headings after nested code fences are selected in the same way `prose()`
  treats fences, and a regression test covers the nested case.
- When a token is available, CI update runs authenticate their GitHub API
  calls. Local runs without a token behave as they do today.
- Malformed redirect metadata is reported as `ValueError`.
- The unit test suite runs once per CI check run, not once per skill.
- The dump is hashed only where the hash is actually verified.

## Affected users and systems

- Weekly `update.yml` runs for nix-language, devenv-project,
  nixpkgs-development and nixos-wiki.
- PR and push `check.yml` runs.
- Maintainers who run `scripts/update.py` locally.
- Generated skill content does not change. Consumers of the skills see no
  difference.

## Constraints

- Keep every existing fail-closed guarantee. No relaxation of hashes, limits,
  publication allowlists or immutable-policy checks.
- PR jobs stay read-only and secret-free (AGENTS.md). A token is only read in
  jobs that already receive `github.token`, and it is never required.
- No new third-party Python dependencies.
- Regenerated references for all skills must be byte-identical
  (`update.py --check` and `git diff --exit-code` still pass).
- The approved provider contract of issue #8 must not change without review.
  Moving the redirect assertion from the update path into tests is such a
  change, so this intent records it.

## Open questions

- Finding 1: should the update path keep a redirect check chosen from the
  retained records (any bundled redirect), or rely only on offline tests?
  The recommendation is to choose from the retained records, so the shipped
  helper is still exercised on real data.
- Finding 3: should update runs use `github.token` from the workflow (the
  recommendation, with no new secret), or stay unauthenticated and add a retry?
