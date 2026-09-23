---
status: approved
issue: 30
intent: intent/2026-09-23-30-nixos-operations.md
---

# Spec: NixOS system operations skill

The intent was approved with its recommended defaults:

- a sibling provider;
- a reviewed map for option links;
- a Nixpkgs master pin.

Research showed that a map to declaring **files** would go stale, so this spec
refines the second default: the reviewed map names **options**, and their
declaring files are resolved automatically. Reject that refinement at this
review if unwanted.

## Facts

At Nixpkgs `9c0ece3d…`:

| Chapter | Top anchor | Links needing resolution |
|---|---|---|
| `installation/changing-config.chapter.md` | `sec-changing-config` | `#ch-configuration` (manual chapter), `#opt-systemd.user.services` |
| `installation/upgrading.chapter.md` | `sec-upgrading` | none |
| `administration/rollback.section.md` | `sec-rollback` | none |
| `administration/cleaning-store.chapter.md` | `sec-nix-gc` | none |
| `administration/boot-problems.section.md` | `sec-boot-problems` | `#opt-fileSystems._name_.neededForBoot`; manpages `kernel-command-line(7)`, `systemd.special(7)` |
| `administration/service-mgmt.chapter.md` | `sec-systemctl` | `#opt-systemd.packages`, `#sec-nix-gc` (selected), `#sect-nixos-systemd-nixos` (same file) |

- Every chapter starts with a `{#id}` heading, so the existing `excerpt()`
  selects each one whole with `children: true`.
- **Markup:** `::: {.warning}` and `::: {.note}` admonitions, including one
  indented block, which the `nixpkgs` manual converter handles. Both manpages
  are in `doc/manpage-urls.json`.
- **Section anchors** are defined under `nixos/doc/manual/`, which the
  `nixpkgs` provider does not index. It indexes only `doc/`.
- **Option anchors** (`opt-…`) are generated from the module system at build
  time. **Declarations move:** at this pin, `fileSystems.<name>.neededForBoot`
  is declared in `nixos/modules/system/boot/stage-1.nix`, not
  `tasks/filesystems.nix`, where a current code search places it.
- **Declaration lookup works:** evaluating
  `lib.optionAttrSetToDocList (import nixos/lib/eval-config.nix { modules = [ ]; … }).options`
  at the pin returns the declaring files for all three options in about 1.6 s:
  - `systemd.user.services`: `system/boot/systemd/user.nix`;
  - `systemd.packages`: `system/boot/systemd.nix`;
  - `fileSystems.<name>.neededForBoot`: `system/boot/stage-1.nix`.

## Design

### 1. Sibling provider `scripts/nixos_operations.py`

- **Reuse:** it imports the manual-format functions from `scripts/nixpkgs.py`:
  `lines`, `headings`, `excerpt`, `expand_includes`, `index_anchors`,
  `convert`, `resolve_revision`, `pinned_tools` and `SHA`.
  `scripts/nixpkgs.py` is **not modified**, so `nixpkgs-development` is
  untouched by construction.
- **Source:** it follows Nixpkgs `master` with its own manifest and pin,
  using the same master-ancestry check as `nixpkgs-development`. The
  evaluator is the pinned Nix toolchain recorded in its manifest
  (`toolchain`), initialised from `nixpkgs-development`'s toolchain.
- **Anchor index:** `index_anchors` runs over every `*.md` under
  `nixos/doc/manual/` and `doc/`, plus `path:` entries.
  - Links to anchors in a selected chapter point to the bundled anchor.
  - Other anchors point to a pinned blob URL "(source section: …)", as
    `convert` already does.
- **Option links:** each selection item may carry
  `option_links: {"opt-<anchor>": "<option name>"}`, reviewed policy.
  - The generator evaluates the pinned NixOS options once (with
    `system.stateVersion` set, to avoid the evaluation warning), and finds
    each named option's declarations.
  - It adds `opt-<anchor> → (declaring file, option name)` to the anchor
    index, so `convert` emits
    `[label](…/blob/REV/<declaring file>) (source section: <option name>)`.
  - **Fails if:**
    - an `#opt-` link has no map entry;
    - a mapped option does not exist at the pin;
    - a mapped option has no declaration inside the source tree;
    - a map entry is unused.
  - The declaring files' hashes are recorded in `inputs`.
- **Output:** `references/operations.md`, with a table of contents and one
  section per chapter, and the same header and COPYING handling as
  `nixpkgs-development`. `GENERATED` is `{references/operations.md, COPYING,
  sources.json}`.
- **Validation:**
  - the selection schema (the nixpkgs fields plus `option_links`);
  - paths must be under `nixos/doc/manual/`;
  - the toolchain and branch are checked;
  - hashes;
  - automation cannot change the selection, upstream, branch or toolchain.

### 2. Selection (reviewed policy)

