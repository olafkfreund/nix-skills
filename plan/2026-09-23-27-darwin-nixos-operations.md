---
status: approved
issue: 27
spec: spec/2026-09-23-27-darwin-nixos-operations.md
---

# Plan: darwin Home Manager and nix-darwin

Branch: `feat/27-darwin-nixos-operations`, based on `main` 1ff19b4.
Intent: `intent/2026-09-23-27-darwin-nixos-operations.md`.
Spec: `spec/2026-09-23-27-darwin-nixos-operations.md`.
NixOS system operations are split out to #30.

## Approved decisions

- **D1 Home Manager selection:**
  - Append six items to `CONFIG["selection"]` in `scripts/home_manager.py`,
    and the same six to `skills/home-manager/sources.json`'s `selection`:

    | Source | Output | Title |
    |---|---|---|
    | `docs/manual/installation/nix-darwin.md` | `references/install-nix-darwin.md` | nix-darwin module installation |
    | `docs/manual/nix-flakes/nix-darwin.md` | `references/flake-nix-darwin.md` | nix-darwin module with flakes |
    | `docs/manual/installation/standalone.md` | `references/install-standalone.md` | Standalone installation |
    | `docs/manual/nix-flakes/standalone.md` | `references/flake-standalone.md` | Standalone with flakes |
    | `docs/manual/usage/rollbacks.md` | `references/rollbacks.md` | Rollbacks |
    | `docs/manual/usage/updating.md` | `references/updating.md` | Updating |

    `generate` iterates the recorded selection, and validation requires it to
    equal `CONFIG`.
  - Regenerate at the pinned revision with
    `update.py --skill home-manager --revision <recorded revision>`.
  - The five existing outputs must stay byte-identical.
- **D2 Home Manager `SKILL.md`** (authored):
  - The first step identifies the installation mode: NixOS module, nix-darwin
    module or standalone, with the concrete signs.
  - Each mode maps to its reference and its apply command: the host's NixOS
    rebuild, `darwin-rebuild`, or `home-manager switch`.
  - The existing "NixOS rebuild workflow" sentence is generalised to the
    host's system manager.
  - Switching, rollback and updating inputs are proposals that need
    authorization.
  - The six new references are linked.
- **D3 nix-darwin provider:**
  - `scripts/nix_darwin.py` is `github_docs` with `skill "nix-darwin"`,
    upstream `https://github.com/nix-darwin/nix-darwin`, branch `master`, and
    selection
    `[{"source": "README.md", "output": "references/readme.md", "title": "nix-darwin README"}]`.
  - It has the `generated_files`, `validate_manifest` and `main` wrappers, as
    in `scripts/microvm.py`.
- **D4 nix-darwin package:**
  - `skills/nix-darwin/` holds the provider-generated `LICENSE`,
    `references/readme.md` and `sources.json`, and an authored `SKILL.md`.
  - The SKILL.md triggers for nix-darwin configuration on macOS, and says to
    read the flake or `configuration.nix` and the pin first.
  - It explains `darwin-rebuild` build, check and switch, and
    generations/rollback, **only with subcommands and flags present in the
    pinned `pkgs/nix-tools/darwin-rebuild.sh`**.
  - Home Manager inside nix-darwin is handed over to the `home-manager` skill.
  - Switch, rollback, activation and uninstall are proposals that need
    authorization. The README's uninstall section is reference only.
- **D5 Registration:** add `nix-darwin` wherever `microvm-nix` is registered:
  - `scripts/check.py`: the upstream map, the provider module map, the
    `github_docs` set and `--skill` choices;
  - `scripts/update.py`: `generated_files`, choices, and dispatch rejecting
    `--release`, `--dump` and `--sha256` like microvm;
  - `scripts/artifact.py`: choices;
  - the `.github/workflows/check.yml` matrix;
  - the `devenv.nix` check loop;
  - the sorted `skills.json`;
  - the README: the table, `ln -s`, the Codex list and the Home Manager
    `skills` example.
- **D6 Updater enrollment (explicitly reviewed):**
  - Add `nix-darwin` to the `update.yml` generate matrix.
  - Add a publish entry with branch `automation/nix-darwin-reference-update`.
