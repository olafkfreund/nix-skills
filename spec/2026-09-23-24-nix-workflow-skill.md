---
status: draft
issue: 24
intent: intent/2026-09-23-24-nix-workflow-skill.md
---

# Spec: Authored skill for everyday Nix practice

The intent was approved without answers to its open questions, so this spec
uses the proposed defaults. Reject any of them at this review:

- The skill is named `nix-workflow`.
- Routing by role lives in this skill, not in a separate entry skill.
- The reviewer who gave the feedback is asked to check the draft before merge.

## Design

### Package

`skills/nix-workflow/` is an authored skill. It has no `sources.json`, no
licence file for third-party text (there is none), no helpers and no updater.
Its name is added to the sorted `skills.json`; `nix/packages.nix` reads that
file, so the flake package and the Home Manager module include the skill
without other changes.

```text
skills/nix-workflow/
  SKILL.md
  references/finding-things.md
  references/shells.md
  references/troubleshooting.md
  references/configuration.md
  references/ecosystem.md
```

`scripts/check_collection.py:58-71` rejects links that leave the package, and
skills are installed individually. So other skills are named in plain text and
never linked, and each mention says what to do when that skill is not
installed. External links point to upstream documentation or repositories
over `https`.

### SKILL.md (entrypoint, short)

- **Frontmatter:** exactly `name` and `description`. The description is one
  plain line, for example: "Choose Nix commands, locate store paths and
  libraries, use development shells, debug builds, configure Nix and navigate
  ecosystem tools." It avoids the characters CONTRIBUTING.md forbids.
- **First step:** establish the context before advising. That is the Nix
  implementation and version (`nix --version`; Nix, Lix and Determinate Nix
  differ), whether `nix-command` and `flakes` are enabled, and whether the
  project uses flakes, npins/niv or channels. Read the repository's own
  instructions first.
- **Core rules**, one or two lines each, with detail in the references:
  1. **Never search `/nix/store` by brute force.**
     - `find` or `ls` over `/nix/store` only reflects what happens to be in the
       local store. It misses packages that were never built, and it breaks
       reproducibility when a found path is hard-coded.
     - Use `nix-locate` for "which package provides this file", and store
       queries for "what does this path depend on".
     - Refer to dependencies through Nix expressions (`${pkgs.foo}/lib`,
       `lib.makeLibraryPath`), not literal store paths.
  2. **Pick the right environment.** Use a project `devShells` output with
     `nix develop`, an ad-hoc tool with `nix shell`, and a single program with
     `nix run`. Never install into the host profile to satisfy one project.
  3. **Search before inventing.** For a build or packaging failure, read
     `nix log`, then search NixOS/nixpkgs issues and pull requests for the
     distinctive error text. Cite what was found before proposing a workaround.
  4. **Use the smallest adequate tool.** Prefer `jq`, `awk`, `sed`, `grep` and
     `nix` subcommands (`nix eval --json`, `nix derivation show`) for
     inspection and transformation. Only write Python or another script when
     the logic actually needs it.
  5. **Know where a setting lives.** A setting belongs to the client, the
     daemon or a remote builder. Only a trusted user can change some of them.
     On NixOS and nix-darwin, Nix configuration is declarative. Never edit
     `/etc/nix/nix.conf`, add trusted users, add substituters, collect garbage
     or switch a system without explicit authorization.
  6. **Treat ecosystem facts as perishable.** Before recommending a tool or
     lang2nix project, check its upstream repository: whether it is archived,
     when it was last released, and whether it has a successor.
- **Routing by role**, a plain-text table:

  | Role | Typical need | Where to look |
  |---|---|---|
  | Developer | A project environment | This skill's shells reference; `devenv-project` for devenv; `nix-language` for expressions |
  | Packager | A derivation or override | `nixpkgs-development` |
  | Home Manager user, including on darwin | A user configuration | `home-manager`; darwin specifics are tracked in #27 |
  | NixOS administrator | System configuration and rebuilds | `nixos-wiki` and the NixOS manual; system operations are tracked in #27 |
  | VM user | A declarative microVM | `microvm-nix` |

  Each named skill is followed by "if installed; otherwise use its upstream
  documentation", with the upstream URL.