| Path | Anchor | Heading | option_links |
|---|---|---|---|
| `nixos/doc/manual/installation/changing-config.chapter.md` | `sec-changing-config` | Changing the Configuration | `opt-systemd.user.services` → `systemd.user.services` |
| `nixos/doc/manual/installation/upgrading.chapter.md` | `sec-upgrading` | Upgrading NixOS | – |
| `nixos/doc/manual/administration/rollback.section.md` | `sec-rollback` | Rolling Back Configuration Changes | – |
| `nixos/doc/manual/administration/cleaning-store.chapter.md` | `sec-nix-gc` | Cleaning the Nix Store | – |
| `nixos/doc/manual/administration/boot-problems.section.md` | `sec-boot-problems` | Boot Problems | `opt-fileSystems._name_.neededForBoot` → `fileSystems.<name>.neededForBoot` |
| `nixos/doc/manual/administration/service-mgmt.chapter.md` | `sec-systemctl` | Service Management | `opt-systemd.packages` → `systemd.packages` |

All items have `children: true`.

### 3. Skill `skills/nixos-operations/`

Generated `COPYING`, `references/operations.md` and `sources.json`, plus an
authored `SKILL.md`:

- **Establish the setup first:** flake or channels; the release (`nixos-version`,
  `system.stateVersion`); the configuration location and the host.
- **Decide what a change needs:**
  - the rebuild modes: switch, boot, test and build, with build and
    dry-build as the safe first steps;
  - generations and rollback;
  - deliberate upgrades;
  - store cleaning without removing generations the user relies on;
  - boot recovery;
  - service inspection with `systemctl` and `journalctl`.
- **Authorization:** switching, boot entries, rollback, garbage collection,
  deleting generations and restarting services are **proposals needing
  authorization**.
- **Manual is reference:** its commands are reference material, and it is
  never a reason to convert between channels and flakes.
- **Version note:** the reference follows Nixpkgs master; check the user's
  release before relying on version-sensitive behaviour.
- **Hand-overs:** Home Manager goes to `home-manager`, packaging to
  `nixpkgs-development`, and community tips to `nixos-wiki`.

### 4. Registration and routing

- **Registration:** add `nixos-operations` wherever `nix-darwin` is
  registered: `check.py`, `update.py` (dispatch as for
  `nixpkgs-development`, allowing `--revision` and `--latest`, and rejecting
  `--release`, `--dump` and `--sha256`), `artifact.py`, the `check.yml`
  matrix, and the `devenv.nix` loop.
- **Weekly updater (reviewed enrollment):** add it to the `update.yml`
  generate matrix, with a publish entry for
  `automation/nixos-operations-reference-update`.
- **Registry and README:** `skills.json`, and README entries (table, links,
  Codex list, Home Manager example, maintenance, automation branch list,
  sources and licensing).
- **Routing:** the NixOS administrator row in `nix-workflow` names
  `nixos-operations`.
- **Initial snapshot:** at the same revision as `nixpkgs-development`
  (`9c0ece3d…`), so both packages start from one pin.

## Alternatives rejected

- **Generalising `scripts/nixpkgs.py` to emit two packages.** It couples two
  manifests, pins and update PRs, and risks `nixpkgs-development`'s
  byte-identity.
- **A reviewed map from anchor to declaring file.** Declarations move between
  files (`neededForBoot`), so the map would go stale.
- **Unpinned search.nixos.org option links.** They are not pinned and cannot
  be validated.
- **Only a declaration lookup, with no reviewed map.** Any new option link
  would then be resolved without review. The map keeps what is linked as
  reviewed policy.
- **Adding content to `nixos-wiki`.** It is wiki-sourced, with a different
  provider and licence handling.
- **Tracking a stable release branch.** It diverges from the rest of the
  collection. SKILL.md tells the agent to check the user's release instead.

## Risks

- **Heavier updates:** the weekly update runs a NixOS options evaluation,
  about 2 s at this pin, and fetches the Nixpkgs source. That is acceptable,
  and `nixpkgs-development` already does both.
- **Upstream edits** that add option links or rename headings fail closed for
  review.
- **`nixpkgs.py` is imported but not changed.** A later refactor of
  `nixpkgs.py` could break this provider. Its tests and `--check` in CI catch
  that.
- **Hosts:** CI runners and local runs only.

## Verification

- **Unit tests** (`tests/test_nixos_operations.py`) with a synthetic source:
  - a selection including children;
  - a bundled cross-reference, and an unbundled one resolved to a pinned URL;
  - option links resolved from stubbed declarations;
  - failures for an unmapped option link, a missing option, an unused map
    entry, and a path outside `nixos/doc/manual/`;
  - schema validation.
- **Regeneration:** `update.py --skill nixos-operations --check` at the pin
  passes.
- **Unchanged:** `update.py --skill nixpkgs-development --check` passes, and
  `git diff main -- scripts/nixpkgs.py skills/nixpkgs-development` is empty.
- **Output content:**
  - `operations.md` contains all six anchors;
  - no `#opt-` links remain;
  - the three option links point to the declaring files above;
  - the `{manpage}` roles are resolved.
- **Full checks:**
  - `check_collection.py` reports 9 skills;
  - the full unit test suite passes;
  - `check.py` plus `--check` for all eight maintained skills;
  - `nix flake check`, and the package build contains `nixos-operations`.
- **CI and dispatch:** CI is green. After merge, an `update.yml` dispatch
  runs the new generate and publish jobs successfully.
