---
name: home-manager
description: Configure and troubleshoot Home Manager user environments and NixOS module integration when working in a declarative Nix flake.
---

# Home Manager

Read the repository instructions, flake inputs, target host, imports, and
existing Home Manager modules before editing. Preserve the project's module
and feature-flag conventions.

Use the [NixOS module reference](references/nixos.md) when Home Manager is
integrated into a NixOS flake. Use [configuration](references/configuration.md)
for user settings and package placement, [dotfiles](references/dotfiles.md)
for managed files, [modular services](references/modular-services.md) for
service modules, and [writing modules](references/writing-modules.md) when
extending Home Manager.

Keep `home.stateVersion` stable unless deliberately performing a migration.
Prefer existing `programs`, `services`, `home.packages`, `home.file`, and
`xdg.configFile` options over custom generation. When Home Manager is loaded as
a NixOS module, apply changes through the host's NixOS rebuild workflow rather
than `home-manager switch`.

Check the user's actual Home Manager revision before relying on version-
specific options. Validate the flake and use a dry build before deployment.
