---
status: draft
issue: 48
spec: spec/2026-09-23-48-update-pr-token.md
---

# Plan: publish update PRs with a user token

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Context.**
- `main` is protected: a PR is required, `collection-check` from GitHub
  Actions (app 15368) must pass, the rules include admins, and force-pushes
  and deletion are blocked.
- The repository secret `UPDATE_PR_TOKEN` holds the agenix
  `api-github-token`: a classic token for `olafkfreund` with account-wide
  scopes and no reported expiry. The owner accepted this risk on 2026-09-23
  over a token limited to this repository.
- If the secret is missing, publication fails, with no fallback.
- The README documents swapping in a fine-grained token limited to this
  repository as a change of secret value only.

**`.github/workflows/update.yml`, job `publish`:**
1. `permissions:` becomes only `contents: read`. `contents: write`,
   `pull-requests: write` and `actions: write` are removed.
2. `actions/checkout` gains `persist-credentials: false`, and keeps
   `ref: default branch` and `fetch-depth: 0`.
3. Step "Update one branch and PR":
   - Its `env` gets `UPDATE_PR_TOKEN: ${{ secrets.UPDATE_PR_TOKEN }}`, and
     `GH_TOKEN` becomes `${{ secrets.UPDATE_PR_TOKEN }}`. No other step
     receives the secret.
   - The first line of `run` is:
     `[ -n "$UPDATE_PR_TOKEN" ] || { echo '::error::UPDATE_PR_TOKEN is not set; update PRs are published with it.'; exit 1; }`
   - The push becomes:

     ```bash
     auth=$(printf 'x-access-token:%s' "$UPDATE_PR_TOKEN" | base64 -w0)
     git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth" \
       push --force-with-lease origin "$UPDATE_BRANCH"
     ```

   - The `gh pr create` error message becomes: "Cannot open update PR with
     UPDATE_PR_TOKEN. Check that the secret is set, valid, and allowed to
     open pull requests on this repository."
   - The #47 dispatch (the comment line and three lines) is removed.
   - The commit author stays `github-actions[bot]`.
4. The `generate` job and `check.yml` are unchanged.

**`README.md`, *Automatic updates*.**
- **What is replaced:** the line "The repository must allow GitHub Actions
  to create PRs …", its follow-on lines about the setting, forks, the
  read-only default permission, "No personal access token is required or
  configured", and the GitHub docs link, plus the #47 paragraph and the
  manual re-run command block.
- **The new text says:**
  - update branches are pushed and PRs opened with `UPDATE_PR_TOKEN`, so
    they get normal `push` and `pull_request` **Check** runs with no approval
    step;
  - `main` is protected (PR required, `collection-check` must pass, admins
    included), so an update merges only after **Check** passes;
  - the accepted risk (a classic account-wide token, exposed only in the
    publish step that pushes and opens the PR), and that swapping in a
    fine-grained token limited to this repository (Contents and Pull
    requests read/write, with an expiry) is only a change to the secret's
    value;
  - if the secret is missing or invalid, publication fails visibly;
  - `GITHUB_TOKEN` stays read-only everywhere.
- The "Failed generation…" and "The initial Nix live updater…" lines stay.

## Steps

1. **`update.yml`.** Make the job edits 1 to 3.
   → Verify:
   - `actionlint` is clean;
   - `grep -n 'secrets\.' .github/workflows/*.yml` shows `UPDATE_PR_TOKEN`
     only in the publish step's `env`;
   - `grep -n 'workflow run' .github/workflows/update.yml` finds nothing;
   - the job's permissions are `contents: read`;
   - checkout has `persist-credentials: false`.
2. **`README.md`.** Make the *Automatic updates* replacement.
   → Verify that `check_collection.py` passes, CONTRIBUTING's
   `#automatic-updates` anchor resolves, and no text still claims "no
   branch protection" or "no personal access token".
3. **Static checks.** `devenv shell check-fast`, `nix flake check`,
   `nix build .#nix-skills --no-link`.
   → All pass. Then commit and push the branch.
4. **Open the PR** with `Refs #48`, linking the intent, spec and plan.
   → Its `collection-check` passes, and branch protection reports it
   mergeable. This is also the first PR through the new protection.
5. **Live test** (approved with this plan):
   `gh workflow run update.yml --ref ci/48-update-pr-token`.
   → For each skill with `changed == 'true'`, confirm:
   - the PR is opened or updated, with the author or updater `olafkfreund`;
   - `pull_request` **Check** runs exist for the head commit, and none is in
     `action_required`;
   - `collection-check` passes;
   - the PR's `mergeStateStatus` is `CLEAN`;
   - the job log does not contain the token (GitHub masks it; check that no
     `ghp_` appears).

   If every skill is a no-op, record that in the PR and leave #48 open until
   the next scheduled run.
6. **Report and wait.** Update the PR description with the live evidence.
   Switch it to `Closes #48` only if step 5 proved the change. Do not merge
   without your approval. Any update PRs from step 5 are merged only with
   your approval.

## Tests

```sh
actionlint
python3 scripts/check_collection.py
devenv shell check-fast
nix flake check
nix build .#nix-skills --no-link
grep -n 'secrets\.' .github/workflows/*.yml
grep -n 'workflow run' .github/workflows/update.yml   # expect no output
```

Live: step 5, with evidence of the run IDs, the PR numbers, the event and
conclusion of the head commit's check suites, and `mergeStateStatus`.

## Rollback

- **Before merge:** close the PR and delete the branch. The secret stays
  unused.
- **After merge:** `git revert` the implementation commit. That restores
  the #47 behaviour (the `GITHUB_TOKEN` push plus a dispatched **Check**).
  Branch protection then requires approving each update PR's pending run.
  To withdraw the token, run
  `gh secret delete UPDATE_PR_TOKEN --repo olafkfreund/nix-skills`. If it
  may have leaked, also revoke it on GitHub and rotate the agenix secret.
