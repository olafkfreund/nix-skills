---
status: approved
issue: 27
intent: intent/2026-09-23-27-darwin-nixos-operations.md
---

# Spec: darwin Home Manager and nix-darwin

The intent was approved without answers, so its recommendations apply:

- **Split.** This task covers darwin only. NixOS system operations moved to
  #30, with its own intent, spec and plan.
- **nix-darwin** becomes its own skill.

Reject either at this review.

## Facts

- `home-manager` is a `github_docs` skill (`scripts/home_manager.py`). It
  copies whole upstream files from a reviewed `CONFIG["selection"]` and pins
  their links. It is pinned at Home Manager `cbcbfa2778e0…` and bundles five
  files, none about darwin.
- **Candidate Home Manager files** at that revision:
  - `docs/manual/installation/nix-darwin.md` (3,962 bytes)
  - `docs/manual/nix-flakes/nix-darwin.md` (2,051)
  - `docs/manual/installation/standalone.md` (2,808)
  - `docs/manual/nix-flakes/standalone.md` (2,888)
  - `docs/manual/usage/rollbacks.md` (1,977)
  - `docs/manual/usage/updating.md` (2,141)
- **nix-darwin** (`github.com/nix-darwin/nix-darwin`, default branch `master`,
  MIT). Its prose documentation is `README.md` (7,242 bytes): prerequisites,
  flake and channel setup, using and updating, uninstalling. Its
  `doc/manual/manual.md` only includes the generated options list, so there is
  no prose to excerpt.
- **Adding a `github_docs` skill touches fixed places**, as #14 did for
  `microvm-nix`:
  - `scripts/check.py`: the upstream map, the provider module map, the
    `github_docs` set and the `--skill` choices;
  - `scripts/update.py`: `generated_files`, the choices and the dispatch;
  - `scripts/artifact.py`: the choices;
  - `.github/workflows/check.yml`: the matrix;
  - `.github/workflows/update.yml`: the generate matrix and a publish entry
    with its branch;
  - the `devenv.nix` check loop;
  - `skills.json` and the README.

## Design

### 1. Home Manager: add the darwin and standalone files

Append six items to `CONFIG["selection"]` in `scripts/home_manager.py`:

| Source | Output | Title |
|---|---|---|
| `docs/manual/installation/nix-darwin.md` | `references/install-nix-darwin.md` | nix-darwin module installation |
| `docs/manual/nix-flakes/nix-darwin.md` | `references/flake-nix-darwin.md` | nix-darwin module with flakes |
| `docs/manual/installation/standalone.md` | `references/install-standalone.md` | Standalone installation |
| `docs/manual/nix-flakes/standalone.md` | `references/flake-standalone.md` | Standalone with flakes |
| `docs/manual/usage/rollbacks.md` | `references/rollbacks.md` | Rollbacks |
| `docs/manual/usage/updating.md` | `references/updating.md` | Updating |

Regenerate at the **pinned** revision (`--revision cbcbfa2778e0…`) so the five
existing outputs stay byte-identical. The package grows by about 16 KB.

Changes to `skills/home-manager/SKILL.md`, which is authored:

- **First step:** find out how Home Manager is installed:
  - as a NixOS module (`home-manager.users.*` in a NixOS configuration);
  - as a nix-darwin module (`home-manager.users.*` in a darwin
    configuration);
  - standalone (a `homeConfigurations` output, or `~/.config/home-manager`).
- **Mode decides the rest:** point each mode to its reference, and state that
  it decides how changes are applied:
  - the NixOS rebuild for the NixOS module;
  - `darwin-rebuild` for the nix-darwin module;
  - `home-manager switch` standalone.
- **Authorization:** switching, rolling back and updating inputs change the
  user's environment, so propose them and do not run them without
  authorization. The existing sentence "apply changes through the host's NixOS
  rebuild workflow" is generalised to the host's system manager.
- Link the new references.

### 2. New `nix-darwin` skill (`github_docs`)

