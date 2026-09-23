# Working on nix-skills

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the collection.

## Workflow

- Start with an issue and a task branch (`feat/<issue>-<slug>` or equivalent).
  Use Conventional Commits; never commit directly to main.
- Tasks tracked as issues or touching multiple files require three artifacts
  named `YYYY-MM-DD-<issue>-<slug>.md`: `intent/` (why), `spec/` (what),
  then `plan/` (how). Each starts with `status: draft` frontmatter and links
  its predecessor. Commit each stage and stop for human review before the next.
- Never self-approve. Record each human approval in its own commit, changing
  only that stage to `status: approved`. Implement only an approved plan.
  Cite its current step; update deviations with the implementation commit.
- Typos, lock-only bumps and one-line configuration changes are exempt.
  Recurring generated-only updates follow their already-approved provider
  contract; changes to that contract require review.
- Read before editing, check Git status, make small reversible changes, run
  relevant tests, and report actual evidence and limitations. Open a PR linking
  all artifacts with `Closes #<issue>`. Do not merge untested or without approval.

## Layout and boundaries

- `skills/<name>/`: portable complete packages. Keep instructions focused;
  link supporting resources and retain source attribution and licenses.
- `skills.json`: sorted unique skill names, not commands or updater settings.
- `scripts/check_collection.py`: offline generic metadata/resource validation.
- `scripts/check.py`, `update.py`, provider modules, `artifact.py`: explicit
  maintained-source validation and tightly scoped automated publication.
- `flake.nix`, `nix/`: data packages, the documentation site and opt-in Home Manager installation.
- `demo/`: separate flake (own `flake.lock`) for the disposable demo VM and its offline
  VM test; `.github/workflows/demo.yml` runs it and is not a required check.
- `docs/`: mdBook site sources; `nix build .#docs` generates the catalog, options and
  update schedule pages and checks links and Nix style. Never edit generated pages.
- Root `devenv.*`: contributor tools; `tests/devenv/` is a separate provider
  fixture. The environment and distribution locks are updated independently.

Registering a skill must not enroll an updater. Never execute contributed
helpers during metadata validation. PR jobs are read-only, have no secrets,
and cannot publish or install. Do not introduce `pull_request_target` execution.
Do not broaden publication allowlists to make a failing update pass.

## Checks

```sh
devenv shell check-fast
nix flake check
nix build .#nix-skills --no-link
nix eval .#packages.aarch64-linux.nix-skills.drvPath --raw
devenv shell check-providers
```

`check-fast` runs collection validation, Python unit tests and actionlint.
Provider regeneration checks require upstream network/cache access; failures
are failures, not skipped tests. See CONTRIBUTING for direct commands.
Stage new Nix files before Git-flake evaluation. Never activate a test home,
rebuild the host, install skills or grant `devenv allow` as part of validation.
Consumers using Home Manager as a NixOS module rebuild through NixOS, never
`home-manager switch`.
