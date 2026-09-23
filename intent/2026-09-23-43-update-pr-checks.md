---
status: draft
issue: 43
author: olafkfreund
---

# Intent: CI on automated reference-update PRs

## Problem

**Update references** (`.github/workflows/update.yml`) regenerates each
maintained skill every Monday. Its `publish` job opens or updates one PR per
skill using the Actions `GITHUB_TOKEN`. GitHub does not start other workflows
for events caused by that token, so **Check** (`.github/workflows/check.yml`)
never runs on these PRs.

**Observed on 2026-09-23.** #22, #23, #32 and #36 were open with "no checks
reported". Each needed a maintainer to run **Check** by hand
(`gh workflow run check.yml --ref <branch>`) before it could be merged
safely. All four then passed.

The README's *Automatic updates* section documents this as a known
limitation, with the manual command as the workaround. In practice:

- **Up to eight untested PRs a week.** Each weekly run can leave that many
  PRs needing a manual step before review. This is easy to forget, and it
  undoes the point of automating the updates.
- **Nothing enforces testing.** `main` has no branch protection and no
  rulesets. An update PR can be merged with no CI at all; only the process
  rule "do not merge untested" prevents it.
- **Validation that already runs is partial.** The `generate` job does run
  `check.py` for its skill and the unit tests, and `artifact.py accept`
  verifies the result. The full **Check** matrix does not run on the PR head:
  - the collection check;
  - every provider;
  - the flake check and the distribution builds.

## Proposed outcome

- **Automatic CI.** Every update PR shows a complete **Check** run on its
  exact head commit, started automatically when the PR is created or updated,
  with no manual step.
- **A clear result.** A reviewer sees pass or fail on the PR like any other
  PR. A failing update is visibly red rather than silently unchecked.
- **Accurate documentation.** The README's *Automatic updates* section
  describes the new behaviour, and drops or narrows the manual-dispatch
  workaround.

## Affected users and systems

- Maintainers who review and merge update PRs.
- `.github/workflows/update.yml` (the `publish` job), possibly
  `.github/workflows/check.yml`, and the README's *Automatic updates*
  section. Possibly workflow tests, if any cover these files; actionlint
  covers syntax.
- The GitHub repository's Actions settings, only if the chosen approach
  requires a change. Any change to settings is made by the owner, not by
  automation.
- No skill content, provider logic, publication allowlist, package or module
  changes. No host is changed.

## Constraints

- **Keep the publication boundary.** It is set by AGENTS.md, CONTRIBUTING.md
  and the approved provider contracts:
  - no `pull_request_target` execution;
  - PR jobs stay read-only with no secrets;
  - the default token permission stays read-only;
  - no allowlist is broadened to make an update pass;
  - the updater never merges or installs.
- **No personal access token.** The README states that none is required or
  configured. Adding a long-lived secret, such as a PAT or a GitHub App
  private key, is a security trade-off the approver must accept explicitly,
  not a default.
- **Least privilege.** Any added permission, for example to start a
  workflow, is scoped to the one job that needs it and justified in the spec.
- **Checks match what they test.** The run must test the PR's head commit,
  not the default branch or a moving ref, and the reviewer must be able to
  see which commit was tested.
- **No change to unrelated PR behaviour.** Human-opened PRs keep their
  current checks.
- **Verified in practice.** The change is proven by an actual update run that
  opens or updates a PR and shows checks on it. A green actionlint alone is
  not enough.

## Open questions

- **Tolerable trade-offs.** A workflow can start **Check** with the existing
  token, but the result may appear as a manual run rather than as the PR's
  own "pull_request" check. The alternative is a GitHub App token, so that
  update PRs behave exactly like human PRs, at the cost of a stored private
  key. Which trade-off is acceptable?
- **Branch protection.** Should `main` also get branch protection that
  requires the aggregate check, so untested merges become impossible rather
  than only discouraged? That is a repository setting the owner changes,
  possibly as a separate task.
- **Scope.** Should the same fix cover update PRs for the newer skills
  automatically (the matrix already lists all eight), and future providers
  as they are added?
