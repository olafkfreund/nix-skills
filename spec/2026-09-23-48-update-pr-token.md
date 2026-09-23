---
status: approved
issue: 48
intent: intent/2026-09-23-48-update-pr-token.md
---

# Spec: publish update PRs with a user token

## Facts

Checked on 2026-09-23.

- **Branch protection on `main`:**
  - required status check `collection-check`, from app 15368 (GitHub
    Actions), with `strict: false`;
  - pull request required, with 0 approvals;
  - `enforce_admins: true`;
  - force-pushes and deletion blocked.

  A direct push was rejected with `GH006`.
- **Repository secret `UPDATE_PR_TOKEN`** was set from
  `/run/agenix/api-github-token` (the agenix secret `api-github-token` in
  `~/.config/nixos/modules/secrets/api-keys.nix`). It is a classic token for
  `olafkfreund` with scopes including `repo`, `workflow`, `delete_repo`,
  `admin:org`, `admin:enterprise`, `admin:repo_hook`, `admin:public_key` and
  `admin:ssh_signing_key`, and GitHub reports no expiry for it. The owner
  accepted this over a token limited to this repository.
- **`update.yml`, job `publish`** (current):
  - permissions `contents: write`, `pull-requests: write` and
    `actions: write`;
  - `actions/checkout` with `fetch-depth: 0` and the default
    `persist-credentials: true`, which stores `GITHUB_TOKEN` in git config;
  - `artifact.py accept` runs, then the step "Update one branch and PR" with
    `GH_TOKEN: ${{ github.token }}`. That step:
    1. `git switch -C` the branch;
    2. commits;
    3. `git push --force-with-lease`;
    4. `gh pr edit` or `gh pr create`;
    5. `gh workflow run check.yml` (#47).
- **GitHub's rule for `GITHUB_TOKEN`:** events it triggers create no new runs,
  and PRs it creates or updates get approval-required `pull_request` runs.
  Events caused by another token, such as a personal token, trigger
  workflows normally.
- **`check.yml`** runs on `push`, `pull_request` and `workflow_dispatch`. A
  branch pushed with a personal token therefore gets both a `push` and a
  `pull_request` **Check**, exactly as human branches do today: each of the
  PRs #38, #40 and #42 showed 22 checks, 11 per event.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Missing secret.** Fail the step with a clear error. There is no fallback
   to `GITHUB_TOKEN`.
2. **Changing the token later.** The README explains that replacing the
   token with a fine-grained one limited to this repository (Contents:
   read/write, Pull requests: read/write) only means changing the secret's
   value. No workflow change is needed.

### `update.yml`, job `publish`

1. **Permissions.** Reduce them to `contents: read`. `GITHUB_TOKEN` no longer
   pushes, opens PRs or starts workflows. This removes `contents: write`,
   `pull-requests: write` and `actions: write` from the job.
2. **Checkout.** Add `persist-credentials: false`, so no token is stored in
   the job's git config. The repository is still fetched with
   `fetch-depth: 0`, so `--force-with-lease` has the remote-tracking refs it
   needs.
3. **"Update one branch and PR".**
   - **Where the secret goes.** Set `UPDATE_PR_TOKEN` and
     `GH_TOKEN: ${{ secrets.UPDATE_PR_TOKEN }}` in this step's `env` only.
     `artifact.py accept` and every earlier step never see the secret. This
     step runs only `git` and `gh`, with no repository or generated code.
   - **Fail on a missing secret:**

     ```bash
     [ -n "$UPDATE_PR_TOKEN" ] || { echo '::error::UPDATE_PR_TOKEN is not set; update PRs are published with it.'; exit 1; }
     ```

   - **Push with the token, without saving it:**

     ```bash
     auth=$(printf 'x-access-token:%s' "$UPDATE_PR_TOKEN" | base64 -w0)
     git -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth" \
       push --force-with-lease origin "$UPDATE_BRANCH"
     ```

     This is the same mechanism `actions/checkout` uses, applied to one
     command. The runner is ephemeral, and GitHub masks the secret in logs.
   - **`gh pr list`, `gh pr edit` and `gh pr create`** are unchanged. They
     now authenticate with `GH_TOKEN`, which is the user token.
   - **The #47 dispatch is removed** (the comment and three lines).
   - **Commit author** stays `github-actions[bot]`. Only the pusher and the
     PR opener change to `olafkfreund`.
   - **The `gh pr create` error text** is changed to: "Cannot open update PR
     with UPDATE_PR_TOKEN. Check that the secret is set, valid, and allowed
     to open pull requests on this repository."
4. **The `generate` job and `check.yml` are unchanged.** They never receive
   the secret.

### `README.md`, *Automatic updates*

Replace the text from "The repository must allow GitHub Actions to create
PRs…" through the manual re-run command block, including the paragraph #47
added, with text that says:

- update branches are pushed and PRs opened with the repository secret
  `UPDATE_PR_TOKEN`, so they get normal `push` and `pull_request` **Check**
  runs with no approval step;
- `main` is protected: a PR is required, `collection-check` must pass, and
  the rules include admins; so an update merges only after **Check** passes;
- **the accepted risk:** the secret currently holds a classic token with
  account-wide scopes. It is exposed only in the publish step that pushes
  and opens the PR. Replacing it with a fine-grained token limited to this
  repository (Contents and Pull requests read/write, with an expiry) is only
  a change to the secret's value;
- if the secret is missing or invalid, publication fails visibly, and the
  validated update branch or artifact is left for inspection;
- `GITHUB_TOKEN` stays read-only everywhere.

Keep the "Failed generation…" and "The initial Nix live updater…" lines.

## Alternatives rejected

- **A fine-grained token limited to this repository.** It is safer and was
  recommended, but the owner chose the existing agenix token. The README
  documents the swap as a change of secret value only.
- **Falling back to `GITHUB_TOKEN` and the dispatch when the secret is
  missing.** It hides a broken token, and keeps two publication paths that
  both need testing.
- **Keeping the #47 dispatch as well.** With a personal token the PR already
  gets `push` and `pull_request` runs, so a third run per update is wasted.
- **Passing the token to `actions/checkout` (`token:`).** That persists it in
  git config for every later step of the job, including `artifact.py
  accept`. The per-command header keeps it out of that step.
- **A GitHub App.** It needs an App to be created and a private key stored.
  The owner chose the existing token.

## Risks

- **The token leaks.** Because of its scopes, a leak would compromise the
  whole account. Exposure is limited to one step that runs only `git` and
  `gh`, on an ephemeral runner, with GitHub masking the secret in logs. All
  actions in the job are pinned by commit hash. The risk remains, and the
  owner accepted it.
- **Push authentication.** It could fail if GitHub rejects basic auth with
  `x-access-token` for a classic token. Classic tokens are accepted as the
  password with any username over HTTPS. The live run proves it, and a
  failure is visible.
- **More CI runs.** A push by the token also triggers a `push` **Check** on
  the automation branch. This matches human branches and is harmless.
- **`--force-with-lease` without a stored credential** uses the refs fetched
  at checkout. This is unchanged from today, because the fetch happens
  before credentials matter.
- **Token rotation or expiry.** Publication fails visibly, and the fix is to
  update the secret.

## Verification

- `actionlint`, `check_collection.py`, `devenv shell check-fast`,
  `nix flake check` and `nix build .#nix-skills --no-link` pass.
- `update.yml` review:
  - the secret appears only in the one step's `env`;
  - the job permissions are `contents: read`;
  - checkout has `persist-credentials: false`;
  - no `gh workflow run` remains.
- **Live, after approval at the plan stage.** Run **Update references** from
  the task branch. For any skill with changes, confirm:
  - its PR is opened or updated by `olafkfreund`;
  - `pull_request` **Check** runs start without approval and complete;
  - `collection-check` on the head commit passes;
  - the PR's `mergeStateStatus` is `CLEAN`, meaning branch protection is
    satisfied.

  If every skill is a no-op, record that and keep #48 open until the next
  scheduled run proves it.
- **This task's own PR** must pass the new branch protection. Its
  `collection-check` must pass before it can merge.
