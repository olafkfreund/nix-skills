# nix-skills

Portable skills for AI coding agents, maintained from pinned upstream sources.

| Skill | Purpose | Initial reference |
| --- | --- | --- |
| [nix-language](skills/nix-language/SKILL.md) | Write, explain, debug, and review Nix expressions | Nix 2.35.2 |
| [devenv-project](skills/devenv-project/SKILL.md) | Configure and troubleshoot devenv project environments | devenv v2.3.1 |

Each package records its release, exact source revision, curated selection, and
input/output hashes in its own `sources.json`. References cover selected topics,
not every upstream feature. Agents must check the project's actual versions.
The Nix skill does not supply NixOS options or replace Nixpkgs API documentation.
The portable `devenv-project` skill is distinct from a machine-specific `devenv`
policy skill and upstream's `devenv-setup`; their behavior is not interchangeable.
Neither skill requires the other.

## Use

Clone this repository and check out a reviewed commit, rather than following a moving branch:

```sh
git clone https://github.com/olafkfreund/nix-skills.git
cd nix-skills
git checkout --detach <reviewed-commit-sha>
```

Copy or link the **whole** desired skill directory into your agent's supported skill directory.
Keep `references/`, `sources.json`, and its license (`COPYING` for Nix, `LICENSE` for devenv) with `SKILL.md`.

For Codex, current documented locations include a project's `.agents/skills/` and the user's `~/.agents/skills/`; symlinked skill directories are supported.
See [official skill discovery documentation](https://learn.chatgpt.com/docs/build-skills).
For example, from the clone, on a machine where this destination is not already managed declaratively:

```sh
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/nix-language" ~/.agents/skills/nix-language
ln -s "$PWD/skills/devenv-project" ~/.agents/skills/devenv-project
```

If your configuration manages agent files declaratively, declare that link or copy in your configuration instead.
No installation is performed by this repository's checks or update workflow.

Invoke `$nix-language` or `$devenv-project` in Codex or let the agent select it from its description.
Other agents can install the same folder using their own skill mechanism.
For an agent without native skill discovery, explicitly ask it to read the chosen `SKILL.md` and the relevant linked references before the task.
Portability of the files does not imply native discovery has been tested in every agent.

To update, select a newly reviewed repository commit, check it out, and replace the complete copied directory (or retain the link to that pinned checkout).
To roll back, repeat with the previous commit.

## Maintain

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

### devenv maintenance

The same commands accept `--skill devenv-project`; omitting `--skill` retains
all existing Nix behavior:

```sh
python3 scripts/check.py --skill devenv-project
python3 scripts/update.py --skill devenv-project --check
python3 scripts/update.py --skill devenv-project --release v2.3.1
python3 scripts/update.py --skill devenv-project --latest
```

Devenv updates use stable GitHub Releases, not unreleased `main`. The updater
converts selected Markdown/MDX sections, preserving tab labels, version notices,
warning meaning, and fenced executable text. Unsupported forms or renamed paths
fail for review. It reads the committed options JSON at the same revision and
records generator/template provenance; it does not rebuild the full website or
option catalogue. Declaration links into devenv are checked and pinned; foreign
links retain their distinct origin. Public devenv.sh links are checked but follow
the moving site, while exact source citations and hashes remain revision-pinned.

`--check` obtains the matching CLI from the pinned upstream flake and evaluates
matching modules in a disposable project using the reviewed auxiliary pins in
`tests/devenv/devenv.lock`. It compares representative defaults against upstream
option data and runs harmless shell/script/task/`enterTest` assertions. Language
and service enablement is evaluated without starting services. The test does not
run `devenv allow` or modify user trust. A candidate update changes only the
module pin in its temporary fixture; unrelated input changes fail for review.
Local builds can use configured substitutes; CI explicitly uses upstream's
published devenv/Cachix cache keys. There is no fallback to the host CLI.

## Automatic updates

After the workflows reach the default branch, **Update references** runs each Monday at 06:17 UTC and on manual dispatch.
Each skill generates and validates with read-only permissions, then passes an
allowlisted artifact to a separate publication job. That job rejects stale bases,
symlinks, traversal, invalid hashes, instruction/selection changes, and changes to
the sibling skill. It updates `automation/nix-reference-update` or
`automation/devenv-reference-update`, with at most one open PR per skill.
Artifacts, branches, and job concurrency are separate for each skill. No-op
artifacts are verified but produce no branch or PR.
It never merges or installs the result.
Reports identify changed selected inputs, coverage changes, and option/built-in metadata changes.
Changes to upstream's devenv setup skill are review signals; authored instructions are never automatically replaced.

The repository must allow GitHub Actions to create PRs under **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**.
This setting is enabled for this repository; forks must configure it separately.
Keep the default token permission read-only: only the publication job requests `contents: write` and `pull-requests: write`.
No personal access token is required or configured.
See [GitHub's repository workflow permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

Token-created PRs may not launch another workflow run automatically.
Validation runs before publication, and maintainers can explicitly run **Check** against the update branch or its exact SHA:

```sh
gh workflow run check.yml --ref main -f ref=automation/nix-reference-update
```

Inspect that run's checked-out SHA before merging; a manually dispatched run should not be assumed to satisfy branch-protection status requirements for the PR head.
If required checks remain pending, use the repository's normal human-triggered PR workflow or keep the PR unmerged until the required checks pass.
Failed generation publishes no package. Failed PR creation leaves a validated update branch and an actionable workflow error.
The initial Nix live updater passed as a no-op. After merging the devenv addition, validate the first live run too; a no-op does not prove changed-source PR publication.

## Sources and licensing

The copied references originate in [Nix](https://github.com/NixOS/nix), whose upstream README identifies LGPL v2.1; the upstream licence accompanies the skill as [COPYING](skills/nix-language/COPYING).
Generated references identify the Nix contributors and link to original files at the recorded revision.
The repository does not relicense that material under MIT or another permissive licence.
The manifest tracks source files, generator helpers, the full language dump, and generated hashes for reproduction.

Design history: [intent](intent/2026-09-22-1-nix-language-skill.md), [spec](spec/2026-09-22-1-nix-language-skill.md), [implementation plan](plan/2026-09-22-1-nix-language-skill.md).

Devenv references originate in [cachix/devenv](https://github.com/cachix/devenv),
under its accompanying [Apache-2.0 LICENSE](skills/devenv-project/LICENSE).
The manifest hashes selected narrative pages, committed generated data,
generators/templates, the upstream setup skill, and the documentation coverage.
Modified excerpts retain source attribution. The repository does not relicense
Nix material under devenv's license.

Devenv design history: [intent](intent/2026-09-22-3-devenv-skill.md),
[spec](spec/2026-09-22-3-devenv-skill.md),
[implementation plan](plan/2026-09-22-3-devenv-skill.md).