- **Provider:** `scripts/nix_darwin.py`, with
  `CONFIG = {skill: "nix-darwin", upstream: "https://github.com/nix-darwin/nix-darwin", branch: "master", selection: [README.md → references/readme.md "nix-darwin README"]}`
  and the three wrapper functions, as in `scripts/microvm.py`.
- **Package** `skills/nix-darwin/`:
  - `LICENSE`, the upstream MIT text, fetched by the provider;
  - `references/readme.md`;
  - `sources.json`;
  - an authored `SKILL.md`. It triggers for nix-darwin system configuration
    on macOS. It says to read the flake or `configuration.nix` and its pin
    first, and explains `darwin-rebuild` build, check and switch, plus
    generations and rollback. Every command and flag named is verified
    against the pinned `darwin-rebuild` source, because it cannot run on this
    Linux host. Home Manager as a nix-darwin module is handed over to the
    `home-manager` skill. Switching, rollback, uninstalling and activation are
    proposals that need authorization. The README's uninstall section is
    reference, never an action to take.
- **Registration** in every place listed under Facts, following the
  `microvm-nix` pattern exactly.
- **Enrollment in the weekly `update.yml` generate and publish matrices,**
  with branch `automation/nix-darwin-reference-update`. AGENTS.md says
  registering a skill must not by itself enroll an updater, so this
  enrollment is an explicit, reviewed part of this spec.
- **Initial content** is generated with
  `update.py --skill nix-darwin --revision <current master SHA>`, recorded in
  `sources.json`.

### 3. Routing

In `skills/nix-workflow/SKILL.md` (authored), the Home Manager row names
`nix-darwin` for darwin systems, with its upstream fallback link. The NixOS
administrator row is unchanged until #30 lands.

## Alternatives rejected

- **A darwin reference inside `home-manager`.** nix-darwin is a system manager
  used without Home Manager too, and mixing the two confuses which command
  applies changes.
- **Authored darwin summaries.** They would drift from upstream, and the
  collection prefers pinned excerpts.
- **Scraping nix-darwin's generated options manual.** It is generated from
  code at build time, so there is no prose source. Options are found through
  the `nix` search tooling or upstream instead.
- **Moving the Home Manager pin in the same change.** That would mix a
  content refresh with a selection change. The weekly update moves the pin
  separately.
- **Enrolling nix-darwin in `check.yml` only, without `update.yml`.** Its
  README would then never refresh. Both are enrolled, or neither.

## Risks

- **nix-darwin's README links** may escape the checkout or use forms
  `pin_links` rejects. That fails closed at generation. If it happens, the plan
  stops and asks.
- **README drift:** the README describes both flake and channel installs.
  Mitigated by the "read the user's actual setup first" rule, and by the
  weekly refresh.
- **`darwin-rebuild` behaviour** changes between versions, for example sudo
  requirements. Commands are verified against the pinned source, and SKILL.md
  tells the agent to check the user's version.
- **Automation scope grows:** one more weekly job and branch. Same permission
  model as the existing providers.
- **Hosts:** CI runners and local runs only. No machine configuration changes.

## Verification

- `python3 scripts/check_collection.py` passes with 8 skills.
- The full `unittest` suite passes. If `test_github_docs` or any other test
  hard-codes provider lists, it is extended.
- `check.py` and `update.py --check` pass for all seven maintained skills,
  including `nix-darwin`.
- The five existing `home-manager` references are byte-identical to `main`.
  The six new ones exist, and their links are pinned or package-relative.
- `nix flake check` passes, and `nix build .#nix-skills` contains
  `share/nix-skills/nix-darwin/`.
- Every `darwin-rebuild` subcommand and flag named in SKILL.md is checked
  against the pinned nix-darwin source.
- CI on the PR is green, including new `check (nix-darwin)` jobs. After merge,
  a manual `update.yml` dispatch shows the nix-darwin generate and publish
  jobs succeed.
