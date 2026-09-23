---
status: draft
issue: 54
author: olafkfreund
---

# Intent: stop two common LLM mistakes in Nix

## Problem

User feedback names the two mistakes they see most often when LLMs work
with Nix:

1. **Brute-force store searches.** For example:

   ```sh
   find /nix/store/*something-* -iname libsomething.so
   ```

   This only sees what happens to be on this machine, and cannot tell which
   path belongs to the user's pin. A store path copied from it breaks on the
   next update. The right questions are "which package provides this file?"
   (`nix-locate`) and "how do I refer to it?" (`${pkgs.foo}/lib`,
   `lib.makeLibraryPath`).
2. **Quoting attribute names that do not need it.** For example
   `pkgs."foo-bar"`, `"foo-bar" = …` or `packages."x86_64-linux"`. The Nix
   manual's identifier grammar is `[A-Za-z_][A-Za-z0-9_'-]*`, so dashes,
   digits after the first character, underscores and apostrophes are all
   fine without quotes. Quotes are needed only for:
   - a name outside that grammar, such as `".config/foo"`, `"2.0"` or
     `"a.b"`;
   - a keyword (`assert else if in inherit let or rec then with`);
   - interpolation (`"${x}"`).

What the collection does today (checked 2026-09-23):

- **(1) is covered in only one place:** `nix-workflow` rule 1 ("Never search
  `/nix/store` by brute force") and `references/finding-things.md`, which
  quotes that exact command as the counterexample. An agent that loads only
  `nixpkgs-development`, `home-manager`, `nixos-coding-agents` or another
  skill never sees the rule, although those are the tasks where library
  paths come up.
- **(2) has no guidance at all.** `nix-language` links to the manual's
  identifier page but does not include it or state the rule.
- **Copied upstream references model the bad habit.** Authored content (the
  README, `nix-workflow`, `nixos-coding-agents` and every `SKILL.md`) has no
  unnecessary quotes. But the verbatim upstream references have 9, in
  `devenv-project`, `home-manager`, `microvm-nix` and `nix-darwin`: for
  example `home.services."php-fpm"`, `darwinConfigurations."Johns-MacBook"`
  and `systemd.network.netdevs."br0"`. Agents imitate the examples they
  read.
- **Nothing checks for either pattern.** `scripts/check_collection.py`
  validates metadata and links, not Nix style. A future authored change
  could reintroduce either pattern unnoticed.

## Proposed outcome

- **Guidance where agents write Nix.** Any skill in the collection that
  writes Nix or deals with libraries and store paths states both rules
  briefly, or points to where they are stated, so the agent sees them
  whichever skill it loaded.
- **The rules are precise.** They are stated with the exact identifier
  grammar and keyword list, so agents also do not over-correct by removing
  quotes that are required.
- **Upstream examples are labelled, not rewritten.** Skills whose references
  quote upstream examples tell the agent not to copy that quoting style. The
  verbatim upstream text stays unchanged.
- **An offline check.** It flags both patterns in authored content: the
  README, `SKILL.md` files, and authored references. The deliberate
  counterexample in `finding-things.md` stays allowed.

## Affected users and systems

- Users of any skill in the collection, through the agents that read them.
- Authored files only: `SKILL.md` files, authored references
  (`nix-workflow`, `nixos-coding-agents`), `scripts/check_collection.py` or
  a small companion check, and tests under `tests/`.
- No change to generated upstream references, providers, updaters,
  packages, modules or the Home Manager module. No host is changed.

## Constraints

- **Generated references stay verbatim.** They are copies of upstream
  documentation, maintained by providers. Changing them would break
  provenance hashes and licensing. The check must not fail on them, and the
  fix for them is labelling in authored text.
- **The check is offline** and never executes contributed helpers, as with
  all metadata validation. It runs in `check-fast` and CI.
- **No false positives on required quotes.** The check must follow the exact
  identifier grammar and keyword list, and ignore interpolated strings, so
  it never tells an agent or contributor to break valid code.
- **Short entrypoints.** `SKILL.md` files stay short: one or two lines per
  rule, with detail in a reference.
- **A behavioural test** covers the check, as CONTRIBUTING requires for
  helpers: it must flag the bad examples and pass the required-quote
  examples.

## Open questions

- **Where the rules live.** Should they sit in one shared place, such as a
  new `nix-language` reference section that other skills link to, or
  briefly in every relevant `SKILL.md`? Skills are portable and installed
  independently, so a link to another skill may not resolve for a user who
  installed only one.
- **Scope of the store-search check.** Should it flag only `find`, `ls` or
  glob searches of `/nix/store` in shell examples, or also hard-coded
  `/nix/store/<hash>-…` paths in Nix examples?
- **Reporting on generated references.** Should the check report
  unnecessary quotes found in generated references as information, so
  reviewers of update PRs see them, or ignore generated files completely?