- **Reference links:** a sentence per reference saying when to read it.

### References (detail, read on demand)

- **`finding-things.md`:**
  - `nix-locate` from nix-index, including that it needs a database. A
    prebuilt database (nix-index-database) avoids a long local indexing run,
    and that run needs the user's consent.
  - `nix search` and search.nixos.org for packages and options.
  - `nix path-info -r` / `-S`, `nix-store -q --references`, `--referrers` and
    `--tree`, `nix why-depends`, `nix derivation show`, and `nix eval`.
  - `comma` (`,`) for one-off runs, noting that it also relies on the database.
  - A worked example: the reported `find /nix/store/*something-* -iname
    libsomething.so` rewritten as `nix-locate` plus a Nix-expression reference.
- **`shells.md`:**
  - The `devShells.<system>.default` output, `nix develop` (including
    `--command`) and `nix develop .#name`.
  - `nix shell nixpkgs#pkg`, `nix run`, and legacy `nix-shell` and `-p` for
    non-flake projects.
  - direnv with `use flake`, and how it differs from devenv's own activation.
  - What does and does not carry into the shell: build inputs, shell hooks and
    environment variables.
  - Why host installation does not change a project's pinned inputs.
  - For devenv projects, hand over to `devenv-project`.
- **`troubleshooting.md`:**
  - Reading `nix log`, `--keep-failed`, `-L` and `--print-build-logs`.
  - Separating evaluation errors from build errors, and
    `--show-trace` for evaluation errors.
  - Searching, with example commands:
    `gh search issues --repo NixOS/nixpkgs "<error text>"` and
    `gh search prs --repo NixOS/nixpkgs "<package>"`, plus the web search forms.
  - The NixOS Discourse, and Hydra build status for "is it broken upstream?".
  - Reporting: cite issue and PR numbers, and say whether a fix exists on the
    user's channel or pin.
  - What not to do: disable the sandbox, checks or hardening to hide a
    failure, or pin random commits without saying so.
- **`configuration.md`:**
  - Configuration sources and precedence: `/etc/nix/nix.conf`,
    `~/.config/nix/nix.conf`, `NIX_CONFIG`, command-line `--option`, and
    `nix config show` to see the result.
  - The client and daemon split in multi-user installs. Some settings only
    take effect if the user is trusted (`trusted-users`), and substituters
    need matching `trusted-public-keys`.
  - `nix store info` (or `ping` on older versions) to see which store a
    command talks to.
  - Remote builders: `builders`, `/etc/nix/machines`, `ssh-ng`, and the
    matching `system` and `features` fields.
  - NixOS `nix.settings`, nix-darwin, and Home Manager `nix.settings`:
    declarative owners whose generated files must not be edited by hand.
  - Everything that changes trust or system state is presented as a proposal
    for the user.
- **`ecosystem.md`:** a table of tools, one line each, giving purpose, when to
  use it and the upstream URL. The table is headed "status checked on
  <date>; verify before recommending". It covers:
  - build and deploy helpers: nh, nix-output-monitor, nvd, nix-diff,
    nix-tree and nix-eval-jobs;
  - pinning: flakes, npins and niv;
  - flake frameworks: flake-parts and flake-utils, plus when not to use one;
  - Nix implementations: Nix, Lix and Determinate Nix;
  - lang2nix tools, starting with "prefer the Nixpkgs language builder first
    (see `nixpkgs-development`)", then common tools per ecosystem with their
    checked status. Archived projects are marked as such, with their successor.

### Style

- Instructions are imperative and short. Commands are shown in fenced
  examples, which `check_collection.py` treats as examples.
