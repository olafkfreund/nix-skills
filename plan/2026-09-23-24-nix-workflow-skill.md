---
status: draft
issue: 24
spec: spec/2026-09-23-24-nix-workflow-skill.md
---

# Plan: Authored skill for everyday Nix practice

Branch: `feat/24-nix-workflow-skill`, based on `main` 539c8ec.
Intent: `intent/2026-09-23-24-nix-workflow-skill.md`.
Spec: `spec/2026-09-23-24-nix-workflow-skill.md`.

## Approved decisions

- **D1 Package:** `skills/nix-workflow/` is authored guidance.
  - It has no `sources.json`, no third-party licence file, no helpers and no
    updater.
  - It contains `SKILL.md` and five references: `finding-things.md`,
    `shells.md`, `troubleshooting.md`, `configuration.md` and `ecosystem.md`.
  - `nix-workflow` is inserted into the sorted `skills.json`, which
    `nix/packages.nix` already reads.
- **D2 Links:**
  - Other skills are named in plain text, never linked, because
    `check_collection.py` rejects links that leave the package and skills are
    installed individually. Each mention adds "if installed; otherwise" with
    an upstream `https` URL.
  - Relative links point only inside the package.
- **D3 SKILL.md:**
  - Frontmatter is exactly `name: nix-workflow` and a one-line plain
    description with no `: `, ` #`, quotes or block scalars.
  - The body is short. The first step is to establish context: `nix --version`
    and the implementation (Nix, Lix or Determinate), whether `nix-command` and
    `flakes` are enabled, how the project pins inputs (flake, npins, niv or
    channels), and the repository's own instructions.
  - Six core rules, as specified:
    1. never brute-force `/nix/store`;
    2. choose between a devShell, `nix shell` and `nix run`;
    3. `nix log`, then search Nixpkgs issues and PRs, then cite the findings;
    4. the smallest adequate tool (`jq`, `awk`, `nix` subcommands) before
       Python;
    5. the client, daemon and remote builder split, with no trust or system
       change without authorization;
    6. check ecosystem facts upstream before recommending anything.
  - A routing table by role: developer, packager, Home Manager user (including
    darwin, #27), NixOS administrator (#27) and VM user, naming
    `devenv-project`, `nix-language`, `nixpkgs-development`, `home-manager`,
    `nixos-wiki` and `microvm-nix`.
  - One sentence per reference saying when to read it.
- **D4 References:** content exactly as listed in the spec's "References"
  section. The reported
  `find /nix/store/*something-* -iname libsomething.so` is the worked example
  in `finding-things.md`.
- **D5 Safety:** any command that changes system, trust or store state is
  labelled as needing the user's authorization. This covers editing
  `nix.conf`, `trusted-users`, substituters, garbage collection, switching and
  building a local nix-index database. No example performs it silently.
- **D6 Accuracy:**
  - Every command and flag shown must exist in Nix 2.34.8 (`--help`) or in
    the named tool's `--help`.
  - Version-sensitive commands are labelled, for example `nix store info`
    with `ping` as the older, deprecated alias.
  - `ecosystem.md` carries the check date, and marks archived repositories
    with their successor, as found by the GitHub API.
- **D7 README (not in the spec, added here):** list `nix-workflow` wherever the
  README enumerates skills: the table, the `ln -s` examples, the Codex
  invocation list and the Home Manager `skills = [ … ]` example. This is
  documentation of the registration only.
- **D8 External review:** the feedback's author reviews the draft skill. Their
  verdict is recorded in the PR before merge. The PR is not merged without
  that review, or without the maintainer explicitly waiving it.

## Steps

Each step is one commit with Conventional Commits and `(#24)`, and cites its
step number.

1. **Skeleton and registration:** add `skills/nix-workflow/SKILL.md` (D3) and
   insert `nix-workflow` into `skills.json`. Leave the reference links for
   step 2 so the checker does not fail on missing files.
   → Verify `python3 scripts/check_collection.py` reports 7 skills.
2. **References:** write the five references (D4, D5), and add their links and
   one-line "when to read" sentences to `SKILL.md`.
   → Verify `check_collection.py` passes (links and anchors inside the
   package) and `grep -rn '/nix/store' skills/nix-workflow` shows the path
   only in the anti-pattern explanation and example.
3. **Command audit (D6):**
   - Extract every command from `skills/nix-workflow` fences and inline code.
   - Check each subcommand and flag with `nix <cmd> --help` (local 2.34.8), and
     `nix run nixpkgs#nix-index -- nix-locate --help`, `gh search issues --help`
     and `gh search prs --help`, fixing anything that does not exist.
   - Save the audit table in the scratchpad for the PR.
   → Verify every row is marked ok, or labelled version-sensitive.
4. **Ecosystem audit (D6):** for each GitHub repository in `ecosystem.md`,
   query `gh api repos/<o>/<r> --jq '[.archived, .pushed_at]'`. Mark archived
   repositories with their successor, and write "Status checked on
   2026-09-23" into the table heading.
   → Verify no listed repository is archived without a marker.
5. **README (D7):** add `nix-workflow` to the skills table, the `ln -s`
   example, the Codex list and the Home Manager `skills` example.
   → Verify `grep -c nix-workflow README.md` is at least 4.
6. **Full verification:** run the commands under Tests below.
7. **PR and review (D8):**
   - Push with `git push -u origin feat/24-nix-workflow-skill`.
   - Open a PR with `Closes #24`, following `.github/pull_request_template.md`.
   - Link the intent, spec and plan.
   - Include the command audit table, the ecosystem check date, the six
     reviewer examples plus three non-triggers with their expected behaviour,
     and a request for the feedback author's review.
   → Verify the PR `Check` workflow is green. Stop there: merge only after the
   external review is recorded, or the maintainer explicitly waives it.

## Tests

```sh
python3 scripts/check_collection.py      # expect: Validated 7 registered skill packages
python3 -m unittest discover -s tests -p 'test_*.py'
nix flake check --no-update-lock-file
nix build .#nix-skills --no-link --print-out-paths \
  | xargs -I{} test -f {}/share/nix-skills/nix-workflow/SKILL.md
git diff --exit-code                     # after the checks, nothing generated or changed
```

Expected result: every command exits 0, and the built package contains
`share/nix-skills/nix-workflow/` with all five references.

Limitation: the trigger and behaviour examples are for reviewers, not an
automated test. No agent run is claimed unless it is actually performed and
reported, naming the agent and its version.

## Rollback

Revert the PR's merge commit, or the individual step commits. That removes
the package directory, the `skills.json` entry and the README lines. No
generated content, provider, lockfile or other skill is touched. Consumers
who pinned the new revision keep the skill until they update, and
`skills = [ … ]` users who named it must drop it after a revert.
