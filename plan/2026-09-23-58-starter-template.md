---
status: approved
issue: 58
spec: spec/2026-09-23-58-starter-template.md
---

# Plan: move from the demo to your own machine

## Approved decisions

These come from the approved spec. The plan can be followed without opening
the intent or spec.

**Shared module: `demo/agentic.nix`.** It is a function
`{ nix-skills, llm-agents }: { config, lib, pkgs, options, ... }: …`,
exported by `demo/flake.nix` as
`nixosModules.agentic = import ./agentic.nix { inherit nix-skills llm-agents; };`.

Options, under `nix-skills.agentic`:
- `enable`, default `false`;
- `agents`, a list of enum `claude-code`, `codex`, `opencode` and
  `gemini-cli`, default `[ "claude-code" ]`;
- `user`, null or string, default `null`;
- `cache.enable`, default `true`;
- `podman.enable`, default `false`;
- `devenv.enable`, default `false`.

When `enable` is set:
- the agents come from
  `llm-agents.packages.${pkgs.stdenv.hostPlatform.system}` and go into
  `environment.systemPackages`, together with `git` and `curl`;
- `nix.settings.experimental-features` gains `nix-command` and `flakes`;
- `cache.enable` adds the Numtide substituter and key through
  `nix.settings.extra-substituters` and `extra-trusted-public-keys`;
- `podman.enable` sets `virtualisation.podman.enable`;
- `devenv.enable` adds `pkgs.devenv`;
- when `user != null` and `options ? home-manager`,
  `home-manager.users.${user}` imports
  `nix-skills.homeManagerModules.default` with
  `programs.nix-skills = { enable = true; agents = <mapped>; }`. The
  mapping: `claude-code` → `"claude"` and `codex` → `"codex"`; `opencode` →
  `"opencode"` only when neither of the other two is selected;
  `gemini-cli` gets nothing;
- an assertion fails when `user != null` and `!(options ? home-manager)`,
  with the message "nix-skills.agentic.user needs the Home Manager NixOS
  module (home-manager.nixosModules.home-manager) imported".

Nothing else: no users, passwords, automatic login, SSH, firewall, boot or
nixpkgs `config` changes.

**Demo (`demo/demo.nix`).**
- It imports the shared module and sets:
  - `nix-skills.agentic.enable = true`;
  - `agents = [ "claude-code" "codex" "opencode" ]`;
  - `user = "demo"`;
  - `podman.enable` and `devenv.enable` both `true`.
- It keeps only the demo-only parts: hostname, `system.stateVersion`, the
  `demo` user with password, `autologinUser`, SSH, the `~/example` files
  (through `home-manager.users.demo.home.file`) and `vmVariant`.
- `demo.agents` is removed. `demo/flake.nix` passes the shared module into
  `demo.nix` by value, and `specialArgs` is dropped if nothing needs it.
- `demo/test.nix`'s checks are unchanged.

**Template.** `templates/agentic-nixos/` contains:
- **`flake.nix`:**
  - inputs:
    - `nixpkgs` (`github:NixOS/nixpkgs/nixos-unstable`);
    - `home-manager` (`github:nix-community/home-manager`, following
      `nixpkgs`);
    - `agentic` (`github:olafkfreund/nix-skills?dir=demo`);
  - `nixosConfigurations.my-machine`, a `nixosSystem` of
    `home-manager.nixosModules.home-manager`,
    `agentic.nixosModules.agentic` and `./configuration.nix`;
  - comments on each input, and on llm-agents.nix having no `follows`.
- **`configuration.nix`:**
  - `imports = [ ./hardware-configuration.nix ];` with the
    `nixos-generate-config --show-hardware-config >
    hardware-configuration.nix` comment;
  - the placeholder boot loader `boot.loader.systemd-boot.enable = true;`
    and `boot.loader.efi.canTouchEfiVariables = true;`, marked "check for
    your machine";
  - `networking.hostName = "my-machine";`;
  - `users.users.alice.isNormalUser = true;`, marked "replace me", with a
    comment to set a password (none is set);
  - `nix-skills.agentic = { enable = true; agents = [ "claude-code" ];
    user = "alice"; }`, with `cache`, `podman` and `devenv` commented;
  - `system.stateVersion` with a comment.
- **`README.md`:** the steps, the agents and their licences, and a link to
  the site.

**Main flake.**
- `templates.agentic-nixos = { path = ./templates/agentic-nixos;
  description = "NixOS configuration with coding agents and nix-skills";
  welcomeText = <the next steps and the start prompt>; }`
- `templates.default = self.templates.agentic-nixos`.
- No new inputs.