- No command in the skill modifies the system or trust settings without being
  labelled as needing authorization.

## Alternatives rejected

- **Add this guidance to the existing skills' `SKILL.md` files.** The
  maintained packages allow only `SKILL.md` as authored content
  (`scripts/check.py`), and `SKILL.md` must stay short. The topics also span
  every skill.
- **Quote wiki or nix.dev pages instead of authoring.** Those sources do not
  cover these anti-patterns or the ecosystem map. nix.dev idioms are tracked
  separately as #25.
- **A separate entry skill (`nix-start`) for routing by role.** It would add a
  second skill that must trigger on the same prompts, and fewer skills is
  simpler. It can be split out later if routing grows.
- **One skill per role now.** The missing role content (darwin, NixOS
  operations) is tracked as #27. This skill routes to it once it exists.
- **A helper script to find files or libraries.** CONTRIBUTING.md prefers
  instructions, and `nix-locate` and store queries already exist.
- **Link to sibling skills.** The checker rejects escaping links, and a
  sibling may not be installed.

## Risks

- **Stale ecosystem facts.** Mitigated by the dated status header, the
  per-tool upstream links, and rule 6 (check before recommending). It is not
  eliminated; the table needs occasional review.
- **Trigger overlap with existing skills.** The description is scoped to
  command-line practice, and the routing table hands over explicitly. This is
  checked with the non-trigger examples below.
- **Version-specific commands.** For example, `nix store ping` was renamed to
  `nix store info`, and experimental-feature requirements differ. Every
  command is checked against the local Nix 2.34.8 `--help`, and
  version-sensitive ones are labelled.
- **Authored guidance can be wrong.** Mitigated by the external review and the
  command audit. Hosts: none; this is a data-only package change.

## Verification

- **Checks:**
  - `python3 scripts/check_collection.py` passes with 7 registered skills.
  - `python3 -m unittest discover -s tests -p 'test_*.py'` passes.
  - `nix flake check --no-update-lock-file` and
    `nix build .#nix-skills --no-link` pass, and the built package contains
    `share/nix-skills/nix-workflow/`.
- **Command audit:** every command in the skill exists with the shown flags,
  checked against `nix <cmd> --help` on Nix 2.34.8, and `nix-locate --help`
  and `gh search --help` via `nix run nixpkgs#…`. The result is recorded in
  the PR.
- **Ecosystem audit:** each listed repository is checked with the GitHub API
  for its `archived` flag and latest release or commit date. The check date is
  written into `ecosystem.md`.
- **Reviewer examples** (in the PR), each with the expected behaviour:
  1. "Where is libssl.so on my system? I need it for a binary."
     Expected: `nix-locate` or a package reference, and no `find /nix/store`.
     For running a foreign binary, defer to the user's local policy (for
     example `nix-ld`) rather than hard-coding a store path.
  2. "Set up a dev environment for this repo; it has a flake.nix."
     Expected: inspect `devShells`, then run `nix develop`, and do not install
     into the host profile.
  3. "Package X fails to build with <error>."
     Expected: `nix log`, then a search of Nixpkgs issues and PRs, then a
     cited finding before any workaround.
  4. "Extract the version field from this flake.lock."
     Expected: a `jq` one-liner, not a Python script.
  5. "Why is my substituter ignored?"
     Expected: check the client/daemon split, `trusted-users` and
     `trusted-public-keys`, and propose changes without making them.
  6. "Should I use poetry2nix for my Python project?"
     Expected: check the upstream status, prefer the Nixpkgs builders, and
     name the successor if the project is archived.
  - Non-triggers: "What does `rec` do?" (`nix-language`); "Write an
    overrideAttrs for this package" (`nixpkgs-development`); "Add a service
    to devenv.nix" (`devenv-project`).
- **External review:** the reviewer who gave the feedback is asked to read the
  draft. Their verdict is recorded in the PR before merge.
