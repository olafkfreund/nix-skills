---
status: approved
issue: 48
author: olafkfreund
---

# Intent: publish update PRs with a user token

## Problem

**`main` is now protected** (set 2026-09-23, owner request):
- a pull request is required;
- the `collection-check` status from the GitHub Actions app must pass;
- the rules apply to admins;
- force-pushes and deletion are blocked.

**Update PRs bypass normal PR checks.** **Update references**
(`.github/workflows/update.yml`, job `publish`) pushes its branch and opens
PRs with the Actions `GITHUB_TOKEN`, so:
- GitHub creates the PR's `pull_request` runs in an approval-required state;
- the **Check** that the publish job starts through `workflow_dispatch`
  (#47) runs on the head commit, but it is not counted in the PR's status
  rollup. Whether it satisfies the new required check is unverified.

In practice, every weekly update PR needs a maintainer to click **Approve
workflows to run** before it can be merged, and the merge box shows no
result until then.

**The README is now wrong.** Its *Automatic updates* section says "`main` has
no branch protection" and "No personal access token is required or
configured".

## Proposed outcome

- **Normal PR checks.** Update PRs behave like human PRs:
  - pushing the update branch and opening the PR use a user token;
  - the PR gets ordinary `pull_request` **Check** runs with no approval
    step;
  - `collection-check` satisfies branch protection;
  - the result shows in the merge box.
- **No redundant run.** The `workflow_dispatch` **Check** added in #47 is
  removed, because the `pull_request` run replaces it.
- **Accurate README.** It states that `main` is protected and that update PRs
  are published with `UPDATE_PR_TOKEN`. It also states the token's scope and
  the accepted risk.

## Affected users and systems

- The repository owner, who reviews and merges update PRs.
- `.github/workflows/update.yml` (job `publish` only), and `README.md`
  (*Automatic updates*).
- The repository Actions secret `UPDATE_PR_TOKEN`, already set by the owner's
  instruction from the agenix secret `api-github-token` (owner
  `olafkfreund`).
- No change to skills, providers, `check.yml`, `artifact.py`, allowlists,
  packages or modules. No host is changed.

## Constraints

- **Accepted risk, recorded.** `UPDATE_PR_TOKEN` is a classic token with
  account-wide scopes, including:
  - `repo`, `workflow` and `delete_repo`;
  - `admin:org`, `admin:enterprise` and `admin:repo_hook`;
  - `admin:public_key` and `admin:ssh_signing_key`.

  GitHub reports no expiry for it. The owner explicitly chose it over a
  fine-grained token limited to this repository, on 2026-09-23. The design
  must therefore limit where the secret is exposed:
  - only in the steps of the `publish` job that push and open PRs;
  - never in `generate`, in `check.yml`, or in any step that runs upstream
    or generated content;
  - not persisted in git credentials longer than needed.
- **Keep the rest of the publication boundary.**
  - no `pull_request_target`;
  - PR jobs stay read-only with no secrets;
  - the workflow-level default permission stays read-only;
  - no broader allowlist;
  - the updater never merges;
  - the artifact acceptance step is unchanged, and still runs before
    anything is pushed.
- **Easy to undo.** Deleting the secret must fail the step visibly, not
  silently fall back to a behaviour nobody reviewed.
- **Verified live.** Proof is a real update run on an update PR:
  - `pull_request` **Check** runs created without approval;
  - `collection-check` satisfying branch protection;
  - the PR showing as mergeable.

## Open questions

- **Missing secret.** If `UPDATE_PR_TOKEN` is missing or revoked, should the
  publish job fail, or fall back to `GITHUB_TOKEN` plus the #47 dispatch?
  Proposed: fail, so a broken token is noticed.
- **Changing the token later.** Should the README and issue say how to
  replace it with a fine-grained token later, as a simple swap of the secret
  value that needs no workflow change?