**`demo.yml`.**
- The path filter gains `templates/**`.
- A new step, after the VM test:
  1. `tmp=$(mktemp -d)`, then
     `(cd "$tmp" && nix flake init -t "$GITHUB_WORKSPACE#agentic-nixos")`;
  2. write `hardware-configuration.nix` with `fileSystems."/" = { device =
     "/dev/disk/by-label/nixos"; fsType = "ext4"; }`,
     `boot.loader.grub.device = "nodev"` and
     `nixpkgs.hostPlatform = "x86_64-linux"`;
  3. `nix eval "$tmp#nixosConfigurations.my-machine.config.system.build.toplevel.drvPath"
     --override-input agentic "path:$GITHUB_WORKSPACE/demo"`.

**Documentation.**
- **`docs/src/how-to/own-machine.md`** ("Set up your own machine"), in
  `SUMMARY.md` after "Install the skills". It covers the order (demo
  first), route A (an existing flake), route B (a template), the options
  table, and the cache, unfree and Gemini CLI notes.
- **`demo-vm.md`:** "Change the agents" refers to
  `nix-skills.agentic.agents`, and "Limits" links to the new page.
- **AGENTS.md:** a `templates/` line.
- **CONTRIBUTING.md:** one line saying the template must keep evaluating,
  which `demo.yml` checks.

### Deviations during implementation

- **Template override.** `--override-input agentic "path:<repo>/demo"` fails
  with `access to absolute path '/nix/store/flake.nix' is forbidden`. That
  form copies only `demo/` into the store, so the demo's relative input
  `path:..` no longer points at the repository. The override uses the
  repository root with `?dir=demo` instead, the same shape users fetch
  (`github:…?dir=demo`): `path:$GITHUB_WORKSPACE?dir=demo` in CI, and
  `path:$PWD?dir=demo` locally.
- **Home Manager state version.** The template also sets
  `home-manager.users.alice.home.stateVersion = "26.05"`, because Home
  Manager refuses to evaluate a user without it.

## Steps

1. **`demo/agentic.nix`, and `demo/demo.nix` and `demo/flake.nix` moved
   onto it.** Stage the files.
   → Verify:
   - `nix eval ./demo#nixosConfigurations.demo.config.home-manager.users.demo.programs.nix-skills.agents`
     is `["claude","codex"]`;
   - the VM test passes locally (`nix build
     ./demo#checks.x86_64-linux.vm-test -L`).
2. **Negative checks,** as throwaway `nix eval --impure --expr`
   expressions, not committed:
   - a `nixosSystem` with the module, `enable = true` and `user = "alice"`,
     and no Home Manager module, fails with the assertion message;
   - with `enable = false`, `environment.systemPackages` equals a baseline
     without the module.
3. **`templates/agentic-nixos/` and the `templates` output.**
   → Verify:
   - `nix flake check` on the main flake passes, which validates
     `templates`;
   - `nix flake init -t .#agentic-nixos` into a temporary directory prints
     the `welcomeText`;
   - the stub-hardware `nix eval … --override-input agentic path:$PWD/demo`
     of `toplevel.drvPath` succeeds locally.
4. **`demo.yml`:** the path filter and the template step.
   → Verify: `actionlint` is clean.
5. **Documentation:** `own-machine.md`, `SUMMARY.md`, `demo-vm.md`,
   AGENTS.md and CONTRIBUTING.md.
   → Verify: `nix build .#docs` and `check_collection.py` pass.
6. **Full checks:** unit tests, `check_collection.py`, `devenv shell
   check-fast`, `nix flake check`, and `nix build .#nix-skills --no-link`.
   Commit in logical groups, push, and open a PR with `Closes #58`.
   → Verify: `collection-check` is green, `demo.yml` passes (VM test and
   template evaluation), and the PR is `CLEAN`. Do not merge without
   approval.

## Tests

```sh
nix build ./demo#checks.x86_64-linux.vm-test -L
nix flake check
tmp=$(mktemp -d); (cd "$tmp" && nix flake init -t "$OLDPWD#agentic-nixos")
nix eval "$tmp#nixosConfigurations.my-machine.config.system.build.toplevel.drvPath" --override-input agentic "path:$PWD/demo"
actionlint
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_collection.py
devenv shell check-fast
nix build .#docs
nix build .#nix-skills --no-link
```

## Rollback

- **Before merge:** close the PR and delete the branch.
- **After merge:** `git revert` the implementation commits. That restores
  the #57 demo module, and removes the shared module, the template, the
  `templates` output and the documentation additions. Users who already
  imported `nixosModules.agentic` would need to drop the import, so a
  revert is announced in the release notes.
