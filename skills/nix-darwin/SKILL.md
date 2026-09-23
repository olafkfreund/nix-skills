---
name: nix-darwin
description: Configure, build and troubleshoot nix-darwin macOS system configurations and darwin-rebuild generations.
---

# nix-darwin

Read the repository instructions, the flake (a `darwinConfigurations` output)
or `configuration.nix`, its nix-darwin and Nixpkgs pins, and the host name
before editing. The bundled [README](references/readme.md) covers
prerequisites, flake and channel setups, updating and uninstalling. It
describes the snapshot in [sources.json](sources.json), not necessarily the
user's pin. Check version-sensitive behaviour against the user's nix-darwin
revision.

## Applying configuration

`darwin-rebuild` builds and activates a configuration:

| Command | Effect | Needs root |
|---|---|---|
| `darwin-rebuild build --flake .#HOST` | Build only, leaving `./result` | No |
| `darwin-rebuild check --flake .#HOST` | Build and run activation checks | Yes |
| `darwin-rebuild switch --flake .#HOST` | Build, activate and make it the current generation | Yes |
| `darwin-rebuild --list-generations` | List system generations | No |
| `darwin-rebuild --rollback` | Activate the previous generation | Yes |
| `darwin-rebuild --switch-generation N` | Activate generation `N` (`-G N`) | Yes |
| `darwin-rebuild changelog --flake .#HOST` | Build, then page the configuration's nix-darwin change log | No |

Without `.#HOST`, the flake attribute defaults to the Mac's `LocalHostName`.
Without `--flake`, `darwin-rebuild` uses `/etc/nix-darwin/flake.nix` if it
exists, and otherwise the channel-based `configuration.nix`. Pass
`--no-flake` to force the latter. Commands that need root are run with
`sudo`.

Start with `build` to validate a change. `check`, `switch`, `activate`,
rollbacks and uninstalling change the running system. Propose them with the
exact command, and run them only with the user's authorization. The README's
uninstall steps are reference, never an action to take on your own.

## Related configuration

Home Manager loaded as a nix-darwin module (`home-manager.darwinModules`) is
applied by `darwin-rebuild`, not `home-manager switch`. Use the
`home-manager` skill if it is installed, or the
[Home Manager manual](https://nix-community.github.io/home-manager/). Nix
settings on nix-darwin are declared through `nix.settings`. Do not edit
`/etc/nix/nix.conf` by hand. Nix itself, and its installer's choices, belong
to the host; check them before changing daemon settings.

Options are not bundled. Search them in the user's pinned nix-darwin source,
or in the nix-darwin option documentation for that revision.

Modified upstream material is covered by [LICENSE](LICENSE).

## Nix style

- Never search `/nix/store` (for example `find /nix/store/*foo-* -name libfoo.so`)
  and never copy a literal store path. Find the providing package with
  `nix-locate`, and refer to it through Nix: `${pkgs.foo}/lib` or
  `lib.makeLibraryPath [ pkgs.foo ]`.
- Do not quote attribute names that are valid identifiers
  (`[A-Za-z_][A-Za-z0-9_'-]*`, dashes included). Write `pkgs.foo-bar` and
  `packages.x86_64-linux`, not `pkgs."foo-bar"`. Quote only other names
  (`".config/foo"`, `"2.0"`), the keywords
  `assert else if in inherit let or rec then with`, and interpolations
  (`"${name}"`). Upstream examples in references sometimes quote needlessly;
  do not copy that style.
