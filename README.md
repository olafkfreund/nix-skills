# nix-skills

Portable skills for AI coding agents, maintained from pinned upstream sources.

| Skill | Purpose | Initial reference |
| --- | --- | --- |
| [nix-language](skills/nix-language/SKILL.md) | Write, explain, debug, and review Nix expressions | Nix 2.35.2 |
| [devenv-project](skills/devenv-project/SKILL.md) | Configure and troubleshoot devenv project environments | devenv v2.3.1 |
| [nixpkgs-development](skills/nixpkgs-development/SKILL.md) | Package software and use Nixpkgs helpers, overlays, and library APIs | master snapshot; development series 26.11 |
| [nixos-wiki](skills/nixos-wiki/SKILL.md) | Find retained NixOS configuration and troubleshooting guidance | 17 curated topics from the 2026-09-22 dump |

Each package records its upstream snapshot identity, curated selection, and
input/output hashes in its own `sources.json`. References cover selected topics,
not every upstream feature. Agents must check the project's actual versions.
The Nix skill does not supply NixOS options or replace Nixpkgs API documentation.
The portable `devenv-project` skill is distinct from a machine-specific `devenv`
policy skill and upstream's `devenv-setup`; their behavior is not interchangeable.
Each skill can be installed independently.

## Use

Clone this repository and check out a reviewed commit, rather than following a moving branch:

```sh
git clone https://github.com/olafkfreund/nix-skills.git
cd nix-skills
git checkout --detach <reviewed-commit-sha>
```

Copy or link the **whole** desired skill directory into your agent's supported skill directory.
Keep `references/`, `sources.json`, and its license (`COPYING` for Nix/Nixpkgs/wiki, `LICENSE` for devenv) with `SKILL.md`.

