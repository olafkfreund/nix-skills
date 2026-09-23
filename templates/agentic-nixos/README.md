# NixOS with coding agents and nix-skills

A starting point for a NixOS configuration with AI coding agents from
[llm-agents.nix](https://github.com/numtide/llm-agents.nix) and the
[nix-skills](https://olafkfreund.github.io/nix-skills/) skills installed for
them. It is not bootable until you fill in the parts marked `CHANGE ME` in
`configuration.nix`.

## Steps

1. Generate your hardware configuration:

   ```sh
   nixos-generate-config --show-hardware-config > hardware-configuration.nix
   ```

2. Edit `configuration.nix`: the boot loader, your user name (replace
   `alice` in both places), and the agents you want.
3. Build first, then switch:

   ```sh
   nixos-rebuild build --flake .#my-machine
   sudo nixos-rebuild switch --flake .#my-machine
   ```

   Home Manager runs as a NixOS module here: never use `home-manager switch`.
4. Set your password (`passwd`), start an agent, sign in, and check the
   skills with `/skills` (Claude Code, Codex).

## Agents

| Value | Binary | Licence |
| --- | --- | --- |
| `claude-code` | `claude` | unfree |
| `codex` | `codex` | Apache-2.0 |
| `opencode` | `opencode` | MIT |
| `gemini-cli` | `gemini` | Apache-2.0 (no skills directory yet) |

Try them first without changing anything in the
[demo VM](https://olafkfreund.github.io/nix-skills/tutorials/demo-vm.html).
More in [Set up your own machine](https://olafkfreund.github.io/nix-skills/how-to/own-machine.html).
