---
name: nix-workflow
description: Choose Nix commands, locate store paths and libraries, use development shells, debug builds, configure Nix and navigate ecosystem tools.
---

# Nix workflow

Establish the context before advising. Read the repository's own instructions.
Check `nix --version`, since Nix, Lix and Determinate Nix differ. Check whether
`nix-command` and `flakes` are enabled (`nix config show experimental-features`),
and whether the project pins inputs with a flake, npins, niv or channels.
Advice that fits one of these can be wrong for another.

## Rules

1. **Never search `/nix/store` by brute force.** A `find` or `ls` over the store
   only sees what happens to be built locally. It misses everything else, and a
   path copied from it breaks as soon as the store changes. Use `nix-locate` to
   find which package provides a file. Use store queries (`nix path-info`,
   `nix why-depends`) for dependencies. Refer to libraries through Nix
   expressions such as `${pkgs.openssl.out}/lib` or `lib.makeLibraryPath`,
   never through literal store paths.
2. **Use the right environment.**
   - For a project, use its `devShells` output with `nix develop`.
   - For a tool the user needs for a moment, use `nix shell nixpkgs#tool`.
   - For one program, use `nix run`.
   - Do not install into the user's profile or system to satisfy one project.
3. **Search before inventing.** When a build or package fails:
   - Read the full log with `nix log`.
   - Search NixOS/nixpkgs issues and pull requests for the distinctive error
     text.
   - Report what you found, with numbers, before proposing a workaround.

   Do not disable the sandbox, checks or hardening to make an error disappear.
4. **Use the smallest adequate tool.** Inspect and transform data with `jq`,
   `awk`, `sed`, `grep` and `nix` subcommands such as `nix eval --json` and
   `nix derivation show`. Write Python or another script only when the logic
   needs it.
5. **Know where a setting lives.** Nix settings belong to the client, the
   daemon or a remote builder. Some take effect only for trusted users. On
   NixOS, nix-darwin and Home Manager, Nix configuration is declarative, and
   generated files are not edited by hand. Do not edit `nix.conf`, add trusted
   users or substituters, collect garbage, or switch a system without the
   user's explicit authorization. Propose the change instead.
6. **Treat ecosystem facts as perishable.** Tools and lang2nix projects are
   archived, renamed or replaced often. Before recommending one, check its
   upstream repository for its status and any successor. Prefer the Nixpkgs
   language builders first.

## Other skills by role

These skills belong to the same collection, but may not all be installed. If
one is missing, use the linked upstream documentation instead.

| Role | Typical need | Use |
|---|---|---|
| Developer | Project environment, expressions | This skill for shells; `devenv-project` for devenv ([devenv.sh](https://devenv.sh/)); `nix-language` for the language ([Nix manual](https://nix.dev/manual/nix/latest/language/)) |
| Packager | Derivations, overrides, overlays | `nixpkgs-development` ([Nixpkgs manual](https://nixos.org/manual/nixpkgs/unstable/)) |
| Home Manager user, including darwin | User configuration | `home-manager` ([Home Manager manual](https://nix-community.github.io/home-manager/)) |
| NixOS administrator | System configuration and rebuilds | `nixos-wiki` ([NixOS manual](https://nixos.org/manual/nixos/stable/), [NixOS Wiki](https://wiki.nixos.org/)) |
| VM user | Declarative microVMs | `microvm-nix` ([microvm.nix](https://microvm-nix.github.io/microvm.nix/)) |

Report what you actually ran, which commands only evaluated and which built
or changed anything, and which advice you could not verify on the user's
version.
