---
status: approved
issue: 30
spec: spec/2026-09-23-30-nixos-operations.md
---

# Plan: NixOS system operations skill

Branch: `feat/30-nixos-operations`, based on `main` 560a62d.
Pinned Nixpkgs: `9c0ece3dc2086e85434c5d2477eb6bc118d20ff8`, the same as
`nixpkgs-development` today.
Intent: `intent/2026-09-23-30-nixos-operations.md`.
Spec: `spec/2026-09-23-30-nixos-operations.md`.

## Approved decisions

- **D1 Sibling provider `scripts/nixos_operations.py`:**
  - It imports from `nixpkgs.py`, **which is not modified**: `lines`,
    `excerpt`, `expand_includes`, `index_anchors`, `convert`,
    `resolve_revision`, `SHA` and `UPSTREAM`. From `update.py` it takes
    `pinned_tools`, `run`, `evaluate`, `digest`, `encoded` and `ROOT`.
  - The package is `skills/nixos-operations`. `GENERATED` is
    `{references/operations.md, COPYING, sources.json}`.
  - Fetching uses the manifest `toolchain` (pinned Nix), then
    `flake prefetch github:NixOS/nixpkgs/<rev>`, checking the locked revision.
    It does not build `lib-docs`.
  - **Anchor index:** `index_anchors` over `doc/**/*.md` and
    `nixos/doc/manual/**/*.md`, plus `path:` entries, with the coverage
    hashes of those files.
  - **Option links:**
    - Selection items carry `option_links: {anchor: option}`.
    - One evaluation of
      `lib.optionAttrSetToDocList (import <src>/nixos/lib/eval-config.nix { modules = [ { system.stateVersion = "<source .version>"; } ]; system = "x86_64-linux"; }).options`,
      filtered to the mapped names. Arguments are passed as JSON, as
      `runtime_check` does.
    - Each mapped anchor adds `(declaring file relative to src, option
      name)` to the index, using the first declaration inside the source
      tree. The declaring files' hashes go into `inputs`.
    - **Fails if:** an `#opt-` link has no map entry, an option is missing
      or has no in-tree declaration, or an entry is unused (checked by
      scanning the excerpt's links).
  - **Output:** `references/operations.md` has a `# Operations` heading, the
    pinned header, a table of contents, and per chapter an upstream source
    link plus `convert(...)` output. `COPYING` comes from the source.
  - **Manifest:** `upstream`, `branch: master`, `revision`, `source_version`,
    `toolchain`, `selection`, `inputs`, `coverage_inputs` and `outputs`.
  - **`validate_manifest(manifest)`:**
    - branch and toolchain checks, as in `nixpkgs.validate_manifest`;
    - every section path under `nixos/doc/manual/`;
    - `anchor` matches `[\w.:-]+` and is unique;
    - `children` is a bool; `heading` is non-empty;
    - `option_links` is optional, and maps `opt-…` anchors to option-name
      strings;
    - the expected inputs are present;
    - provenance paths are relative.
  - **`main(args)`:**
    - reads the manifest JSON directly, with no pre-validation, so the
      initial snapshot needs no bootstrap;
    - `resolve_revision` if `--latest`, otherwise `args.revision` or the
      recorded revision;
    - generate; `--check` compares bytes; otherwise `publish` (which
      validates the staged package) and writes `.update-report.md`.
- **D2 Selection:** the six chapters from spec section 2, with the anchors,
  headings, `children: true` and the three `option_links`.
- **D3 Registration:**
  - `check.py`:
    - the upstream map (`https://github.com/NixOS/nixpkgs`);
    - an `elif skill == "nixos-operations"` branch calling
      `validate_manifest`, with `coverage_inputs` as coverage;
    - `immutable_policy` adding `branch` and `toolchain` for this skill;
    - the choices.
  - `update.py`: `generated_files`, the choices, and dispatch allowing
    `--revision`, `--latest` and `--check`, while rejecting `--release`,
    `--dump` and `--sha256`.
  - `artifact.py`: the choices.
  - the `check.yml` matrix;
  - the `update.yml` generate matrix, and a publish entry for
    `automation/nixos-operations-reference-update` (reviewed enrollment);
  - the `devenv.nix` loop, `skills.json`, and README entries (table, links,
    Codex list, Home Manager example, maintenance, automation branch list,
    sources and licensing).
- **D4 SKILL.md:** as spec section 3.
  - **State-changing actions are proposals:** rebuilds other than build and
    dry-build, switching, boot entries, rollback, garbage collection,
    deleting generations, and restarting services.
  - **Commands:** `nixos-rebuild` subcommands and flags named must exist in
    the pinned Nixpkgs `nixos-rebuild` sources.
- **D5 Routing:** the NixOS administrator row in `nix-workflow` names
  `nixos-operations`.
- **Stop rule:** stop, revise this plan and ask if any of these happens:
  - `convert` rejects a construct in a selected chapter;
  - a link can't be resolved under D1;
  - `nixpkgs-development` output or `scripts/nixpkgs.py` would change.

## Steps

Each step is one commit with `(#30)`, citing its step number.

1. **Provider (D1)** with `tests/test_nixos_operations.py`, using a synthetic
   source and stubbed evaluation:
   - selection;
   - bundled, unbundled and same-file cross-references;
   - option links resolved from stubbed declarations;
   - failures for an unmapped option, a missing option, an unused entry and
     a path outside `nixos/doc/manual/`;
   - schema errors.

   → Verify: the new tests pass, and `git diff main -- scripts/nixpkgs.py`
   is empty.
2. **Registration (D3 code and workflows):**
   → Verify:
   - the full unit test suite passes;
   - `nixos-operations` appears alongside `nix-darwin` in every
     registration site;
   - the workflows parse;
   - `--release` is rejected.
3. **Package (D2, D4):** seed `sources.json` with upstream, branch, revision,
   the `nixpkgs-development` toolchain and the selection, then write
   `SKILL.md`. Generate with
   `update.py --skill nixos-operations --revision 9c0ece3d…`, and register it
   in `skills.json`.
   → Verify:
   - `check.py` and `update.py --check` pass for `nixos-operations`;
   - `operations.md` has all six anchors, no `](#opt-` links, and the three
     option links to `stage-1.nix`, `systemd.nix` and `systemd/user.nix`;
   - manpage links are present;
   - the `nixos-rebuild` commands in SKILL.md are audited against the pinned
     source;
   - `check_collection.py` reports 9 skills.
4. **Routing and README (D3 README, D5):**
   → Verify the collection check passes and the new URLs return 200.
5. **Full verification:** run the commands under Tests below.
6. **PR:** push, and open a PR with `Closes #30` and the evidence.
   → Verify CI is green. Merge on the maintainer's approval. Then dispatch
   `update.yml`, and confirm the `nixos-operations` jobs succeed.

## Tests

```sh
python3 scripts/check_collection.py            # expect 9 skills
python3 -m unittest discover -s tests -p 'test_*.py'
for s in nix-language devenv-project home-manager microvm-nix nix-darwin nixos-operations nixpkgs-development nixos-wiki; do
  python3 scripts/check.py --skill "$s"
  python3 scripts/update.py --skill "$s" --check
done
git diff main --stat -- scripts/nixpkgs.py skills/nixpkgs-development   # expect empty
nix flake check --no-update-lock-file
nix build .#nix-skills --no-link --print-out-paths | xargs -I{} test -f {}/share/nix-skills/nixos-operations/SKILL.md
git diff --exit-code
```

Expected result: every command exits 0.

## Rollback

Revert the PR's merge commit, or the individual step commits. The provider,
package, registrations and updater enrollment are removed. `nixpkgs.py` and
`nixpkgs-development` were never changed. If an update PR was opened, close
it and delete `automation/nixos-operations-reference-update`.
