# Maintain the collection

For a new skill, bug fix or development setup, start with
[CONTRIBUTING.md](https://github.com/olafkfreund/nix-skills/blob/main/CONTRIBUTING.md) and [AGENTS.md](https://github.com/olafkfreund/nix-skills/blob/main/AGENTS.md).
`skills.json` registers portable packages; it does not enroll source updaters.
Read-only PR checks validate the collection, package/module builds and explicit
maintained providers. A reviewed merge makes a contribution available to users
who choose to update their pin.

## Development environment

The root Devenv environment supplies Python, Git, GitHub CLI, Zstandard,
actionlint and Nix, plus two commands:

```sh
devenv info
devenv shell check-fast
devenv shell check-providers
nix flake check
```

`check-fast` runs offline collection validation, unit tests and workflow lint;
`check-providers` also runs all six explicit maintained-source checks, including
network-dependent regeneration. Entering the environment does not run either
command, regenerate sources, install skills or start services. The environment
was validated with Devenv 2.3.1 and the committed module/input pins.

`devenv.lock` owns project tooling; `flake.lock` owns distribution/test inputs.
Update them deliberately and separately. The provider fixture under
`tests/devenv/` has its own lock and remains independent.

Reading the skill needs only a Markdown-capable agent.
Offline validation needs Python 3.10 or newer; regeneration additionally needs Git, Nix with `nix-command` and `flakes`, and network access to upstream Git tags, source/build caches, and the versioned manual.
Nix may build the pinned executable if a substitute is unavailable; no global package installation is required.

Run from the repository root:

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/update.py --check
```

`--check` obtains Nix from the manifest's exact upstream revision, regenerates in temporary storage, checks published manual pages/anchors, evaluates `tests/language.nix` with that executable, and compares bytes without modifying the package.
The host Nix is only the bootstrap tool; it is not the documentation generator.
Network failures are failures, not skipped checks.

Explicitly update on a task branch with either:

```sh
python3 scripts/update.py --release 2.35.2
python3 scripts/update.py --latest
```

`--latest` selects the highest numeric stable upstream tag and verifies that the source declares `officialRelease = true` before generating a changed version.
Upstream currently publishes tags rather than GitHub Release objects, so the updater does not rely on `/releases/latest`.
A moved/deleted pinned tag fails for investigation.
An unchanged latest revision is a no-op; use `--check` to force regeneration of the current pin.
Generation validates links before replacing files and restores previous bytes if replacement fails.
Normal process failures are covered; filesystem/power-loss durability is not a database transaction.

Curated paths, headings, built-in names, and any missing upstream link definitions live under `selection` in `sources.json`.
Selection edits require review; the bot cannot change them.
The initial derivation selection supplies the upstream page's missing `system` configuration-option link definition.
Upstream source sections retain their wording; reference links, anchors, and incidental prose whitespace are adapted, while fenced code examples are preserved.
Only the selected subset is bundled; linked manual pages follow the upstream major/minor documentation series, which may receive later patch-level updates.
Exact copied-source provenance remains pinned to a full commit SHA.
