# Automatic updates

After the workflows reach the default branch, **Update references** runs each Monday at 06:17 UTC and on manual dispatch.
Each skill generates and validates with read-only permissions, then passes an
allowlisted artifact to a separate publication job. That job rejects stale bases,
symlinks, traversal, invalid hashes, instruction/selection changes, Nixpkgs evaluator/branch-policy changes, and changes to
the sibling skill. It updates `automation/nix-reference-update`,
`automation/devenv-reference-update`, `automation/home-manager-reference-update`,
`automation/microvm-nix-reference-update`, `automation/nix-darwin-reference-update`,
`automation/nixos-operations-reference-update`,
`automation/nixpkgs-reference-update`,
or `automation/nixos-wiki-reference-update`,
with at most one open PR per skill.
Artifacts, branches, and job concurrency are separate for each skill. No-op
artifacts are verified but produce no branch or PR.
It never merges or installs the result.
Reports identify changed selected inputs, coverage changes, and option/built-in metadata changes.
Changes to upstream's devenv setup skill are review signals; authored instructions are never automatically replaced.

Update branches are pushed, and update PRs opened, with the repository secret `UPDATE_PR_TOKEN`, so they get the same
`push` and `pull_request` **Check** runs as any other branch, with no approval step.
`main` is protected: a PR is required, `collection-check` from GitHub Actions must pass, and the rules include admins,
so an update can only merge after **Check** passes.
`GITHUB_TOKEN` stays read-only everywhere; the publication job only reads the repository with it.

`UPDATE_PR_TOKEN` currently holds a classic token with account-wide scopes, an accepted risk. It is exposed only to the
single publication step that pushes the branch and opens the PR, never to generation, artifact acceptance or **Check**,
and it is not stored in the job's git configuration.
To narrow it, replace the secret's value with a fine-grained token limited to this repository
(Contents and Pull requests: read and write, with an expiry); no workflow change is needed:

```sh
gh secret set UPDATE_PR_TOKEN --repo olafkfreund/nix-skills
```

If the secret is missing or invalid, publication fails with an error naming it.

Failed generation publishes no package. Failed PR creation leaves a validated update branch and an actionable workflow error.
The initial Nix live updater passed as a no-op. After merging the devenv addition, validate the first live run too; a no-op does not prove changed-source PR publication.
