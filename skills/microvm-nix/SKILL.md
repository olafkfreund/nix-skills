---
name: microvm-nix
description: Configure and troubleshoot declarative microVMs with microvm.nix when working in a NixOS flake.
---

# microvm.nix

Read the repository instructions, flake inputs, target host, VM
`nixosConfigurations`, imports, and existing microVM modules before editing.
Preserve the project's module and feature-flag conventions.

Use [declaring VMs](references/declaring.md) and the [introduction](references/intro.md)
for the module shape. Use [declarative deployment](references/declarative.md),
[host integration](references/host.md), and [host systemd](references/host-systemd.md)
for host-managed VMs. Consult [options](references/options.md), the networking
references, and [shares](references/shares.md) only for the relevant workload.

Distinguish a VM's NixOS configuration from the host's `microvm.vms`
management. Treat host paths, shared stores, networking, interfaces, and device
passthrough as trust boundaries. Existing deployed VMs may require the
documented `microvm` update flow instead of an automatic host rebuild update.

Validate the flake and dry-build the affected host or VM before starting or
updating runtime services.
