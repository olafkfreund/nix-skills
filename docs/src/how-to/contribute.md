# Contribute a skill

Contributions follow the repository's
[CONTRIBUTING.md](https://github.com/olafkfreund/nix-skills/blob/main/CONTRIBUTING.md)
and [AGENTS.md](https://github.com/olafkfreund/nix-skills/blob/main/AGENTS.md).
In short:

1. **Open an issue** and work on a task branch (`feat/<issue>-<slug>`),
   with Conventional Commits.
2. **Write the design first.** Tasks that are tracked as issues or touch
   several files need three reviewed documents, each approved before the
   next: `intent/` (why), `spec/` (what) and `plan/` (how). Nobody approves
   their own.
3. **Add the package:** `skills/<name>/SKILL.md` with exactly `name` and
   `description` frontmatter, detail in linked `references/`, and the name
   in the sorted `skills.json`.
4. **Keep provenance.** Copied upstream material needs `sources.json` and
   the upstream licence. Hand-written skills need neither.
5. **Follow the [Nix style rules](../reference/nix-style.md).**
6. **Run the checks** before opening the pull request:

   ```sh
   devenv shell check-fast
   nix flake check
   nix build .#nix-skills --no-link
   nix build .#docs
   ```

`main` is protected: a pull request and a passing `collection-check` are
required. Registering a skill never enrols it in automatic updates; a new
upstream updater needs its own design review.

## Documentation pages

Site pages live in `docs/src/` and must be listed in `docs/src/SUMMARY.md`.
The skill catalog, the update schedule and the module options are generated
when the site is built; never edit them by hand.
