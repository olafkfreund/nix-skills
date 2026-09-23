# Narrow the update token

Update pull requests are pushed and opened with the repository secret
`UPDATE_PR_TOKEN`, so they get normal pull request checks. It currently
holds a classic token with account-wide scopes, an accepted risk recorded
in the design history. This guide replaces it with a token that can only
touch this repository.

## 1. Create a fine-grained token

On GitHub, go to **Settings → Developer settings → Personal access tokens →
Fine-grained tokens → Generate new token**, and choose:

- **Repository access:** only `olafkfreund/nix-skills`;
- **Permissions:** Contents *read and write*, Pull requests *read and
  write* (Metadata *read* is added automatically);
- **Expiration:** a date you will notice, for example 90 days.

## 2. Replace the secret

```sh
gh secret set UPDATE_PR_TOKEN --repo olafkfreund/nix-skills
```

Paste the new token when prompted. No workflow change is needed.

## 3. Verify

Run **Update references** (`gh workflow run update.yml`). For any skill
with upstream changes, the update pull request should be opened by your
account and show normal checks. If the secret is missing or lacks
permission, the publication step fails with an error naming
`UPDATE_PR_TOKEN`.

Replacing the secret removes the old token from this repository. Revoke the
old token on GitHub only if nothing else uses it; a token kept in a secrets
store such as agenix is often shared with other tools.