- **D7 Initial snapshot:**
  - Seed `skills/nix-darwin/sources.json` with `upstream`, `branch`, the
    current `master` SHA from `git ls-remote` as `revision`, and the D3
    `selection`, as #14 did for its initial snapshots.
  - Generate with `update.py --skill nix-darwin --revision <that SHA>`.
- Deviation (step 4): the README also documents each maintained provider in
  a maintenance section, the automation branch list and the sources/licensing
  paragraph. nix-darwin is added to all three, since a new weekly branch and
  licence would otherwise be undocumented.
- **D8 Routing:** in `skills/nix-workflow/SKILL.md`, the Home Manager row names
  `nix-darwin` for darwin systems, with an upstream fallback link.
- **Stop rule:** stop, revise this plan and ask if any of these happens:
  - `pin_links` rejects a link in any new source;
  - an existing `home-manager` reference changes bytes;
  - `darwin-rebuild.sh` lacks a command the skill would need.

## Steps

Each step is one commit, with Conventional Commits and `(#27)`, citing the
step number.

1. **Home Manager (D1, D2):** update `CONFIG` and `sources.json` selection,
   regenerate at the pinned revision, then edit `SKILL.md`.
   → Verify:
   - `git diff main --stat -- skills/home-manager/references/{nixos,configuration,dotfiles,modular-services,writing-modules}.md`
     is empty;
   - the six new references exist;
   - `check.py --skill home-manager` and `update.py --skill home-manager --check`
     pass;
   - `python3 -m unittest tests.test_github_docs` passes.
2. **nix-darwin provider and registration (D3, D5, D6):**
   - Add `scripts/nix_darwin.py`, and register it in the code and workflows.
   - Extend any test that hard-codes provider or skill lists.

   → Verify:
   - `python3 -m unittest discover` passes;
   - the matrix and choice lists contain `nix-darwin` wherever they contain
     `microvm-nix` (`grep -c` parity);
   - the workflows still parse (`yq`).
3. **nix-darwin package (D4, D7):** seed `sources.json`, generate the initial
   snapshot, then write `SKILL.md` and add the name to `skills.json`.
   → Verify:
   - `check.py --skill nix-darwin` and `update.py --skill nix-darwin --check`
     pass;
   - `check_collection.py` reports 8 skills;
   - every `darwin-rebuild` subcommand and flag named in `SKILL.md` appears in
     the pinned `pkgs/nix-tools/darwin-rebuild.sh`, fetched at the recorded
     revision.
4. **Routing and README (D5 README part, D8):** update `nix-workflow`'s
   routing row, and add `nix-darwin` to the four README listings.
   → Verify `check_collection.py` passes, and the new URLs return 200.
5. **Full verification:** run the commands under Tests below.
6. **PR:**
   - Push with `git push -u origin feat/27-darwin-nixos-operations`.
   - Open a PR with `Closes #27`, following the template.
   - Link the intent, spec and plan.
   - Include the byte-identity evidence, the `darwin-rebuild` audit and the
     updater enrollment note.

   → Verify CI is green, including the new `check (nix-darwin)` job. Merge
   only on the maintainer's approval. After merge, dispatch `update.yml` and
   confirm the `nix-darwin` generate and publish jobs succeed.

## Tests

```sh
python3 scripts/check_collection.py            # expect 8 skills
python3 -m unittest discover -s tests -p 'test_*.py'
for s in nix-language devenv-project home-manager microvm-nix nix-darwin nixpkgs-development nixos-wiki; do
  python3 scripts/check.py --skill "$s"
  python3 scripts/update.py --skill "$s" --check
done
git diff main --stat -- skills/home-manager/references/{nixos,configuration,dotfiles,modular-services,writing-modules}.md   # expect empty
nix flake check --no-update-lock-file
nix build .#nix-skills --no-link --print-out-paths | xargs -I{} test -f {}/share/nix-skills/nix-darwin/SKILL.md
git diff --exit-code
```

Expected result: every command exits 0.

Limitation: `darwin-rebuild` cannot run on this x86_64-linux host. Its
guidance is verified against the pinned source script only, and no macOS run
is claimed.

## Rollback

Revert the PR's merge commit, or the individual step commits:

- **Home Manager:** its selection and six references go back to five.
- **nix-darwin:** its package, provider, registrations and updater enrollment
  are removed.
- **Open automation PR:** if a nix-darwin update PR was opened after merge,
  close it and delete `automation/nix-darwin-reference-update`.
