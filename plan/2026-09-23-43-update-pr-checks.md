---
status: approved
issue: 43
spec: spec/2026-09-23-43-update-pr-checks.md
---

# Plan: CI on automated reference-update PRs

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Why.** Update PRs are opened by **Update references** with the Actions
`GITHUB_TOKEN`. GitHub creates their `pull_request` runs in an
approval-required state, which appears as zero jobs and "no checks". So
**Check** never ran on #22, #23, #32 or #36 until it was started by hand.
`main` has no branch protection.

**How.** The publish job starts **Check** itself through `workflow_dispatch`,
which GitHub always runs even from `GITHUB_TOKEN`. It uses no stored secret.
The approval-required `pull_request` run still appears, and may be ignored or
approved.

**Scope.**
- All eight skills in the `publish` matrix, and future ones automatically.
- Branch protection is out of scope, as an owner follow-up.
- No change to `check.yml`, `artifact.py`, allowlists, the generate job,
  skills, packages or modules.

**Permission.** `actions: write` is added to the `publish` job only. GitHub's
fine-grained permission table lists
`POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches` under
Actions: write. The workflow default stays `contents: read`.

**Step code.** Appended to the end of the existing "Update one branch and PR"
step, so it only runs when `changed == 'true'`, after `gh pr edit` or
`gh pr create`:

```bash
head=$(git rev-parse HEAD)
gh workflow run check.yml --ref "$UPDATE_BRANCH" -f ref="$head"
echo "Started Check for $UPDATE_BRANCH at $head"
```

- `--ref "$UPDATE_BRANCH"` attaches the check runs to the PR's head commit.
- `-f ref="$head"` pins the commit that is checked out.
- The per-skill concurrency group already serialises pushes to the branch.

**README.** In *Automatic updates*:
- **The permissions sentence** becomes: "only the publication job requests
  `contents: write`, `pull-requests: write` and `actions: write`, the last
  only to start **Check** on the update PR".
- **The paragraph from "Token-created PRs may not launch another workflow run
  automatically."** through the "If required checks remain pending…" line is
  replaced with text saying:
  - the publish job starts **Check** on each update PR's head commit, and the
    results appear on the PR;
  - GitHub also shows an approval-required `pull_request` run for
    token-created PRs, which may be approved or left alone, because the
    started **Check** is the validation;
  - confirm the **Check** is for the PR's current head commit before merging;
  - `main` is not protected, so never merge an update whose **Check** has not
    passed;
  - the fallback to re-run by hand is
    `gh workflow run check.yml --ref <update-branch> -f ref=<head-sha>`.

  The existing example `--ref main -f ref=automation/nix-reference-update`
  is replaced, because it does not attach checks to the PR head.
- The "Failed generation…" and "The initial Nix live updater…" lines stay.

### Deviation during implementation

The live run (step 4, run 35872976967) opened #44, #45 and #46, and started
**Check** runs 35873159037, 35873160335 and 35873160843. They ran as
`workflow_dispatch` with actor `github-actions[bot]`, on the exact head
commits `fa778c7`, `70cd489` and `052dcef`, and each passed 11 of 11 jobs.

However, the PRs' `statusCheckRollup` is `null`, and `gh pr checks` reports
"no checks". The head commit carries two check suites: the successful
dispatched one, and the `pull_request` one in `ACTION_REQUIRED`. GitHub does
not count a dispatched run in the PR's status. So the README sentence "so its
results appear on the PR" was wrong.

It is corrected to say:
- the results are attached to the head commit;
- how to read them (`gh run list --workflow check.yml --commit <sha>`);
- that approving the pending run gives the usual PR check.

The intent's "sees pass or fail on the PR like any other PR" is therefore
only partly met: the tests always run automatically, but the merge box needs
one approval click or a lookup by commit. The PR references #43 rather than
closing it, pending the owner's decision on that gap.

## Steps

1. **`.github/workflows/update.yml`.** Add `actions: write` to
   `jobs.publish.permissions`, and append the step code above to "Update one
   branch and PR".
   → Verify that `actionlint` is clean, that `git diff` touches only those
   two places, and that the workflow-level `permissions` is still
   `contents: read`.
2. **`README.md`.** Make the two *Automatic updates* edits above.
   → Verify that `check_collection.py` passes and that CONTRIBUTING's
   `#automatic-updates` anchor still resolves.
3. **Static checks.** `devenv shell check-fast`, `nix flake check`,
   `nix build .#nix-skills --no-link`.
   → All pass. Then commit and push the branch.
4. **Live proof** (the step you approved with this plan):
   `gh workflow run update.yml --ref ci/43-update-pr-checks`. The workflow
   definition comes from the branch, and content is still generated from
   `main` and published only through the existing artifact acceptance.
   → For each skill that reports `changed == 'true'`, confirm:
   - its update PR was opened or updated;
   - the publish log shows "Started Check for <branch> at <sha>";
   - a `workflow_dispatch` **Check** run with actor `github-actions[bot]`
     exists with that `head_sha`;
   - all 11 jobs finish;
   - the PR's head commit shows that check suite.

   If every skill is a no-op, record that in the PR and keep #43 open until
   the next scheduled Monday run proves it on a real update PR.

   Any update PRs this run creates are ordinary automation PRs. They are
   reviewed and merged only with your approval, as usual.
5. **PR.** Open it with `Closes #43` only if step 4 proved the change live;
   otherwise use `Refs #43`. Link the intent, spec and plan, and report the
   live-run evidence.
   → CI is green. Do not merge without your approval.

## Tests

```sh
actionlint
python3 scripts/check_collection.py
devenv shell check-fast
nix flake check
nix build .#nix-skills --no-link
```

Live: step 4, with evidence of the run ID, the head SHA, and the check-suite
conclusion on each updated PR.

## Rollback

- **Before merge:** close the PR and delete the branch. Any update PRs
  opened by step 4 are ordinary automation PRs and can be closed; the next
  scheduled run recreates them.
- **After merge:** `git revert` the commit. The publish job returns to
  `contents: write` and `pull-requests: write` without starting **Check**,
  and the README returns to the manual-dispatch instructions.