For Codex, current documented locations include a project's `.agents/skills/` and the user's `~/.agents/skills/`; symlinked skill directories are supported.
See [official skill discovery documentation](https://learn.chatgpt.com/docs/build-skills).
For example, from the clone, on a machine where this destination is not already managed declaratively:

```sh
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/nix-language" ~/.agents/skills/nix-language
ln -s "$PWD/skills/devenv-project" ~/.agents/skills/devenv-project
ln -s "$PWD/skills/nixpkgs-development" ~/.agents/skills/nixpkgs-development
ln -s "$PWD/skills/nixos-wiki" ~/.agents/skills/nixos-wiki
```

If your configuration manages agent files declaratively, declare that link or copy in your configuration instead.
No installation is performed by this repository's checks or update workflow.

Invoke `$nix-language`, `$devenv-project`, `$nixpkgs-development`, or `$nixos-wiki` in Codex or let the agent select it from its description.
Other agents can install the same folder using their own skill mechanism.
For an agent without native skill discovery, explicitly ask it to read the chosen `SKILL.md` and the relevant linked references before the task.
Portability of the files does not imply native discovery has been tested in every agent.

To update, select a newly reviewed repository commit, check it out, and replace the complete copied directory (or retain the link to that pinned checkout).
To roll back, repeat with the previous commit.

## Maintain

For a new skill, bug fix or development setup, start with
[CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).
`skills.json` registers portable packages; it does not enroll source updaters.
Read-only PR checks validate the collection, package/module builds and explicit
maintained providers. A reviewed merge makes a contribution available to users
who choose to update their pin.

### Declarative installation on NixOS

Add the input to your existing system flake, then commit its lock file:

```nix
inputs.nix-skills.url = "github:olafkfreund/nix-skills";
```

Within your existing Home Manager-as-NixOS module configuration, import the
module for the chosen user (replace `alice`; `inputs` must be in scope):

```nix
home-manager.users.alice = {
  imports = [ inputs.nix-skills.homeManagerModules.default ];
  programs.nix-skills = {
    enable = true;
    skills = [ "nix-language" "devenv-project" "nixpkgs-development" "nixos-wiki" ];
    # Omitting skills selects the complete registered collection.
    directory = ".agents/skills";
  };
};
```

This links complete immutable skill directories, including resources and
licenses, under the user's home. Existing files retain Home Manager's normal
collision protection; links are never forced. Disabling the module adds no
installation effects. Unknown or duplicate names and absolute/traversing
destinations are rejected. The module builds data with your existing `pkgs`;
it does not replace your host's Nixpkgs input or install an agent.

Validate and rebuild through your existing **NixOS** workflow. Do not run
`home-manager switch` when Home Manager is a NixOS module. The default path and
symlink support follow [Codex's documented discovery locations](https://learn.chatgpt.com/docs/build-skills).
For another agent, select its documented relative directory; native discovery
in other agents is not claimed by package/module checks.

Without Home Manager, the collection is also a data package:

```nix
environment.systemPackages = [
  inputs.nix-skills.packages.${pkgs.stdenv.hostPlatform.system}.nix-skills
];
```

This exposes `share/nix-skills/<name>` in the package; it does not create user
discovery links. Declare those separately in your own configuration. Individual
outputs, for example `packages.x86_64-linux.nix-language`, contain the same
complete directory. `default` contains all registered skills. Packages are
exported for x86_64-linux and aarch64-linux; our validation distinguishes native
x86_64 builds from aarch64 evaluation.

Review updates to the consumer's locked `nix-skills` input before rebuilding.
Roll back by restoring the previous lock and rebuilding, or using your system's
previous generation. Repository builds and checks never activate a home or host.

### Development environment

The root Devenv environment supplies Python, Git, GitHub CLI, Zstandard,
actionlint and Nix, plus two commands:

```sh
devenv info
devenv shell check-fast
devenv shell check-providers
nix flake check
```

`check-fast` runs offline collection validation, unit tests and workflow lint;
`check-providers` also runs all four explicit maintained-source checks, including
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

### Nixpkgs maintenance

```sh
python3 scripts/check.py --skill nixpkgs-development
python3 scripts/update.py --skill nixpkgs-development --check
python3 scripts/update.py --skill nixpkgs-development --revision 7561e7e3e12a06677b1525a12bcccb0b4e4c601d
python3 scripts/update.py --skill nixpkgs-development --latest
```

Nixpkgs tracks **master snapshots**, not releases or channel promotions. The
`.version` value is development-series metadata. `--latest` resolves master once,
requires descendant ancestry from the previous snapshot, and regenerates/tests
any advanced SHA, even when only provenance changed. An identical SHA is a no-op.
Rewinds, divergence, unavailable inputs and unverifiable ancestry fail for review.
Explicit full-SHA repinning is reviewed work; `--release` is rejected for Nixpkgs.

The updater copies selected `doc/` sections and builds the pinned source's
`nixpkgs-manual.lib-docs` derivation for twelve curated library APIs. It does not
rebuild the whole website. Its independently pinned Nix 2.35.2 evaluator cannot
change through automated updates. If substitutes are unavailable, Nix may build
that evaluator, nixdoc and their dependencies; network/cache access and disk space
are needed. Authored instructions, selection, branch and evaluator policy remain
reviewed files. The snapshot records consumed inputs, coverage, generated API
records and outputs, including the upstream MIT license.

`--check` verifies deterministic generation and runs a small pinned fixture for
argument/attribute overrides, overlays, library/fileset results and generic module
composition. It builds a local-source package to check phase hooks and installed
output, and executes a small shell helper. Language helpers are evaluated for
availability; their full ecosystems are not built. Checks have been exercised on
x86_64-linux; this is not a claim of cross-platform or native-agent discovery tests.
No services, host configuration, user trust or installed skills are changed.

Custom manual anchors are resolved to bundled sections or pinned source files
with named sections. Unsupported documentation syntax fails before replacement.
Fenced code is preserved, including illustrative or historical upstream examples;
the Python excerpt identifies an upstream duplicate argument needing adaptation.
Consumers must use their own project's pin rather than assume master APIs exist
in older Nixpkgs. Roll back by restoring the entire skill from a reviewed commit.

### NixOS Wiki maintenance and lookup

The wiki skill bundles 17 reviewed English topic pages, the copyright policy and
latest template source, with one retained revision per page. It preserves raw
wikitext, examples and notices; it does not render MediaWiki templates or mirror
the whole wiki. Search excerpts can omit caveats, so read page notices and complete
examples before use. Advice still needs checking against the consumer's actual pin.

```sh
python3 skills/nixos-wiki/scripts/wiki.py search 'rebuild'
python3 skills/nixos-wiki/scripts/wiki.py show 'Nixos-rebuild'
python3 skills/nixos-wiki/scripts/wiki.py show 'Garbage Collection' --follow
python3 skills/nixos-wiki/scripts/wiki.py show 'Template:Warning'
python3 scripts/check.py --skill nixos-wiki
python3 scripts/update.py --skill nixos-wiki --check
```

Lookup and `--check` need only Python 3.10+, work offline, and never execute wiki
examples. `show` limits each original-text window to 200 lines / 16 KiB and gives
continuation arguments (`--start`, `--offset`); `--lines` can request a smaller
window. Template search requires `--templates`. Missing redirect targets are
labeled as live, unpinned links; revision citations do not pin templates used by
the live website's renderer. Other agents may read individual JSON records instead.

Ingestion additionally requires `zstd`; CI supplies it from a fixed Nixpkgs commit.
No global installation is needed. On a task branch or disposable copy:

```sh
python3 scripts/update.py --skill nixos-wiki --latest
python3 scripts/update.py --skill nixos-wiki --dump /path/to/wikidump.xml.zst --sha256 <expected-sha256>
```

The updater bounds download/decompression/XML processing, rejects DTD/entities,
and verifies the compressed hash and decoder success. It rejects regressions,
mutated revision identities, missing primary titles, broken primary redirects and
copyright-policy changes. Same-dump and irrelevant-history/recompression changes
are no-ops; advanced retained revisions with identical text are reported as
provenance-only updates. Changes require review, including template changes.

Retained JSON contains the exact consumed text and metadata, allowing offline
reproduction after the moving dump URL changes. The compressed checksum identifies
the original acquisition; the subset cannot reconstruct the full historical XML.
No full dump, contributor identities/history or media are distributed. Source
origin, selection, namespace/size/schema policy and copyright-policy identity are
immutable to automation, as are SKILL.md and the package's lookup helper. Restore
the complete package from a reviewed repository commit to roll back.

## Automatic updates

After the workflows reach the default branch, **Update references** runs each Monday at 06:17 UTC and on manual dispatch.
Each skill generates and validates with read-only permissions, then passes an
allowlisted artifact to a separate publication job. That job rejects stale bases,
symlinks, traversal, invalid hashes, instruction/selection changes, Nixpkgs evaluator/branch-policy changes, and changes to
the sibling skill. It updates `automation/nix-reference-update` or
`automation/devenv-reference-update`, `automation/nixpkgs-reference-update`, or
`automation/nixos-wiki-reference-update`,
with at most one open PR per skill.
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

Nixpkgs references originate in [NixOS/nixpkgs](https://github.com/NixOS/nixpkgs),
under its accompanying [MIT COPYING](skills/nixpkgs-development/COPYING).
The license of the nixdoc generator does not replace the upstream source license.
Nixpkgs design history: [intent](intent/2026-09-22-5-nixpkgs-skill.md),
[spec](spec/2026-09-22-5-nixpkgs-skill.md),
[implementation plan](plan/2026-09-22-5-nixpkgs-skill.md).

Wiki text is from the [official NixOS Wiki](https://wiki.nixos.org/), under the
retained [MIT COPYING](skills/nixos-wiki/COPYING) from copyright-policy revision
22887. Media can have other terms and is excluded. Wiki design history:
[intent](intent/2026-09-22-8-nixos-wiki-skill.md),
[spec](spec/2026-09-22-8-nixos-wiki-skill.md),
[plan](plan/2026-09-22-8-nixos-wiki-skill.md).
