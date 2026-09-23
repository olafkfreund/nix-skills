---
status: approved
issue: 43
intent: intent/2026-09-23-43-update-pr-checks.md
---

# Spec: CI on automated reference-update PRs

## Facts

Checked on 2026-09-23 against GitHub's documentation and this repository's
own runs.

- **GitHub's rules.** From
  [triggering a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow):
  - "Events triggered by the `GITHUB_TOKEN` will not create a new workflow
    run", except that "`workflow_dispatch` and `repository_dispatch` events
    always create workflow runs".
  - "When a workflow using `GITHUB_TOKEN` creates or updates a pull request,
    the resulting `pull_request` event creates workflow runs in an
    approval-required state." A user with write access starts them with
    **Approve workflows to run** in the PR's merge box.
  - To avoid that step, GitHub recommends "a GitHub App installation access
    token or a personal access token".
- **What this repository shows.**
  - On each of #22, #23, #32 and #36, the bot-created `pull_request` **Check**
    run had zero jobs while it waited for approval. When the PR was merged
    unapproved, it ended as `failure` ("workflow file issue").
    `gh pr checks` reported "no checks" while the PRs were open.
  - A manual run started with `gh workflow run check.yml --ref <branch>`
    attached all 11 check runs to the PR's head commit. On #36 the head
    commit `1f6182d` carries that successful `workflow_dispatch` check
    suite.
- **`check.yml`.**
  - It runs on `push`, `pull_request` and `workflow_dispatch`. The dispatch
    trigger has an optional `ref` input, and every job checks out
    `${{ inputs.ref || github.sha }}`.
  - Concurrency group:
    `check-${{ github.event.pull_request.number || github.ref }}-${{ inputs.ref }}`.
  - Default permission: `contents: read`.
- **`update.yml`.**
  - The `publish` job has `contents: write` and `pull-requests: write`, and
    one concurrency group per skill.
  - It runs only after `artifact.py accept` has verified the artifact.
  - Its "Update one branch and PR" step, when `changed == 'true'`:
    1. `git switch -C "$UPDATE_BRANCH"` from the default branch;
    2. commit and `git push --force-with-lease`;
    3. then `gh pr edit` or `gh pr create`.
- **`main`** has no branch protection and no rulesets.
- **Tests.** No test in `tests/` covers `update.yml` or `check.yml`.
  actionlint checks their syntax.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Trade-off.** Use the existing `GITHUB_TOKEN` to start **Check**, with no
   stored secret. The approval-required `pull_request` run still appears, and
   the README explains that it can be ignored or approved.
2. **Branch protection.** Out of scope. It is a repository setting for the
   owner, and is recommended as a separate follow-up.
3. **Scope.** All skills in the `publish` matrix, currently eight. Future
   providers are covered automatically, because the change lives in the
   shared step.

### Change

In `.github/workflows/update.yml`, job `publish`:

1. Add `actions: write` to the job's `permissions`, next to the existing
   `contents: write` and `pull-requests: write`. The workflow-level default
   stays `contents: read`. `actions: write` is the permission GitHub's REST
   endpoint "Create a workflow dispatch event" requires. It is scoped to this
   one job.
2. At the end of the existing "Update one branch and PR" step (so still only
   when `changed == 'true'`), after the PR is created or edited, start
   **Check** on the exact commit just pushed:

   ```bash
   head=$(git rev-parse HEAD)
   gh workflow run check.yml --ref "$UPDATE_BRANCH" -f ref="$head"
   echo "Started Check for $UPDATE_BRANCH at $head"
   ```

   - `--ref "$UPDATE_BRANCH"` makes the run's head commit the branch tip,
     which is `$head` because the per-skill concurrency group serialises
     publication. So the check runs attach to the PR's head commit.
   - `-f ref="$head"` makes every **Check** job check out exactly that
     commit, even if the branch moves before the jobs start.
   - A failure to start the run fails the step visibly. The PR has already
     been opened by then, so a maintainer sees both the PR and the error.

In `README.md`, *Automatic updates*: replace the paragraph that begins
"Token-created PRs may not launch another workflow run automatically" and
its example command. The new text says:

- The publish job starts **Check** on each update PR's head commit, and the
  results appear on the PR.
- GitHub additionally shows an approval-required `pull_request` run for
  token-created PRs. A maintainer may approve it or leave it; the started
  **Check** is the validation.
- Before merging, confirm that the **Check** results are for the PR's
  current head commit.
- `main` is not protected, so reviewers must not merge an update whose
  **Check** has not passed.

It also updates the permissions sentence: "only the publication job requests
`contents: write`, `pull-requests: write` and `actions: write`". The manual
command stays, as the fallback for re-running.

No change to `check.yml`: its existing `workflow_dispatch` trigger and `ref`
input are enough. No change to `artifact.py`, allowlists, the generate job,
or any skill.

## Alternatives rejected

- **Approve workflows to run, by hand, on each PR.** It gives a genuine
  `pull_request` check with no code change, but it is still a manual step per
  PR, which is the problem the intent describes.
- **A GitHub App or personal token for publication.** Update PRs would then
  behave exactly like human ones. But it adds a stored long-lived secret,
  contradicts the documented "no personal access token" design, and needs
  owner setup. The intent requires explicit acceptance for this, and none
  was given.
- **A `workflow_run` trigger in `check.yml`** that fires on **Update
  references** completion. It runs in the default branch's context, would
  need its own logic to find which branches changed, and moves towards the
  privileged-trigger patterns AGENTS.md forbids (`pull_request_target`-like
  execution).
- **The publish job running the checks itself.** That duplicates `check.yml`
  inside a job holding write permissions, and mixes validation with
  publication.
- **Having the publish job approve the pending `pull_request` run through
  the API.** It is not verified that `GITHUB_TOKEN` may approve runs it
  triggered, and a bot approving itself defeats the point of approval.

## Risks

- **Broader job permission.** `actions: write` also lets the publish job
  cancel or re-run workflows and start others. Mitigations:
  - it is scoped to the one job that already holds `contents: write`, a
    stronger permission;
  - the step starts only `check.yml`, by fixed name;
  - the job runs no code from the update branch; it checks out the default
    branch and runs only the verified artifact acceptance.
- **Two runs on the PR** (the pending approval run and the started **Check**)
  may confuse reviewers. Mitigated by the README text.
- **The run's head commit is wrong** if something else pushes the branch
  between the push and the dispatch. The branch is written only by this
  job, under its per-skill concurrency group. `-f ref="$head"` also pins the
  commit that is checked out.
- **Starting the run is rejected** if the permission is insufficient. The
  step fails visibly, and verification catches it on the first real run.
- **No update to test with.** If upstream sources have not changed, the run
  has nothing to publish and cannot exercise the new step. See Verification.

## Verification

- `actionlint` passes, and so do `devenv shell check-fast` and
  `nix flake check`. Nothing else is affected.
- **Live proof, after approval at the plan stage.** Before merging, run
  **Update references** from the task branch:
  `gh workflow run update.yml --ref ci/43-update-pr-checks`. The workflow
  file comes from the branch, and content is still generated from `main`.
  For every skill that has upstream changes, confirm:
  - an update PR is opened or updated;
  - a `workflow_dispatch` **Check** run was started by `github-actions[bot]`
    for that PR's head commit;
  - all its jobs finished, and the PR's head commit shows the check suite.
- **If every skill is a no-op,** record that, merge on the basis of static
  review and actionlint, and keep #43 open until the next scheduled Monday
  run shows the check on a real update PR.
