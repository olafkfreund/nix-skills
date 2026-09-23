# Set up your own machine

Put coding agents and the skills on your own NixOS machine with one module,
`nixosModules.agentic`. Try everything first in the
[demo VM](../tutorials/demo-vm.md); the demo is built on this same module.

The module only adds what its options ask for: agent packages, the skills
for one user's agents, and optionally the Numtide binary cache, Podman and
devenv. It never adds users, passwords, logins, SSH, firewall or boot
settings, and it does not touch your nixpkgs `config`.

## Route A: an existing flake configuration

Add the input. It is the repository's `demo/` flake, which pins
llm-agents.nix:

```nix
inputs.agentic.url = "github:olafkfreund/nix-skills?dir=demo";
```

Import the module next to Home Manager's NixOS module, and set the options:

```nix
nixosConfigurations.my-machine = nixpkgs.lib.nixosSystem {
  modules = [
    home-manager.nixosModules.home-manager
    inputs.agentic.nixosModules.agentic
    ./configuration.nix
  ];
};
```

```nix
# configuration.nix
nix-skills.agentic = {
  enable = true;
  agents = [ "claude-code" "codex" ];
  user = "alice";
};
```

Build with `nixos-rebuild build --flake .#my-machine`, then switch. When
Home Manager is a NixOS module, never use `home-manager switch`.

If you already install the skills through `homeManagerModules.default`
yourself, set `user = null` so that the module installs only the agents.

## Route B: a new configuration from the template

```sh
mkdir my-nixos && cd my-nixos
nix flake init -t github:olafkfreund/nix-skills#agentic-nixos
nixos-generate-config --show-hardware-config > hardware-configuration.nix
```

Edit the parts of `configuration.nix` marked `CHANGE ME`: the boot loader,
your user (the template sets no password) and the agents. Then build and
switch as in route A. The template is a starting point: it does not boot
until your hardware configuration is in place.

## Options

| Option | Default | Effect |
| --- | --- | --- |
| `nix-skills.agentic.enable` | `false` | Turns the module on |
| `nix-skills.agentic.agents` | `[ "claude-code" ]` | Agents from llm-agents.nix: `claude-code`, `codex`, `opencode`, `gemini-cli` |
| `nix-skills.agentic.user` | `null` | The Home Manager user whose agents get the skills; `null` installs none |
| `nix-skills.agentic.cache.enable` | `true` | Adds `https://cache.numtide.com` and its key to `nix.settings` |
| `nix-skills.agentic.podman.enable` | `false` | Enables rootless Podman for sandboxed agents |
| `nix-skills.agentic.devenv.enable` | `false` | Adds devenv |

## Notes

- **Skill directories.** With Claude Code or Codex selected, the skills go
  into `~/.claude/skills` and `~/.agents/skills`. OpenCode reads those too,
  so it only gets its own directory when neither is selected. Gemini CLI
  has no skill directory in the Home Manager module yet.
- **Licences.** `claude-code` is labelled unfree upstream; `codex`,
  `opencode` and `gemini-cli` are free. llm-agents.nix marks its unfree
  licence as allowed, so no `allowUnfree` setting is needed or effective.
- **Cache.** Adding a binary cache means trusting its key. Set
  `cache.enable = false` to build everything yourself.
- **Updates.** `nix flake update agentic` moves the agents and the module
  to the demo flake's latest pins. Review the lock change, then rebuild.
- **Missing Home Manager.** Setting `user` without importing
  `home-manager.nixosModules.home-manager` fails with an assertion that
  says so.
