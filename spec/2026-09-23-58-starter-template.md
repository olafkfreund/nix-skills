---
status: approved
issue: 58
intent: intent/2026-09-23-58-starter-template.md
---

# Spec: move from the demo to your own machine

## Facts

Checked on 2026-09-23.

- **The demo module mixes shared and demo-only parts.** `demo/demo.nix`
  (from #57) contains:
  - **the shared parts:** the `demo.agents` option (an enum of
    `claude-code`, `codex`, `opencode` and `gemini-cli`), the agent
    packages from `llm-agents.packages.<system>`, the mapping to
    `programs.nix-skills.agents` (OpenCode only when neither Claude Code
    nor Codex is selected), flakes and the Numtide cache, Podman, devenv,
    git and curl;
  - **the demo-only parts:** the `demo` user with `initialPassword`,
    `services.getty.autologinUser`, `services.openssh.enable`, the
    `~/example` files and `virtualisation.vmVariant`.

  It receives `nix-skills` and `llm-agents` through `specialArgs`, which an
  external configuration cannot provide cleanly.
- **The demo flake as an input.** Consumed as
  `github:olafkfreund/nix-skills?dir=demo`, its `path:..` input resolves to
  the same revision. Its lock (llm-agents.nix and so on) is honoured
  transitively.
- **Templates add no inputs.** A flake's `templates.<name>` output is
  `{ path, description, welcomeText }` and adds no inputs.
  `nix flake init -t <flake>#<name>` copies `path`, never overwrites
  existing files, and prints `welcomeText`. `nix flake check` validates the
  `templates` output.
- **Existing coverage.** The demo VM test (`demo/test.nix`) and the
  non-blocking `demo.yml` workflow already cover the demo configuration on
  x86_64-linux.

## Design

### Default answers to the intent's open questions

The intent was approved without answers. These defaults apply unless the spec
review changes them:

1. **Location.** The shared module lives in the `demo/` flake as
   `nixosModules.agentic`. The main flake gains only a `templates` output,
   with no inputs.
2. **Home Manager.** The module configures skills for one named user through
   an option.
3. **Podman and devenv.** Both are opt-in options, off by default.
4. **Template shape.** A complete minimal `flake.nix` and `configuration.nix`
   with marked hardware placeholders, plus a README. Existing flakes use the
   module instead.

### Shared module: `demo/agentic.nix` → `nixosModules.agentic`

`agentic.nix` is a function of the demo flake's inputs, returning a NixOS
module:

```nix
{ nix-skills, llm-agents }:
{ config, lib, pkgs, options, ... }: { … }
```

`demo/flake.nix` exports it as
`nixosModules.agentic = import ./agentic.nix { inherit nix-skills llm-agents; };`.
The consumer passes no `specialArgs`.

**Options,** under `nix-skills.agentic`:

| Option | Type | Default | Effect |
| --- | --- | --- | --- |
| `enable` | bool | `false` | Turns everything below on |
| `agents` | list of enum `claude-code`, `codex`, `opencode`, `gemini-cli` | `[ "claude-code" ]` | Agent packages from llm-agents.nix, added to `environment.systemPackages` |
| `user` | null or string | `null` | The user whose Home Manager configuration gets the skills. With `null`, the skills are not installed. |
| `cache.enable` | bool | `true` | Adds the Numtide substituter and key through `nix.settings.extra-*` |
| `podman.enable` | bool | `false` | `virtualisation.podman.enable` |
| `devenv.enable` | bool | `false` | Adds `pkgs.devenv` to the system packages |

**Behaviour when enabled:**
- `nix.settings.experimental-features` gains `nix-command` and `flakes`,
  merged rather than replaced.
- **Skills,** when `user != null`:
  - `home-manager.users.${user}` imports
    `nix-skills.homeManagerModules.default`, with
    `programs.nix-skills = { enable = true; agents = <mapped>; }`;
  - the mapping is the existing rule, moved from `demo.nix`;
  - this whole block applies only when `options ? home-manager`.
- **An assertion** fails with a clear message when `user != null` and the
  Home Manager NixOS module is not imported.
- **Nothing else:** no users, passwords, automatic login, SSH, firewall,
  boot or nixpkgs `config` changes.

### The demo uses the shared module

`demo/demo.nix` imports `nixosModules.agentic` and sets:
- `nix-skills.agentic = { enable = true; agents = [ "claude-code" "codex"
  "opencode" ]; user = "demo"; podman.enable = true; devenv.enable = true; }`;
- only its demo-only parts: the user, the password, automatic login, SSH,
  `~/example` and `vmVariant`, plus hostname and `system.stateVersion`.

The `demo.agents` option is removed, and the tutorial's "Change the agents"
section points to `nix-skills.agentic.agents`. `specialArgs` stays only for
what `demo.nix` itself still needs, which is none if the module is imported
by value.

The **VM test is unchanged** in what it checks: agents, skill directories,
no duplicate OpenCode directory, Podman, devenv and `~/example`. It now
covers the shared module.

### Template: `templates/agentic-nixos/` → main flake `templates.agentic-nixos`

- **`flake.nix`:**
  - inputs:
    - `nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";`
    - `home-manager` (following `nixpkgs`);
    - `agentic.url = "github:olafkfreund/nix-skills?dir=demo";`
  - `nixosConfigurations.my-machine`, which imports
    `home-manager.nixosModules.home-manager`,
    `agentic.nixosModules.agentic` and `./configuration.nix`.

  The comments explain each input, and why llm-agents.nix is not
  `follows`-ed.
- **`configuration.nix`:**
  - `imports = [ ./hardware-configuration.nix ];`, with a comment to run
    `nixos-generate-config --show-hardware-config >
    hardware-configuration.nix`;
  - a marked placeholder for the boot loader;
  - `networking.hostName`;
  - one example user, `alice`, with `isNormalUser`, and "replace me"
    comments. No password; the comment says to set one.
  - `nix-skills.agentic = { enable = true; agents = [ "claude-code" ];
    user = "alice"; }`, with the other options commented;
  - `system.stateVersion`, with a comment.
- **`README.md`:** the steps (generate the hardware configuration, edit the
  placeholders, then `nixos-rebuild build --flake .#my-machine`, then
  `switch`), which agents exist, and the licence note.
- **Main flake:** `templates.agentic-nixos = { path =
  ./templates/agentic-nixos; description = "…"; welcomeText = "…"; }` and
  `templates.default = templates.agentic-nixos`. `welcomeText` lists the
  next steps and ends with the start prompt.

### Tests

- **Demo VM test,** in `demo.yml`: unchanged checks, now exercising the
  shared module.
- **Template evaluation,** a new step in `demo.yml`:
  1. `nix flake init -t "$PWD#agentic-nixos"` into a temporary directory;
  2. write a stub `hardware-configuration.nix`: `fileSystems."/"`,
     `boot.loader.grub.device = "nodev"`, and the `nixpkgs.hostPlatform`;
  3. run `nix eval --override-input agentic "path:$PWD/demo"
     .#nixosConfigurations.my-machine.config.system.build.toplevel.drvPath`.

  This proves the template's wiring against the current commit, without
  building a system.
- **Main flake:** `nix flake check` validates `templates`.

The `demo.yml` path filter gains `templates/**`.

### Documentation

- **`docs/src/how-to/own-machine.md`** ("Set up your own machine"), listed
  in `SUMMARY.md` under How-to guides. It covers:
  - the recommended order (try the demo, then this);
  - route A, an existing flake: add the `agentic` input, import the module,
    set the options, rebuild with `nixos-rebuild`, never `home-manager
    switch`;
  - route B, a new configuration: `nix flake init -t …`, then generate the
    hardware configuration;
  - the options table;
  - the notes on cache, unfree labels and Gemini CLI.
- **`docs/src/tutorials/demo-vm.md`:** "Change the agents" refers to
  `nix-skills.agentic.agents`, and "Limits" links to the new page.
- **AGENTS.md:** `templates/` in the layout. **CONTRIBUTING.md:** one line
  saying the template must keep evaluating, which `demo.yml` checks.

## Alternatives rejected

- **The shared module in the main flake, taking agent packages as an
  argument.** Users would then have to add llm-agents.nix themselves, and
  get the per-system package set right. The demo flake already pins it.
- **Leaving the Home Manager part to the user.** Then the mapping rule
  (OpenCode duplicates) is back in every user's hands, which is the problem
  the intent describes.
- **Podman and devenv on by default.** Importing the module would change
  more of the system than the user asked for.
- **Only a flake fragment, no complete template.** New users would get
  nothing that evaluates, and existing users are better served by the
  module.
- **Building the template's system in CI.** It needs real hardware
  settings. Evaluating the `drvPath` with a stub proves the wiring at much
  lower cost.
- **Setting a user password in the template.** A password in a copied file
  ends up in version control. The user sets their own.

## Risks

- **Consumers of `?dir=demo` get the demo's lock.** llm-agents.nix and
  nixpkgs versions follow what `demo/flake.lock` pins. The template adds
  `follows` only for nixpkgs where it is safe, and documents
  `nix flake update agentic`.
- **Renaming `demo.agents`** changes the documented override. It is only
  weeks old and the tutorial is updated in the same change.
- **An `options ? home-manager` check** misreading an unusual Home Manager
  setup. It is covered by the assertion, and by the VM test, which uses the
  standard Home Manager NixOS module.
- **The template drifting from the module.** Prevented by the evaluation
  step in `demo.yml`.
- **`nixos-unstable` in the template.** llm-agents.nix needs the unstable
  line. Documented.

## Verification

- `nix build ./demo#checks.x86_64-linux.vm-test -L` passes locally, with
  the demo now on the shared module.
- **Template evaluation, locally:** init into a temporary directory, add
  the stub hardware file, and `nix eval --override-input agentic
  path:$PWD/demo` of `toplevel.drvPath` succeeds.
- **Negative checks:**
  - `user = "alice"` without the Home Manager module fails with the
    assertion message;
  - `enable = false` adds nothing, compared by evaluating
    `environment.systemPackages`.
- **Main repository:** `nix flake check` (now validating `templates`),
  `nix build .#docs` with the new page, unit tests, `check_collection.py`,
  `check-fast` and `actionlint` all pass.
- **CI:** `demo.yml` passes on the pull request, covering both the VM test
  and the template evaluation.
